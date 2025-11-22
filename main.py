# main.py

import os
import sys
import datetime
from PyQt5.QtWidgets import QApplication

# Imports da interface
from gui.main_window import MognoMainWindow
from gui.signals import SignalManager
from gui.widgets.widgets import ToastNotification

# Núcleo do sistema
from core.app_state import AppState
from core.auth import AuthManager

# Utilidades
from utils.logger import adicionar_log
from utils.helpers import clean_pycache

# Configurações globais
from config.settings import APP_NAME, APP_VERSION

# -------------------------------------------------------------------------
# Inicialização
# -------------------------------------------------------------------------

# Limpa terminal
os.system('cls')

# Garante que o diretório raiz está no caminho de importação
#sys.path.append(os.path.abspath(os.path.dirname(__file__)))

#Exclui todos os dados de cache (__pycache__)
clean_pycache()

# Estado global da aplicação
app_state = AppState()

# -------------------------------------------------------------------------

def main():
    """Função principal da aplicação Mogno Toolbox."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Ignora warnings de depreciação
    #warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Inicializa gerenciadores principais
    signal_manager = SignalManager()
    main_window = MognoMainWindow(signal_manager, app_state)
    auth_manager = AuthManager(signal_manager, main_window, app_state)
    main_window.auth_manager = auth_manager

    # ---------------------------------------------------------------------
    # Autenticação
    # ---------------------------------------------------------------------
    signal_manager.login_successful.connect(
        lambda token, ulogin, uid, c: auth_manager.handle_login_successful(token, ulogin, uid, c)
    )
    signal_manager.login_failed.connect(
        lambda msg: auth_manager.handle_login_failed(msg)
    )

    # ---------------------------------------------------------------------
    # Toasts (notificações)
    # ---------------------------------------------------------------------
    signal_manager.show_toast_success.connect(
        lambda msg: ToastNotification(main_window, msg, type="success")
    )

    signal_manager.show_toast_warning.connect(
        lambda msg: ToastNotification(main_window, msg, type="warning")
    )

    signal_manager.show_toast_error.connect(
        lambda msg: ToastNotification(main_window, msg, type="error")
    )

    signal_manager.show_toast.connect(
        lambda msg, tipo: ToastNotification(main_window, msg, type=tipo)
    )

    # ---------------------------------------------------------------------
    # Inicialização visual
    # ---------------------------------------------------------------------
    adicionar_log("=" * 60)
    adicionar_log(f"🚀 {APP_NAME} - {APP_VERSION}")
    adicionar_log(f"📅 Iniciado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    adicionar_log("=" * 60)

    # Exibir a janela
    main_window.show()

    # Iniciar o loop de eventos
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
