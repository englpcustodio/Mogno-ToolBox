# mogno_app/services/redis_service.py

"""
Serviço de integração com Redis para consultas de status e últimas posições.
"""

import redis
import base64
import binascii
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import adicionar_log
from utils.helpers import epoch_to_datetime
from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB_2, REDIS_DB_4

import os
import sys

# === DEPURAÇÃO DE CAMINHOS ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO_DIR = os.path.join(BASE_DIR, "compiled_protos")

print("📂 Diretório base:", BASE_DIR)
print("📦 Pasta dos protos:", PROTO_DIR)

# Adiciona a pasta compiled_protos ao sys.path se ainda não estiver
if PROTO_DIR not in sys.path:
    sys.path.insert(0, PROTO_DIR)
    print(f"✅ Adicionado ao sys.path: {PROTO_DIR}")
else:
    print(f"ℹ️ Pasta já presente no sys.path")

print("🔍 sys.path final:")
for p in sys.path:
    print("   ", p)
print("===============================")

from compiled_protos import evento_pb2, maxpb_report_pb2

def conectar_redis(db):
    """
    Estabelece a conexão com o Redis e retorna a conexão.
    """
    redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=db, decode_responses=False)
    try:
        redis_conn.ping()
        adicionar_log(f"✅ Conexão com Redis (DB {db}) estabelecida.")
        return redis_conn
    except redis.ConnectionError as e:
        adicionar_log(f"❌ Não foi possível conectar ao Redis (DB {db}): {e}")
        return None

def ultima_posicao_tipo(seriais):
    """
    Obtém a última posição para uma lista de seriais.
    """   
    redis_conn = conectar_redis(REDIS_DB_4)
    if not redis_conn:
        return []
    
    resultados = []
    tipos = ['gsm', 'lorawan', 'p2p']

    def obter_dados(chave, serial, tipo):
        try:
            valor = redis_conn.get(chave)
            if valor:
                adicionar_log(f"✅ Dados encontrados para serial {serial} ({tipo})")
                valor_decodificado = base64.b64decode(valor)
                ultima_posicao = evento_pb2.Evento()
                ultima_posicao.ParseFromString(valor_decodificado)
                #print(ultima_posicao) #DEBUG

                datahoraevento = None
                if hasattr(ultima_posicao, 'data_hora_evento') and ultima_posicao.data_hora_evento:
                    datahoraevento = epoch_to_datetime(ultima_posicao.data_hora_evento / 1000)
                
                versao_hw = None
                if hasattr(ultima_posicao, 'rastreador') and hasattr(ultima_posicao.rastreador, 'versao_hardware'):
                    versao_hw = ultima_posicao.rastreador.versao_hardware
                
                return {
                    'Serial': serial,
                    'Modelo de HW': versao_hw,
                    'Tipo': tipo,
                    'DataHora Evento': datahoraevento,
                    'Dados': ultima_posicao
                }
        except Exception as e:
            adicionar_log(f"⚠️ Erro ao decodificar última posição (serial {serial}, tipo {tipo}): {e}")
        return None

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for serial in seriais:
            for tipo in tipos:
                chave = f'storage:ultima_posicao_{tipo}:{serial}'
                futures.append(executor.submit(obter_dados, chave, serial, tipo))

        for future in as_completed(futures):
            resultado = future.result()
            if resultado:
                resultados.append(resultado)
    
    redis_conn.close()
    adicionar_log(f"📊 Total de posições obtidas via Redis: {len(resultados)}")

    return resultados

def status_equipamento(seriais):
    """
    Obtém o status dos equipamentos para uma lista de seriais.
    """  
    redis_conn = conectar_redis(REDIS_DB_2)
    if not redis_conn:
        return []
    
    resultados = []

    def obter_dados(chave, serial):
        try:
            valor = redis_conn.get(chave)
            if valor:
                status_equipamento_proto = maxpb_report_pb2.ReportStatus()
                status_equipamento_proto.ParseFromString(binascii.unhexlify(valor))
                
                return {
                    'Serial': serial,
                    'Dados': status_equipamento_proto
                }
        except Exception as e:
            adicionar_log(f"⚠️ Erro ao decodificar status (serial {serial}): {e}")
        return None

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for serial in seriais:
            chave = f'mxtstatus:{serial}'
            futures.append(executor.submit(obter_dados, chave, serial))

        for future in as_completed(futures):
            resultado = future.result()
            if resultado:
                resultados.append(resultado)
    
    redis_conn.close()
    return resultados

def obter_dados_consumo(mes, ano):
    """
    Obtém dados de consumo GSM para um mês e ano específicos.
    """
    redis_conn = conectar_redis(REDIS_DB_4)
    if not redis_conn:
        return {}
    
    chave = f"gateway:consumo_gsm:{mes}_{ano}"
    
    try:
        trafego_dados_bytes = redis_conn.hgetall(chave)
        redis_conn.close()
        
        if trafego_dados_bytes:
            return {serial.decode('utf-8'): valor.decode('utf-8') for serial, valor in trafego_dados_bytes.items()}
    except Exception as e:
        adicionar_log(f"❌ Erro ao obter dados de consumo: {e}")
        if redis_conn:
            redis_conn.close()
    
    return {}
