# reports/report_traffic_data_redis.py
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from utils.logger import adicionar_log
import traceback


def gerar_relatorio(serials, resultados, output_path):
    """
    Gera relatório de Consumo de Dados (via Redis).
    Exibe tráfego em Bytes, KB, MB e GB,
    ordenado do maior para o menor consumo.
    """
    try:
        adicionar_log("📁 [traffic_data] Iniciando geração do relatório de tráfego...")

        if not resultados:
            adicionar_log("⚠️ Nenhum dado disponível para gerar relatório de consumo.")
            return None

        # Diretório destino (já criado pelo handler, mas garantimos)
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        # -------------------------------
        # PARSE + CONVERSÃO DOS DADOS
        # -------------------------------
        dados_convertidos = []
        for serial, valor in resultados.items():
            try:
                # Normalizações comuns (Redis → Python)
                if isinstance(serial, bytes):
                    serial = serial.decode("utf-8", errors="replace")

                if isinstance(valor, (bytes, bytearray)):
                    valor = valor.decode("utf-8", errors="replace")

                valor_float = float(valor)

                dados_convertidos.append({
                    "Serial": serial,
                    "Bytes": valor_float,
                    "KB": valor_float / 1024,
                    "MB": valor_float / (1024 ** 2),
                    "GB": valor_float / (1024 ** 3),
                })

            except Exception as e:
                adicionar_log(f"⚠️ Erro processando item '{serial}': {e}")
                continue

        if not dados_convertidos:
            adicionar_log("⚠️ Nenhum item pôde ser convertido. Abortando relatório.")
            return None

        # Ordenação
        dados_convertidos.sort(key=lambda x: x["Bytes"], reverse=True)
        adicionar_log(f"📊 {len(dados_convertidos)} seriais processados e ordenados.")

        # -------------------------------
        # CRIAÇÃO DO EXCEL
        # -------------------------------
        wb = Workbook()
        ws = wb.active
        ws.title = "Consumo_de_Dados"

        headers = [
            "Seriais",
            "Tráfego de dados (Bytes)",
            "Tráfego de dados (kB)",
            "Tráfego de dados (MB)",
            "Tráfego de dados (GB)"
        ]
        ws.append(headers)

        # Linhas
        for item in dados_convertidos:
            ws.append([
                item["Serial"],
                round(item["Bytes"], 2),
                round(item["KB"], 2),
                round(item["MB"], 2),
                round(item["GB"], 4),
            ])

        # -------------------------------
        # FORMATAÇÃO VISUAL
        # -------------------------------
        _formatar_planilha(ws)

        wb.save(output_path)
        adicionar_log(f"✅ Relatório de tráfego salvo em: {output_path}")
        return output_path

    except Exception as e:
        adicionar_log(f"❌ Erro ao gerar relatório de consumo: {e}")
        adicionar_log(traceback.format_exc())
        return None


# -------------------------------------------------------------------------
# FORMATADOR VISUAL ESPECÍFICO (mantido aqui para independência)
# -------------------------------------------------------------------------
def _formatar_planilha(ws):
    """Aplica cores, zebra, cabeçalho e alertas >50MB / <1MB."""

    # Cabeçalho
    header_fill = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
    font_header = Font(bold=True, color="FFFFFF")
    border = Border(
        left=Side(style="thin", color="000000"),
        right=Side(style="thin", color="000000"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="thin", color="000000"),
    )

    for cell in ws[1]:
        cell.font = font_header
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    zebra_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    red_fill = PatternFill(start_color="FF9999", end_color="FF9999", fill_type="solid")     # Consumo > 50 MB
    yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # Consumo < 1 MB

    for i, row in enumerate(ws.iter_rows(min_row=2, max_col=5), start=2):
        try:
            mb_value = row[3].value  # Tráfego em MB

            # Determinação da cor
            if isinstance(mb_value, (float, int)):
                if mb_value > 50:
                    row_fill = red_fill
                elif mb_value < 1:
                    row_fill = yellow_fill
                else:
                    row_fill = zebra_fill if i % 2 == 0 else None
            else:
                row_fill = zebra_fill if i % 2 == 0 else None

            # Aplica formatação
            for cell in row:
                if row_fill:
                    cell.fill = row_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = border

        except Exception as e:
            adicionar_log(f"⚠️ Erro ao formatar linha {i}: {e}")

    # Largura automática
    for col in ws.columns:
        max_len = max(len(str(c.value)) if c.value else 0 for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = max(10, min(max_len + 3, 60))

    ws.freeze_panes = "A2"
