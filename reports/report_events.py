# reports/report_events.py
"""
Gerador de relatório Excel para análise de eventos de rastreadores.
Cria aba de resumo consolidado e abas detalhadas por tipo de evento.
"""

import traceback
from datetime import datetime
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from utils.logger import adicionar_log
from reports.reports_utils import (
    parse_proto_eventos,
    parse_date_value,
    extrair_tipo_evento,
    calcular_periodo_dias,
    formatar_cabecalho_customizado,
    mesclar_e_formatar_celula,
    ajustar_largura_colunas,
    aplicar_estilo_zebra,
    formatar_planilha_completa,
    criar_aba_seriais_sem_evento
)

# ========== MAPEAMENTO DE EVENTOS ==========
EVENT_NAMES = {
    0: "POSICAO", 1: "PANICO", 2: "FAKE_VIOLADO", 3: "FAKE_RESTAURADO",
    4: "ANTENA_GPS_CORTADA", 5: "ANTENA_GPS_RECONECTADA", 6: "IGNICAO_ON",
    7: "IGNICAO_OFF", 8: "BATERIA_EXTERNA_PERDIDA", 9: "BATERIA_EXTERNA_RECONECTADA",
    10: "BATERIA_EXTERNA_BAIXA", 11: "BATERIA_INTERNA_PERDIDA", 12: "BATERIA_INTERNA_RECONECTADA",
    13: "BATERIA_INTERNA_BAIXA", 14: "BATERIA_INTERNA_ERRO", 15: "INICIO_SLEEP",
    16: "RESET_RASTREADOR", 17: "INICIO_SUPER_SLEEP", 18: "BLOQUEIO_ANTIFURTO",
    19: "DESBLOQUEIO_ANTIFURTO", 20: "RESPOSTA_POSICAO_SOLICITADA", 21: "POSICAO_EM_SLEEP",
    22: "POSICAO_EM_SUPER_SLEEP", 23: "OPERADORA_CELULAR", 24: "ALARME_ANTIFURTO",
    25: "DADOS_VIAGEM", 26: "DADOS_ESTACIONAMENTO", 27: "PAINEL_VIOLADO",
    28: "PAINEL_RESTAURADO", 29: "TECLADO_CONECTADO", 30: "TECLADO_DESCONECTADO",
    31: "SENSOR_LIVRE_RESTAURADO", 32: "MACRO", 33: "MENSAGEM_NUMERICA",
    34: "TERMINO_SLEEP", 35: "TERMINO_SUPER_SLEEP", 36: "INICIO_DEEP_SLEEP",
    37: "TERMINO_DEEP_SLEEP", 38: "BATERIA_BACKUP_RECONECTADA", 39: "BATERIA_BACKUP_DESCONECTADA",
    40: "ANTENA_GPS_EM_CURTO", 41: "ANTIFURTO_RESTAURADO", 42: "ANTIFURTO_VIOLADO",
    43: "INICIO_MODO_PANICO", 44: "FIM_MODO_PANICO", 45: "ALERTA_ACELERACAO_FORA_PADRAO",
    46: "ALERTA_FREADA_BRUSCA", 47: "ALERTA_CURVA_AGRESSIVA", 48: "ALERTA_DIRECAO_ACIMA_VELOCIDADE_PADRAO",
    49: "JAMMING_DETECTADO", 50: "PLATAFORMA_ACIONADA", 51: "BOTAO_ANTIFURTO_PRESSIONADO",
    52: "EVENTO_GENERICO", 53: "CARCACA_VIOLADA", 54: "JAMMING_RESTAURADO",
    55: "GPS_FALHA", 56: "IDENTIFICACAO_CONDUTOR", 57: "BLOQUEADOR_VIOLADO",
    58: "BLOQUEADOR_RESTAURADO", 59: "COLISAO", 60: "ECU_VIOLADA",
    61: "ECU_INSTALADA", 62: "IDENTIFICACAO_CONDUTOR_NAO_CADASTRADO", 63: "FREQ_CONT_PULSOS_ACIMA_LIMITE",
    64: "PLATAFORMA_DESACIONADA", 65: "BETONEIRA_CARREGANDO", 66: "BETONEIRA_DESCARREGANDO",
    67: "PORTA_ABERTA", 68: "PORTA_FECHADA", 69: "ALERTA_FREADA_BRUSCA_ACELERACAO_FORA_PADRAO",
    70: "TIMEOUT_IDENTIFICADOR_CONDUTOR", 71: "BAU_ABERTO", 72: "BAU_FECHADO",
    73: "CARRETA_ENGATADA", 74: "CARRETA_DESENGATADA", 75: "TECLADO_MENSAGEM",
    76: "ACAO_EMBARCADA_ACIONADA", 77: "ACAO_EMBARCADA_DESACIONADA", 78: "FIM_VELOCIDADE_ACIMA_DO_PADRAO",
    79: "ENTRADA_EM_BANGUELA", 80: "SAIDA_DE_BANGUELA", 81: "RPM_EXCEDIDO",
    82: "ALERTA_DE_DIRECAO_COM_VELOCIDADE_EXCESSIVA_NA_CHUVA", 83: "FIM_DE_VELOCIDADE_ACIMA_DO_PADRAO_NA_CHUVA",
    84: "VEICULO_PARADO_COM_MOTOR_FUNCIONANDO", 85: "VEICULO_PARADO", 86: "CALIBRACAO_AUTOMATICA_DO_RPM_REALIZADA",
    87: "CALIBRACAO_DO_ODOMETRO_FINALIZADA", 88: "MODO_ERB", 89: "EMERGENCIA_OU_POSICAO_DE_DISPOSITIVO_RF_EM_MODO_ERB",
    90: "EMERGENCIA_POR_PRESENCA", 91: "EMERGENCIA_POR_RF", 92: "DISPOSITIVO_PRESENCA_AUSENTE",
    93: "BATERIA_VEICULO_ABAIXO_LIMITE_PRE_DEFINIDO", 94: "LEITURA_OBD", 95: "VEICULO_PARADO_COM_RPM",
    96: "MODO_EMERGENCIA_POR_JAMMING", 97: "EMERGENCIA_POR_GPRS", 98: "DETECCAO_RF",
    99: "DISPOSITIVO_PRESENCA_RECUPERADO", 100: "ENTRADA_MODO_EMERGENCIA", 101: "SAIDA_MODO_EMERGENCIA",
    102: "EMERGENCIA", 103: "INICIO_DE_MOVIMENTO", 104: "FIM_DE_MOVIMENTO",
    105: "VEICULO_PARADO_COM_IGNICAO_LIGADA", 106: "REGRA_GEOGRAFICO", 107: "ALERTA_DE_IGNICAO_SEM_FAROL",
    108: "FIM_DE_IGNICAO_SEM_FAROL", 109: "INICIO_MOVIMENTO_SEM_BATERIA_EXTERNA", 110: "FIM_MOVIMENTO_SEM_BATERIA_EXTERNA",
    111: "RASTREAMENTO_ATIVADO", 112: "RASTREAMENTO_DESATIVADO", 113: "ALERTA_DE_MOTORISTA_COM_SONOLENCIA",
    114: "ALERTA_DE_MOTORISTA_COM_DISTRACAO", 115: "ALERTA_DE_MOTORISTA_BOCEJANDO", 116: "ALERTA_DE_MOTORISTA_AO_TELEFONE",
    117: "ALERTA_DE_MOTORISTA_FUMANDO"
}


def _processar_eventos(eventos_data):
    """
    Processa eventos brutos e extrai informações estruturadas.

    Returns:
        tuple: (eventos_parseados, tipos_eventos_unicos, seriais_com_eventos)
    """
    eventos_parseados = []
    tipos_eventos = set()
    seriais_com_eventos = set()

    for evento in eventos_data:
        try:
            proto = evento.get('proto', '')
            serial = evento.get('serial', 'N/A')

            # ✅ USA PARSER ESPECÍFICO PARA PROTO
            dados_parseados = parse_proto_eventos(proto)

            # Extrai tipo do evento
            tipo_evento = extrair_tipo_evento(proto)
            tipos_eventos.add(tipo_evento)
            seriais_com_eventos.add(serial)

            # Adiciona campos da API
            dados_parseados['Serial'] = serial
            dados_parseados['tipo_evento'] = tipo_evento
            dados_parseados['horario_api'] = evento.get('horario', 'N/A')
            dados_parseados['latitude_api'] = evento.get('latitude', 'N/A')
            dados_parseados['longitude_api'] = evento.get('logitude', 'N/A')
            dados_parseados['direcao_api'] = evento.get('direcao', 'N/A')
            dados_parseados['fix_gps'] = 'Sim' if evento.get('fix') == '1' else 'Não'
            dados_parseados['online'] = 'Sim' if evento.get('onLine') == '1' else 'Não'
            dados_parseados['numero_sequencial_api'] = evento.get('numeroSequencial', 'N/A')

            eventos_parseados.append(dados_parseados)

        except Exception as e:
            adicionar_log(f"⚠️ Erro ao processar evento: {e}")
            continue

    return eventos_parseados, sorted(tipos_eventos), seriais_com_eventos


def _gerar_resumo_eventos(eventos_parseados, start_datetime, end_datetime, filtros_str):
    """
    Gera dados consolidados para aba de resumo.

    Returns:
        dict: {serial: {tipo_evento: {'ultima_data': datetime, 'quantidade': int}}}
    """
    resumo = defaultdict(lambda: defaultdict(lambda: {'ultima_data': None, 'quantidade': 0}))

    for evento in eventos_parseados:
        try:
            serial = evento.get('Serial', 'N/A')
            tipo_evento = evento.get('tipo_evento', 'DESCONHECIDO')
            horario = evento.get('horario_api', 'N/A')

            # Atualiza última data/hora
            if horario != 'N/A':
                try:
                    data_atual = datetime.strptime(horario, "%d/%m/%Y %H:%M:%S")
                    if resumo[serial][tipo_evento]['ultima_data'] is None or \
                       data_atual > resumo[serial][tipo_evento]['ultima_data']:
                        resumo[serial][tipo_evento]['ultima_data'] = data_atual
                except:
                    pass

            # Incrementa quantidade
            resumo[serial][tipo_evento]['quantidade'] += 1

        except Exception as e:
            adicionar_log(f"⚠️ Erro ao processar resumo: {e}")
            continue

    return resumo


def _criar_aba_resumo(wb, resumo_data, start_datetime, end_datetime, filtros_list):
    """
    Cria aba "Resumo_Eventos" com layout especificado.
    """
    try:
        ws = wb.create_sheet("Resumo_Eventos", 0)  # Primeira aba

        # ========== LINHA 1: Período de Avaliação ==========
        dias_periodo = calcular_periodo_dias(start_datetime, end_datetime)
        ws.append([
            "Período de Avaliação dos eventos",
            start_datetime,
            end_datetime,
            f"{dias_periodo} dias"
        ])

        # Formata linha 1
        for col in range(1, 5):
            cell = ws.cell(1, col)
            cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            cell.font = Font(bold=True, size=11)

        # ========== LINHA 2: Filtros Pesquisados ==========
        filtros_row = ["Filtros de Eventos pesquisados"] + filtros_list
        ws.append(filtros_row)

        # Formata linha 2
        for col in range(1, len(filtros_row) + 1):
            cell = ws.cell(2, col)
            cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
            cell.font = Font(bold=True, size=11)

        # ========== LINHA 3: Cabeçalho de Dados ==========
        headers = ["Serial"]
        for filtro in filtros_list:
            headers.append(filtro)
            headers.append(f"Quantidade_{filtro}")

        ws.append(headers)

        # Formata cabeçalho (linha 3)
        formatar_cabecalho_customizado(ws, 3, "305496")

        # ========== LINHAS 4+: Dados por Serial ==========
        for serial, tipos_data in sorted(resumo_data.items()):
            row = [serial]

            for filtro in filtros_list:
                if filtro in tipos_data:
                    ultima_data = tipos_data[filtro]['ultima_data']
                    quantidade = tipos_data[filtro]['quantidade']

                    data_str = ultima_data.strftime("%d/%m/%Y %H:%M:%S") if ultima_data else "N/A"
                    row.append(data_str)
                    row.append(quantidade)
                else:
                    row.append("N/A")
                    row.append(0)

            ws.append(row)

        # ✅ AJUSTA LARGURA AO FINAL
        ajustar_largura_colunas(ws, min_width=15, max_width=40)

        # Congela painéis (linha 3)
        ws.freeze_panes = 'A4'

        # Autofilter
        if ws.max_column >= 1 and ws.max_row >= 3:
            last_col = get_column_letter(ws.max_column)
            ws.auto_filter.ref = f"A3:{last_col}{ws.max_row}"

        adicionar_log(f"✅ Aba 'Resumo_Eventos' criada com {len(resumo_data)} seriais")

    except Exception as e:
        adicionar_log(f"❌ Erro ao criar aba de resumo: {e}")
        adicionar_log(traceback.format_exc())


def _criar_abas_detalhadas(wb, eventos_parseados, tipos_eventos, modo_rapido=True):
    """
    Cria abas detalhadas por tipo de evento.

    Args:
        modo_rapido: Se True, não aplica zebra (mais rápido)
    """
    # Agrupa eventos por tipo
    eventos_por_tipo = defaultdict(list)

    for evento in eventos_parseados:
        tipo = evento.get('tipo_evento', 'DESCONHECIDO')
        eventos_por_tipo[tipo].append(evento)

    # Cria aba para cada tipo
    for tipo_evento in tipos_eventos:
        try:
            eventos = eventos_por_tipo.get(tipo_evento, [])

            if not eventos:
                adicionar_log(f"ℹ️ Tipo '{tipo_evento}': sem eventos")
                continue

            # Nome da aba (máximo 31 caracteres)
            sheet_name = tipo_evento[:31]

            # Coleta todas as chaves disponíveis
            todas_chaves = set()
            for ev in eventos:
                todas_chaves.update(ev.keys())

            # Ordena colunas: Serial e tipo_evento primeiro
            colunas_prioritarias = ['Serial', 'tipo_evento', 'horario_api', 'data_hora_evento']
            headers = [c for c in colunas_prioritarias if c in todas_chaves]
            headers += sorted([c for c in todas_chaves if c not in colunas_prioritarias])

            # Cria aba
            ws = wb.create_sheet(sheet_name)
            ws.append(headers)

            # Ordena eventos por data (mais recente primeiro)
            def get_datetime(ev):
                for hint in ['horario_api', 'data_hora_evento', 'data_hora_recebimento']:
                    val = ev.get(hint)
                    if val:
                        dt = parse_date_value(val)
                        if dt:
                            return dt
                return datetime.fromtimestamp(0)

            eventos_ordenados = sorted(eventos, key=get_datetime, reverse=True)

            # Escreve dados
            for evento in eventos_ordenados:
                row = []
                for header in headers:
                    valor = evento.get(header, "")

                    # Trunca strings muito longas
                    if isinstance(valor, str) and len(valor) > 32000:
                        valor = valor[:32000] + "… [TRUNCADO]"

                    row.append(valor)

                ws.append(row)

            # ✅ FORMATAÇÃO COM TOGGLE (modo_rapido)
            formatar_cabecalho_customizado(ws, 1, "70AD47")  # Verde

            # Só aplica zebra se NÃO for modo rápido
            if not modo_rapido and ws.max_row <= 50000:
                aplicar_estilo_zebra(ws, min_row=2)

            # ✅ AJUSTA LARGURA AO FINAL
            ajustar_largura_colunas(ws, min_width=12, max_width=50)

            ws.freeze_panes = 'A2'

            # Autofilter
            if ws.max_column >= 1 and ws.max_row >= 1:
                last_col = get_column_letter(ws.max_column)
                ws.auto_filter.ref = f"A1:{last_col}{ws.max_row}"

            adicionar_log(f"  ✅ Aba '{sheet_name}': {len(eventos)} eventos")

        except Exception as e:
            adicionar_log(f"❌ Erro ao criar aba '{tipo_evento}': {e}")
            continue


def gerar_relatorio(serials, eventos_data, output_path, start_datetime=None, end_datetime=None, 
                   filtros_str="", modo_rapido=True):
    """
    Gera relatório Excel completo com resumo e abas detalhadas.

    Args:
        serials (list): Lista de seriais requisitados
        eventos_data (list): Lista de dicionários com dados dos eventos
        output_path (str): Caminho do arquivo de saída
        start_datetime (str): Data/hora início (formato "dd/MM/yyyy HH:mm:ss")
        end_datetime (str): Data/hora fim
        filtros_str (str): String com IDs dos filtros (ex: "6,7,56")
        modo_rapido (bool): Se True, não aplica zebra (padrão: True)

    Returns:
        str: Caminho do arquivo gerado ou None em caso de erro
    """
    try:
        adicionar_log(f"📊 Gerando relatório de eventos: {output_path}")
        adicionar_log(f"⚡ Modo rápido: {'ATIVADO' if modo_rapido else 'DESATIVADO'}")

        if not eventos_data:
            adicionar_log("⚠️ Nenhum evento para gerar relatório")
            return None

        # ========== 1. PROCESSA EVENTOS ==========
        adicionar_log("📋 Processando eventos...")
        eventos_parseados, tipos_eventos, seriais_com_eventos = _processar_eventos(eventos_data)

        if not eventos_parseados:
            adicionar_log("⚠️ Nenhum evento válido processado")
            return None

        # ========== 2. IDENTIFICA SERIAIS SEM EVENTOS ==========
        seriais_requisitados = set(serials)
        seriais_sem_evento = sorted(seriais_requisitados - seriais_com_eventos)

        adicionar_log(f"📊 Seriais requisitados: {len(seriais_requisitados)}")
        adicionar_log(f"📊 Seriais com eventos: {len(seriais_com_eventos)}")
        adicionar_log(f"📊 Seriais sem eventos: {len(seriais_sem_evento)}")

        # ========== 3. GERA RESUMO ==========
        adicionar_log("📋 Gerando dados de resumo...")

        # Converte IDs de filtros em nomes
        filtros_list = []
        if filtros_str:
            for fid in filtros_str.split(','):
                try:
                    filtros_list.append(EVENT_NAMES.get(int(fid.strip()), f"Evento_{fid}"))
                except:
                    pass

        if not filtros_list:
            filtros_list = list(tipos_eventos)

        resumo_data = _gerar_resumo_eventos(eventos_parseados, start_datetime, end_datetime, filtros_str)

        # ========== 4. CRIA WORKBOOK ==========
        wb = Workbook()
        wb.remove(wb.active)  # Remove aba padrão

        # ========== 5. CRIA ABA DE RESUMO (posição 0) ==========
        _criar_aba_resumo(wb, resumo_data, start_datetime, end_datetime, filtros_list)

        # ========== 6. CRIA ABA SERIAIS_SEM_EVENTO (posição 1) ==========
        if seriais_sem_evento:
            criar_aba_seriais_sem_evento(wb, seriais_sem_evento, filtros_list)

        # ========== 7. CRIA ABAS DETALHADAS ==========
        adicionar_log("📋 Gerando abas detalhadas por tipo de evento...")
        _criar_abas_detalhadas(wb, eventos_parseados, tipos_eventos, modo_rapido=modo_rapido)

        # ========== 8. SALVA ARQUIVO ==========
        wb.save(output_path)

        adicionar_log(f"✅ Relatório gerado com sucesso!")
        adicionar_log(f"   📊 Resumo: {len(resumo_data)} seriais")
        adicionar_log(f"   📋 Tipos de eventos: {len(tipos_eventos)}")
        adicionar_log(f"   📄 Total de eventos: {len(eventos_data)}")
        adicionar_log(f"   ⚠️ Seriais sem eventos: {len(seriais_sem_evento)}")

        return output_path

    except Exception as e:
        adicionar_log(f"❌ Erro ao gerar relatório de eventos: {e}")
        adicionar_log(traceback.format_exc())
        return None
