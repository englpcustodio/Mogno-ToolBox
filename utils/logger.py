# mogno_app/utils/logger.py

import datetime

# Widget de texto associado dinamicamente (referência para o QTextEdit da GUI)
_progress_text_widget = None


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
        adicionar_log("📋 Logs da interface limpos.") # Adiciona um log sobre a limpeza

