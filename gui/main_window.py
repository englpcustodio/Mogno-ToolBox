# mogno_app/gui/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QMessageBox, QFileDialog, QVBoxLayout
)
from PyQt5.QtCore import Qt, QTimer

from config.settings import APP_NAME, APP_VERSION
from core.serial_management import ler_arquivo_serials
from gui.login_tab import LoginTab
from gui.equipment_tab import EquipmentTab
from gui.events_tab import EventsTab
from gui.commands_tab import CommandsTab
from gui.health_tab import HealthTab
from gui.scheduler_tab import SchedulerTab
from gui.logs_tab import LogsTab
from gui.about_tab import AboutTab
from gui.signals import SignalManager
from gui.toast import ToastNotification
from utils.logger import adicionar_log
from utils.gui_utils import log_message, update_progress, set_execution_complete
from reports.gerar_relatorio_ultima_pos import relatorio_ultimaposicao_excel
from reports.gerar_relatorio_status_maxtrack import relatorio_status_excel
from reports.gerar_relatorio_trafegodados import relatorio_trafegodados_excel


class MognoMainWindow(QMainWindow):
    def __init__(self, signal_manager):
        super().__init__()

        self.signal_manager = signal_manager

        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.resize(1200, 900)
        self.setMinimumSize(1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.login_tab = LoginTab()
        self.equipment_tab = EquipmentTab()
        self.scheduler_tab = SchedulerTab()
        self.events_tab = EventsTab()
        self.commands_tab = CommandsTab()
        self.health_tab = HealthTab()
        self.logs_tab = LogsTab()
        self.about_tab = AboutTab()

        self.tab_widget.addTab(self.login_tab, "🔐 Login Mogno")

        self.app_state = {
            "dados_atuais": {},
            "scheduler": None
        }

        # Controle interno de requisições (nomes de tarefas em andamento)
        self.active_requests = set()
        self.requisicoes_concluidas = False

        # ===================== CONEXÕES DE SINAIS ===================== #
        self.signal_manager.token_status_updated.connect(self.login_tab.update_token_status)

        # Sinais da aba EquipmentTab
        self.equipment_tab.file_selected.connect(self.handle_file_selected)
        self.equipment_tab.start_last_position_api.connect(self.handle_last_position_api)
        self.equipment_tab.start_last_position_redis.connect(self.handle_last_position_redis)
        self.equipment_tab.start_status_equipment.connect(self.handle_status_equipment)
        self.equipment_tab.start_data_consumption.connect(self.handle_data_consumption)
        self.equipment_tab.generate_consolidated_report.connect(self.handle_consolidated_report)
        self.equipment_tab.generate_separate_reports.connect(self.handle_separate_reports)

        # Progresso e finalização
        self.signal_manager.equipment_progress_updated.connect(self.update_equipment_progress)
        self.signal_manager.last_position_completed.connect(lambda *_: self._mark_request_done("last_position"))
        self.signal_manager.status_equipment_completed.connect(lambda *_: self._mark_request_done("status_equipment"))
        self.signal_manager.data_consumption_completed.connect(lambda *_: self._mark_request_done("data_consumption"))

        # Falhas também devem marcar requisição como encerrada
        self.signal_manager.request_failed.connect(lambda msg: self._handle_request_failure(msg))

        # Toasts e relatórios
        self.signal_manager.generate_consolidated_report.connect(self.handle_generate_consolidated_report)
        self.signal_manager.show_toast.connect(lambda msg, tipo: ToastNotification(self, msg, type=tipo))

        # Sinais da aba Scheduler
        self.scheduler_tab.scheduler_saved.connect(self.handle_scheduler_saved)
        self.scheduler_tab.scheduler_deleted.connect(self.handle_scheduler_deleted)
        self.scheduler_tab.scheduler_enabled_changed.connect(self.handle_scheduler_enabled_changed)

    # ===================== ABA LOGIN ===================== #
    def show_tabs_after_login(self):
        """Exibe todas as abas após login"""
        self.tab_widget.clear()
        self.tab_widget.addTab(self.login_tab, "🔐 Login Mogno")
        self.tab_widget.addTab(self.equipment_tab, "🔍 Análise de Equipamentos")
        self.tab_widget.addTab(self.events_tab, "📊 Análise de Eventos")
        self.tab_widget.addTab(self.commands_tab, "⚙️ Gestão de Comandos")
        self.tab_widget.addTab(self.health_tab, "🩺 Saúde da Base")
        self.tab_widget.addTab(self.scheduler_tab, "⏱️ Agendador de Tarefas")
        self.tab_widget.addTab(self.logs_tab, "📋 Logs")
        self.tab_widget.addTab(self.about_tab, "ℹ️ Sobre")
        self.tab_widget.setCurrentIndex(1)

    # ===================== CONTROLE DE REQUISIÇÕES ===================== #
    def _mark_request_start(self, name: str):
        """Marca uma requisição como iniciada"""
        self.active_requests.add(name)
        self.requisicoes_concluidas = False
        try:
            self.equipment_tab.btn_generate_report.setEnabled(False)
        except Exception:
            pass
        adicionar_log(f"🟡 Iniciada requisição: {name} — active: {self.active_requests}")

    def _mark_request_done(self, name: str):
        """Marca uma requisição como concluída. Habilita relatório quando não houver mais requisições."""
        if name in self.active_requests:
            self.active_requests.remove(name)
            adicionar_log(f"✅ Requisição finalizada: {name} — restantes: {self.active_requests}")

        # Se não há mais requisições pendentes, considerar tudo concluído
        if not self.active_requests:
            self.requisicoes_concluidas = True
            adicionar_log("✅ Todas as requisições foram concluídas (flag atualizado).")

            try:
                # Atualiza UI de forma garantida no thread principal
                def atualizar_ui():
                    if hasattr(self.equipment_tab, "btn_generate_report"):
                        self.equipment_tab.btn_generate_report.setEnabled(True)
                    if hasattr(self.equipment_tab, "btn_pause_requests"):
                        self.equipment_tab.btn_pause_requests.setEnabled(False)
                    if hasattr(self.equipment_tab, "btn_cancel_requests"):
                        self.equipment_tab.btn_cancel_requests.setEnabled(False)
                    if hasattr(self.equipment_tab, "progress_status_label"):
                        self.equipment_tab.progress_status_label.setText("✅ Requisições concluídas.")

                QTimer.singleShot(0, atualizar_ui)
            except Exception as e:
                adicionar_log(f"⚠️ Erro ao atualizar UI pós-requisição: {e}")


    def _handle_request_failure(self, message: str):
        """Trata falhas sem travar o ciclo de finalização"""
        adicionar_log(f"❌ Falha em requisição: {message}")
        # Pode haver múltiplas requisições, não sabemos qual falhou,
        # então consideramos todas concluídas se não restar nenhuma ativa
        if self.active_requests:
            # Retira uma qualquer (não sabemos qual falhou)
            _ = self.active_requests.pop()
        if not self.active_requests:
            self._mark_request_done("erro_desconhecido")

    # ===================== HANDLERS DAS REQUISIÇÕES ===================== #
    def handle_file_selected(self, filepath):
        try:
            result = ler_arquivo_serials(filepath)
            self.equipment_tab.current_serials = result["unicos"]
            self.equipment_tab.update_serial_status()
            log_message(self.scheduler_tab.logs_text,
                        f"✅ {len(result['unicos'])} seriais únicos carregados (duplicados removidos: {result['duplicados']})")
        except Exception as e:
            adicionar_log(f"❌ Erro ao carregar arquivo: {e}")
            log_message(self.scheduler_tab.logs_text, f"❌ Erro ao carregar arquivo: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar arquivo:\n{e}")

    def handle_last_position_api(self, api_type, serials):
        adicionar_log(f"🚀 Iniciando via API Mogno ({api_type})")
        log_message(self.scheduler_tab.logs_text, f"🚀 Requisição via API Mogno ({api_type}) iniciada")
        self._mark_request_start("last_position")
        self.signal_manager.request_last_position_api.emit(api_type, serials)

    def handle_last_position_redis(self, serials):
        adicionar_log("🚀 Iniciando via Redis (Últimas Posições)")
        log_message(self.scheduler_tab.logs_text, "🚀 Requisição via Redis iniciada")
        self._mark_request_start("last_position")
        self.signal_manager.request_last_position_redis.emit(serials)

    def handle_status_equipment(self, serials):
        adicionar_log("🚀 Status dos equipamentos (Maxtrack)")
        log_message(self.scheduler_tab.logs_text, "🚀 Requisição de status iniciada")
        self._mark_request_start("status_equipment")
        self.signal_manager.request_status_equipment.emit(serials)

    def handle_data_consumption(self, serials, month, year):
        adicionar_log(f"🚀 Consumo de dados {month}/{year}")
        log_message(self.scheduler_tab.logs_text, f"🚀 Requisição de consumo ({month}/{year}) iniciada")
        self._mark_request_start("data_consumption")
        self.signal_manager.request_data_consumption.emit(serials, month, year)

    # ===================== RELATÓRIOS ===================== #
    def handle_consolidated_report(self, opcoes):
        adicionar_log("📊 Gerando relatório consolidado")
        log_message(self.scheduler_tab.logs_text, "📊 Gerando relatório consolidado...")
        self.signal_manager.generate_consolidated_report.emit(opcoes)

    def handle_generate_consolidated_report(self, opcoes):
        serials = opcoes.get("serials", [])
        dados = self.app_state.get("dados_atuais", {})

        if "last_position" in opcoes["enabled_queries"]:
            relatorio_ultimaposicao_excel(serials, dados.get("last_position_redis", []))

        if "status_equipment" in opcoes["enabled_queries"]:
            relatorio_status_excel(serials, dados.get("status_equipment", []))

        if "data_consumption" in opcoes["enabled_queries"]:
            relatorio_trafegodados_excel(dados.get("data_consumption", {}))

        adicionar_log("📁 Relatórios gerados com sucesso.")
        log_message(self.scheduler_tab.logs_text, "📁 Relatórios gerados com sucesso.")
        QTimer.singleShot(0, lambda: QMessageBox.information(self, "Relatórios Gerados", "📁 Relatórios gerados com sucesso!"))

    def handle_separate_reports(self, opcoes):
        adicionar_log("📊 Gerando relatórios separados")
        log_message(self.scheduler_tab.logs_text, "📊 Gerando relatórios separados...")
        self.signal_manager.generate_separate_reports.emit(opcoes)

    # ===================== AGENDADOR ===================== #
    def handle_scheduler_saved(self, scheduler_config):
        adicionar_log(f"📅 Agendamento salvo: {scheduler_config.get('type', 'unknown')}")
        log_message(self.scheduler_tab.logs_text, "✅ Agendamento salvo")
        self.signal_manager.scheduler_saved.emit(scheduler_config)

    def handle_scheduler_deleted(self, scheduler_id):
        adicionar_log(f"🗑️ Agendamento removido: {scheduler_id}")
        log_message(self.scheduler_tab.logs_text, "🗑️ Agendamento removido")
        self.signal_manager.scheduler_deleted.emit(scheduler_id)

    def handle_scheduler_enabled_changed(self, enabled):
        status = "habilitado" if enabled else "desabilitado"
        adicionar_log(f"⏱️ Agendamento {status}")
        log_message(self.scheduler_tab.logs_text, f"⏱️ Agendamento {status}")

    # ===================== AUXILIARES ===================== #
    def update_equipment_progress(self, current, total, status_text="Processando..."):
        update_progress(
            self.equipment_tab.progress_bar,
            self.equipment_tab.progress_status_label,
            current, total, status_text
        )

    def set_equipment_execution_complete(self, success=True):
        self.requisicoes_concluidas = success
        set_execution_complete(
            self.equipment_tab.btn_start_requests,
            self.equipment_tab.btn_pause_requests,
            self.equipment_tab.btn_cancel_requests,
            self.equipment_tab.btn_generate_report,
            self.equipment_tab.progress_status_label,
            success
        )

    def log_to_scheduler_tab(self, message):
        log_message(self.scheduler_tab.logs_text, message)
