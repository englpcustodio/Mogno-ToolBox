# mogno_app/gui/about_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from config.settings import (
    APP_NAME, APP_VERSION, RELEASE_DATE, LAUNCH_DATE,
    DEVELOPER_NAME, DEVELOPER_CONTACT, LOGO_MOGNO_PATH, RELEASE_NOTES_PATH
)

class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configura os widgets da aba sobre com centralização."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setAlignment(Qt.AlignCenter)

        info_container = QWidget()
        info_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        info_layout = QVBoxLayout(info_container)
        info_layout.setAlignment(Qt.AlignCenter)

        info_label = QLabel(
            f"{APP_NAME}\n"
            f"Data do 1º Lançamento: {LAUNCH_DATE}\n"
            f"Desenvolvedor: {DEVELOPER_NAME}\n"
            f"Contatos: {DEVELOPER_CONTACT}\n\n"
            f"Versão Atual: {APP_VERSION} - Liberada em: {RELEASE_DATE}"
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 11pt;")
        info_layout.addWidget(info_label)

        layout.addWidget(info_container)

        release_notes = QTextEdit()
        release_notes.setReadOnly(True)
        release_notes.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        try:
            with open(RELEASE_NOTES_PATH, "r", encoding="utf-8") as f:
                conteudo = f.read()
        except Exception as e:
            conteudo = "Erro ao carregar informações do Sobre: " + str(e)

        release_notes.setText(conteudo)
        layout.addWidget(release_notes)

        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)

        try:
            pixmap = QPixmap(LOGO_MOGNO_PATH).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo = QLabel()
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(lbl_logo)
        except Exception:
            lbl_logo = QLabel("[Logo não encontrada]")
            lbl_logo.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(lbl_logo)

        layout.addWidget(logo_container)
