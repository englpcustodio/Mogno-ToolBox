# mogno_app/core/auth.py

import datetime
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import adicionar_log # Importa o logger da nova localização
from config.settings import MOGNO_BASE_URL # Importa a URL base das configurações

selenium_driver = None

def realizar_login_selenium(login_input, senha_input, manter_aberto=False):
    """
    Realiza login no sistema Mogno usando Selenium.
    Retorna (jwt_token, user_login, user_id, cookie_dict) ou (None, None, None, None) em caso de falha.
    """
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

    adicionar_log("🔍 [DEBUG] realizar_login_selenium chamada")
    adicionar_log(f"🔍 [DEBUG] Parâmetros - Login: {login_input}, Manter aberto: {manter_aberto}")


    try:
        adicionar_log("🔍 [DEBUG] Configurando ChromeDriver")
        adicionar_log(f"🔑 Tentando realizar login com usuário: {login_input}")
        driver.get(MOGNO_BASE_URL) # Usa a URL base das configurações
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "Login"))).send_keys(login_input)
        driver.find_element(By.ID, "password").send_keys(senha_input)
        driver.find_element(By.ID, "btn-entrar").click()
        wait.until(EC.url_contains("pesquisaeventos.html"))
        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        jwt = cookie_dict.get('Authorization', '')
        if jwt.startswith("Bearer "):
            jwt = jwt[7:]
        adicionar_log("✅ Login efetuado com sucesso!")
        return jwt, cookie_dict.get("login"), cookie_dict.get("userId"), cookie_dict
    except Exception as e:
        adicionar_log(f"❌ Erro ao tentar realizar login: {e}")
        return None, None, None, None
    finally:
        # O driver só deve ser fechado se não for para manter aberto
        if not manter_aberto and driver:
            driver.quit()
            selenium_driver = None # Limpa a referência global

