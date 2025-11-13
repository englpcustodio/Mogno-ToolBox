# mogno_app/config/settings.py

import os
import sys

# --- Caminhos de Recursos Estáticos ---
# Função auxiliar para lidar com caminhos em ambiente PyInstaller
def get_resource_path(relative_path):
    """Obtém o caminho absoluto para um recurso, considerando PyInstaller."""
    try:
        # PyInstaller cria um atributo _MEIPASS para o caminho temporário
        base_path = sys._MEIPASS
    except Exception:
        # Caso não esteja empacotado, usa o diretório atual
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- Configurações Gerais da Aplicação ---
APP_NAME = "Mogno ToolBox - CEABS"
APP_VERSION = "v1.3"
RELEASE_DATE = "11/08/2025"
LAUNCH_DATE = "13/07/2025"
DEVELOPER_NAME = "M.Eng. Luis P. Custodio"
DEVELOPER_CONTACT = "luis.custodio@ceabs.com.br | engenharia@ceabs.com.br"

# Caminhos para assets
LOGO_CEABS_PATH = get_resource_path("assets/logo_CEABS.png")
LOGO_MOGNO_PATH = get_resource_path("assets/mogno100x100.png")
BACKGROUND_IMAGE_PATH = get_resource_path("assets/background_login.jpg")
RELEASE_NOTES_PATH = get_resource_path("assets/Release_Notes.txt")

# --- Configurações do Redis (para futura integração) ---
REDIS_HOST = 'redis-arquitetura-read.ceabsservicos.com'
REDIS_PORT = 6379
REDIS_DB_2 = 2 # Banco de Dados: Status
REDIS_DB_4 = 4 # Banco de dados para últimas posições/trafego de dados

# --- Configurações da API Mogno ---
MOGNO_BASE_URL = "https://mognotst.ceabs.com.br"
MOGNO_LOGIN_PAGE = f"{MOGNO_BASE_URL}"
MOGNO_RASTREADORES_ENDPOINT = "/api/tools/getLastPosition/2"
MOGNO_RASTREADORES_REFERER = "/paginas/gps/pesquisaultimoevento.html"
MOGNO_ISCAS_ENDPOINT = "/api/tools/rf/getLastPosition/2"
MOGNO_ISCAS_REFERER = "/paginas/rf/pesquisaultimoeventorf.html"

# --- Configurações Padrão de Requisição ---
DEFAULT_STEP = 20
DEFAULT_MAX_WORKERS = 4
DEFAULT_AJUSTE_STEP = 10
DEFAULT_TENTATIVAS_TIMEOUT = 3
DEFAULT_REQUEST_TIMEOUT = 15 # Segundos

# --- Cores para o Mapa (Folium) ---
MAP_PERIOD_COLORS = {
    "periodo_hoje": "green",
    "periodo_0_7": "blue",
    "periodo_7_15": "beige",
    "periodo_15_30": "orange",
    "periodo_30_cima": "red"
}
