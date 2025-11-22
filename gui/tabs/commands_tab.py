# mogno_app/gui/commands_tab.py

"""
Aba "Gestão de Comandos" - Placeholder para futura implementação.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class CommandsTab(QWidget):
    """
    Aba de Gestão de Comandos (placeholder).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Aba 'Gestão de Comandos' - Em desenvolvimento")
        label.setStyleSheet("font-size: 14pt; color: gray;")
        layout.addWidget(label)
