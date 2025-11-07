# mogno_app/core/auth.py

import datetime
import traceback
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
    adicionar_log("🧪 [DEBUG] Iniciando função realizar_login_selenium()")

    options = Options()
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])

    if not manter_aberto:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

    try:
        adicionar_log("🧪 [DEBUG] Criando driver do Chrome")
        driver = webdriver.Chrome(options=options)
        selenium_driver = driver

        adicionar_log(f"🔑 Tentando login com usuário: {login_input}")
        driver.get(MOGNO_BASE_URL)
        adicionar_log("🧪 [DEBUG] Página carregada")

        wait = WebDriverWait(driver, 10)
        adicionar_log("🧪 [DEBUG] Esperando campo de login")
        wait.until(EC.presence_of_element_located((By.ID, "Login"))).send_keys(login_input)

        adicionar_log("🧪 [DEBUG] Preenchendo senha")
        driver.find_element(By.ID, "password").send_keys(senha_input)

        adicionar_log("🧪 [DEBUG] Clicando no botão de login")
        driver.find_element(By.ID, "btn-entrar").click()

        adicionar_log("🧪 [DEBUG] Aguardando redirecionamento")
        wait.until(EC.url_contains("pesquisaeventos.html"))

        adicionar_log("🧪 [DEBUG] Coletando cookies")
        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        jwt = cookie_dict.get('Authorization', '')

        if jwt.startswith("Bearer "):
            jwt = jwt[7:]

        adicionar_log("✅ Login via Selenium realizado com sucesso")
        return jwt, cookie_dict.get("login"), cookie_dict.get("userId"), cookie_dict

    except Exception as e:
        adicionar_log(f"❌ [ERRO] Falha no login Selenium: {e}")
        adicionar_log(traceback.format_exc())
        return None, None, None, None

    finally:
        if not manter_aberto and selenium_driver:
            adicionar_log("🧪 [DEBUG] Fechando driver")
            selenium_driver.quit()
            selenium_driver = None

def iniciar_login_thread(login, senha, manter_aberto, signal_manager, main_window, app_state):
    adicionar_log("🧪 [DEBUG] Iniciando login thread")

    if not login or not senha:
        signal_manager.token_status_updated.emit("Preencha usuário e senha para autenticar.", "red")
        adicionar_log("❌ Login ou senha vazios")
        return

    main_window.login_tab.set_login_button_enabled(False)

    def login_thread():
        try:
            adicionar_log("🧪 [DEBUG] Entrando na thread de login")
            jwt, user_login, user_id, cookie_dict = realizar_login_selenium(login, senha, manter_aberto)

            if jwt:
                adicionar_log("🧪 [DEBUG] Login bem-sucedido, chamando handle_login_successful")
                handle_login_successful(jwt, user_login, user_id, cookie_dict, signal_manager, main_window, app_state)
            else:
                adicionar_log("🧪 [DEBUG] Login falhou, chamando handle_login_failed")
                handle_login_failed("Erro no login: confira usuário, senha e/ou conexão CEABS (VPN/cabo)", signal_manager)

        except Exception as e:
            adicionar_log(f"❌ [ERRO] Exceção na thread de login: {e}")
            adicionar_log(traceback.format_exc())
            handle_login_failed(f"Erro na thread de login: {e}", signal_manager)

        finally:
            adicionar_log("🧪 [DEBUG] Finalizando thread de login")
            main_window.login_tab.set_login_button(True)

    Thread(target=login_thread, daemon=True).start()

def handle_login_successful(jwt, user_login, user_id, cookie_dict, signal_manager, main_window, app_state):
    adicionar_log("🧪 [DEBUG] Executando handle_login_successful")
    app_state["jwt_token"] = jwt
    app_state["user_login"] = user_login
    app_state["user_id"] = user_id
    app_state["cookie_dict"] = cookie_dict
    app_state["token_expiry"] = datetime.datetime.now() + datetime.timedelta(hours=3)

    expiry_str = app_state["token_expiry"].strftime("%d/%/%Y %H:%M:%S")
    signal_manager.token_status_updated.emit(f"✅ Token válido até {expiry_str}", "green")

    try:
        main_window.show_tabs_after_login()
    except Exception as e:
        adicionar_log(f"❌ Erro ao chamar show_tabs_after_login: {e}")

    adicionar_log(f"✅ Login realizado com sucesso! Usuário: {user_login}")

def handle_login_failed(message, signal_manager):
    adicionar_log("🧪 [DEBUG] Executando handle_login_failed")
    signal_manager.token_status_updated.emit(message, "red")
    adicionar_log(f"❌ Falha no login: {message}")
