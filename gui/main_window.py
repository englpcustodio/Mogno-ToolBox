# gui/main_window.py
"""
Janela principal da aplicação Mogno Toolbox.
Responsável por conectar a interface gráfica (tabs) com a lógica de backend:
- Login e autenticação
- Requisições via API e Redis
- Progresso e logs
- Geração de relatórios
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtCore import QTimer

# Importações principais
from gui.tabs.login_tab import LoginTab
from gui.tabs.equipment_tab import EquipmentTab
from gui.signals import SignalManager
from gui.tabs.events_tab import EventsTab
from core.app_state import AppState
from core.request_handlers import RequestHandler
from core.report_handlers import ReportHandler
from core.auth import AuthManager
from core.credential_manager import CredentialManager
from utils.logger import adicionar_log

class MognoMainWindow(QMainWindow):
    """Janela principal que integra GUI e backend da aplicação."""

    def __init__(self, signal_manager: SignalManager, app_state: AppState):
        super().__init__()
        self.setWindowTitle("Mogno Toolbox")
        self.setGeometry(100, 100, 1200, 800)

        self.signal_manager = signal_manager
        self.app_state = app_state
        self.credential_manager = CredentialManager()

        # Inicializa controladores principais
        self.request_handler = RequestHandler(self.app_state, self.signal_manager)
        self.report_handler = ReportHandler(self.app_state, self.signal_manager, self)
        self.auth_manager = AuthManager(self.signal_manager, self, self.app_state)

        # Inicializa interface
        self._setup_ui()
        self._connect_signals()

        # Esconder abas de funcionalidade até o login
        self.hide_tabs_before_login()

        # Tentar login automático ao iniciar
        QTimer.singleShot(100, self._attempt_auto_login_on_startup)

    # -------------------------------------------------------------------------
    # UI SETUP
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        """Cria as abas principais da interface."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.login_tab = LoginTab(self.signal_manager, self.app_state)
        self.equipment_tab = EquipmentTab(self.app_state)
        self.events_tab = EventsTab(self.app_state, self.signal_manager)  # ✅ NOVO

        self.tabs.addTab(self.login_tab, "🔐 Login")
        self.tabs.addTab(self.equipment_tab, "⚙️ Análise de Equipamentos")
        self.tabs.addTab(self.events_tab, "📋 Análise de Eventos")  # ✅ NOVO
    
    def hide_tabs_before_login(self):
        """Esconde as abas de funcionalidade até o login ser bem-sucedido."""
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) != self.login_tab:
                self.tabs.setTabEnabled(i, False)
        self.tabs.setCurrentWidget(self.login_tab)
        adicionar_log("Abas de funcionalidade desabilitadas. Requer login.")

    def show_tabs_after_login(self):
        """Mostra e habilita as abas de funcionalidade após o login."""
        for i in range(self.tabs.count()):
            self.tabs.setTabEnabled(i, True)
        self.tabs.setCurrentWidget(self.equipment_tab)
        adicionar_log("Abas de funcionalidade habilitadas após login bem-sucedido.")

    # -------------------------------------------------------------------------
    # CONEXÕES DE SINAIS
    # -------------------------------------------------------------------------
    def _connect_signals(self):
        """Conecta todos os sinais da interface à lógica de backend."""

        # LOGIN ---------------------------------------------------------------
        self.login_tab.login_requested.connect(self._handle_login_requested)
        self.signal_manager.login_successful.connect(self._handle_app_state_on_login_success)
        self.signal_manager.login_failed.connect(self._handle_app_state_on_login_failed)
        self.signal_manager.reauthentication_required.connect(self.hide_tabs_before_login)

        # EQUIPAMENTOS --------------------------------------------------------
        self.equipment_tab.start_last_position_api.connect(self.handle_last_position_api)
        self.equipment_tab.start_last_position_redis.connect(self.handle_last_position_redis)
        self.equipment_tab.start_status_equipment.connect(self.handle_status_equipment)
        self.equipment_tab.start_data_consumption.connect(self.handle_data_consumption)

        # ✅ APENAS RELATÓRIOS SEPARADOS
        self.equipment_tab.generate_separate_reports.connect(self.handle_separate_reports)

        self.equipment_tab.file_selected.connect(self.equipment_tab.handle_file_selected)
        self.signal_manager.all_requests_finished.connect(self._handle_all_requests_finished)

        # ✅ NOVO: EVENTOS
        self.events_tab.start_events_request.connect(self.handle_events_request)
        self.events_tab.generate_events_report.connect(self.handle_events_report)
        self.signal_manager.events_request_completed.connect(self.events_tab._handle_request_completed)


        # Progresso geral
        self.signal_manager.equipment_progress_updated.connect(self.update_equipment_progress)

    # -------------------------------------------------------------------------
    # LOGIN HANDLERS
    # -------------------------------------------------------------------------
    def _handle_login_requested(self, username: str, password: str, keep_browser_open: bool, 
                                remember_user: bool, remember_password: bool):
        """Recebe o pedido de login da interface e o repassa ao AuthManager."""
        try:
            adicionar_log(f"🔐 Login solicitado para {username}")
            self.auth_manager.start_login(username, password, keep_browser_open, 
                                         remember_user, remember_password, is_auto_login=False)
        except Exception as e:
            adicionar_log(f"❌ Erro ao processar login: {e}")
            self.signal_manager.show_toast_error.emit(f"Erro ao iniciar o login: {e}")
            self.signal_manager.token_status_updated.emit("Erro ao iniciar o login.", "red")
            self.signal_manager.enable_start_button.emit(True)

    def _handle_app_state_on_login_success(self, token, user_login, user_id, cookie_dict):
        """Atualiza o estado da aplicação após login bem-sucedido."""
        adicionar_log(f"✅ Login bem-sucedido — Usuário: {user_login}")
        self.login_tab.registrar_login_sucesso()

        remember_user, remember_password = self.login_tab.get_remember_options()
        is_auto_login = self.login_tab.is_auto_login_checked()

        self.app_state.set("last_login_credentials", {
            "username": user_login,
            "password": self.login_tab.entry_senha.text().strip() if remember_password else "",
            "remember_user": remember_user,
            "remember_password": remember_password,
            "auto_login": is_auto_login
        })

    def _handle_app_state_on_login_failed(self, msg):
        """Lida com a falha de login."""
        adicionar_log(f"❌ Falha no login: {msg}")

    def _attempt_auto_login_on_startup(self):
        """Tenta realizar login automático ao iniciar a aplicação."""
        username, password, remember_user, remember_password = self.credential_manager.load_credentials()
        last_login_options = self.app_state.get("last_login_credentials", {})

        if not username and not password:
            adicionar_log("ℹ️ Nenhuma credencial salva. Aguardando login manual.")
            return

        if username and password and remember_user and remember_password and last_login_options.get("auto_login"):
            adicionar_log("🚀 Tentando login automático ao iniciar...")
            self.auth_manager.start_auto_login()
            return

        adicionar_log("ℹ️ Credenciais incompletas. Aguardando login manual.")

    # -------------------------------------------------------------------------
    # REQUISIÇÕES - API E REDIS
    # -------------------------------------------------------------------------
    def handle_last_position_api(self, api_type: str, serials: list):
        """Inicia a requisição de últimas posições via API Mogno."""
        adicionar_log(f"🚀 Requisição de últimas posições ({api_type}) iniciada para {len(serials)} seriais.")
        self._mark_request_start("last_position_api")
        self.request_handler.execute_last_position_api(api_type, serials)

    def handle_last_position_redis(self, serials: list):
        """Inicia a requisição de últimas posições via Redis."""
        adicionar_log(f"🚀 Requisição de últimas posições via Redis iniciada ({len(serials)} seriais).")
        self._mark_request_start("last_position_redis")
        self.request_handler.execute_last_position_redis(serials)

    def handle_status_equipment(self, serials: list):
        """Inicia a requisição de status dos equipamentos."""
        adicionar_log(f"🚀 Requisição de status iniciada ({len(serials)} seriais).")
        self._mark_request_start("status_equipment")
        self.request_handler.execute_status_equipment(serials)

    def handle_data_consumption(self, month: str, year: str):
        """Inicia a requisição de consumo de dados."""
        adicionar_log(f"🚀 Requisição de consumo de dados {month}/{year} iniciada.")
        self._mark_request_start("data_consumption")
        self.request_handler.execute_data_consumption(month, year)


    def handle_events_request(self, serials, start_dt, end_dt, event_filters):
        """Inicia requisição de eventos com multithread."""
        adicionar_log(f"🚀 Requisição de eventos iniciada para {len(serials)} seriais.")
        self._mark_request_start("events")

        # ✅ Define número de workers baseado na quantidade de seriais
        max_workers = min(10, max(2, len(serials) // 10))  # Entre 2 e 10 workers
        adicionar_log(f"🧵 Usando {max_workers} threads para processar {len(serials)} seriais")

        self.request_handler.execute_events_request(
            serials, 
            start_dt, 
            end_dt, 
            event_filters,
            max_workers=max_workers  # ✅ Passa número de workers
        )

    # -------------------------------------------------------------------------
    # RELATÓRIOS
    # -------------------------------------------------------------------------
    def handle_separate_reports(self, options: dict):
        """Gera relatórios separados por tipo de requisição."""
        adicionar_log("📁 Gerando relatórios...")
        self.report_handler.generate_reports(options)  # ← Chama o método unificado

    # Handler para geração de relatório de eventos
    def handle_events_report(self, data):
        """Gera relatório de eventos."""
        #adicionar_log("📊 Gerando relatório de eventos...")
        self.report_handler.generate_events_report(data)


    # -------------------------------------------------------------------------
    # PROGRESSO / CONTROLE DE EXECUÇÃO
    # -------------------------------------------------------------------------
    def update_equipment_progress(self, current: int, total: int, label: str):
        """Atualiza o progresso da aba de equipamentos."""
        try:
            self.equipment_tab.progress_bar.setValue(int((current / total) * 100))
            self.equipment_tab.progress_status_label.setText(f"{label} ({current}/{total})")
        except Exception as e:
            adicionar_log(f"⚠️ Erro ao atualizar progresso: {e}")

    # -------------------------------------------------------------------------
    # UTILITÁRIOS
    # -------------------------------------------------------------------------
    def _mark_request_start(self, name: str):
        """Marca o início de uma requisição."""
        adicionar_log(f"🔄 Iniciando execução para [{name}].")
        self.app_state.set("request_in_progress", True)

    def _handle_all_requests_finished(self):
        """Marca o término de todas as requisições."""
        self._mark_request_done("all_requests")
        self.equipment_tab.mark_requests_finished()  # ← HABILITA O BOTÃO

    def _mark_request_done(self, name: str):
        """Marca o término de uma requisição."""
        #adicionar_log(f"✅ Execução concluída para [{name}].")
        self.app_state.set("request_in_progress", False)

    def closeEvent(self, event):
        """Sobrescreve o evento de fechamento para encerrar o driver Selenium."""
        adicionar_log("Fechando aplicação. Encerrando driver Selenium, se ativo.")
        if hasattr(self, 'auth_manager'):
            self.auth_manager.close_driver()
        super().closeEvent(event)


# -------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# -------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    signal_manager = SignalManager()
    app_state = AppState()
    window = MognoMainWindow(signal_manager, app_state)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
