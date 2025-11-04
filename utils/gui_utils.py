# utils/gui_utils.py
from datetime import datetime
from PyQt5.QtGui import QTextCursor

def parse_serials(text):
    """Parseia string de seriais separados por ';' e retorna contagem e lista."""
    serials = [s.strip() for s in text.split(";") if s.strip()]
    return len(serials), serials

def toggle_widget_enabled(widgets, enabled):
    """Ativa/desativa uma lista de widgets."""
    for widget in widgets:
        widget.setEnabled(enabled)

def log_message(text_edit, message):
    """Adiciona mensagem ao QTextEdit de logs com timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    text_edit.append(f"[{timestamp}] {message}")
    cursor = text_edit.textCursor()
    cursor.movePosition(cursor.End)
    text_edit.setTextCursor(cursor)

def clear_logs(text_edit):
    """Limpa logs e adiciona mensagem de confirmação."""
    text_edit.clear()
    log_message(text_edit, "📋 Logs limpos")

def update_progress(progress_bar, status_label, value, max_value=100, status_text="Processando..."):
    """Atualiza barra de progresso e label."""
    if max_value > 0:
        percent = int(100 * value / max_value)
        progress_bar.setValue(percent)
        status_label.setText(f"{status_text} ({percent}%)")

def set_execution_complete(start_btn, pause_btn, cancel_btn, report_btn, status_label, success=True):
    """Configura estado de botões e label após execução."""
    start_btn.setEnabled(True)
    start_btn.setText("🚀 Iniciar Requisições")
    pause_btn.setEnabled(False)
    cancel_btn.setEnabled(False)
    report_btn.setEnabled(success)
    if success:
        status_label.setText("✅ Execução concluída")
        status_label.setStyleSheet("color: green; font-weight: bold;")
    else:
        status_label.setText("❌ Execução com erros")
        status_label.setStyleSheet("color: red; font-weight: bold;")
