# mogno_app/gui/event_handlers.py
"""
Handlers para eventos da interface gráfica.
"""
import datetime
from threading import Thread
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from core.auth import realizar_login_selenium
from core.serial_management import ler_arquivo_serials  # Suporte a .xlsx, duplicados, colunas
from utils.logger import adicionar_log


class GUIEventHandler:
    """Gerenciador de eventos da GUI"""

    def __init__(self, app_state, signal_manager, main_window):
        self.app_state = app_state
        self.signal_manager = signal_manager
        self.main_window = main_window

    def handle_login_request(self, login, senha, manter_aberto):
        """Processa requisição de login"""

        if not login or not senha:
            self.signal_manager.token_status_updated.emit(
                "Preencha usuário e senha para autenticar.", "red"
            )
            adicionar_log("❌ Login ou senha vazios")
            return

        # Desabilita o botão de login enquanto processa
        self.main_window.login_tab.set_login_button_enabled(False)

        def login_thread():
            try:
                jwt, user_login, user_id, cookie_dict = realizar_login_selenium(
                    login, senha, manter_aberto
                )
                if jwt:
                    self.signal_manager.login_successful.emit(jwt, user_login, user_id, cookie_dict)
                else:
                    self.signal_manager.login_failed.emit(
                        "Erro no login: confira usuário, senha e/ou conexão CEABS (VPN/cabo)"
                    )
            except Exception as e:
                import traceback
                adicionar_log(f"❌ Erro na thread de login: {e}")
                adicionar_log(traceback.format_exc())
                self.signal_manager.login_failed.emit(f"Erro na thread de login: {e}")
            finally:
                self.main_window.login_tab.set_login_button_enabled(True)

        thread = Thread(target=login_thread, daemon=True)
        thread.start()

    def handle_login_successful(self, jwt, user_login, user_id, cookie_dict):
        """Processa login bem-sucedido"""
        self.app_state["jwt_token"] = jwt
        self.app_state["user_login"] = user_login
        self.app_state["user_id"] = user_id
        self.app_state["cookie_dict"] = cookie_dict
        self.app_state["token_expiry"] = datetime.datetime.now() + datetime.timedelta(hours=8)

        expiry_str = self.app_state["token_expiry"].strftime("%d/%m/%Y %H:%M:%S")
        self.signal_manager.token_status_updated.emit(
            f"✅ Token válido até {expiry_str}", "green"
        )

        try:
            self.main_window.show_tabs_after_login()
        except Exception as e:
            adicionar_log(f"❌ Erro ao chamar show_tabs_after_login: {e}")

        adicionar_log(f"✅ Login realizado com sucesso! Usuário: {user_login}")

    def handle_login_failed(self, message):
        """Processa falha no login"""
        self.signal_manager.token_status_updated.emit(message, "red")
        adicionar_log(f"❌ Falha no login: {message}")

    def handle_file_selected(self, filepath):
        """Processa seleção de arquivo"""
        try:
            result = ler_arquivo_serials(filepath)
            self.main_window.equipment_tab.current_serials = result["unicos"]
            self.main_window.equipment_tab.update_serial_status()
            adicionar_log(
                f"📁 Arquivo carregado: {len(result['unicos'])} seriais únicos "
                f"(duplicados removidos: {result['duplicados']})"
            )
        except Exception as e:
            adicionar_log(f"❌ Erro ao carregar arquivo: {e}")
            QMessageBox.critical(self.main_window, "Erro", f"Erro ao carregar arquivo:\n{e}")

    def start_token_check_timer(self):
        """Inicia timer de verificação de token"""
        if not hasattr(self.main_window, "_token_check_timer"):
            self.main_window._token_check_timer = QTimer()
            self.main_window._token_check_timer.timeout.connect(self.check_token_periodically)
            self.main_window._token_check_timer.start(60000)
            adicionar_log("⏰ Timer de verificação de token iniciado")

    def check_token_periodically(self):
        """Verifica periodicamente se o token está válido"""
        if self.app_state["jwt_token"] and self.app_state["token_expiry"]:
            agora = datetime.datetime.now()
            restante = self.app_state["token_expiry"] - agora
            if restante.total_seconds() > 0:
                horas, resto = divmod(int(restante.total_seconds()), 3600)
                minutos, _ = divmod(resto, 60)
                self.signal_manager.token_status_updated.emit(
                    f"Token expira em: {horas}h {minutos}min", "green"
                )
            else:
                self.signal_manager.token_status_updated.emit(
                    "Token expirou. Faça login novamente.", "red"
                )
