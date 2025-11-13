# mogno_app/core/auth.py
import datetime
import traceback
import jwt
from threading import Thread, Lock
from PyQt5.QtCore import QTimer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from utils.logger import adicionar_log
from config.settings import MOGNO_BASE_URL

class AuthManager:
    """
    Gerencia login via Selenium em uma thread separada, mantém controle do driver
    (quando pedir para manter aberto) e gerencia verificação periódica do token.
    """

    def __init__(self, signal_manager, main_window, app_state, chrome_driver_path=None):
        self.signal_manager = signal_manager
        self.main_window = main_window
        self.app_state = app_state
        self._driver = None
        self._driver_lock = Lock()
        self.chrome_driver_path = chrome_driver_path  # opcional: se quiser apontar para chromedriver
        self._token_timer = None

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

        # inicializa driver
        adicionar_log("🔁 Inicializando webdriver Chrome para login (Selenium).")
        if self.chrome_driver_path:
            driver = webdriver.Chrome(executable_path=self.chrome_driver_path, options=options)
        else:
            driver = webdriver.Chrome(options=options)

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

    # ---------- Threaded start ----------
    def start_login(self, login, senha, manter_aberto=False):
        if not login or not senha:
            self.signal_manager.show_toast_error.emit("❌ Preencha usuário e senha")
            self.signal_manager.token_status_updated.emit("Preencha usuário e senha para autenticar.", "red")
            adicionar_log("❌ Login ou senha vazios")
            return

        # desabilita botão de login via sinal 
        try:
            self.signal_manager.enable_start_button.emit(False)
        except Exception:
            pass

        def _login_worker():
            try:
                token, user_login, user_id, cookie_dict = self._perform_selenium_login(login, senha, manter_aberto)
                if token:
                    # Emite sinal de sucesso com os dados
                    self.signal_manager.login_successful.emit(token, user_login or "", user_id or "", cookie_dict or {})
                else:
                    self.signal_manager.login_failed.emit("Erro no login: confira usuário, senha e/ou conexão CEABS (VPN/cabo)")
            except Exception as e:
                adicionar_log(f"❌ Exceção na thread de login: {e}")
                adicionar_log(traceback.format_exc())
                self.signal_manager.login_failed.emit(f"Erro na thread de login: {e}")
            finally:
                try:
                    self.signal_manager.enable_start_button.emit(True)
                except Exception:
                    pass

        Thread(target=_login_worker, daemon=True).start()

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
            self.signal_manager.show_toast.emit("✅ Login realizado com sucesso!", "success")
        except Exception:
            pass

        try:
            if hasattr(self.main_window, "show_tabs_after_login"):
                self.main_window.show_tabs_after_login()
        except Exception as e:
            adicionar_log(f"❌ Erro ao chamar show_tabs_after_login: {e}")

        # inicia timer de verificação periódica do token
        self._start_token_timer()

    def handle_login_failed(self, message):
        try:
            self.signal_manager.token_status_updated.emit(message, "red")
            self.signal_manager.show_toast.emit(message, "error")
        except Exception:
            pass
        adicionar_log(f"❌ Falha no login: {message}")

    # ---------- Timer para verificar validade do token ----------
    def _start_token_timer(self, interval_seconds=60):
        if self._token_timer:
            return  # já iniciado

        self._token_timer = QTimer()
        self._token_timer.timeout.connect(self._verify_token_periodically)
        self._token_timer.start(interval_seconds * 1000)
        adicionar_log("⏰ Timer de verificação de token iniciado")

    def _verify_token_periodically(self):
        token = self.app_state.get("jwt_token")
        expiry = self.app_state.get("token_expiry")

        if not token or not expiry:
            try:
                self.signal_manager.token_status_updated.emit("Token ausente. Faça login.", "red")
            except Exception:
                pass
            return

        agora = datetime.datetime.now()
        restante = expiry - agora

        if restante.total_seconds() > 0:
            horas, resto = divmod(int(restante.total_seconds()), 3600)
            minutos, _ = divmod(resto, 60)
            try:
                self.signal_manager.token_status_updated.emit(f"Token expira em: {horas}h {minutos}min", "green")
            except Exception:
                pass
        else:
            try:
                self.signal_manager.token_status_updated.emit("Token expirou. Faça login novamente.", "red")
                self.signal_manager.show_toast.emit("⚠️ Sessão expirada. Faça login novamente.", "warning")
            except Exception:
                pass
            adicionar_log("⚠️ Token expirado - requer novo login")
            # opcional: limpar token do app_state
            self.app_state.set("jwt_token", None)
            self.app_state.set("token_expiry", None)

    # ---------- Utilitários ----------
    def close_driver(self):
        with self._driver_lock:
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
                self._driver = None
