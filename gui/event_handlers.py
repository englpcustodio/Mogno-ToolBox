# mogno_app/gui/event_handlers.py
"""
Handlers para eventos da interface gráfica.
"""
import datetime
from threading import Thread
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from core.auth import realizar_login_selenium
from core.serial_management import ler_arquivo_serials  # Atualizado para nova função (suporte a .xlsx, duplicados, colunas)
from utils.logger import adicionar_log

class GUIEventHandler:
    """Gerenciador de eventos da GUI"""
    def __init__(self, app_state, signal_manager, main_window):
        self.app_state = app_state
        self.signal_manager = signal_manager
        self.main_window = main_window

    def handle_login_request(self, login, senha, manter_aberto):
        """Processa requisição de login"""
        print("=" * 80)
        print("🔍 [CONSOLE] handle_login_request CHAMADO")
        print(f"🔍 [CONSOLE] Login: {login}, Senha: {'*' * len(senha)}")
        print("=" * 80)
        adicionar_log("🔍 [DEBUG] handle_login_request chamado")
        adicionar_log(f"🔍 [DEBUG] Login: {login}, Senha: {'*' * len(senha) if senha else 'vazio'}")

        if not login or not senha:
            print("❌ [CONSOLE] Login ou senha vazios")
            adicionar_log("❌ [DEBUG] Login ou senha vazios")
            self.signal_manager.token_status_updated.emit(
                "Preencha usuário e senha para autenticar.", "red"
            )
            return

        print("🔍 [CONSOLE] Desabilitando botão de login")
        adicionar_log("🔍 [DEBUG] Desabilitando botão de login")
        self.main_window.login_tab.set_login_button_enabled(False)
        print("🔍 [CONSOLE] Botão desabilitado com sucesso")
        adicionar_log("🔍 [DEBUG] Botão desabilitado com sucesso")

        def login_thread():
            try:
                print("=" * 80)
                print("🔄 [CONSOLE] ===== THREAD DE LOGIN INICIADA =====")
                print("=" * 80)
                adicionar_log("🔄 [DEBUG] ===== THREAD DE LOGIN INICIADA =====")
                adicionar_log("🔄 Realizando login...")
                print("🔍 [CONSOLE] Chamando realizar_login_selenium...")
                adicionar_log("🔍 [DEBUG] Chamando realizar_login_selenium...")
                print("🔍 [CONSOLE] ANTES de chamar realizar_login_selenium")
                jwt, user_login, user_id, cookie_dict = realizar_login_selenium(
                    login, senha, manter_aberto
                )
                print("🔍 [CONSOLE] DEPOIS de chamar realizar_login_selenium")
                adicionar_log(f"🔍 [DEBUG] realizar_login_selenium retornou")
                adicionar_log(f"🔍 [DEBUG] JWT presente: {jwt is not None}")
                print(f"🔍 [CONSOLE] JWT presente: {jwt is not None}")

                if jwt:
                    print("✅ [CONSOLE] Login bem-sucedido, emitindo sinal")
                    adicionar_log("✅ [DEBUG] Login bem-sucedido, emitindo sinal")
                    self.signal_manager.login_successful.emit(jwt, user_login, user_id, cookie_dict)
                else:
                    print("❌ [CONSOLE] Login falhou")
                    adicionar_log("❌ [DEBUG] Login falhou, emitindo sinal de falha")
                    self.signal_manager.login_failed.emit(
                        "Erro no login: confira usuário, senha e/ou conexão CEABS (VPN/cabo)"
                    )
            except Exception as e:
                print("=" * 80)
                print(f"❌ [CONSOLE] ===== EXCEÇÃO NA THREAD DE LOGIN =====")
                print(f"❌ [CONSOLE] Tipo: {type(e).__name__}")
                print(f"❌ [CONSOLE] Mensagem: {e}")
                print("=" * 80)
                adicionar_log(f"❌ [DEBUG] ===== EXCEÇÃO NA THREAD DE LOGIN =====")
                adicionar_log(f"❌ [DEBUG] Tipo da exceção: {type(e).__name__}")
                adicionar_log(f"❌ [DEBUG] Mensagem: {e}")
                import traceback
                print(traceback.format_exc())
                self.signal_manager.login_failed.emit(f"Erro na thread de login: {e}")
            finally:
                print("=" * 80)
                print("🔍 [CONSOLE] ===== FINALIZANDO THREAD DE LOGIN =====")
                print("=" * 80)
                adicionar_log("🔍 [DEBUG] ===== FINALIZANDO THREAD DE LOGIN =====")
                self.main_window.login_tab.set_login_button_enabled(True)
                print("🔍 [CONSOLE] Botão reabilitado")

        print("🔍 [CONSOLE] Criando thread de login")
        adicionar_log("🔍 [DEBUG] Criando thread de login")
        thread = Thread(target=login_thread, daemon=True)
        print("🔍 [CONSOLE] Iniciando thread...")
        thread.start()
        print("🔍 [CONSOLE] Thread iniciada com sucesso")
        adicionar_log("🔍 [DEBUG] Thread iniciada com sucesso")

    def handle_login_successful(self, jwt, user_login, user_id, cookie_dict):
        """Processa login bem-sucedido"""
        print("=" * 80)
        print("🟩 [CONSOLE] handle_login_successful CHAMADO")
        print(f"🟩 [CONSOLE] JWT recebido? {jwt is not None}")
        print(f"🟩 [CONSOLE] Usuário: {user_login}")
        print(f"🟩 [CONSOLE] User ID: {user_id}")
        print("=" * 80)
        adicionar_log("🟩 [DEBUG] handle_login_successful chamado")
        adicionar_log("🟩 [DEBUG] Começando processamento pós-login")
        print("🟩 [CONSOLE] Começando processamento pós-login")

        # Atualizar estado global UMA ÚNICA VEZ
        adicionar_log("🟩 [DEBUG] Atualizando estado global com token")
        print("🟩 [CONSOLE] Atualizando estado global com token")
        self.app_state["jwt_token"] = jwt
        self.app_state["user_login"] = user_login
        self.app_state["user_id"] = user_id
        self.app_state["cookie_dict"] = cookie_dict
        self.app_state["token_expiry"] = datetime.datetime.now() + datetime.timedelta(hours=8)
        print("🟩 [CONSOLE] Estado global atualizado")
        adicionar_log("🟩 [DEBUG] Estado global atualizado")

        # Emitir sinal de atualização de status do token
        print("🟩 [CONSOLE] Emitindo sinal token_status_updated")
        adicionar_log("🟩 [DEBUG] Emitindo sinal token_status_updated")
        expiry_str = self.app_state["token_expiry"].strftime("%d/%m/%Y %H:%M:%S")
        self.signal_manager.token_status_updated.emit(
            f"✅ Token válido até {expiry_str}", "green"
        )
        print("🟩 [CONSOLE] Sinal token_status_updated emitido")
        adicionar_log("🟩 [DEBUG] Sinal token_status_updated emitido")

        # Habilitar abas
        print("🟩 [CONSOLE] Chamando show_tabs_after_login")
        adicionar_log("🟩 [DEBUG] Chamando show_tabs_after_login")
        try:
            self.main_window.show_tabs_after_login()
            print("🟩 [CONSOLE] show_tabs_after_login retornou com sucesso")
            adicionar_log("🟩 [DEBUG] show_tabs_after_login retornou com sucesso")
        except Exception as e:
            print(f"❌ [CONSOLE] Erro ao chamar show_tabs_after_login: {e}")
            adicionar_log(f"❌ [DEBUG] Erro ao chamar show_tabs_after_login: {e}")
            import traceback
            print(traceback.format_exc())

        # Inicializar scheduler após login (em thread separada para não travar)
        print("🟩 [CONSOLE] Inicializando scheduler")
        if not self.app_state.get("scheduler"):
            def init_scheduler():
                try:
                    from core.scheduler import Scheduler, set_scheduler
                    self.app_state["scheduler"] = Scheduler()
                    set_scheduler(self.app_state["scheduler"])
                    adicionar_log("✅ Scheduler inicializado")
                    print("🟩 [CONSOLE] Scheduler inicializado com sucesso")
                except Exception as e:
                    print(f"❌ [CONSOLE] Erro ao inicializar scheduler: {e}")
                    adicionar_log(f"❌ Erro ao inicializar scheduler: {e}")
            Thread(target=init_scheduler, daemon=True).start()

        # Log de sucesso
        adicionar_log(f"✅ Login realizado com sucesso! Usuário: {user_login}")
        print(f"✅ [CONSOLE] Login realizado com sucesso! Usuário: {user_login}")
        adicionar_log("🟩 [DEBUG] handle_login_successful concluído")
        print("🟩 [CONSOLE] handle_login_successful concluído")
        print("=" * 80)

    def handle_login_failed(self, message):
        """Processa falha no login"""
        print(f"❌ [CONSOLE] handle_login_failed: {message}")
        self.signal_manager.token_status_updated.emit(message, "red")
        adicionar_log(f"❌ Falha no login: {message}")

    def handle_file_selected(self, filepath):
        """Processa seleção de arquivo"""
        try:
            result = ler_arquivo_serials(filepath)  # Atualizado para nova função
            self.main_window.equipment_tab.current_serials = result['unicos']
            self.main_window.equipment_tab.update_serial_status()
            adicionar_log(f"📁 Arquivo carregado: {len(result['unicos'])} seriais únicos (duplicados removidos: {result['duplicados']})")
        except Exception as e:
            adicionar_log(f"❌ Erro ao carregar arquivo: {e}")
            QMessageBox.critical(self.main_window, "Erro", f"Erro ao carregar arquivo:\n{e}")

    def start_token_check_timer(self):
        """Inicia timer de verificação de token"""
        if not hasattr(self.main_window, '_token_check_timer'):
            self.main_window._token_check_timer = QTimer()
            self.main_window._token_check_timer.timeout.connect(self.check_token_periodically)
            self.main_window._token_check_timer.start(60000)
            adicionar_log("⏰ Timer de verificação de token iniciado")

    def check_token_periodically(self):
        """Verifica periodicamente se o token está válido"""
        if self.app_state['jwt_token'] and self.app_state['token_expiry']:
            agora = datetime.datetime.now()
            restante = self.app_state['token_expiry'] - agora
            if restante.total_seconds() > 0:
                horas, resto = divmod(int(restante.total_seconds()), 3600)
                minutos, _ = divmod(resto, 60)
                self.signal_manager.token_status_updated.emit(f"Token expira em: {horas}h {minutos}min", "green")
            else:
                self.signal_manager.token_status_updated.emit("Token expirou. Faça login novamente.", "red")
