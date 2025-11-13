# reports/report_last_position_redis.py
import os
import re
import openpyxl
from datetime import datetime
from openpyxl.utils import get_column_letter # Adicionado para _formatar_planilha
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side # Adicionado para _formatar_planilha
from utils.helpers import epoch_to_datetime, auto_size_columns
from utils.logger import adicionar_log

# ----------------------------------------------------------
# Funções auxiliares (parse e criação de abas detalhadas)
# ----------------------------------------------------------

def parse_dados(dados_str):
    """Converte string estruturada em dict achatado, tratando blocos e chaves aninhadas."""
    dados = {}
    prefixos = []
    dados_str = re.sub(r'&amp;lt;[^&amp;gt;]*&amp;gt;', '', dados_str)
    dados_str = re.sub(r'\r', '', dados_str)
    dados_str = re.sub(r'\n+', '\n', dados_str.strip())

    for linha in dados_str.splitlines():
        linha = linha.strip()
        if not linha:
            continue

        if linha == '}':
            if prefixos:
                prefixos.pop()
            continue

        if linha.endswith('{'):
            prefixos.append(linha[:-1].strip())
            continue

        if ':' in linha:
            try:
                chave, valor = linha.split(':', 1)
                chave = chave.strip()
                valor = valor.strip().strip('"')
                valor = re.sub(r'\s+', ' ', valor)

                if valor.lower() in ('true', 'false'):
                    valor = valor.lower() == 'true'
                elif re.match(r'^-?\d+(\.\d+)?$', valor):
                    valor = float(valor) if '.' in valor else int(valor)

                chave_formatada = f"{'_'.join(prefixos)}_{chave}" if prefixos else chave
                dados[chave_formatada] = valor
            except Exception as e:
                adicionar_log(f"⚠️ Erro ao processar linha '{linha}': {e}")

    return dados

def _create_detailed_sheet(wb, sheet_name, serial_raw_data_map):
    """Cria uma aba detalhada (GSM, LoRaWAN, P2P)."""
    if not serial_raw_data_map:
        return None

    ws = wb.create_sheet(sheet_name)
    all_parsed = []
    unique_keys = []

    for serial, raw in serial_raw_data_map.items():
        parsed = parse_dados(raw)
        parsed["Serial"] = serial
        all_parsed.append(parsed)
        for k in parsed.keys():
            if k not in unique_keys:
                unique_keys.append(k)

    # AQUI ESTÁ A MUDANÇA: Removido o 'sorted()' para manter a ordem de inserção
    headers = ["Serial"] + [k for k in unique_keys if k != "Serial"]
    ws.append(headers)

    for item in all_parsed:
        row = []
        for h in headers:
            val = item.get(h, "")
            if isinstance(val, str) and len(val) > 32000:
                val = val[:32000] + "… [TRUNCADO]"
            row.append(val)
        ws.append(row)

    return ws

def _formatar_planilha(ws):
    """Formatação visual padrão para relatórios."""
    bold_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    gray_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    thin_border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))

    for cell in ws[1]:
        cell.font = bold_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
        if i % 2 == 0:
            for c in row: c.fill = gray_fill
        for c in row:
            c.border = thin_border
            c.alignment = Alignment(horizontal="center", vertical="center")

    for col in ws.columns:
        max_len = max(len(str(c.value)) if c.value else 0 for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = max_len + 3
    ws.freeze_panes = "A2"

# ----------------------------------------------------------
# Função principal de geração de relatório
# ----------------------------------------------------------

def gerar_relatorio(serials_list_from_handler, resultados, output_path_from_handler, separado=True):
    """Gera e salva relatório Excel de últimas posições (Redis/API)."""
    try:
        if not resultados:
            adicionar_log("⚠️ Nenhum dado disponível para gerar relatório de últimas posições (Redis).")
            return None

        # O ReportHandler já fornece o caminho completo para salvar o arquivo.
        # Usamos 'output_path_from_handler' diretamente.
        final_output_path = output_path_from_handler

        # Inicializa o workbook
        wb = openpyxl.Workbook()
        ws_main = wb.active
        ws_main.title = "Resumo_Tipos"

        # Inicialização de contadores e dicionários
        contagem = {"gsm": 0, "lorawan": 0, "p2p": 0}
        serial_data = {}
        dados_gsm, dados_lorawan, dados_p2p = {}, {}, {}

        # Processa os resultados
        for resultado in resultados:
            serial = resultado.get("Serial")
            tipo = str(resultado.get("Tipo", "")).lower().strip()

            if not serial or not tipo:
                continue

            if serial not in serial_data:
                serial_data[serial] = {
                    "Modelo de HW": "N/A",
                    "Pacote GSM": "NÃO",
                    "DataHoraEvento GSM": "N/A",
                    "Pacote LoRaWAN": "NÃO",
                    "DataHoraEvento LoRaWAN": "N/A",
                    "Pacote P2P": "NÃO",
                    "DataHoraEvento P2P": "N/A",
                    "Dados GSM": "",
                    "Dados LoRaWAN": "",
                    "Dados P2P": "",
                }

            dados = str(resultado.get("Dados", ""))
            modelo_hw = str(resultado.get("Modelo de HW", "N/A"))
            datahora_evento = str(resultado.get("DataHora Evento", "N/A"))

            # Trunca dados muito longos (segurança do Excel)
            if len(dados) > 32000:
                dados = dados[:32000] + "… [TRUNCADO]"

            # Atribuição por tipo
            if tipo == "gsm":
                serial_data[serial]["Modelo de HW"] = modelo_hw
                serial_data[serial]["Pacote GSM"] = "SIM"
                serial_data[serial]["DataHoraEvento GSM"] = datahora_evento
                serial_data[serial]["Dados GSM"] = dados
                dados_gsm[serial] = dados
                contagem["gsm"] += 1

            elif tipo == "lorawan":
                serial_data[serial]["Modelo de HW"] = modelo_hw
                serial_data[serial]["Pacote LoRaWAN"] = "SIM"
                serial_data[serial]["DataHoraEvento LoRaWAN"] = datahora_evento
                serial_data[serial]["Dados LoRaWAN"] = dados
                dados_lorawan[serial] = dados
                contagem["lorawan"] += 1

            elif tipo == "p2p":
                serial_data[serial]["Modelo de HW"] = modelo_hw
                serial_data[serial]["Pacote P2P"] = "SIM"
                serial_data[serial]["DataHoraEvento P2P"] = datahora_evento
                serial_data[serial]["Dados P2P"] = dados
                dados_p2p[serial] = dados
                contagem["p2p"] += 1

        # -------------------------
        # Planilha principal (Resumo)
        # -------------------------
        ws_main.append(["Total de Seriais", len(serials_list_from_handler)])
        ws_main.append(["Com comunicação GSM", contagem["gsm"]])
        ws_main.append(["Com comunicação LoRaWAN", contagem["lorawan"]])
        ws_main.append(["Com comunicação P2P", contagem["p2p"]])
        ws_main.append(["Sem comunicação", len(serials_list_from_handler) - len(serial_data)])
        ws_main.append([])

        headers = [
            "Serial", "Modelo de HW",
            "Pacote GSM", "DataHoraEvento GSM",
            "Pacote LoRaWAN", "DataHoraEvento LoRaWAN",
            "Pacote P2P", "DataHoraEvento P2P",
            "Dados GSM", "Dados LoRaWAN", "Dados P2P"
        ]
        ws_main.append(headers)

        for serial in serials_list_from_handler:
            d = serial_data.get(serial, {})
            ws_main.append([
                serial,
                d.get("Modelo de HW", "N/A"),
                d.get("Pacote GSM", "NÃO"),
                d.get("DataHoraEvento GSM", "N/A"),
                d.get("Pacote LoRaWAN", "NÃO"),
                d.get("DataHoraEvento LoRaWAN", "N/A"),
                d.get("Pacote P2P", "NÃO"),
                d.get("DataHoraEvento P2P", "N/A"),
                d.get("Dados GSM", ""),
                d.get("Dados LoRaWAN", ""),
                d.get("Dados P2P", "")
            ])

        # -------------------------
        # Abas detalhadas
        # -------------------------
        sheets_to_format = [ws_main] # Renomeado para sheets_to_format

        for nome, dados_tipo in [
            ("GSM_Detalhado", dados_gsm),
            ("LoRaWAN_Detalhado", dados_lorawan),
            ("P2P_Detalhado", dados_p2p)
        ]:
            ws = _create_detailed_sheet(wb, nome, dados_tipo)
            if ws:
                sheets_to_format.append(ws)

        # Ajuste de colunas e formatação
        for ws in sheets_to_format:
            _formatar_planilha(ws) # Aplica a formatação

        # Salvar workbook no caminho fornecido
        wb.save(final_output_path)

        adicionar_log(f"✅ Relatório gerado: '{final_output_path}'")
        return final_output_path

    except Exception as e:
        adicionar_log(f"❌ Erro ao gerar relatório de últimas posições (Redis): {e}")
        return None
