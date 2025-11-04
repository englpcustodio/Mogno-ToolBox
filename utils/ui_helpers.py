# mogno_app/utils/ui_helpers.py

"""
Funções auxiliares para criação de componentes de UI.
"""

from PyQt5.QtWidgets import QGroupBox, QFrame, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils.styles import GROUPBOX_STYLE, COLUMN_FRAME_STYLE


def create_group_box(title):
    """Cria um QGroupBox estilizado"""
    group = QGroupBox(title)
    group.setStyleSheet(GROUPBOX_STYLE)
    return group


def create_column_frame():
    """Cria um QFrame para colunas"""
    frame = QFrame()
    frame.setFrameStyle(QFrame.Box | QFrame.Plain)
    frame.setStyleSheet(COLUMN_FRAME_STYLE)
    return frame


def create_section_title(text, icon=""):
    """Cria um título de seção estilizado"""
    label = QLabel(f"{icon} {text}" if icon else text)
    label.setFont(QFont("Segoe UI", 14, QFont.Bold))
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("color: #2E7D32; margin-bottom: 10px;")
    return label


def create_separator():
    """Cria uma linha separadora"""
    separator = QFrame()
    separator.setFrameShape(QFrame.HLine)
    separator.setFrameShadow(QFrame.Sunken)
    separator.setStyleSheet("background-color: #CCCCCC; margin: 10px 0;")
    return separator


def create_styled_button(text, style, width=None, height=None):
    """Cria um botão estilizado"""
    button = QPushButton(text)
    button.setStyleSheet(style)
    if width:
        button.setFixedWidth(width)
    if height:
        button.setFixedHeight(height)
    return button


def create_info_label(text):
    """Cria um label informativo"""
    label = QLabel(text)
    label.setStyleSheet("color: gray; font-size: 9pt; margin-leftpx;")
    return label
