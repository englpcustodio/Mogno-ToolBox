## login.py
#import datetime
##from datetime import datetime, timedelta
#
#from threading import Thread
#from selenium import webdriver
#from selenium.webdriver.common.by import By
#from selenium.webdriver.chrome.options import Options
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#import tkinter as tk
#from tkinter import messagebox
#from logs import adicionar_log
#
#selenium_driver = None
#
#def atualizar_tempo_token(lbl_token_status, token_expiry):
#    if token_expiry is None:
#        lbl_token_status.config(text="Token não gerado ainda.", fg="blue")
#    else:
#        agora = datetime.datetime.now()
#        restante = token_expiry - agora
#        if restante.total_seconds() > 0:
#            horas, resto = divmod(int(restante.total_seconds()), 3600)
#            minutos, _ = divmod(resto, 60)
#            lbl_token_status.config(text=f"Token expira em: {horas}h {minutos}min", fg="green")
#        else:
#            lbl_token_status.config(text="Token expirou. Realizando novo login...", fg="red")
#
#def verificar_token_periodicamente(var, estado, fazer_login_fn, root):
#    atualizar_tempo_token(var['lbl_token_status'], estado['token_expiry'])
#    if estado['token_expiry'] and datetime.datetime.now() >= estado['token_expiry'] - datetime.timedelta(minutes=1):
#        adicionar_log("⏳ Token expirado. Realizando novo login automático...")
#        var['btn_login'].config(state=tk.DISABLED)
#        def relogin_thread():
#            fazer_login_fn(auto=True)
#            var['btn_login'].config(state=tk.NORMAL)
#            var['btn_iniciar'].config(state=tk.NORMAL)
#        Thread(target=relogin_thread, daemon=True).start()
#    root.after(60000, lambda: verificar_token_periodicamente(var, estado, fazer_login_fn, root))
#
#def realizar_login_selenium(login_input, senha_input, manter_aberto=False):
#    global selenium_driver
#    options = Options()
#    options.add_argument("--disable-logging")
#    options.add_argument("--log-level=3")
#    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
#    if not manter_aberto:
#        options.add_argument("--headless")
#        options.add_argument("--disable-gpu")
#        options.add_argument("--window-size=1920,1080")
#    driver = webdriver.Chrome(options=options)
#    selenium_driver = driver
#    try:
#        adicionar_log(f"🔐 Tentando realizar login com usuário: {login_input}")
#        driver.get("https://mognotst.ceabs.com.br")
#        wait = WebDriverWait(driver, 10)
#        wait.until(EC.presence_of_element_located((By.ID, "Login"))).send_keys(login_input)
#        driver.find_element(By.ID, "password").send_keys(senha_input)
#        driver.find_element(By.ID, "btn-entrar").click()
#        wait.until(EC.url_contains("pesquisaeventos.html"))
#        cookies = driver.get_cookies()
#        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
#        jwt = cookie_dict.get('Authorization', '')
#        if jwt.startswith("Bearer "):
#            jwt = jwt[7:]
#        adicionar_log("✅ Login efetuado com sucesso!")
#        return jwt, cookie_dict.get("login"), cookie_dict.get("userId"), cookie_dict
#    except Exception as e:
#        adicionar_log(f"❌ Erro ao tentar realizar login: {e}")
#        return None, None, None, None
#    finally:
#        if not manter_aberto:
#            driver.quit()
#
#def fazer_login(var, estado, success_callback, auto=False):
#    """
#    Faz login usando Selenium, atualiza estado e chama o callback de sucesso.
#    var: dicionário compartilhado de variáveis GUI (entries, labels, etc)
#    estado: dicionário de estado global
#    success_callback: função a ser chamada ao sucesso do login
#    auto: booleano para diferenciar login automático/manual
#    """
#    login_input = var['entry_login'].get().strip()
#    senha_input = var['entry_senha'].get().strip()
#    manter_aberto = var['var_manter_navegador'].get()
#    if auto:
#        adicionar_log("🔄 Login automático selecionado.")
#    else:
#        adicionar_log("🔑 Iniciando login manual...")
#    if not login_input or not senha_input:
#        var['lbl_token_status'].config(
#            text="Preencha login e senha para autenticar.",
#            fg="red",
#            font=("Segoe UI", 10, "bold")
#        )
#        return
#
#    def login_thread():
#        adicionar_log("🔃 Realizando login...")
#        var['btn_login'].config(state=tk.DISABLED)
#        var['btn_iniciar'].config(state=tk.DISABLED)
#        try:
#            jwt, login_c, userid, cookie_dict = realizar_login_selenium(login_input, senha_input, manter_aberto)
#            if not jwt:
#                adicionar_log("❌ Falha no login.")
#                var['lbl_token_status'].config(
#                    text="Erro no login: confira usuário, senha e/ou conexão CEABS (VPN/cabo)",
#                    fg="red",
#                    font=("Segoe UI", 10, "bold"),
#                    wraplength=300,
#                    justify="center"
#                )
#                estado['jwt_token'] = None
#                return
#            estado['jwt_token'] = jwt
#            estado['user_login'] = login_c
#            estado['user_id'] = userid
#            estado['token_expiry'] = datetime.datetime.now() + datetime.timedelta(hours=3)
#            estado['cookie_dict'] = cookie_dict
#            adicionar_log(f"✅ JWT gerado! Token válido até: {estado['token_expiry']}")
#            var['lbl_token_status'].config(
#                text=f"Login realizado com sucesso às {datetime.datetime.now().strftime('%H:%M:%S')}.",
#                fg="green",
#                font=("Segoe UI", 10, "bold")
#            )
#            success_callback(jwt, login_c, userid, cookie_dict)
#        except Exception as e:
#            var['lbl_token_status'].config(
#                text="Erro no login: confira login, senha e conexão CEABS (VPN/cabo).",
#                fg="red",
#                font=("Segoe UI", 10, "bold")
#            )
#            adicionar_log(f"Erro no login thread: {e}")
#        finally:
#            var['btn_login'].config(state=tk.NORMAL)
#
#    Thread(target=login_thread, daemon=True).start()



# login.py (versão PyQt)
import datetime

from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QTimer
from logs import adicionar_log

selenium_driver = None

def atualizar_tempo_token(lbl_token_status, token_expiry):
    """Atualiza a exibição do tempo restante de validade do token"""
    if token_expiry is None:
        lbl_token_status.setText("Token não gerado ainda.")
        lbl_token_status.setStyleSheet("color: blue;")
    else:
        agora = datetime.datetime.now()
        restante = token_expiry - agora
        if restante.total_seconds() > 0:
            horas, resto = divmod(int(restante.total_seconds()), 3600)
            minutos, _ = divmod(resto, 60)
            lbl_token_status.setText(f"Token expira em: {horas}h {minutos}min")
            lbl_token_status.setStyleSheet("color: green;")
        else:
            lbl_token_status.setText("Token expirou. Realizando novo login...")
            lbl_token_status.setStyleSheet("color: red;")

def verificar_token_periodicamente(window, estado, fazer_login_fn):
    """Verifica periodicamente se o token está válido e renova se necessário"""
    atualizar_tempo_token(window.lbl_token_status, estado['token_expiry'])
    if estado['token_expiry'] and datetime.datetime.now() >= estado['token_expiry'] - datetime.timedelta(minutes=1):
        adicionar_log("⚠️ Token expirado. Realizando novo login automático...")
        window.btn_login.setEnabled(False)
        def relogin_thread():
            fazer_login_fn(auto=True)
            window.btn_login.setEnabled(True)
            window.btn_iniciar.setEnabled(True)
        Thread(target=relogin_thread, daemon=True).start()
    
    # Agendar próxima verificação usando QTimer
    QTimer.singleShot(60000, lambda: verificar_token_periodicamente(window, estado, fazer_login_fn))

def realizar_login_selenium(login_input, senha_input, manter_aberto=False):
    """Realiza login no sistema usando Selenium"""
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
        driver.get("https://mognotst.ceabs.com.br")
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
        if not manter_aberto:
            driver.quit()
