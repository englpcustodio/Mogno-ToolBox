# reports/report_traffic_data_redis.py
"""
Gerador de Relatório de Consumo de Dados via Redis.

Cria 2 abas:
1. "Consumo_de_Dados" - Dados encontrados no Redis (ordenados por consumo)
2. "Consumo_seriais" - Comparativo entre seriais requisitados e dados encontrados
"""

import os
import re
from datetime import datetime
from openpyxl import Workbook
from utils.logger import adicionar_log
from reports.reports_utils import formatar_planilha_consumo
import traceback


def gerar_relatorio(serials, resultados, output_path):
    """
    Gera relatório de Consumo de Dados (via Redis) com 2 abas.

    Args:
        serials (list): Lista de seriais inseridos pelo usuário
        resultados (dict): Dados do Redis {serial: valor_bytes}
        output_path (str): Caminho do arquivo Excel de saída

    Returns:
        str: Caminho do arquivo gerado ou None se erro
    """
    try:
        adicionar_log("📁 [traffic_data] Iniciando geração do relatório de tráfego...")

        if not resultados:
            adicionar_log("⚠️ Nenhum dado disponível para gerar relatório de consumo.")
            return None

        # Diretório destino
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        # ═══════════════════════════════════════════════════════════════════
        # ETAPA 1: PARSE E CONVERSÃO DOS DADOS DO REDIS
        # ═══════════════════════════════════════════════════════════════════
        dados_convertidos = []
        serials_encontrados = set()

        for serial, valor in resultados.items():
            try:
                # Sanitiza serial
                serial_limpo = _sanitizar_serial(serial)
                if not serial_limpo:
                    continue

                # Converte valor para float
                valor_float = _converter_valor(valor)
                if valor_float is None:
                    continue

                # Valida range
                if valor_float < 0 or valor_float > 1e15:
                    adicionar_log(f"⚠️ Valor fora do range para {serial_limpo}: {valor_float}")
                    continue

                dados_convertidos.append({
                    "Serial": serial_limpo,
                    "Bytes": valor_float,
                    "KB": valor_float / 1024,
                    "MB": valor_float / (1024 ** 2),
                    "GB": valor_float / (1024 ** 3),
                })
                serials_encontrados.add(serial_limpo)
            except Exception as e:
                adicionar_log(f"⚠️ Erro processando item '{serial}': {e}")
                continue

        if not dados_convertidos:
            adicionar_log("⚠️ Nenhum item pôde ser convertido. Abortando relatório.")
            return None

        # Ordenação por consumo
        dados_convertidos.sort(key=lambda x: x["Bytes"], reverse=True)
        adicionar_log(f"📊 {len(dados_convertidos)} seriais processados e ordenados.")

        # ═══════════════════════════════════════════════════════════════════
        # ETAPA 2: CRIAÇÃO DO EXCEL COM 2 ABAS
        # ═══════════════════════════════════════════════════════════════════
        wb = Workbook()
        ws_principal = wb.active
        ws_principal.title = "Consumo_de_Dados"

        # ─────────────────────────────────────────────────────────────────
        # ABA 1: CONSUMO_DE_DADOS (dados do Redis)
        # ─────────────────────────────────────────────────────────────────
        headers = [
            "Seriais",
            "Tráfego de dados (Bytes)",
            "Tráfego de dados (kB)",
            "Tráfego de dados (MB)",
            "Tráfego de dados (GB)"
        ]
        ws_principal.append(headers)

        for item in dados_convertidos:
            ws_principal.append([
                item["Serial"],
                round(item["Bytes"], 2),
                round(item["KB"], 2),
                round(item["MB"], 2),
                round(item["GB"], 4),
            ])

        # Formata aba principal
        formatar_planilha_consumo(ws_principal, incluir_zebra=True)

        # ─────────────────────────────────────────────────────────────────
        # ABA 2: CONSUMO_SERIAIS (comparativo - APENAS se houver serials)
        # ─────────────────────────────────────────────────────────────────
        if serials:
            ws_comparativo = wb.create_sheet("Consumo_seriais")
            _gerar_aba_comparativo(ws_comparativo, serials, dados_convertidos, serials_encontrados)
            formatar_planilha_consumo(ws_comparativo, incluir_zebra=True)

        # ═══════════════════════════════════════════════════════════════════
        # ETAPA 3: SALVAR ARQUIVO
        # ═══════════════════════════════════════════════════════════════════
        wb.save(output_path)
        adicionar_log(f"✅ Relatório de tráfego salvo em: {output_path}")
        return output_path

    except Exception as e:
        adicionar_log(f"❌ Erro ao gerar relatório de consumo: {e}")
        adicionar_log(traceback.format_exc())
        return None


# ═════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═════════════════════════════════════════════════════════════════════════════

def _sanitizar_serial(serial):
    """
    Remove caracteres de controle e inválidos do serial.

    Args:
        serial: String ou bytes com o serial

    Returns:
        str: Serial sanitizado ou None se vazio
    """
    try:
        # Decodifica se for bytes
        if isinstance(serial, bytes):
            serial_str = serial.decode("utf-8", errors="replace")
        else:
            serial_str = str(serial)

        # Remove caracteres de controle (0x00-0x1F, 0x7F-0x9F)
        serial_limpo = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', serial_str)
        serial_limpo = serial_limpo.strip()

        return serial_limpo if serial_limpo else None

    except Exception:
        return None


def _converter_valor(valor):
    """
    Converte valor para float com validação.

    Args:
        valor: Bytes, string ou número

    Returns:
        float: Valor convertido ou None se inválido
    """
    try:
        # Decodifica se for bytes
        if isinstance(valor, bytes):
            valor_str = valor.decode("utf-8", errors="replace")
        else:
            valor_str = str(valor)

        # Remove caracteres não numéricos (exceto . - +)
        valor_limpo = ''.join(c for c in valor_str if c.isdigit() or c in ['.', '-', '+'])

        if not valor_limpo:
            return None

        return float(valor_limpo)

    except (ValueError, TypeError):
        return None


def _gerar_aba_comparativo(ws, serials, dados_convertidos, serials_encontrados):
    """
    Popula a aba "Consumo_seriais" com comparativo.

    Mostra:
    - Seriais requisitados
    - Status (Encontrado / Não encontrado)
    - Dados de consumo (se encontrado)

    Args:
        ws: Worksheet para a aba comparativa
        serials (list): Lista de seriais inseridos
        dados_convertidos (list): Dados do Redis já convertidos
        serials_encontrados (set): Seriais que retornaram dados
    """
    try:
        adicionar_log(f"📊 Gerando aba comparativa com {len(serials)} seriais inseridos...")

        # Headers
        headers = [
            "Seriais",
            "Status",
            "Tráfego de dados (Bytes)",
            "Tráfego de dados (kB)",
            "Tráfego de dados (MB)",
            "Tráfego de dados (GB)"
        ]
        ws.append(headers)

        # Cria dict para acesso rápido
        dados_dict = {item["Serial"]: item for item in dados_convertidos}

        # Processa cada serial inserido
        for serial in serials:
            serial_limpo = _sanitizar_serial(serial)
            if not serial_limpo:
                continue

            if serial_limpo in serials_encontrados:
                # Serial encontrado no Redis
                item = dados_dict[serial_limpo]
                ws.append([
                    serial_limpo,
                    "✅ Encontrado",
                    round(item["Bytes"], 2),
                    round(item["KB"], 2),
                    round(item["MB"], 2),
                    round(item["GB"], 4),
                ])
            else:
                # Serial NÃO encontrado no Redis
                ws.append([
                    serial_limpo,
                    "❌ Não encontrado",
                    "-",
                    "-",
                    "-",
                    "-",
                ])

        adicionar_log(f"✅ Aba comparativa populada: {len(serials)} seriais")

    except Exception as e:
        adicionar_log(f"❌ Erro ao gerar aba comparativa: {e}")
        adicionar_log(traceback.format_exc())
