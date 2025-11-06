# mogno_app/main.py

import os
import sys
import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import qRegisterMetaType, QTimer

# Importações da GUI
from gui.main_window import MognoMainWindow
from gui.signals import SignalManager

# Importações dos handlers
from gui.event_handlers import GUIEventHandler
from core.request_handlers import RequestHandler
from core.report_handlers import ReportHandler

# Importações de utilitários
from utils.logger import adicionar_log, configurar_componente_logs_qt, limpar_logs
from config.settings import APP_NAME, APP_VERSION

os.system('cls')  # Limpa o terminal com registros anteriores.

# Estado global da aplicação
app_state = {
    "executando_requisicoes": False,
    "tempo_inicio_requisicoes": None,
    "jwt_token": None,
    "user_login": None,
    "user_id": None,
    "token_expiry": None,
    "cookie_dict": None,
    "serials_carregados": [],
    "csv_filepath": None,
    "dados_atuais": {},
    "scheduler": None
}

def main():
    """Função principal da aplicação"""
    # Criar aplicação PyQt
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Suprimir avisos não-críticos do Qt no console
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Criar gerenciador de sinais
    signal_manager = SignalManager()
    
    # Criar janela principal
    main_window = MognoMainWindow(signal_manager)
    
    # Criar handlers
    gui_handler = GUIEventHandler(app_state, signal_manager, main_window)
    request_handler = RequestHandler(app_state, signal_manager)
    report_handler = ReportHandler(app_state, signal_manager, main_window)
    
    # ========== CONECTAR SINAIS DE LOGIN ==========
    try:
        main_window.login_tab.login_requested.connect(gui_handler.handle_login_request)
        signal_manager.login_successful.connect(gui_handler.handle_login_successful)
        signal_manager.login_failed.connect(gui_handler.handle_login_failed)
        signal_manager.token_status_updated.connect(main_window.login_tab.update_token_status)
    except Exception as e:
        adicionar_log(f"❌ Erro ao conectar sinais de login: {e}")
    
    # ========== CONECTAR SINAIS DA EQUIPMENTTAB ==========
    signal_manager.request_last_position_api.connect(request_handler.execute_last_position_api)
    signal_manager.request_last_position_redis.connect(request_handler.execute_last_position_redis)
    signal_manager.request_status_equipment.connect(request_handler.execute_status_equipment)
    signal_manager.request_data_consumption.connect(request_handler.execute_data_consumption)
    signal_manager.generate_consolidated_report.connect(report_handler.generate_consolidated_report)
    signal_manager.generate_separate_reports.connect(report_handler.generate_separate_reports)
    signal_manager.csv_file_selected.connect(gui_handler.handle_file_selected)
    
    # ========== CONECTAR SINAIS DA LOGSTAB ==========
    configurar_componente_logs_qt(main_window.logs_tab.get_log_text_edit())
    main_window.logs_tab.clear_logs_requested.connect(limpar_logs)
    
    # ========== INICIALIZAÇÃO ==========
    adicionar_log("=" * 60)
    adicionar_log(f"🚀 {APP_NAME} - {APP_VERSION}")
    adicionar_log(f"📅 Iniciado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    adicionar_log("=" * 60)
    
    # Iniciar timer de verificação de token
    gui_handler.start_token_check_timer()
    
    # Login automático se configurado
    if main_window.login_tab.is_auto_login_checked():
        user, pwd, keep = main_window.login_tab.get_login_credentials()
        if user and pwd:
            QTimer.singleShot(500, lambda: gui_handler.handle_login_request(user, pwd, keep))
    
    # Exibir a janela
    main_window.show()
    
    # Iniciar loop de eventos
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
