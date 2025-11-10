# mogno_app/main.py

import os
import sys
import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor
from gui.toast import ToastNotification
from gui.main_window import MognoMainWindow
from gui.signals import SignalManager
from core.request_handlers import RequestHandler
from core.report_handlers import ReportHandler
from utils.logger import adicionar_log, configurar_componente_logs_qt, limpar_logs
from config.settings import APP_NAME, APP_VERSION

# Importações do novo auth centralizado
from core.auth import (
    iniciar_login_thread,
    handle_login_successful,
    handle_login_failed,
    iniciar_token_check_timer
)

# Limpa o terminal com registros anteriores
os.system('cls')

# Força o Python a incluir a raiz do projeto no caminho de importação
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

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
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    signal_manager = SignalManager()
    main_window = MognoMainWindow(signal_manager)

    request_handler = RequestHandler(app_state, signal_manager)
    report_handler = ReportHandler(app_state, signal_manager, main_window)

    # ========== CONECTAR SINAIS DE LOGIN ==========
    try:
        adicionar_log("🧩 [MAIN] Conectando sinais de login...")

        # Sinal emitido pela LoginTab quando o usuário clica em “Realizar Login”
        main_window.login_tab.login_requested.connect(
            lambda login, senha, manter_aberto: iniciar_login_thread(
                login, senha, manter_aberto, signal_manager, main_window, app_state
            )
        )

        signal_manager.login_successful.connect(
            lambda jwt, user_login, user_id, cookie_dict: handle_login_successful(
                jwt, user_login, user_id, cookie_dict, signal_manager, main_window, app_state
            )
        )

        signal_manager.login_failed.connect(
            lambda message: handle_login_failed(message, signal_manager, main_window)
        )

        signal_manager.token_status_updated.connect(
            main_window.login_tab.update_token_status
        )

        # ✅ NOVO: controla o botão de login de forma thread-safe
        signal_manager.enable_start_button.connect(
            main_window.login_tab.set_login_button_enabled
        )

        adicionar_log("✅ [MAIN] Todos os sinais de login conectados com sucesso")

    except Exception as e:
        adicionar_log(f"❌ [MAIN] Erro ao conectar sinais de login: {e}")

    # ========== CONECTAR SINAIS DE TOASTS ==========  
    signal_manager.show_toast_success.connect(
        lambda msg: ToastNotification(main_window, msg, type="success")
    )
    signal_manager.show_toast_warning.connect(
        lambda msg: ToastNotification(main_window, msg, type="warning")
    )
    signal_manager.show_toast_error.connect(
        lambda msg: ToastNotification(main_window, msg, type="error")
    )
    
   
    # ========== CONECTAR SINAIS DA EQUIPMENTTAB ==========
    signal_manager.request_last_position_api.connect(request_handler.execute_last_position_api)
    signal_manager.request_last_position_redis.connect(request_handler.execute_last_position_redis)
    signal_manager.request_status_equipment.connect(request_handler.execute_status_equipment)
    signal_manager.request_data_consumption.connect(request_handler.execute_data_consumption)
    signal_manager.generate_consolidated_report.connect(report_handler.generate_consolidated_report)
    signal_manager.generate_separate_reports.connect(report_handler.generate_separate_reports)
    signal_manager.csv_file_selected.connect(main_window.equipment_tab.handle_file_selected)

    # ========== CONECTAR SINAIS DA LOGSTAB ==========
    configurar_componente_logs_qt(main_window.logs_tab.get_log_text_edit())
    main_window.logs_tab.clear_logs_requested.connect(limpar_logs)

    # ========== INICIALIZAÇÃO ==========
    adicionar_log("=" * 60)
    adicionar_log(f"🚀 {APP_NAME} - {APP_VERSION}")
    adicionar_log(f"📅 Iniciado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    adicionar_log("=" * 60)

    # Iniciar timer de verificação de token
    iniciar_token_check_timer(main_window, app_state, signal_manager)

    # Login automático se configurado
    if main_window.login_tab.is_auto_login_checked():
        user, pwd, keep = main_window.login_tab.get_login_credentials()
        if user and pwd:
            adicionar_log("🧠 [MAIN] Login automático ativado — agendando tentativa em 500ms")
            QTimer.singleShot(500, lambda: iniciar_login_thread(
                user, pwd, keep, signal_manager, main_window, app_state
            ))

    # Exibir a janela
    main_window.show()

    # Auto disparo do login (se marcado)
    #QTimer.singleShot(2000, lambda: main_window.login_tab._emit_login_request())

    adicionar_log("🟢 [MAIN] Interface exibida — aguardando interações do usuário")

    # Iniciar loop de eventos
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
