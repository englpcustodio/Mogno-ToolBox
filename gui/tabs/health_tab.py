# mogno_app/gui/health_tab.py

"""
Aba "Saúde da Base" - Placeholder para futura implementação.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class HealthTab(QWidget):
    """
    Aba de Saúde da Base (placeholder).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Aba 'Saúde da Base' - Em desenvolvimento")
        label.setStyleSheet("font-size: 14pt; color: gray;")
        layout.addWidget(label)
