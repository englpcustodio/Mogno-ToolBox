import os
import openpyxl
import re
from datetime import datetime
from utils.helpers import epoch_to_datetime, auto_size_columns
from utils.logger import adicionar_log

def relatorio_ultimaposicao_excel(seriais, resultados):
    """Salva os dados dos seriais em um arquivo Excel.
        seriais (list): Lista de seriais.
        resultados (list): Lista de resultados com informações para cada serial.
    """

    DIR_LAST_POS = 'relatorios_gerados/ultimas_posicoes'

    # Criação do diretório se não existir
    if not os.path.exists(DIR_LAST_POS):
        os.makedirs(DIR_LAST_POS)

    # Formatação da data e hora para o nome do arquivo
    data_hora_formatada = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f'relatorio_ultimaposicao_{data_hora_formatada}.xlsx'

    # Caminho completo do arquivo
    caminho_arquivo = os.path.join(DIR_LAST_POS, nome_arquivo)

    # Inicializa a aba/planilha principal
    wb = openpyxl.Workbook()
    ws_main = wb.active
    ws_main.title = "tipos_comunicacao"

    # Contagem dos tipos de comunicação
    contagem = {'gsm': 0, 'lorawan': 0, 'p2p': 0}
    serial_data = {}
    dados_gsm = {}      # Armazena dados brutos (string) para a aba GSM
    dados_lorawan = {}  # Armazena dados brutos (string) para a aba LoRaWAN
    dados_p2p = {}      # Armazena dados brutos (string) para a aba P2P

    # Processa os resultados para coletar dados
    for resultado in resultados:
        serial = resultado.get('Serial')
        tipo = resultado.get('Tipo')
        if serial is None or tipo is None:
            continue  # Ignora entradas sem serial ou tipo

        # Inicializa um dicionário para cada serial se não existir
        if serial not in serial_data:
            serial_data[serial] = {
                'Modelo de HW': 'N/A',
                'Pacote GSM': 'NÃO',
                'Dados GSM': 'N/A',
                'DataHoraEvento GSM': 'N/A',
                'Pacote LoRaWAN': 'NÃO',
                'Dados LoRaWAN': 'N/A',
                'DataHoraEvento LoRaWAN': 'N/A',
                'Pacote P2P': 'NÃO',
                'Dados P2P': 'N/A',
                'DataHoraEvento P2P': 'N/A',
            }

        # Atualiza informações com base no tipo
        dados = str(resultado.get('Dados', 'N/A'))
        datahora_evento = str(resultado.get('DataHora Evento', 'N/A'))
        modelo_hw = str(resultado.get('Modelo de HW', 'N/A'))

        # Atualização dos dados correspondentes ao tipo
        if tipo == 'gsm':
            serial_data[serial]['Modelo de HW'] = modelo_hw
            serial_data[serial]['Pacote GSM'] = 'SIM'
            serial_data[serial]['Dados GSM'] = dados
            serial_data[serial]['DataHoraEvento GSM'] = datahora_evento
            dados_gsm[serial] = dados  # Armazena dados brutos para a aba GSM
            contagem['gsm'] += 1
        elif tipo == 'lorawan':
            serial_data[serial]['Modelo de HW'] = modelo_hw
            serial_data[serial]['Pacote LoRaWAN'] = 'SIM'
            serial_data[serial]['Dados LoRaWAN'] = dados
            serial_data[serial]['DataHoraEvento LoRaWAN'] = datahora_evento
            dados_lorawan[serial] = dados  # Armazena dados brutos para a aba LoRaWAN
            contagem['lorawan'] += 1
        elif tipo == 'p2p':
            serial_data[serial]['Modelo de HW'] = modelo_hw
            serial_data[serial]['Pacote P2P'] = 'SIM'
            serial_data[serial]['Dados P2P'] = dados
            serial_data[serial]['DataHoraEvento P2P'] = datahora_evento
            dados_p2p[serial] = dados  # Armazena dados brutos para a aba P2P
            contagem['p2p'] += 1

    # Adiciona informações gerais na planilha principal
    ws_main.append(["Total de Seriais", len(seriais)])
    ws_main.append(["Com comunicação GSM", contagem['gsm']])
    ws_main.append(["Com comunicação LoRaWAN", contagem['lorawan']])
    ws_main.append(["Com comunicação P2P", contagem['p2p']])
    total_seriais_sem_comunicacao = len(seriais) - len(serial_data)
    ws_main.append(["Sem comunicação", total_seriais_sem_comunicacao])
    ws_main.append([]) # Linha em branco para separar

    # Adicionando cabeçalhos para a planilha principal
    headers = [
        "Serial", "Modelo de HW", "Pacote GSM", "DataHoraEvento GSM",
        "Pacote LoRaWAN", "DataHoraEvento LoRaWAN",
        "Pacote P2P", "DataHoraEvento P2P",
        "Dados GSM", "Dados LoRaWAN", "Dados P2P"
    ]
    ws_main.append(headers) 

    # Preenche as linhas com os dados dos seriais na planilha principal
    for serial in seriais:
        data = serial_data.get(serial, {
            'Modelo de HW': 'N/A',
            'Pacote GSM': 'NÃO',
            'DataHoraEvento GSM': 'N/A',
            'Pacote LoRaWAN': 'NÃO',
            'DataHoraEvento LoRaWAN': 'N/A',
            'Pacote P2P': 'NÃO',
            'DataHoraEvento P2P': 'N/A',
            'Dados GSM': 'N/A',
            'Dados LoRaWAN': 'N/A',
            'Dados P2P': 'N/A'
        })
        row = [
            serial,
            data.get('Modelo de HW', 'N/A'),
            data.get('Pacote GSM', 'NÃO'),
            data.get('DataHoraEvento GSM', 'N/A'),
            data.get('Pacote LoRaWAN', 'NÃO'),
            data.get('DataHoraEvento LoRaWAN', 'N/A'),
            data.get('Pacote P2P', 'NÃO'),
            data.get('DataHoraEvento P2P', 'N/A'),
            data.get('Dados GSM', 'N/A'),
            data.get('Dados LoRaWAN', 'N/A'),
            data.get('Dados P2P', 'N/A')
        ]
        ws_main.append(row)

    # Criação e preenchimento das abas detalhadas para GSM, LoRaWAN e P2P
    sheets_to_resize = [ws_main]

    ws_gsm_detailed = _create_detailed_sheet(wb, "GSM_Detalhado", dados_gsm)
    if ws_gsm_detailed:
        sheets_to_resize.append(ws_gsm_detailed)

    ws_lorawan_detailed = _create_detailed_sheet(wb, "LoRaWAN_Detalhado", dados_lorawan)
    if ws_lorawan_detailed:
        sheets_to_resize.append(ws_lorawan_detailed)

    ws_p2p_detailed = _create_detailed_sheet(wb, "LoRaP2P_Detalhado", dados_p2p)
    if ws_p2p_detailed:
        sheets_to_resize.append(ws_p2p_detailed)

    # Ajusta a largura das colunas para todas as planilhas criadas
    for sheet in sheets_to_resize:
        auto_size_columns(sheet)

    # Salvando o arquivo
    wb.save(caminho_arquivo)
    adicionar_log(f"📁 Relatório gerado: {caminho_arquivo}")
    return caminho_arquivo


def parse_dados(dados_str):
    """
    Processa uma string de dados e retorna um dicionário com as chaves formatadas,
    considerando as chaves aninhadas.
    """
    dados = {}
    prefixos = []
    
    # Remove tags HTML e limpa espaços
    dados_str = re.sub(r'&lt;[^&gt;]*&gt;', '', dados_str)  # Remove todas as tags HTML
    dados_str = re.sub(r'\n+', '\n', dados_str)  # Remove quebras de linha extras
    dados_str = dados_str.strip()  # Limpa espaços no início e no fim

    # Divide em linhas
    linhas = dados_str.splitlines()
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        
        # Caso de fechamento de bloco
        if linha == '}':
            if prefixos:
                prefixos.pop()  # Remove o último prefixo
            continue
        
        # Caso de abertura de bloco com: chave {
        if linha.endswith('{'):
            chave = linha[:-1].strip()  # Remove o '{'
            prefixos.append(chave)  # Adiciona a chave ao prefixo
            continue

        # Caso padrão: chave: valor
        if ':' in linha:
            chave, valor = linha.split(':', 1)
            chave = chave.strip()  # Remove espaços na chave
            valor = valor.strip()  # Remove espaços no valor
            
            # Formata a chave com os prefixos
            chave_formatada = f"{'_'.join(prefixos)}_{chave}" if prefixos else chave
            dados[chave_formatada] = valor  # Salva o valor no dicionário

    return dados

def _create_detailed_sheet(wb, sheet_name, serial_raw_data_map):
    """
    Cria uma aba detalhada para um tipo de comunicação (GSM, LoRaWAN, P2P),
    parseando os dados e expandindo o dicionário em colunas.
    """
    if not serial_raw_data_map:
        return None
    
    ws = wb.create_sheet(sheet_name)  # Cria uma nova aba
    all_parsed_data_with_serials = []
    all_unique_keys = []  # Usando uma lista para manter a ordem

    # 1. Parsear todos os dados e coletar todas as chaves únicas
    for serial, raw_data_string in serial_raw_data_map.items():
        if raw_data_string and raw_data_string != 'N/A':
            parsed_dict = parse_dados(raw_data_string)  # Agora retorna um dicionário
            if parsed_dict:  # Verifica se o dicionário não está vazio
                parsed_dict['Serial'] = serial  # Adiciona o serial ao dicionário
                all_parsed_data_with_serials.append(parsed_dict)

                # Adiciona chaves únicas
                for key in parsed_dict.keys():
                    if key not in all_unique_keys:
                        all_unique_keys.append(key)
        else:
            # Inclui o serial mesmo que não haja dados para ele neste tipo de comunicação
            all_parsed_data_with_serials.append({'Serial': serial})

    if not all_parsed_data_with_serials:
        return None

    # 2. Definir cabeçalhos: Serial + chaves únicas
    headers = ['Serial'] + all_unique_keys
    ws.append(headers)  # Adiciona o cabeçalho como a primeira linha

    # 3. Preencher as linhas
    for item_dict in all_parsed_data_with_serials:
        row = [item_dict.get('Serial', 'N/A')]
        for key in all_unique_keys:
            value = item_dict.get(key, 'N/A')  # Preencher a linha com o valor
            row.append(value)
        ws.append(row)  # Adiciona a linha à planilha

    return ws  # Retorna a planilha para que possa ser redimensionada
