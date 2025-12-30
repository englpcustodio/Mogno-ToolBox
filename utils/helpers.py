# mogno_app/utils/helpers.py

import os
import shutil
from datetime import datetime # Adicionado para epoch_to_datetime
from utils.logger import adicionar_log # Importa o logger da nova localização


# Exclui todos os dados de cache (__pycache__) das pastas ao iniciar a aplicação (evita dados em cache que podem comprometer alguma modificação recente)
def clean_pycache():
    root = "."  # ou o caminho do seu projeto

    for dirpath, dirnames, filenames in os.walk(root):
        if "__pycache__" in dirnames:
            full_path = os.path.join(dirpath, "__pycache__")
            #print(f"Removendo: {full_path}")
            shutil.rmtree(full_path)
    return()

def parse_serials(text):
    """Parseia string de seriais separados por ';' e retorna contagem e lista."""
    serials = [s.strip() for s in text.split(";") if s.strip()]
    return len(serials), serials

# Achata um JSON aninhado (dict) em um dicionário plano
def flatten_json(d, parent_key='', sep='_'):
    """
    Achata um dicionário JSON aninhado em um dicionário plano.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, sub_item in enumerate(v):
                if isinstance(sub_item, dict):
                    items.extend(flatten_json(sub_item, f"{new_key}_{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}_{i}", sub_item))
        else:
            items.append((new_key, v))
    return dict(items)

# Divide uma lista em sublistas de tamanho_lote
def dividir_lotes(lista, tamanho_lote):
    """
    Divide uma lista em sublistas (lotes) de um tamanho especificado.
    """
    return [lista[i:i + tamanho_lote] for i in range(0, len(lista), tamanho_lote)]

# Retorna o próximo valor de step, ajustado
def step_autoajustar(step_atual, ajuste_step):
    """
    Calcula o novo valor de 'step' para auto-ajuste, garantindo que seja no mínimo 1.
    """
    return max(1, step_atual - ajuste_step)

# Número total de lotes a serem requisitados
def lotes_total(total, step):
    """
    Calcula o número total de lotes com base no total de itens e no tamanho do step.
    """
    return ((total - 1) // step) + 1 if step > 0 else 1

# Formata segundos em hh:mm:ss
def formatar_tempo(segundos):
    """
    Formata um número de segundos em uma string no formato HH:MM:SS.
    """
    horas, resto = divmod(int(segundos), 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

# Calcula e mostra o tempo médio entre requisições ao final
def calcular_tempo_medio_entre_requisicoes(timestamps, formatar_tempo_func=None):
    """
    Calcula e registra o tempo médio entre os timestamps fornecidos.
    Usa a função adicionar_log diretamente (importada no topo do módulo).
    """
    if len(timestamps) < 2:
        return
    intervalos = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    tempo_medio = sum(intervalos) / len(intervalos)
    if formatar_tempo_func is not None:
        tempo_str = formatar_tempo_func(tempo_medio)
    else:
        tempo_str = f"{tempo_medio:.2f}s"
    adicionar_log(f"Tempo médio entre lotes: {tempo_str}") # Chamada corrigida

def epoch_to_datetime(epoch_seconds):
    """
    Converte um timestamp epoch (em segundos) para um objeto datetime.
    
    Args:
        epoch_seconds: Timestamp em segundos (ou milissegundos, será detectado)
        
    Returns:
        Objeto datetime ou None se inválido
    """
    if epoch_seconds is None:
        return None
    
    try:
        # Se o valor for muito grande, provavelmente está em milissegundos
        if epoch_seconds > 10000000000:  # Timestamp após ano 2286 em segundos
            epoch_seconds = epoch_seconds / 1000
        
        return datetime.fromtimestamp(epoch_seconds)
    except Exception as e:
        adicionar_log(f"⚠️ Erro ao converter epoch para datetime: {e}")
        return None

def calcular_periodo_dias(start_datetime, end_datetime):
    """
    Calcula o número de dias entre duas datas.

    Suporta múltiplos formatos de data:
    - "dd/MM/yyyy HH:mm:ss" (padrão da aplicação)
    - "dd-MM-yyyy HH:mm:ss"
    - "yyyy-MM-dd HH:mm:ss"
    - "dd/MM/yyyy"
    - "dd-MM-yyyy"

    Args:
        start_datetime (str): Data/hora inicial
        end_datetime (str): Data/hora final

    Returns:
        int: Número de dias entre as datas (mínimo 1 se houver diferença)

    Exemplos:
        >>> calcular_periodo_dias('29/11/2025 00:00:00', '29/12/2025 23:59:59')
        30
        >>> calcular_periodo_dias('29/12/2025 10:00:00', '29/12/2025 15:00:00')
        1  # Menos de 24h, mas conta como 1 dia
    """
    try:
        # Lista de formatos suportados
        formatos = [
            "%d/%m/%Y %H:%M:%S",  # dd/MM/yyyy HH:mm:ss (padrão)
            "%d-%m-%Y %H:%M:%S",  # dd-MM-yyyy HH:mm:ss
            "%Y-%m-%d %H:%M:%S",  # yyyy-MM-dd HH:mm:ss
            "%d/%m/%Y",           # dd/MM/yyyy
            "%d-%m-%Y",           # dd-MM-yyyy
        ]

        dt_start = None
        dt_end = None

        # Tenta parsear com cada formato
        for fmt in formatos:
            try:
                dt_start = datetime.strptime(start_datetime, fmt)
                dt_end = datetime.strptime(end_datetime, fmt)
                break  # Encontrou formato válido
            except ValueError:
                continue  # Tenta próximo formato

        # Se não conseguiu parsear nenhum formato
        if dt_start is None or dt_end is None:
            adicionar_log(f"⚠️ Formato de data não reconhecido:")
            adicionar_log(f"   Start: '{start_datetime}'")
            adicionar_log(f"   End: '{end_datetime}'")
            return 0

        # Calcula diferença
        diferenca = dt_end - dt_start
        dias = diferenca.days

        # Se for menos de 24h mas houver diferença, conta como 1 dia
        #if dias == 0 and diferenca.total_seconds() > 0:
        #    dias = 1

        # Log de sucesso
        adicionar_log(f"📅 Período calculado: {dias} dias")
        return dias

    except Exception as e:
        adicionar_log(f"❌ Erro ao calcular período: {e}")
        adicionar_log(f"   Start: '{start_datetime}'")
        adicionar_log(f"   End: '{end_datetime}'")
        return 0