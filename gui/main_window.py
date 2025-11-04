# mogno_app/gui/main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QMessageBox, QFileDialog, QVBoxLayout
)
from PyQt5.QtCore import Qt, QTimer

from gui.login_tab import LoginTab
from gui.equipment_tab import EquipmentTab
from gui.events_tab import EventsTab
from gui.commands_tab import CommandsTab
from gui.health_tab import HealthTab
from gui.scheduler_tab import SchedulerTab
from gui.logs_tab import LogsTab
from gui.about_tab import AboutTab

from gui.signals import SignalManager
from config.settings import APP_NAME, APP_VERSION
from utils.logger import adicionar_log
from utils.gui_utils import log_message, update_progress, set_execution_complete

from reports.gerar_relatorio_ultima_pos import relatorio_ultimaposicao_excel
from reports.gerar_relatorio_status_maxtrack import relatorio_status_excel
from reports.gerar_relatorio_trafegodados import relatorio_trafegodados_excel

class MognoMainWindow(QMainWindow):
    def __init__(self, signal_manager):
        super().__init__()
        print("🟦 [CONSOLE] MognoMainWindow.__init__ chamado")

        self.signal_manager = signal_manager
        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.resize(1200, 900)
        self.setMinimumSize(1100, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        print("🟦 [CONSOLE] Criando abas...")
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

        # Conectar sinais
        print("🟦 [CONSOLE] Conectando sinais...")
        self.signal_manager.token_status_updated.connect(self.login_tab.update_token_status)
        
        # Sinais da EquipmentTab
        self.equipment_tab.file_selected.connect(self.handle_file_selected)
        self.equipment_tab.start_last_position_api.connect(self.handle_last_position_api)
        self.equipment_tab.start_last_position_redis.connect(self.handle_last_position_redis)
        self.equipment_tab.start_status_equipment.connect(self.handle_status_equipment)
        self.equipment_tab.start_data_consumption.connect(self.handle_data_consumption)
        self.equipment_tab.generate_consolidated_report.connect(self.handle_consolidated_report)
        self.equipment_tab.generate_separate_reports.connect(self.handle_separate_reports)
       
        # Conectar sinais de progresso e conclusão
        self.signal_manager.equipment_progress_updated.connect(self.update_equipment_progress)
        self.signal_manager.last_position_completed.connect(lambda _: self.set_equipment_execution_complete(True))
        self.signal_manager.status_equipment_completed.connect(lambda _: self.set_equipment_execution_complete(True))
        self.signal_manager.data_consumption_completed.connect(lambda _: self.set_equipment_execution_complete(True))
        self.signal_manager.generate_consolidated_report.connect(self.handle_generate_consolidated_report)

        # Sinais da SchedulerTab
        self.scheduler_tab.scheduler_saved.connect(self.handle_scheduler_saved)
        self.scheduler_tab.scheduler_deleted.connect(self.handle_scheduler_deleted)
        self.scheduler_tab.scheduler_enabled_changed.connect(self.handle_scheduler_enabled_changed)

        self.requisicoes_concluidas = False # garantir que as requisições foram concluídas

        adicionar_log("✅ Interface principal inicializada")

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
        adicionar_log("✅ Abas habilitadas após login")

    # ========== Handlers ==========
    def handle_file_selected(self, filepath):
        """Processa arquivo CSV/Excel selecionado"""
        from core.serial_management import ler_arquivo_serials
        try:
            result = ler_arquivo_serials(filepath)
            self.equipment_tab.current_serials = result["unicos"]
            self.equipment_tab.update_serial_status()
            adicionar_log(f"📁 Arquivo carregado: {len(result['unicos'])} seriais únicos")
            log_message(
                self.scheduler_tab.logs_text,
                f"✅ {len(result['unicos'])} seriais únicos carregados (duplicados removidos: {result['duplicados']})"
            )
        except Exception as e:
            adicionar_log(f"❌ Erro ao carregar arquivo: {e}")
            log_message(self.scheduler_tab.logs_text, f"❌ Erro ao carregar arquivo: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar arquivo:\n{e}")

    def handle_last_position_api(self, api_type, serials):
        adicionar_log(f"🚀 Iniciando via API Mogno ({api_type})")
        log_message(self.scheduler_tab.logs_text, f"🚀 Requisição via API Mogno ({api_type}) iniciada")
        self.signal_manager.request_last_position_api.emit(api_type, serials)

    def handle_last_position_redis(self, serials):
        adicionar_log("🚀 Iniciando via Redis")
        log_message(self.scheduler_tab.logs_text, "🚀 Requisição via Redis iniciada")
        self.signal_manager.request_last_position_redis.emit(serials)

    def handle_status_equipment(self, serials):
        adicionar_log("🚀 Status dos equipamentos (Maxtrack)")
        log_message(self.scheduler_tab.logs_text, "🚀 Requisição de status iniciada")
        self.signal_manager.request_status_equipment.emit(serials)

    def handle_data_consumption(self, serials, month, year):
        adicionar_log(f"🚀 Consumo de dados {month}/{year}")
        log_message(self.scheduler_tab.logs_text, f"🚀 Requisição de consumo ({month}/{year}) iniciada")
        self.signal_manager.request_data_consumption.emit(serials, month, year)

    def handle_consolidated_report(self, opcoes):
        adicionar_log("📊 Gerando relatório consolidado")
        log_message(self.scheduler_tab.logs_text, "📊 Gerando relatório consolidado...")
        self.signal_manager.generate_consolidated_report.emit(opcoes)

    def handle_generate_consolidated_report(self, opcoes):
        """Gera relatório consolidado com base nas opções selecionadas"""

        serials = opcoes.get("serials", [])
        dados = self.app_state.get("dados_atuais", {})

        if "last_position" in opcoes["enabled_queries"]:
            resultados = dados.get("last_position_redis", [])
            relatorio_ultimaposicao_excel(serials, resultados)

        if "status_equipment" in opcoes["enabled_queries"]:
            resultados = dados.get("status_equipment", [])
            relatorio_status_excel(serials, resultados)

        if "data_consumption" in opcoes["enabled_queries"]:
            resultados = dados.get("data_consumption", {})
            relatorio_trafegodados_excel(resultados)

        adicionar_log("📁 Relatórios gerados com sucesso.")
        log_message(self.scheduler_tab.logs_text, "📁 Relatórios gerados com sucesso.")

        def mostrar_mensagem():
                QMessageBox.information(self, "Relatórios Gerados", "📁 Relatórios gerados com sucesso!")
        QTimer.singleShot(0, mostrar_mensagem)

    def handle_separate_reports(self, opcoes):
        adicionar_log("📊 Gerando relatórios separados")
        log_message(self.scheduler_tab.logs_text, "📊 Gerando relatórios separados...")
        self.signal_manager.generate_separate_reports.emit(opcoes)

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

    # ========== Auxiliares ==========
    def update_equipment_progress(self, current, total, status_text="Processando..."):
        update_progress(self.equipment_tab.progress_bar,
                        self.equipment_tab.progress_status_label,
                        current, total, status_text)

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
        """Adiciona mensagem aos logs da SchedulerTab"""
        log_message(self.scheduler_tab.logs_text, message)
