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
#MOGNO_BASE_URL = "https://mogno.ceabs.com.br"
MOGNO_LOGIN_PAGE = f"{MOGNO_BASE_URL}"
MOGNO_RASTREADORES_ENDPOINT = "/api/tools/getLastPosition/2"
MOGNO_RASTREADORES_REFERER = "/paginas/gps/pesquisaultimoevento.html"
MOGNO_ISCAS_ENDPOINT = "/api/tools/rf/getLastPosition/2"
MOGNO_ISCAS_REFERER = "/paginas/rf/pesquisaultimoeventorf.html"

# NOVO: Endpoint para análise de eventos
MOGNO_EVENTS_ENDPOINT = "/api/tools/getPositions/{serial}/{start_date}/{end_date}/{page}"
MOGNO_EVENTS_REFERER = "/paginas/gps/pesquisaeventos.html"

# --- Configurações Padrão de Requisição ---
DEFAULT_STEP = 20
DEFAULT_MAX_WORKERS = 4
DEFAULT_AJUSTE_STEP = 10
DEFAULT_TENTATIVAS_TIMEOUT = 3
DEFAULT_REQUEST_TIMEOUT = 15 # Segundos
# Configurações de Eventos
EVENTS_MAX_WORKERS = 10  # Número de threads simultâneas
EVENTS_REQUEST_TIMEOUT = 30  # Timeout por requisição (segundos)

# --- Cores para o Mapa (Folium) ---
MAP_PERIOD_COLORS = {
    "periodo_hoje": "green",
    "periodo_0_7": "blue",
    "periodo_7_15": "beige",
    "periodo_15_30": "orange",
    "periodo_30_cima": "red"
}

EVENT_NAMES = [
    (0, "POSICAO"), (1, "PANICO"), (2, "FAKE_VIOLADO"), (3, "FAKE_RESTAURADO"), (4, "ANTENA_GPS_CORTADA"),
    (5, "ANTENA_GPS_RECONECTADA"), (6, "IGNICAO_ON"), (7, "IGNICAO_OFF"), (8, "BATERIA_EXTERNA_PERDIDA"),
    (9, "BATERIA_EXTERNA_RECONECTADA"), (10, "BATERIA_EXTERNA_BAIXA"), (11, "BATERIA_INTERNA_PERDIDA"),
    (12, "BATERIA_INTERNA_RECONECTADA"), (13, "BATERIA_INTERNA_BAIXA"), (14, "BATERIA_INTERNA_ERRO"),
    (15, "INICIO_SLEEP"), (16, "RESET_RASTREADOR"), (17, "INICIO_SUPER_SLEEP"), (18, "BLOQUEIO_ANTIFURTO"),
    (19, "DESBLOQUEIO_ANTIFURTO"), (20, "RESPOSTA_POSICAO_SOLICITADA"), (21, "POSICAO_EM_SLEEP"),
    (22, "POSICAO_EM_SUPER_SLEEP"), (23, "OPERADORA_CELULAR"), (24, "ALARME_ANTIFURTO"), (25, "DADOS_VIAGEM"),
    (26, "DADOS_ESTACIONAMENTO"), (27, "PAINEL_VIOLADO"), (28, "PAINEL_RESTAURADO"), (29, "TECLADO_CONECTADO"),
    (30, "TECLADO_DESCONECTADO"), (31, "SENSOR_LIVRE_RESTAURADO"), (32, "MACRO"), (33, "MENSAGEM_NUMERICA"),
    (34, "TERMINO_SLEEP"), (35, "TERMINO_SUPER_SLEEP"), (36, "INICIO_DEEP_SLEEP"), (37, "TERMINO_DEEP_SLEEP"),
    (38, "BATERIA_BACKUP_RECONECTADA"), (39, "BATERIA_BACKUP_DESCONECTADA"), (40, "ANTENA_GPS_EM_CURTO"),
    (41, "ANTIFURTO_RESTAURADO"), (42, "ANTIFURTO_VIOLADO"), (43, "INICIO_MODO_PANICO"), (44, "FIM_MODO_PANICO"),
    (45, "ALERTA_ACELERACAO_FORA_PADRAO"), (46, "ALERTA_FREADA_BRUSCA"), (47, "ALERTA_CURVA_AGRESSIVA"),
    (48, "ALERTA_DIRECAO_ACIMA_VELOCIDADE_PADRAO"), (49, "JAMMING_DETECTADO"), (50, "PLATAFORMA_ACIONADA"),
    (51, "BOTAO_ANTIFURTO_PRESSIONADO"), (52, "EVENTO_GENERICO"), (53, "CARCACA_VIOLADA"),
    (54, "JAMMING_RESTAURADO"), (55, "GPS_FALHA"), (56, "IDENTIFICACAO_CONDUTOR"), (57, "BLOQUEADOR_VIOLADO"),
    (58, "BLOQUEADOR_RESTAURADO"), (59, "COLISAO"), (60, "ECU_VIOLADA"), (61, "ECU_INSTALADA"),
    (62, "IDENTIFICACAO_CONDUTOR_NAO_CADASTRADO"), (63, "FREQ_CONT_PULSOS_ACIMA_LIMITE"),
    (64, "PLATAFORMA_DESACIONADA"), (65, "BETONEIRA_CARREGANDO"), (66, "BETONEIRA_DESCARREGANDO"),
    (67, "PORTA_ABERTA"), (68, "PORTA_FECHADA"), (69, "ALERTA_FREADA_BRUSCA_ACELERACAO_FORA_PADRAO"),
    (70, "TIMEOUT_IDENTIFICADOR_CONDUTOR"), (71, "BAU_ABERTO"), (72, "BAU_FECHADO"), (73, "CARRETA_ENGATADA"),
    (74, "CARRETA_DESENGATADA"), (75, "TECLADO_MENSAGEM"), (76, "ACAO_EMBARCADA_ACIONADA"),
    (77, "ACAO_EMBARCADA_DESACIONADA"), (78, "FIM_VELOCIDADE_ACIMA_DO_PADRAO"), (79, "ENTRADA_EM_BANGUELA"),
    (80, "SAIDA_DE_BANGUELA"), (81, "RPM_EXCEDIDO"),
    (82, "ALERTA_DE_DIRECAO_COM_VELOCIDADE_EXCESSIVA_NA_CHUVA"),
    (83, "FIM_DE_VELOCIDADE_ACIMA_DO_PADRAO_NA_CHUVA"),
    (84, "VEICULO_PARADO_COM_MOTOR_FUNCIONANDO"), (85, "VEICULO_PARADO"),
    (86, "CALIBRACAO_AUTOMATICA_DO_RPM_REALIZADA"),
    (87, "CALIBRACAO_DO_ODOMETRO_FINALIZADA"), (88, "MODO_ERB"),
    (89, "EMERGENCIA_OU_POSICAO_DE_DISPOSITIVO_RF_EM_MODO_ERB"), (90, "EMERGENCIA_POR_PRESENCA"),
    (91, "EMERGENCIA_POR_RF"), (92, "DISPOSITIVO_PRESENCA_AUSENTE"),
    (93, "BATERIA_VEICULO_ABAIXO_LIMITE_PRE_DEFINIDO"), (94, "LEITURA_OBD"),
    (95, "VEICULO_PARADO_COM_RPM"), (96, "MODO_EMERGENCIA_POR_JAMMING"), (97, "EMERGENCIA_POR_GPRS"),
    (98, "DETECCAO_RF"), # Adicionado DETECCAO_RF com ID 98
    (99, "DISPOSITIVO_PRESENCA_RECUPERADO"), (100, "ENTRADA_MODO_EMERGENCIA"),
    (101, "SAIDA_MODO_EMERGENCIA"), (102, "EMERGENCIA"), (103, "INICIO_DE_MOVIMENTO"),
    (104, "FIM_DE_MOVIMENTO"), (105, "VEICULO_PARADO_COM_IGNICAO_LIGADA"),
    (106, "REGRA_GEOGRAFICO"), (107, "ALERTA_DE_IGNICAO_SEM_FAROL"),
    (108, "FIM_DE_IGNICAO_SEM_FAROL"), (109, "INICIO_MOVIMENTO_SEM_BATERIA_EXTERNA"),
    (110, "FIM_MOVIMENTO_SEM_BATERIA_EXTERNA"), (111, "RASTREAMENTO_ATIVADO"),
    (112, "RASTREAMENTO_DESATIVADO"), (113, "ALERTA_DE_MOTORISTA_COM_SONOLENCIA"),
    (114, "ALERTA_DE_MOTORISTA_COM_DISTRACAO"), (115, "ALERTA_DE_MOTORISTA_BOCEJANDO"),
    (116, "ALERTA_DE_MOTORISTA_AO_TELEFONE"), (117, "ALERTA_DE_MOTORISTA_FUMANDO")
]
