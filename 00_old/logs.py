# logs.py (versão PyQt)
import datetime

# Widget de texto associado dinamicamente
progress_text = None

# Define o QTextEdit que receberá os logs
def configurar_componente_logs_qt(componente_text):
    global progress_text
    progress_text = componente_text

def adicionar_log(texto):
    """Adiciona uma entrada de log com timestamp, no widget registrado."""
    timestamp = datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
    mensagem = f"{timestamp} {texto}\n"
    if progress_text: 
        progress_text.append(mensagem)
        # Rolar para o final
        cursor = progress_text.textCursor()
        cursor.movePosition(cursor.End)
        progress_text.setTextCursor(cursor)
    else:
        # Se não houver widget definido, imprime no console
        print(mensagem)

def limpar_logs():
    """Limpa o conteúdo atual da área de logs."""
    if progress_text:
        progress_text.clear()

def log_inicio(tipo_api, modo_legivel, total, step, adicionar_log):
    tipo_legivel = "Rastreadores" if tipo_api == "rastreadores" else "Iscas"
    adicionar_log(
        f'Iniciando Requisições de {tipo_legivel} no modo "{modo_legivel}": {lotes_total(total, step)} lotes de {step} seriais.'
    )

# Importação para manter compatibilidade
from utils import lotes_total
