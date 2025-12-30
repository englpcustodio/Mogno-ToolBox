# mogno_app/services/redis_service.py
"""
Serviços Redis refatorados:
- Todas as requisições são feitas em paralelo via ThreadPoolExecutor
- Adiciona retries com backoff exponencial
- Tratamento de erros e logs consistentes
- Compatível com RequestHandler otimizado
"""
import os
import sys
import time
import redis
import base64
import binascii
import traceback

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from utils.logger import adicionar_log
from utils.helpers import epoch_to_datetime
from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB_2, REDIS_DB_4

# === DEPURAÇÃO DE CAMINHOS ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO_DIR = os.path.join(BASE_DIR, "compiled_protos")

# Adiciona a pasta compiled_protos ao sys.path se ainda não estiver
if PROTO_DIR not in sys.path:
    sys.path.insert(0, PROTO_DIR)
else:
    print(f"ℹ️ Pasta já presente no sys.path")

from compiled_protos import evento_pb2, maxpb_report_pb2

def conectar_redis(db: int) -> Optional[redis.Redis]:
    """Estabelece conexão com Redis, com verificação de saúde."""
    try:
        redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=db, decode_responses=False)
        redis_conn.ping()
        adicionar_log(f"✅ Conexão com Redis (DB {db}) estabelecida.")
        return redis_conn
    except redis.ConnectionError as e:
        adicionar_log(f"❌ Falha ao conectar Redis (DB {db}): {e}")
        return None

def _retry(func, *args, retries: int = 2, backoff: float = 0.5, **kwargs):
    """Executa função com retries e backoff exponencial simples."""
    for attempt in range(retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt >= retries:
                raise
            adicionar_log(f"⚠️ Tentativa {attempt+1}/{retries} falhou: {e}. Retentando em {backoff*(2**attempt):.1f}s...")
            time.sleep(backoff * (2 ** attempt))
    return None


# =========================================================
# Última Posição
# =========================================================

def ultima_posicao_tipo(seriais: List[str]) -> List[Dict[str, Any]]:
    """
    Obtém a última posição para cada serial em paralelo.
    """ 
    redis_conn = conectar_redis(REDIS_DB_4)
    if not redis_conn:
        return []

    resultados = []
    tipos = ["gsm", "lorawan", "p2p"]

    def obter_dados(serial: str, tipo: str):
        try:
            chave = f"storage:ultima_posicao_{tipo}:{serial}"
            valor = redis_conn.get(chave)
            if not valor:
                return None

            valor_decodificado = base64.b64decode(valor)
            ultima_posicao = evento_pb2.Evento()
            ultima_posicao.ParseFromString(valor_decodificado)

            datahoraevento = None

            if hasattr(ultima_posicao, "data_hora_evento") and ultima_posicao.data_hora_evento:
                datahoraevento = epoch_to_datetime(ultima_posicao.data_hora_evento / 1000)

            versao_hw = None
            if hasattr(ultima_posicao, "rastreador") and hasattr(ultima_posicao.rastreador, "versao_hardware"):
                versao_hw = ultima_posicao.rastreador.versao_hardware

            print(ultima_posicao.rastreador.numero_serie, {tipo}, datahoraevento)

            return {
                "Serial": serial,
                "Modelo de HW": versao_hw,
                "Tipo": tipo,
                "DataHora Evento": datahoraevento,
                "Dados": ultima_posicao,
            }

        except Exception as e:
            adicionar_log(f"⚠️ Erro ao processar serial {serial} ({tipo}): {e}")
            return None

    futures = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        for serial in seriais:
            for tipo in tipos:
                futures.append(executor.submit(_retry, obter_dados, serial, tipo))

        for fut in as_completed(futures):
            try:
                resultado = fut.result()
                if resultado:
                    resultados.append(resultado)
            except Exception as e:
                adicionar_log(f"⚠️ Erro em futuro Redis (ultima_posicao): {e}")

    try:
        redis_conn.close()
    except Exception:
        pass

    return resultados


# =========================================================
# Status dos Equipamentos
# =========================================================

def status_equipamento(seriais: List[str]) -> List[Dict[str, Any]]:
    """
    Obtém status dos equipamentos (mxtstatus) em paralelo.
    """
    adicionar_log(f"🚀 Consultando status de {len(seriais)} equipamentos no Redis DB {REDIS_DB_2}...")
    redis_conn = conectar_redis(REDIS_DB_2)
    if not redis_conn:
        return []

    resultados = []

    def obter_dados(serial: str):
        try:
            chave = f"mxtstatus:{serial}"
            valor = redis_conn.get(chave)
            if not valor:
                return None

            status_proto = maxpb_report_pb2.ReportStatus()
            status_proto.ParseFromString(binascii.unhexlify(valor))

            return {"Serial": serial, "Dados": status_proto}

        except Exception as e:
            adicionar_log(f"⚠️ Erro ao processar status do serial {serial}: {e}")
            return None

    futures = []
    with ThreadPoolExecutor(max_workers=80) as executor:
        for serial in seriais:
            futures.append(executor.submit(_retry, obter_dados, serial))

        for fut in as_completed(futures):
            try:
                resultado = fut.result()
                if resultado:
                    resultados.append(resultado)
            except Exception as e:
                adicionar_log(f"⚠️ Erro em futuro Redis (status_equipamento): {e}")

    try:
        redis_conn.close()
    except Exception:
        pass

    adicionar_log(f"📊 Total de status obtidos via Redis: {len(resultados)}")
    return resultados


# =========================================================
# Consumo de Dados no Servidor
# =========================================================

def obter_dados_consumo(mes: int, ano: int) -> Dict[str, Any]:
    """
    Obtém dados de consumo GSM (hash gateway:consumo_gsm:mes_ano).
    Retorna dict com valores já convertidos para float validado.

    Args:
        mes (int): Mês (1-12)
        ano (int): Ano (ex: 2025)

    Returns:
        Dict[str, float]: {serial: bytes_consumidos}
    """
    try:
        mes_int = int(mes)
    except ValueError:
        adicionar_log(f"⚠️ Mês inválido recebido: {mes}. Valor ajustado para 1.")
        mes_int = 1

    adicionar_log(f"🚀 Obtendo consumo de dados para {mes_int}/{ano} no Redis DB {REDIS_DB_4}...")
    redis_conn = conectar_redis(REDIS_DB_4)
    if not redis_conn:
        return {}

    chave = f"gateway:consumo_gsm:{mes_int}_{ano}"

    try:
        trafego_dados_bytes = _retry(redis_conn.hgetall, chave, retries=2, backoff=0.5)
        if not trafego_dados_bytes:
            adicionar_log(f"⚠️ Nenhum dado encontrado em {chave}")
            return {}

        resultado = {}
        erros = 0
        total = len(trafego_dados_bytes)

        for idx, (serial, valor) in enumerate(trafego_dados_bytes.items(), start=1):
            try:
                # Decodifica serial
                if isinstance(serial, bytes):
                    serial_str = serial.decode("utf-8", errors="replace").strip()
                else:
                    serial_str = str(serial).strip()

                # Decodifica valor
                if isinstance(valor, bytes):
                    valor_str = valor.decode("utf-8", errors="replace").strip()
                else:
                    valor_str = str(valor).strip()

                # Converte para float
                valor_float = float(valor_str)

                # Valida range
                if valor_float < 0 or valor_float > 1e15:
                    adicionar_log(f"⚠️ Valor suspeito ignorado para {serial_str}: {valor_float}")
                    erros += 1
                    continue

                resultado[serial_str] = valor_float

                # Log a cada 100 registros
                if idx % 100 == 0:
                    adicionar_log(f"📊 Processados {idx}/{total} registros")

            except (ValueError, UnicodeDecodeError) as e:
                erros += 1
                continue

        if erros > 0:
            adicionar_log(f"⚠️ {erros} registros ignorados por erro")

        adicionar_log(f"📶 {len(resultado)} registros de consumo obtidos com sucesso.")
        return resultado

    except Exception as e:
        adicionar_log(f"❌ Erro ao obter consumo GSM ({mes_int}/{ano}): {e}")
        return {}

    finally:
        try:
            redis_conn.close()
        except Exception:
            pass
