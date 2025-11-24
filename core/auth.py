# mogno_app/core/auth.py
import datetime
import traceback
import jwt
import time
from threading import Thread, Lock
from PyQt5.QtCore import QTimer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.logger import adicionar_log
from config.settings import MOGNO_BASE_URL
from core.credential_manager import CredentialManager # Importar o novo manager

class AuthManager:
    """
    Gerencia login via Selenium em uma thread separada, mantém controle do driver
    (quando pedir para manter aberto) e gerencia verificação periódica do token.
    """

    def __init__(self, signal_manager, main_window, app_state, chrome_driver_path=None):
        self.signal_manager = signal_manager
        self.main_window = main_window
        self.app_state = app_state
        self.credential_manager = CredentialManager() # Instanciar o CredentialManager
        self._driver = None
        self._driver_lock = Lock()
        self.chrome_driver_path = chrome_driver_path  # opcional: se quiser apontar para chromedriver
        self._token_timer = None
        self._login_in_progress = False # Flag para evitar múltiplas tentativas de login simultâneas

        # Conectar os sinais de login_successful e login_failed do SignalManager
        # para que o AuthManager possa reagir a eles e iniciar o timer, etc.
        self.signal_manager.login_successful.connect(self.handle_login_successful)
        self.signal_manager.login_failed.connect(self.handle_login_failed)

    # ---------- Selenium login (retorna token, user_login, user_id, cookie_dict) ----------
    def _perform_selenium_login(self, login_input, senha_input, manter_aberto=False, timeout=15):
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        if not manter_aberto:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        # Fecha qualquer driver existente antes de iniciar um novo, se não for para manter aberto
        if not manter_aberto:
            self.close_driver()

        adicionar_log("🔁 Inicializando webdriver Chrome para login (Selenium).")
        try:
            if self.chrome_driver_path:
                driver = webdriver.Chrome(executable_path=self.chrome_driver_path, options=options)
            else:
                driver = webdriver.Chrome(options=options)
        except Exception as e:
            adicionar_log(f"❌ Erro ao inicializar o driver Chrome: {e}")
            adicionar_log(traceback.format_exc())
            return None, None, None, None

        try:
            driver.get(MOGNO_BASE_URL)
            wait = WebDriverWait(driver, timeout)
            wait.until(EC.presence_of_element_located((By.ID, "Login"))).send_keys(login_input)
            driver.find_element(By.ID, "password").send_keys(senha_input)
            driver.find_element(By.ID, "btn-entrar").click()
            wait.until(EC.url_contains("pesquisaeventos.html"))

            cookies = driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            token = cookie_dict.get('Authorization', '') or cookie_dict.get('authorization', '')

            if token and token.startswith("Bearer "):
                token = token[7:]

            return token, cookie_dict.get("login"), cookie_dict.get("userId"), cookie_dict

        except Exception as e:
            adicionar_log(f"❌ Erro ao tentar realizar login (Selenium): {e}")
            adicionar_log(traceback.format_exc())
            return None, None, None, None

        finally:
            if not manter_aberto:
                try:
                    driver.quit()
                except Exception:
                    pass
            else:
                # Guarda referência do driver para possível inspeção manual
                with self._driver_lock:
                    self._driver = driver

    # ---------- Threaded start com retentativas ----------
    def start_login(self, login, senha, manter_aberto=False, remember_user=False, remember_password=False, is_auto_login=True, max_retries=2):
        if self._login_in_progress:
            adicionar_log("⚠️ Tentativa de login ignorada: um login já está em andamento.")
            self.signal_manager.show_toast_warning.emit("Um login já está em andamento. Por favor, aguarde.")
            return

        if not login or not senha:
            self.signal_manager.show_toast_error.emit("❌ Preencha usuário e senha")
            self.signal_manager.token_status_updated.emit("Preencha usuário e senha para autenticar.", "red")
            adicionar_log("❌ Login ou senha vazios")
            return

        self._login_in_progress = True
        # desabilita botão de login via sinal
        try:
            self.signal_manager.enable_start_button.emit(False)
        except Exception:
            pass

        def _login_worker():
            try:
                token, user_login, user_id, cookie_dict = None, None, None, None
                for attempt in range(1, max_retries + 1):
                    adicionar_log(f"🔐 Tentativa de login {attempt}/{max_retries} para {login}...")
                    token, user_login, user_id, cookie_dict = self._perform_selenium_login(login, senha, manter_aberto)
                    if token:
                        adicionar_log(f"✅ Login bem-sucedido na tentativa {attempt}.")
                        break
                    else:
                        adicionar_log(f"❌ Login falhou na tentativa {attempt}. Aguardando para tentar novamente...")
                        time.sleep(2) # Pequena pausa antes de retentar

                if token:
                    # Salva credenciais se as opções estiverem marcadas
                    self.credential_manager.save_credentials(login, senha, remember_user, remember_password)
                    self.app_state.set("last_login_credentials", {
                        "username": login, 
                        "password": senha, 
                        "remember_user": remember_user, 
                        "remember_password": remember_password, 
                        "auto_login": is_auto_login}
                        )
                    self.signal_manager.login_successful.emit(token, user_login or "", user_id or "", cookie_dict or {})
                else:
                    error_msg = "Falha no login após múltiplas tentativas. Verifique usuário, senha e/ou conexão CEABS (VPN/cabo)."
                    self.signal_manager.login_failed.emit(error_msg)
            except Exception as e:
                adicionar_log(f"❌ Exceção na thread de login: {e}")
                adicionar_log(traceback.format_exc())
                self.signal_manager.login_failed.emit(f"Erro na thread de login: {e}")
            finally:
                self._login_in_progress = False
                try:
                    self.signal_manager.enable_start_button.emit(True)
                except Exception:
                    pass

        Thread(target=_login_worker, daemon=True).start()

    def start_auto_login(self):
        """Tenta realizar o login automaticamente com as credenciais salvas."""
        if self._login_in_progress:
            adicionar_log("⚠️ Tentativa de login automático ignorada: um login já está em andamento.")
            return

        username, password, remember_user, remember_password = self.credential_manager.load_credentials()
        last_login_options = self.app_state.get("last_login_credentials")

        if username and password and remember_user and remember_password and last_login_options and last_login_options.get("auto_login"):
            adicionar_log("🚀 Iniciando login automático...")
            self.signal_manager.token_status_updated.emit("Tentando login automático...", "blue")
            # Usar os mesmos parâmetros de manter_aberto, etc., que foram usados no último login manual
            # Por simplicidade, vamos assumir que o auto_login não mantém o navegador aberto por padrão.
            # Se precisar manter, este parâmetro precisaria ser salvo também.
            self.start_login(username, password, manter_aberto=False, remember_user=remember_user, remember_password=remember_password, is_auto_login=True)
        else:
            adicionar_log("ℹ️ Login automático não configurado ou credenciais incompletas.")

            # Primeira execução: não emitir erro
            if not self.app_state.get("jwt_token"):
                self.signal_manager.token_status_updated.emit(
                    "Realize o login para acessar as funcionalidades.",
                    "blue"
                )
                return

            # Apenas emitir reauthentication_required se já existiu um login anterior
            self.signal_manager.token_status_updated.emit(
                "Login automático não disponível. Faça login manual.",
                "red"
            )
            self.signal_manager.reauthentication_required.emit()


    # ---------- Handlers (chamados por quem receber os sinais) ----------
    def handle_login_successful(self, token, user_login, user_id, cookie_dict):
        """
        Atualiza AppState com token e dados, decodifica o JWT (sem verificar assinatura),
        e inicia timer periódico de verificação.
        """
        self.app_state.set("jwt_token", token)
        self.app_state.set("user_login", user_login)
        self.app_state.set("user_id", user_id)
        self.app_state.set("cookie_dict", cookie_dict)

        try:
            if not token or token.count('.') != 2:
                raise ValueError("Formato inválido de JWT")

            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                expiry = datetime.datetime.fromtimestamp(exp_timestamp)
                self.app_state.set("token_expiry", expiry)
                adicionar_log(f"🕒 Token expira em: {expiry.strftime('%d/%m/%Y %H:%M:%S')}")
            else:
                raise ValueError("Campo 'exp' ausente no token")

        except Exception as e:
            adicionar_log(f"⚠️ Erro ao decodificar JWT: {e}")
            # fallback conservador: 3 horas
            expiry = datetime.datetime.now() + datetime.timedelta(hours=3)
            self.app_state.set("token_expiry", expiry)

        expiry_str = self.app_state.get("token_expiry").strftime("%d/%m/%Y %H:%M:%S")
        try:
            self.signal_manager.token_status_updated.emit(f"✅ Token válido até {expiry_str}", "green")
            self.signal_manager.show_toast_success.emit("✅ Login realizado com sucesso!")
        except Exception:
            pass

        try:
            # Chama o método da MainWindow para mostrar as abas
            self.main_window.show_tabs_after_login()
        except Exception as e:
            adicionar_log(f"❌ Erro ao chamar show_tabs_after_login: {e}")

        # inicia timer de verificação periódica do token
        self._start_token_timer()

    def handle_login_failed(self, message):
        try:
            self.signal_manager.token_status_updated.emit(message, "red")
            self.signal_manager.show_toast_error.emit(message)
        except Exception:
            pass
        adicionar_log(f"❌ Falha no login: {message}")
        # Se o login falhou, e não foi um login automático, ou se foi e falhou,
        # resetar o estado para permitir um novo login manual.
        self.signal_manager.reauthentication_required.emit()


    # ---------- Timer para verificar validade do token ----------
    def _start_token_timer(self, interval_seconds=60):
        if self._token_timer and self._token_timer.isActive():
            self._token_timer.stop() # Parar timer anterior se houver
            adicionar_log("⏰ Timer de verificação de token reiniciado.")

        self._token_timer = QTimer()
        self._token_timer.timeout.connect(self._verify_token_periodically)
        self._token_timer.start(interval_seconds * 1000)
        adicionar_log("⏰ Timer de verificação de token iniciado")

    def _verify_token_periodically(self):
        token = self.app_state.get("jwt_token")
        expiry = self.app_state.get("token_expiry")
        last_login_options = self.app_state.get("last_login_credentials", {})
        is_auto_login_enabled = last_login_options.get("auto_login", False)

        if not token or not expiry:
            adicionar_log("ℹ️ Nenhum token carregado no AppState.")
        
            # Primeira inicialização → não avisar erro de token
            last_login = self.app_state.get("last_login_credentials")
            if not last_login:
                self.signal_manager.token_status_updated.emit(
                    "Realize o login para acessar as funcionalidades.",
                    "blue"
                )
                return
        
            # Usuário já havia logado antes → agora sim é erro
            self.signal_manager.token_status_updated.emit("Token ausente. Faça login.", "red")
        
            if is_auto_login_enabled:
                adicionar_log("🔄 Tentando login automático...")
                self.start_auto_login()
            else:
                self.signal_manager.reauthentication_required.emit()
            return
        

        agora = datetime.datetime.now()
        restante = expiry - agora

        if restante.total_seconds() > 0:
            horas, resto = divmod(int(restante.total_seconds()), 3600)
            minutos, _ = divmod(resto, 60)
            # Atualiza o status do token apenas se estiver próximo de expirar (ex: menos de 30 minutos)
            if restante.total_seconds() < 1800: # 30 minutos
                self.signal_manager.token_status_updated.emit(f"Token expira em: {horas}h {minutos}min", "orange")
            else:
                self.signal_manager.token_status_updated.emit(f"Token válido. Expira em: {horas}h {minutos}min", "green")
        else:
            adicionar_log("⚠️ Token expirado. Requer novo login.")
            self.signal_manager.token_status_updated.emit("Token expirou. Faça login novamente.", "red")
            self.signal_manager.show_toast_warning.emit("⚠️ Sessão expirada. Faça login novamente.")
            # Limpar token do app_state
            self.app_state.set("jwt_token", None)
            self.app_state.set("token_expiry", None)

            if is_auto_login_enabled:
                adicionar_log("🔄 Tentando login automático devido a token expirado.")
                self.start_auto_login()
            else:
                self.signal_manager.reauthentication_required.emit()

    # ---------- Utilitários ----------
    def close_driver(self):
        with self._driver_lock:
            if self._driver:
                try:
                    self._driver.quit()
                    adicionar_log("🌐 Driver Selenium encerrado.")
                except Exception as e:
                    adicionar_log(f"❌ Erro ao encerrar driver Selenium: {e}")
                self._driver = None
