# reports/report_last_position.py
"""
Gerador Unificado de Relatório: Últimas Posições
Suporta dados de API Mogno e Redis com tratamento específico para cada origem.
Mantém formatações e layouts específicos para cada fonte.
"""

import os
import traceback
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from core.app_state import AppState
from reports.reports_utils import (
    parse_dados_redis,
    carregar_regras_hw,
    parse_date_value,
    formatar_cabecalho,
    aplicar_estilo_zebra,
    ajustar_largura_colunas,
    formatar_planilha_completa,
    criar_aba_detalhada_ordenada,
    criar_abas_por_periodo
)

from utils.logger import adicionar_log

# =============================================================================
# GERAÇÃO ESPECÍFICA PARA REDIS
# =============================================================================

def gerar_relatorio_redis(serials_list, resultados, output_path, selected_periods=None):
    """
    Gera relatório completo para dados do Redis.
    Mantém toda a lógica original com abas de resumo, detalhadas e por período.

    Args:
        serials_list: Lista de seriais solicitados
        resultados: Lista de registros com dados
        output_path: Caminho completo para salvar o arquivo
        selected_periods: Lista de períodos a incluir (ex: ["Hoje", "1-7"])
    """
    try:
        adicionar_log("📍 [Redis] Iniciando geração do relatório...")

        # Carrega regras HW (agora usando função centralizada)
        REGRAS_HW = carregar_regras_hw()

        wb = Workbook()
        ws_main = wb.active
        ws_main.title = "Resumo_Tipos"

        # Estruturas de dados
        contagem = {"gsm": 0, "lorawan": 0, "p2p": 0}
        serial_data = {}
        dados_gsm = {}
        dados_lorawan = {}
        dados_p2p = {}
        modelo_counts = {}

        # Inicializa todos os seriais
        for s in serials_list:
            serial_data[s] = {
                "Modelo de HW": "N/A",
                "Data GSM": None,
                "Data LoRaWAN": None,
                "Data P2P": None,
                "Tem GSM": False,
                "Tem LORAWAN": False,
                "Tem P2P": False
            }
            modelo_counts["N/A"] = modelo_counts.get("N/A", 0) + 1

        adicionar_log(f"ℹ️ Processando {len(resultados)} registros...")

        # Processa resultados 
        """
            Avalia o cabeçalho de um arquivo contendo alguma destas opções de escrita
            para seriais, tipo do evento, modelo de hardware, o pacote bruto e data hora do evento
        
        """

        for idx, resultado in enumerate(resultados):
            try:
                if not isinstance(resultado, dict):
                    continue

                serial = (resultado.get("Serial") or 
                         resultado.get("serial") or 
                         resultado.get("rastreador_numero_serie"))

                tipo_raw = (resultado.get("Tipo") or 
                           resultado.get("tipo") or 
                           resultado.get("tipo_evento") or "")
                tipo = str(tipo_raw).lower().strip()

                modelo_hw = (resultado.get("Modelo de HW") or 
                            resultado.get("modelo_hw") or 
                            resultado.get("rastreador_versao_hardware") or "N/A")

                dados_raw = (resultado.get("Dados", "") or 
                            resultado.get("raw_package") or 
                            resultado.get("raw") or "")

                data_evt = (resultado.get("DataHora Evento") or 
                           resultado.get("data_hora_evento") or 
                           resultado.get("data_hora_recebimento") or 
                           resultado.get("data_hora_armazenamento"))

                if serial is None:
                    continue

                # Adiciona serial se não estava na lista
                if serial not in serial_data:
                    serial_data[serial] = {
                        "Modelo de HW": "N/A",
                        "Data GSM": None,
                        "Data LoRaWAN": None,
                        "Data P2P": None,
                        "Tem GSM": False,
                        "Tem LORAWAN": False,
                        "Tem P2P": False
                    }
                    serials_list.append(serial)
                    modelo_counts["N/A"] = modelo_counts.get("N/A", 0) + 1

                # Atualiza modelo de HW
                current_model = serial_data[serial]["Modelo de HW"]
                if modelo_hw != "N/A" and current_model == "N/A":
                    serial_data[serial]["Modelo de HW"] = modelo_hw
                    modelo_counts["N/A"] = max(0, modelo_counts.get("N/A", 0) - 1)
                    modelo_counts[modelo_hw] = modelo_counts.get(modelo_hw, 0) + 1

                # ✅ Normaliza data usando função centralizada
                dt_obj = parse_date_value(data_evt)
                data_evt_fmt = dt_obj.strftime("%d/%m/%Y - %H:%M:%S") if dt_obj else str(data_evt) if data_evt else None

                # Classifica por tipo
                if "gsm" in tipo:
                    serial_data[serial]["Data GSM"] = data_evt_fmt or serial_data[serial]["Data GSM"]
                    serial_data[serial]["Tem GSM"] = True
                    dados_gsm[serial] = dados_raw
                    contagem["gsm"] += 1

                elif "lora" in tipo or "lorawan" in tipo:
                    serial_data[serial]["Data LoRaWAN"] = data_evt_fmt or serial_data[serial]["Data LoRaWAN"]
                    serial_data[serial]["Tem LORAWAN"] = True
                    dados_lorawan[serial] = dados_raw
                    contagem["lorawan"] += 1

                elif "p2p" in tipo:
                    serial_data[serial]["Data P2P"] = data_evt_fmt or serial_data[serial]["Data P2P"]
                    serial_data[serial]["Tem P2P"] = True
                    dados_p2p[serial] = dados_raw
                    contagem["p2p"] += 1

            except Exception as e:
                adicionar_log(f"⚠️ Erro processando registro #{idx}: {e}")
                continue

        total_seriais = len(serials_list)
        adicionar_log(f"ℹ️ Total de seriais: {total_seriais}")

        # Calcula valores esperados
        expected = {"gsm": 0, "lorawan": 0, "p2p": 0}
        for s in serials_list:
            modelo = serial_data.get(s, {}).get("Modelo de HW", "N/A")
            regras = REGRAS_HW.get(modelo)
            if regras:
                for req in regras.get("required", []):
                    if req in expected:
                        expected[req] += 1

        # =====================================================================
        # ABA RESUMO_TIPOS
        # =====================================================================

        ws_main.append(["Total de Seriais Inseridos", total_seriais])

        if not REGRAS_HW:
            ws_main.append(["⚠️ Tabela de modelo de HW não encontrada. Validação comprometida."])

        ws_main.append([])

        ws_main.append(["Tipo de Comunicação", "Encontrado", "Valor Esperado", "Valor Relativo (%)", "Valor Absoluto (%)"])

        def calc_rel(found, expect):
            return (found / expect * 100) if expect else 0.0

        def calc_abs(found, total):
            return (found / total * 100) if total else 0.0

        count_known = len([s for s in serials_list if serial_data.get(s, {}).get("Modelo de HW") != "N/A"])
        total_base = count_known if count_known > 0 else total_seriais

        ws_main.append([
            "GSM",
            contagem["gsm"],
            expected["gsm"],
            f"{calc_rel(contagem['gsm'], expected['gsm']):.1f}%",
            f"{calc_abs(contagem['gsm'], total_base):.1f}%"
        ])

        ws_main.append([
            "LoRaWAN",
            contagem["lorawan"],
            expected["lorawan"],
            f"{calc_rel(contagem['lorawan'], expected['lorawan']):.1f}%",
            f"{calc_abs(contagem['lorawan'], total_base):.1f}%"
        ])

        ws_main.append([
            "P2P",
            contagem["p2p"],
            expected["p2p"],
            f"{calc_rel(contagem['p2p'], expected['p2p']):.1f}%",
            f"{calc_abs(contagem['p2p'], total_base):.1f}%"
        ])

        sem_comunic = len([s for s in serials_list 
                          if not serial_data.get(s, {}).get("Tem GSM") 
                          and not serial_data.get(s, {}).get("Tem LORAWAN") 
                          and not serial_data.get(s, {}).get("Tem P2P")])

        ws_main.append([
            "Sem comunicação",
            sem_comunic,
            "-",
            "-",
            f"{calc_abs(sem_comunic, total_seriais):.1f}%"
        ])

        ws_main.append([])

        # Contagem por modelo
        ws_main.append(["Modelo de HW", "Quantidade"])
        for modelo in sorted(modelo_counts.keys(), key=lambda s: str(s).lower()):
            ws_main.append([modelo, modelo_counts[modelo]])

        ws_main.append([])

        # Tabela principal
        headers = ["Serial", "Modelo de HW", "Posição GSM", "Data/Hora GSM", 
                  "Posição LoRaWAN", "Data/Hora LoRaWAN", "Posição P2P", "Data/Hora P2P"]
        ws_main.append(headers)
        main_header_row = ws_main.max_row

        serials_sorted = sorted(serials_list, 
                               key=lambda s: str(serial_data.get(s, {}).get("Modelo de HW", "N/A")).lower())

        for s in serials_sorted:
            info = serial_data.get(s, {})
            modelo = info.get("Modelo de HW", "N/A")
            regras = REGRAS_HW.get(modelo)

            def get_pos_status(has_flag, proto):
                if has_flag:
                    return "SIM"
                if not REGRAS_HW or not regras:
                    return "NÃO"
                if proto in regras.get("required", []) or proto in regras.get("optional", []):
                    return "NÃO"
                return "NÃO POSSUI"

            ws_main.append([
                s,
                modelo,
                get_pos_status(info.get("Tem GSM"), "gsm"),
                info.get("Data GSM") or "N/A",
                get_pos_status(info.get("Tem LORAWAN"), "lorawan"),
                info.get("Data LoRaWAN") or "N/A",
                get_pos_status(info.get("Tem P2P"), "p2p"),
                info.get("Data P2P") or "N/A"
            ])

        # Formata aba principal usando funções centralizadas
        formatar_cabecalho(ws_main, main_header_row)
        aplicar_estilo_zebra(ws_main, main_header_row + 1)
        ajustar_largura_colunas(ws_main)
        ws_main.freeze_panes = f"A{main_header_row + 1}"

        if ws_main.max_column >= 1:
            last_col = get_column_letter(ws_main.max_column)
            ws_main.auto_filter.ref = f"A{main_header_row}:{last_col}{ws_main.max_row}"

        # =====================================================================
        # ABA EQUIP_SEM_POSICAO
        # =====================================================================

        ws_sem = wb.create_sheet("Equip_sem_posicao")
        ws_sem.append(["Serial"])

        for s in serials_list:
            info = serial_data.get(s, {})
            if not info.get("Tem GSM") and not info.get("Tem LORAWAN") and not info.get("Tem P2P"):
                ws_sem.append([s])

        # Formata usando função centralizada
        formatar_planilha_completa(ws_sem)

        wb._sheets.remove(ws_sem)
        wb._sheets.insert(1, ws_sem)

        # =====================================================================
        # ABAS POR PERÍODO (usando função centralizada com selected_periods)
        # =====================================================================

        # Obtém configuração de abas do app_state
        app_state = AppState()
        sheet_config = app_state.get("sheet_config", {})

        # Tipos de comunicação: se vier do diálogo, usa; se não, usa todos
        comm_types = sheet_config.get("comm_types")
        if comm_types is None:
            comm_types = ["GSM", "LoRaWAN", "P2P"]
            adicionar_log(f"⚠️ Sem tipos do usuário, usando todos: {comm_types}")
        else:
            adicionar_log(f"📊 Tipos do usuário: {comm_types}")

        # Períodos: se veio como parâmetro (selected_periods), ele é a fonte da verdade
        # se não, tenta sheet_config["periods"]; se ainda não tiver, usa todos
        if selected_periods is not None:
            periods = selected_periods
            adicionar_log(f"📊 Períodos recebidos por parâmetro: {periods}")
        else:
            periods = sheet_config.get("periods")
            if periods is None:
                periods = ["Hoje", "1-7", "8-15", "+16"]
                adicionar_log(f"⚠️ Sem períodos do usuário, usando todos: {periods}")
            else:
                adicionar_log(f"📊 Períodos do usuário (sheet_config): {periods}")


        # Cria abas detalhadas (sempre)
        criar_aba_detalhada_ordenada(wb, "GSM_Detalhado", dados_gsm, 'redis')
        criar_aba_detalhada_ordenada(wb, "LoRaWAN_Detalhado", dados_lorawan, 'redis')
        criar_aba_detalhada_ordenada(wb, "P2P_Detalhado", dados_p2p, 'redis')

        # CRIA ABAS POR PERÍODO APENAS PARA TIPOS SELECIONADOS
        if "GSM" in comm_types and dados_gsm:
            adicionar_log(f"📊 Criando abas GSM para períodos: {periods}")
            criar_abas_por_periodo(wb, "GSM", dados_gsm, 'redis', periods)
        else:
            if "GSM" not in comm_types:
                adicionar_log("ℹ️ GSM não selecionado pelo usuário")
            else:
                adicionar_log("ℹ️ GSM sem dados")

        if "LoRaWAN" in comm_types and dados_lorawan:
            adicionar_log(f"📊 Criando abas LoRaWAN para períodos: {periods}")
            criar_abas_por_periodo(wb, "LoRaWAN", dados_lorawan, 'redis', periods)
        else:
            if "LoRaWAN" not in comm_types:
                adicionar_log("ℹ️ LoRaWAN não selecionado pelo usuário")
            else:
                adicionar_log("ℹ️ LoRaWAN sem dados")

        if "P2P" in comm_types and dados_p2p:
            adicionar_log(f"📊 Criando abas P2P para períodos: {periods}")
            criar_abas_por_periodo(wb, "P2P", dados_p2p, 'redis', periods)
        else:
            if "P2P" not in comm_types:
                adicionar_log("ℹ️ P2P não selecionado pelo usuário")
            else:
                adicionar_log("ℹ️ P2P sem dados")

        # Salva arquivo
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wb.save(output_path)
        adicionar_log(f"✅ Relatório Redis salvo em: {os.path.abspath(output_path)}")

        return output_path

    except Exception as e:
        adicionar_log(f"❌ Erro em gerar_relatorio_redis: {e}")
        adicionar_log(traceback.format_exc())
        return None


# =============================================================================
# GERAÇÃO ESPECÍFICA PARA API
# =============================================================================

def gerar_relatorio_api(serials, resultados, output_path):
    """
    Gera relatório simplificado para dados da API Mogno.
    Mantém formatação original da API.

    Args:
        serials: Lista de seriais solicitados
        resultados: Lista de registros com dados
        output_path: Caminho completo para salvar o arquivo
    """
    try:
        adicionar_log("📡 [API] Iniciando geração do relatório...")

        if not resultados:
            adicionar_log("⚠️ Nenhum dado disponível para gerar relatório (API).")
            return None

        wb = Workbook()
        ws = wb.active
        ws.title = "Ultimas_Posicoes_API"

        # Cabeçalhos e dados
        if isinstance(resultados, list) and resultados:
            if isinstance(resultados[0], dict):
                headers = list(resultados[0].keys())
            else:
                headers = ["Serial", "Valor"]
        else:
            headers = ["Dados"]

        ws.append(headers)

        # Normaliza valores antes de escrever
        for item in resultados:
            if isinstance(item, dict):
                row = []
                for value in item.values():
                    # Converte objetos não suportados para string
                    if isinstance(value, (dict, list)):
                        value = str(value)
                    elif not isinstance(value, (str, int, float, bool, type(None))):
                        # Converte enums, protobuf, etc. para string
                        value = str(value)

                    # Trunca strings muito longas
                    if isinstance(value, str) and len(value) > 32000:
                        value = value[:32000] + "… [TRUNCADO]"

                    row.append(value)

                ws.append(row)
            else:
                ws.append([str(item)])

        # Formata usando função centralizada
        formatar_planilha_completa(ws)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wb.save(output_path)
        adicionar_log(f"✅ Relatório API salvo em: {os.path.relpath(output_path)}")

        return output_path

    except Exception as e:
        adicionar_log(f"❌ Erro em gerar_relatorio_api: {e}")
        adicionar_log(traceback.format_exc())
        return None


# =============================================================================
# FUNÇÃO PRINCIPAL UNIFICADA (INTERFACE PÚBLICA)
# =============================================================================

def gerar_relatorio(serials, resultados, output_path, selected_periods=None, origem='redis'):
    """
    Interface unificada para geração de relatórios de Últimas Posições.
    A origem é determinada pelo tipo de requisição (não há detecção automática).

    Args:
        serials: Lista de seriais solicitados
        resultados: Lista de registros com dados
        output_path: Caminho completo para salvar o arquivo
        selected_periods: Lista de períodos a incluir (ex: ["Hoje", "1-7"])
        origem: 'redis' ou 'api' (obrigatório)

    Returns:
        str: Caminho do arquivo gerado ou None em caso de erro
    """
    try:
        if not resultados and not serials:
            adicionar_log("⚠️ Nenhum dado disponível para gerar relatório.")
            return None

        # Usa origem explícita
        adicionar_log(f"🔍 Origem: {origem.upper()}")

        # Delega para função específica
        if origem == 'redis':
            return gerar_relatorio_redis(serials, resultados, output_path, selected_periods)
        else:
            return gerar_relatorio_api(serials, resultados, output_path)

    except Exception as e:
        adicionar_log(f"❌ Erro crítico em gerar_relatorio: {e}")
        adicionar_log(traceback.format_exc())
        return None
