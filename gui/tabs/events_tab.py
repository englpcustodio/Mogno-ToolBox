# mogno_app/gui/events_tab.py

"""
Aba "Análise de Eventos" - Placeholder para futura implementação.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class EventsTab(QWidget):
    """
    Aba de Análise de Eventos (placeholder).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Aba 'Análise de Eventos' - Em desenvolvimento")
        label.setStyleSheet("font-size: 14pt; color(label)")