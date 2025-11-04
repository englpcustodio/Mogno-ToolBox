# mogno_app/utils/logger.py

import datetime
# from utils.helpers import lotes_total # REMOVIDO: lotes_total não é uma função de logger

# Widget de texto associado dinamicamente (referência para o QTextEdit da GUI)
_progress_text_widget = None

def configurar_componente_logs_qt(componente_text):
    """
    Define o QTextEdit da GUI que receberá os logs.
    """
    global _progress_text_widget
    _progress_text_widget = componente_text

def adicionar_log(texto):
    """
    Adiciona uma entrada de log com timestamp, no widget registrado ou no console.
    """
    timestamp = datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
    mensagem = f"{timestamp} {texto}\n"
    if _progress_text_widget:
        _progress_text_widget.append(mensagem)
        # Rolar para o final
        cursor = _progress_text_widget.textCursor()
        cursor.movePosition(cursor.End)
        _progress_text_widget.setTextCursor(cursor)
    else:
        # Se não houver widget definido, imprime no console
        print(mensagem)

def limpar_logs():
    """
    Limpa o conteúdo atual da área de logs no widget da GUI.
    """
    if _progress_text_widget:
        _progress_text_widget.clear()
        adicionar_log("Logs da interface limpos.") # Adiciona um log sobre a limpeza

def log_inicio(tipo_api, modo_legivel, total_serials, step_size, lotes_total_func):
    """
    Registra uma mensagem de início de requisições.
    Recebe lotes_total_func como parâmetro para evitar dependência circular.
    """
    tipo_legivel = "Rastreadores" if tipo_api == "rastreadores" else "Iscas"
    num_lotes = lotes_total_func(total_serials, step_size)
    adicionar_log(
        f'Iniciando Requisições de {tipo_legivel} no modo "{modo_legivel}": {num_lotes} lotes de {step_size} seriais.'
    )

