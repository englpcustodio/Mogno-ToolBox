import datetime
import os
import pandas as pd
import folium
from folium.plugins import MarkerCluster

# Definir a pasta de saída para os arquivos
OUTPUT_DIR = "output_files_mogno"

CORES_PERIODOS = {
    "periodo_hoje": "green",
    "periodo_0_7": "blue",
    "periodo_7_15": "beige",   # Folium não tem yellow, beige é o mais próximo
    "periodo_15_30": "orange",
    "periodo_30_cima": "red"
}

def detectar_periodo(data_str, hoje=None):
    """
    Recebe data como string "%d/%m/%Y" e retorna a string do período correspondente.
    """
    if not data_str or pd.isnull(data_str):
        return None
    
    if hoje is None:
        hoje = pd.Timestamp.now().normalize()
        
    try:
        data = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
    except Exception:
        return None
        
    if pd.isnull(data):
        return None
        
    diff = (hoje - data).days
    
    if diff == 0:
        return "periodo_hoje"
    elif 0 < diff <= 6:
        return "periodo_0_7"
    elif 7 <= diff <= 14:
        return "periodo_7_15"
    elif 15 <= diff <= 29:
        return "periodo_15_30"
    elif diff >= 30:
        return "periodo_30_cima"
    else:
        return None

def formatar_tempo_sem_posicao(data_str, hoje=None):
    """
    Recebe data como string "%d/%m/%Y" e retorna uma string descrevendo 
    o tempo decorrido desde esta data até hoje.
    """
    if not data_str or pd.isnull(data_str):
        return "—"
    
    if hoje is None:
        hoje = pd.Timestamp.now().normalize()
        
    try:
        data = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
    except Exception:
        return "—"
        
    if pd.isnull(data):
        return "—"
    
    # Calcular a diferença em dias
    diff_dias = (hoje - data).days
    
    # Se for hoje mesmo
    if diff_dias == 0:
        return "Hoje"
    
    # Calcular anos, meses e dias
    anos = diff_dias // 365
    meses = (diff_dias % 365) // 30
    dias = diff_dias % 30
    
    # Construir a string de resposta
    resultado = []
    
    if anos > 0:
        resultado.append(f"{anos} {'ano' if anos == 1 else 'anos'}")
        
    if meses > 0:
        resultado.append(f"{meses} {'mês' if meses == 1 else 'meses'}")
        
    if dias > 0 or (anos == 0 and meses == 0):  # Garantir que mostra pelo menos os dias
        resultado.append(f"{dias} {'dia' if dias == 1 else 'dias'}")
        
    return ", ".join(resultado)

def gerar_mapa(dados, nome_arquivo_mapa=None):
    """
    Gera um mapa de marcadores (Folium) com uma lista de dicts contendo
    latitude, longitude, serial.
    """
    # Garantir que o diretório de saída existe
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Se não for fornecido um nome para o arquivo, criar um baseado na data/hora
    if not nome_arquivo_mapa:
        nome_arquivo_mapa = f"Mapa_Posicoes_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    # Construir o caminho completo para o arquivo
    nome_arquivo_mapa = os.path.join(OUTPUT_DIR, nome_arquivo_mapa)
    
    # Filtrar pontos válidos (com latitude e longitude)
    pontos = [
        d for d in dados
        if "latitude" in d and "longitude" in d and
        pd.notnull(d["latitude"]) and pd.notnull(d["longitude"]) and
        float(d["latitude"]) != 0 and float(d["longitude"]) != 0
    ]
    
    if not pontos:
        return None
        
    # Inicializar o mapa
    lat_centro = float(pontos[0]['latitude'])
    lon_centro = float(pontos[0]['longitude'])
    mapa = folium.Map(location=[lat_centro, lon_centro], zoom_start=6)
    marker_cluster = MarkerCluster().add_to(mapa)
    
    # Adicionar os marcadores
    for d in pontos:
        lat = float(d["latitude"])
        lon = float(d["longitude"])
        data = d.get('data', '')
        periodo = detectar_periodo(data)
        tempo_sem_posicao = formatar_tempo_sem_posicao(data)
        cor = CORES_PERIODOS.get(periodo, "gray")
        horario = d.get('horario', '')
        cliente = d.get('cliente', '—')  # Placeholder
        placa = d.get('placa', '—')      # Placeholder
        modelo = d.get('versao_hardware', '')
        serial = d.get('serial', '')
        versao_fw = d.get('versaofirmware', '')
        fixval = d.get('fix', None)
        gps = "Fixado" if str(fixval).strip() == "1" else (fixval if fixval not in [None, ''] else "—")
        tipoevento = d.get('tipoevento', '')
        
        popup = (
            f"<b>Data/hora:</b> {data} {horario}<br>"
            f"<b>Cliente:</b> {cliente}<br>"
            f"<b>Placa:</b> {placa}<br>"
            f"<b>Modelo:</b> {modelo}<br>"
            f"<b>Serial:</b> {serial}  "
            f"<b>Versão FW:</b> {versao_fw}  "
            f"<b>GPS:</b> {gps}<br>"
            f"<b>Último evento:</b> {tipoevento}<br>"
            f"<b>Última posição:</b> {tempo_sem_posicao}"
        )
        
        folium.Marker(
            [lat, lon],
            popup=popup,
            tooltip=str(serial),
            icon=folium.Icon(color=cor, icon="car", prefix="fa")
        ).add_to(marker_cluster)
    
    # Salvar o mapa no arquivo
    mapa.save(nome_arquivo_mapa)
    
    return nome_arquivo_mapa
