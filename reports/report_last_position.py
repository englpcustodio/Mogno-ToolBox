# reports/report_last_position.py
"""
Gerador Unificado de Relatório: Últimas Posições
Suporta dados de API Mogno e Redis com tratamento específico para cada origem.
Mantém formatações e layouts específicos para cada fonte.

Atualizado para:
- Total de Seriais Válidos
- Valor Absoluto (%) = Encontrado / Total Inseridos * 100
- Separação de Data e Hora (GSM, LoRaWAN, P2P)
- Ordenação por prioridade: GSM (mais recente) -> P2P -> LoRaWAN
- Contagens por período baseadas nas abas por período geradas
- Ordenação da aba Equip_sem_posicao do menor para o maior
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
        # contagem por serial (único): quantos seriais trouxeram posição por tecnologia
        found_serials = {"gsm": set(), "lorawan": set(), "p2p": set()}
        serial_data = {}
        dados_gsm = {}
        dados_lorawan = {}
        dados_p2p = {}
        modelo_counts = {}

        # Inicializa todos os seriais
        for s in serials_list:
            serial_data[s] = {
                "Modelo de HW": "N/A",
                "dt_gsm": None,
                "dt_lora": None,
                "dt_p2p": None,
                "Data GSM": None,
                "Hora GSM": None,
                "Data LoRaWAN": None,
                "Hora LoRaWAN": None,
                "Data P2P": None,
                "Hora P2P": None,
                "Tem GSM": False,
                "Tem LORAWAN": False,
                "Tem P2P": False
            }
            modelo_counts["N/A"] = modelo_counts.get("N/A", 0) + 1

        adicionar_log(f"ℹ️ Processando {len(resultados)} registros...")

        # Processa resultados
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
                        "dt_gsm": None,
                        "dt_lora": None,
                        "dt_p2p": None,
                        "Data GSM": None,
                        "Hora GSM": None,
                        "Data LoRaWAN": None,
                        "Hora LoRaWAN": None,
                        "Data P2P": None,
                        "Hora P2P": None,
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

                # Normaliza data usando função centralizada (retorna datetime ou None)
                dt_obj = parse_date_value(data_evt)

                # Classifica por tipo
                if "gsm" in tipo:
                    # guarda o datetime mais recente para o serial (se houver múltiplos)
                    existing = serial_data[serial].get("dt_gsm")
                    if dt_obj and (existing is None or dt_obj > existing):
                        serial_data[serial]["dt_gsm"] = dt_obj
                        serial_data[serial]["Data GSM"] = dt_obj.strftime("%d/%m/%Y")
                        serial_data[serial]["Hora GSM"] = dt_obj.strftime("%H:%M:%S")
                    serial_data[serial]["Tem GSM"] = True
                    dados_gsm[serial] = dados_raw
                    found_serials["gsm"].add(serial)

                elif "lora" in tipo or "lorawan" in tipo:
                    existing = serial_data[serial].get("dt_lora")
                    if dt_obj and (existing is None or dt_obj > existing):
                        serial_data[serial]["dt_lora"] = dt_obj
                        serial_data[serial]["Data LoRaWAN"] = dt_obj.strftime("%d/%m/%Y")
                        serial_data[serial]["Hora LoRaWAN"] = dt_obj.strftime("%H:%M:%S")
                    serial_data[serial]["Tem LORAWAN"] = True
                    dados_lorawan[serial] = dados_raw
                    found_serials["lorawan"].add(serial)

                elif "p2p" in tipo:
                    existing = serial_data[serial].get("dt_p2p")
                    if dt_obj and (existing is None or dt_obj > existing):
                        serial_data[serial]["dt_p2p"] = dt_obj
                        serial_data[serial]["Data P2P"] = dt_obj.strftime("%d/%m/%Y")
                        serial_data[serial]["Hora P2P"] = dt_obj.strftime("%H:%M:%S")
                    serial_data[serial]["Tem P2P"] = True
                    dados_p2p[serial] = dados_raw
                    found_serials["p2p"].add(serial)

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
        # CRIA ABAS DETALHADAS E POR PERÍODO (para depois contabilizar os períodos)
        # =====================================================================

        # Cria abas detalhadas (sempre)
        criar_aba_detalhada_ordenada(wb, "GSM_Detalhado", dados_gsm, 'redis')
        criar_aba_detalhada_ordenada(wb, "LoRaWAN_Detalhado", dados_lorawan, 'redis')
        criar_aba_detalhada_ordenada(wb, "P2P_Detalhado", dados_p2p, 'redis')

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

        # =====================================================================
        # ABA RESUMO_TIPOS - Agora com Totais, Válidos, Valores relativos e absolutos,
        # e colunas de contagem por período
        # =====================================================================

        # Funções utilitárias
        def calc_rel(found, expect):
            return (found / expect * 100) if expect else 0.0

        def calc_abs(found, total):
            return (found / total * 100) if total else 0.0

        # Contadores únicos por tecnologia (encontrado)
        contagem = {
            "gsm": len(found_serials["gsm"]),
            "lorawan": len(found_serials["lorawan"]),
            "p2p": len(found_serials["p2p"])
        }

        # Quantidade sem comunicação (seriais que não aparecem em nenhum conjunto)
        sem_comunic = len([s for s in serials_list
                          if s not in found_serials["gsm"]
                          and s not in found_serials["lorawan"]
                          and s not in found_serials["p2p"]])

        # Total válidos = inseridos - sem comunicação
        total_validos = total_seriais - sem_comunic

        # Cabeçalho inicial e totais
        ws_main.append(["Total de Seriais Inseridos", total_seriais])
        ws_main.append(["Total de Seriais Válidos", total_validos])

        if not REGRAS_HW:
            ws_main.append(["⚠️ Tabela de modelo de HW não encontrada. Validação comprometida."])

        ws_main.append([])

        # Cabeçalhos da tabela
        # Primeiro linha com títulos fixos
        header_row_1 = [
            "Tipo de Comunicação", "Encontrado", "Valor Esperado", "Valor Relativo (%)", "Valor Absoluto (%)"
        ]
        # Em seguida, colunas de períodos (dinâmicas conforme 'periods')
        period_headers = ["Período " + p for p in periods]
        ws_main.append(header_row_1 + period_headers)
        main_header_row_index = ws_main.max_row

        # Função para contar quantos seriais há em uma aba específica criada (se existir)
        def count_entries_in_sheet(wb_obj, sheet_name):
            if sheet_name not in wb_obj.sheetnames:
                return 0
            ws = wb_obj[sheet_name]
            count = 0
            # procura na primeira coluna, a partir da linha 2
            for r in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1, values_only=True):
                if r and r[0] not in (None, ""):
                    count += 1
            return count

        # Mapeia os nomes das abas de período que provavelmente foram criadas por criar_abas_por_periodo
        # Ex.: "GSM_Hoje", "GSM_1-7", "GSM_8-15", "GSM_+16"
        def build_period_sheet_name(prefix, period_label):
            # mantemos o label tal como vem (ex: "+16")
            # remove espaços e usa underline para consistência
            label = str(period_label).strip()
            return f"{prefix}_{label}"

        # Obtem contagens por período para um dado prefixo (GSM, LoRaWAN, P2P)
        def get_period_counts_for_prefix(prefix):
            counts = []
            for p in periods:
                sheet_name = build_period_sheet_name(prefix, p)
                cnt = count_entries_in_sheet(wb, sheet_name)
                counts.append(cnt)
            return counts

        # Prepara linhas para cada tecnologia
        # GSM
        gsm_counts_by_period = get_period_counts_for_prefix("GSM")
        lorawan_counts_by_period = get_period_counts_for_prefix("LoRaWAN")
        p2p_counts_by_period = get_period_counts_for_prefix("P2P")

        ws_main.append([
            "GSM",
            contagem["gsm"],
            expected["gsm"],
            f"{calc_rel(contagem['gsm'], expected['gsm']):.1f}%",
            f"{calc_abs(contagem['gsm'], total_seriais):.1f}%"
        ] + gsm_counts_by_period)

        ws_main.append([
            "LoRaWAN",
            contagem["lorawan"],
            expected["lorawan"],
            f"{calc_rel(contagem['lorawan'], expected['lorawan']):.1f}%",
            f"{calc_abs(contagem['lorawan'], total_seriais):.1f}%"
        ] + lorawan_counts_by_period)

        ws_main.append([
            "P2P",
            contagem["p2p"],
            expected["p2p"],
            f"{calc_rel(contagem['p2p'], expected['p2p']):.1f}%",
            f"{calc_abs(contagem['p2p'], total_seriais):.1f}%"
        ] + p2p_counts_by_period)

        ws_main.append([
            "Sem comunicação",
            sem_comunic,
            "-",
            "-",
            f"{calc_abs(sem_comunic, total_seriais):.1f}%"
        ] + (["-"] * len(periods)))

        ws_main.append([])

        # Contagem por modelo
        ws_main.append(["Modelo de HW", "Quantidade"])
        for modelo in sorted(modelo_counts.keys(), key=lambda s: str(s).lower()):
            ws_main.append([modelo, modelo_counts[modelo]])

        ws_main.append([])

        # Tabela principal: cabeçalhos com Data/Hora separados
        headers = [
            "Serial", "Modelo de HW", "Posição GSM",
            "Data GSM", "Hora GSM",
            "Posição LoRaWAN", "Data LoRaWAN", "Hora LoRaWAN",
            "Posição P2P", "Data P2P", "Hora P2P"
        ]
        ws_main.append(headers)
        main_header_row = ws_main.max_row

        # Ordena serials: prioridade dt_gsm (desc), se não há, dt_p2p, se não, dt_lora
        def sort_key_for_serial(s):
            info = serial_data.get(s, {})
            # prefer GSM, then P2P, then LoRaWAN
            dt = info.get("dt_gsm") or info.get("dt_p2p") or info.get("dt_lora")
            # retornamos uma tupla (has_dt, dt) para ordenar; sem dt -> menor
            if dt:
                return (1, dt)
            else:
                return (0, datetime.min)

        serials_sorted = sorted(serials_list, key=sort_key_for_serial, reverse=True)

        # Helper to get position status baseado em regras e flags
        def get_pos_status(has_flag, modelo, proto):
            if has_flag:
                return "SIM"
            if not REGRAS_HW or not modelo:
                return "NÃO"
            regras = REGRAS_HW.get(modelo)
            if not regras:
                return "NÃO"
            if proto in regras.get("required", []) or proto in regras.get("optional", []):
                return "NÃO"
            return "NÃO POSSUI"

        for s in serials_sorted:
            info = serial_data.get(s, {})
            modelo = info.get("Modelo de HW", "N/A")

            row = [
                s,
                modelo,
                get_pos_status(info.get("Tem GSM"), modelo, "gsm"),
                info.get("Data GSM") or "N/A",
                info.get("Hora GSM") or "N/A",
                get_pos_status(info.get("Tem LORAWAN"), modelo, "lorawan"),
                info.get("Data LoRaWAN") or "N/A",
                info.get("Hora LoRaWAN") or "N/A",
                get_pos_status(info.get("Tem P2P"), modelo, "p2p"),
                info.get("Data P2P") or "N/A",
                info.get("Hora P2P") or "N/A"
            ]
            ws_main.append(row)

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
        sem_list = []

        for s in serials_list:
            info = serial_data.get(s, {})
            if not info.get("Tem GSM") and not info.get("Tem LORAWAN") and not info.get("Tem P2P"):
                sem_list.append(s)

        # Ordena sem_list do menor para o maior (tenta int -> fallback str)
        def sort_sem_key(x):
            try:
                return int(x)
            except Exception:
                return str(x)

        sem_list_sorted = sorted(sem_list, key=sort_sem_key)

        for s in sem_list_sorted:
            ws_sem.append([s])

        # Formata usando função centralizada
        formatar_planilha_completa(ws_sem)

        # Reposiciona a aba sem_posicao para segunda posição
        # garantindo que ela exista na lista de sheets
        try:
            if ws_sem in wb._sheets:
                wb._sheets.remove(ws_sem)
                wb._sheets.insert(1, ws_sem)
        except Exception:
            # fallback: ignore se falhar
            pass

        # =====================================================================
        # Salva arquivo
        # =====================================================================

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
