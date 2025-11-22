# mogno_app/gui/gui_utils.py
"""
Funções auxiliares específicas da GUI.
Essas funções não criam widgets — apenas manipulam widgets existentes.
"""

def toggle_widget_enabled(widgets, enabled: bool):
    """
    Ativa ou desativa uma lista de widgets.
    widgets: list[QWidget]
    enabled: bool
    """
    for widget in widgets:
        widget.setEnabled(enabled)


def update_progress(progress_bar, status_label, value, max_value=100, status_text="Processando..."):
    """
    Atualiza uma barra de progresso e sua label associada.
    progress_bar: QProgressBar
    status_label: QLabel
    value: int
    max_value: int
    status_text: str
    """
    if max_value <= 0:
        max_value = 1

    percent = int(100 * value / max_value)
    progress_bar.setValue(percent)
    status_label.setText(f"{status_text} ({percent}%)")


def set_execution_complete(start_btn, pause_btn, cancel_btn, report_btn, status_label, success=True):
    """
    Configura automaticamente o estado dos botões e mensagens
    após a conclusão das requisições.
    """
    # Habilita ou desabilita botões
    start_btn.setEnabled(True)
    start_btn.setText("🚀 Iniciar Requisições")
    pause_btn.setEnabled(False)
    cancel_btn.setEnabled(False)
    report_btn.setEnabled(success)

    # Atualiza mensagem de status
    if success:
        status_label.setText("✅ Execução concluída")
        status_label.setStyleSheet("color: green; font-weight: bold;")
    else:
        status_label.setText("❌ Execução com erros")
        status_label.setStyleSheet("color: red; font-weight: bold;")
