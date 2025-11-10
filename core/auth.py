# mogno_app/core/auth.py

import datetime
import traceback
import jwt
from threading import Thread
from PyQt5.QtCore import QTimer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import adicionar_log
from config.settings import MOGNO_BASE_URL

selenium_driver = None

def realizar_login_selenium(login_input, senha_input, manter_aberto=False):
    global selenium_driver
    options = Options()
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])

    if not manter_aberto:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    selenium_driver = driver

    try:
        adicionar_log(f"🔑 Tentando realizar login com usuário: {login_input}")
        driver.get(MOGNO_BASE_URL)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "Login"))).send_keys(login_input)
        driver.find_element(By.ID, "password").send_keys(senha_input)
        driver.find_element(By.ID, "btn-entrar").click()
        wait.until(EC.url_contains("pesquisaeventos.html"))

        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        token = cookie_dict.get('Authorization', '')

        if token.startswith("Bearer "):
            token = token[7:]

        return token, cookie_dict.get("login"), cookie_dict.get("userId"), cookie_dict

    except Exception as e:
        adicionar_log(f"❌ Erro ao tentar realizar login: {e}")
        adicionar_log(traceback.format_exc())
        return None, None, None, None

    finally:
        if not manter_aberto and driver:
            driver.quit()
            selenium_driver = None

def iniciar_login_thread(login, senha, manter_aberto, signal_manager, main_window, app_state):
    if not login or not senha:
        signal_manager.show_toast_error.emit("❌ Preencha usuário e senha")
        signal_manager.token_status_updated.emit("Preencha usuário e senha para autenticar.", "red")
        adicionar_log("❌ Login ou senha vazios")
        return

    # Desabilita botão de login via sinal (seguro)
    signal_manager.enable_start_button.emit(False)

    def login_thread():
        try:
            token, user_login, user_id, cookie_dict = realizar_login_selenium(login, senha, manter_aberto)
            if token:
                signal_manager.login_successful.emit(token, user_login, user_id, cookie_dict)
            else:
                signal_manager.login_failed.emit("Erro no login: confira usuário, senha e/ou conexão CEABS (VPN/cabo)")
        except Exception as e:
            adicionar_log(f"❌ Erro na thread de login: {e}")
            adicionar_log(traceback.format_exc())
            signal_manager.login_failed.emit(f"Erro na thread de login: {e}")
        finally:
            signal_manager.enable_start_button.emit(True)

    Thread(target=login_thread, daemon=True).start()


def handle_login_successful(token, user_login, user_id, cookie_dict, signal_manager, main_window, app_state):
    app_state["jwt_token"] = token
    app_state["user_login"] = user_login
    app_state["user_id"] = user_id
    app_state["cookie_dict"] = cookie_dict

    try:
        if token.count('.') != 2:
            raise ValueError("Formato inválido de JWT")

        payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = payload.get("exp")

        if exp_timestamp:
            expiry = datetime.datetime.fromtimestamp(exp_timestamp)
            app_state["token_expiry"] = expiry
            adicionar_log(f"🕒 Token expira em: {expiry.strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            raise ValueError("Campo 'exp' ausente no token")

    except Exception as e:
        adicionar_log(f"⚠️ Erro ao decodificar JWT: {e}")
        app_state["token_expiry"] = datetime.datetime.now() + datetime.timedelta(hours=3)

    expiry_str = app_state["token_expiry"].strftime("%d/%m/%Y %H:%M:%S")
    signal_manager.token_status_updated.emit(f"✅ Token válido até {expiry_str}", "green")
    signal_manager.show_toast.emit("✅ Login realizado com sucesso!", "success")


    try:
        main_window.show_tabs_after_login()
    except Exception as e:
        adicionar_log(f"❌ Erro ao chamar show_tabs_after_login: {e}")

    adicionar_log(f"✅ Login realizado com sucesso! Usuário: {user_login}")

def handle_login_failed(message, signal_manager, main_window):
    signal_manager.token_status_updated.emit(message, "red")
    adicionar_log(f"❌ Falha no login: {message}")
    signal_manager.show_toast.emit(message, "error")

def iniciar_token_check_timer(main_window, app_state, signal_manager):
    if not hasattr(main_window, "_token_check_timer"):
        main_window._token_check_timer = QTimer()
        main_window._token_check_timer.timeout.connect(
            lambda: verificar_token_periodicamente(app_state, signal_manager, main_window)
        )
        main_window._token_check_timer.start(60000)
        adicionar_log("⏰ Timer de verificação de token iniciado")

def verificar_token_periodicamente(app_state, signal_manager, main_window):
    token = app_state.get("jwt_token")
    expiry = app_state.get("token_expiry")

    if not token or not expiry:
        signal_manager.token_status_updated.emit("Token ausente. Faça login.", "red")
        return

    agora = datetime.datetime.now()
    restante = expiry - agora

    if restante.total_seconds() > 0:
        horas, resto = divmod(int(restante.total_seconds()), 3600)
        minutos, _ = divmod(resto, 60)
        signal_manager.token_status_updated.emit(
            f"Token expira em: {horas}h {minutos}min", "green"
        )
    else:
        signal_manager.token_status_updated.emit("Token expirou. Faça login novamente.", "red")
        signal_manager.show_toast.emit("⚠️ Sessão expirada. Faça login novamente.", "warning")
