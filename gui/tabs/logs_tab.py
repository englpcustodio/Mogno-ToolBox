# mogno_app/gui/logs_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal

class LogsTab(QWidget):
    # Sinal para limpar os logs
    clear_logs_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configura os widgets da aba de logs com centralização."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setAlignment(Qt.AlignCenter)

        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 5, 0, 5)

        self.chk_gerar_log = QCheckBox("Gerar arquivo de logs (.txt)")
        self.chk_gerar_log.setChecked(True)
        top_layout.addWidget(self.chk_gerar_log, 1)

        btn_limpar_logs = QPushButton("Limpar Logs")
        btn_limpar_logs.setFixedWidth(120)
        btn_limpar_logs.clicked.connect(self.clear_logs_requested.emit) # Emite sinal
        top_layout.addWidget(btn_limpar_logs, 0, Qt.AlignRight)

        layout.addWidget(top_bar)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMinimumHeight(400)
        layout.addWidget(self.progress_text)

    def get_log_text_edit(self):
        """Retorna a referência ao QTextEdit para que o logger possa escrever nele."""
        return self.progress_text

    def should_generate_log_file(self):
        """Retorna se o checkbox de gerar arquivo de log está marcado."""
        return self.chk_gerar_log.isChecked()
