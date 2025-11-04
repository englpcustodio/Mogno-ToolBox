# utils.py (versão PyQt)
import os
import sys
import json
from time import time
from PyQt5.QtCore import QTimer

def get_resource_path(rel_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

# Achata um JSON aninhado (dict) em um dicionário plano
def flatten_json(d, parent_key='', sep='_'):
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

# Atualiza o cronômetro na interface usando QTimer
def atualizar_cronometro_qt(label, tempo_inicio, flag_execucao_func):
    """
    Atualiza um QLabel com o tempo decorrido a cada segundo
    
    Args:
        label: QLabel para exibir o tempo
        tempo_inicio: timestamp de início (float)
        flag_execucao_func: função que retorna True enquanto deve continuar atualizando
    """
    if tempo_inicio is None:
        return
        
    decorrido = int(time() - tempo_inicio)
    label.setText(f"⏱️ Tempo decorrido: {formatar_tempo(decorrido)}")
    
    if flag_execucao_func():
        QTimer.singleShot(1000, lambda: atualizar_cronometro_qt(label, tempo_inicio, flag_execucao_func))

# Divide uma lista em sublistas de tamanho_lote
def dividir_lotes(lista, tamanho_lote):
    return [lista[i:i + tamanho_lote] for i in range(0, len(lista), tamanho_lote)]

# Retorna o próximo valor de step, ajustado
def step_autoajustar(step_atual, ajuste_step):
    return max(1, step_atual - ajuste_step)

# Número total de lotes a serem requisitados
def lotes_total(total, step):
    return ((total-1)//step)+1 if step > 0 else 1

# Formata segundos em hh:mm:ss
def formatar_tempo(segundos):
    horas, resto = divmod(int(segundos), 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

# Calcula e mostra o tempo médio entre requisições ao final
def calcular_tempo_medio_entre_requisicoes(timestamps, adicionar_log, formatar_tempo_func=None):
    if len(timestamps) < 2:
        return
    intervalos = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    tempo_medio = sum(intervalos) / len(intervalos)
    if formatar_tempo_func is not None:
        tempo_str = formatar_tempo_func(tempo_medio)
    else:
        tempo_str = f"{tempo_medio:.2f}s"
    adicionar_log(f"Tempo médio entre lotes: {tempo_str}")
