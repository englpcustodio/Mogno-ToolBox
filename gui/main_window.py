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
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget)

# Importações principais
from gui.login_tab import LoginTab
from gui.equipment_tab import EquipmentTab
from gui.signals import SignalManager
from core.app_state import AppState
from core.request_handlers import RequestHandler
from core.report_handlers import ReportHandler
from utils.logger import adicionar_log

class MognoMainWindow(QMainWindow):
    """Janela principal que integra GUI e backend da aplicação."""
    def __init__(self, signal_manager: SignalManager, app_state: AppState):
        super().__init__()
        self.setWindowTitle("Mogno Toolbox")
        self.setGeometry(100, 100, 1200, 800)
        
        self.signal_manager = signal_manager
        self.app_state = app_state

        # Inicializa controladores principais
        self.request_handler = RequestHandler(self.app_state, self.signal_manager)
        self.report_handler = ReportHandler(self.app_state, self.signal_manager, self)

        # Inicializa interface
        self._setup_ui()
        self._connect_signals()

    # -------------------------------------------------------------------------
    # UI SETUP
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        """Cria as abas principais da interface."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Login e aba de equipamentos
        self.login_tab = LoginTab(self.signal_manager, self.app_state)
        self.equipment_tab = EquipmentTab(self.app_state)

        # Adiciona abas
        self.tabs.addTab(self.login_tab, "🔐 Login")
        self.tabs.addTab(self.equipment_tab, "⚙️ Análise de Equipamentos")

    # -------------------------------------------------------------------------
    # CONEXÕES DE SINAIS
    # -------------------------------------------------------------------------
    def _connect_signals(self):
        """Conecta todos os sinais da interface à lógica de backend."""

        # LOGIN ---------------------------------------------------------------
        self.login_tab.login_requested.connect(self._handle_login_requested)
        self.signal_manager.login_successful.connect(self._handle_login_success)
        self.signal_manager.login_failed.connect(self._handle_login_failed)

        # EQUIPAMENTOS --------------------------------------------------------
        self.equipment_tab.start_last_position_api.connect(self.handle_last_position_api)
        self.equipment_tab.start_last_position_redis.connect(self.handle_last_position_redis)
        self.equipment_tab.start_status_equipment.connect(self.handle_status_equipment)
        self.equipment_tab.start_data_consumption.connect(self.handle_data_consumption)
        self.equipment_tab.generate_separate_reports.connect(self.handle_separate_reports)
        self.equipment_tab.file_selected.connect(self.equipment_tab.handle_file_selected)
        self.signal_manager.all_requests_finished.connect(self.equipment_tab.mark_requests_finished)

        # Progresso geral
        self.signal_manager.equipment_progress_updated.connect(self.update_equipment_progress)

    # -------------------------------------------------------------------------
    # LOGIN HANDLERS
    # -------------------------------------------------------------------------
    def _handle_login_requested(self, username: str, password: str, keep_browser_open: bool):
        """Recebe o pedido de login da interface e o repassa ao AuthManager."""
        try:
            adicionar_log(f"🔐 Login solicitado para {username}")
            self.auth_manager.start_login(username, password, keep_browser_open)
        except Exception as e:
            adicionar_log(f"❌ Erro ao processar login: {e}")
            self.login_tab.update_token_status("Erro ao iniciar o login.", "red")
            self.login_tab.set_login_button_enabled(True)

    def _handle_login_success(self, token, username):
        adicionar_log(f"✅ Login bem-sucedido — Usuário: {username}")
        self.login_tab.registrar_login_sucesso()
        self.app_state.set("jwt_token", token)
        self.app_state.set("usuario_logado", username)
    
    def _handle_login_failed(self, msg):
        adicionar_log(f"❌ Falha no login: {msg}")
        self.login_tab.update_token_status(f"Erro: {msg}", "red")
        self.login_tab.set_login_button_enabled(True)

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
        """ Inicia a requisição de consumo de dados. Não requer seriais; usa apenas mês e ano. """
        adicionar_log(f"🚀 Requisição de consumo de dados {month}/{year} iniciada.")
        self._mark_request_start("data_consumption")
        self.request_handler.execute_data_consumption(month, year)

    # -------------------------------------------------------------------------
    # RELATÓRIOS
    # -------------------------------------------------------------------------
    def handle_separate_reports(self, options: dict):
        """Gera relatórios separados por tipo de requisição."""
        adicionar_log("📁 Gerando relatórios separados...")
        self.report_handler.generate_separate_reports(options)

    # -------------------------------------------------------------------------
    # PROGRESSO / CONTROLE DE EXECUÇÃO
    # -------------------------------------------------------------------------
    def update_equipment_progress(self, *args):
        """
        Atualiza o progresso da aba de equipamentos.
        Aceita formatos variados de sinal (current, total, label).
        """
        try:
            if len(args) == 3:
                current, total, label = args
                self.equipment_tab.progress_bar.setValue(int((current / total) * 100))
                self.equipment_tab.progress_status_label.setText(f"{label} ({current}/{total})")
            elif len(args) == 2:
                current, total = args
                self.equipment_tab.progress_bar.setValue(int((current / total) * 100))
            elif len(args) == 1:
                current = args[0]
                self.equipment_tab.progress_bar.setValue(int(current))
        except Exception as e:
            adicionar_log(f"⚠️ Erro ao atualizar progresso: {e}")

    # -------------------------------------------------------------------------
    # UTILITÁRIOS
    # -------------------------------------------------------------------------
    def _mark_request_start(self, name: str):
        """Marca o início de uma requisição."""
        adicionar_log(f"🔄 Iniciando execução para [{name}].")
        self.app_state.set("request_in_progress", True)

    def _mark_request_done(self, name: str):
        """Marca o término de uma requisição."""
        adicionar_log(f"✅ Execução concluída para [{name}].")
        self.app_state.set("request_in_progress", False)

# -------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL (opcional para testes)
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
