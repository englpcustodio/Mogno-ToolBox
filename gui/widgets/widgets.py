# mogno_app/gui/widgets.py

from PyQt5.QtWidgets import (
    QLabel, QGroupBox, QFrame, QPushButton,
    QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont

from gui.styles import GROUPBOX_STYLE, COLUMN_FRAME_STYLE

# =====================================================================
# 🟩 WIDGETS SIMPLES (GroupBox, Frames, Títulos, Botões, etc)
# =====================================================================

def create_group_box(title):
    group = QGroupBox(title)
    group.setStyleSheet(GROUPBOX_STYLE)
    return group


def create_column_frame():
    frame = QFrame()
    frame.setFrameStyle(QFrame.Box | QFrame.Plain)
    frame.setStyleSheet(COLUMN_FRAME_STYLE)
    return frame


def create_section_title(text, icon=""):
    label = QLabel(f"{icon} {text}" if icon else text)
    label.setFont(QFont("Segoe UI", 14, QFont.Bold))
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("color: #2E7D32; margin-bottom: 10px;")
    return label


def create_separator():
    separator = QFrame()
    separator.setFrameShape(QFrame.HLine)
    separator.setFrameShadow(QFrame.Sunken)
    separator.setStyleSheet("background-color: #CCCCCC; margin: 10px 0;")
    return separator


def create_styled_button(text, style, width=None, height=None):
    button = QPushButton(text)
    button.setStyleSheet(style)
    if width:
        button.setFixedWidth(width)
    if height:
        button.setFixedHeight(height)
    return button


def create_info_label(text):
    label = QLabel(text)
    label.setStyleSheet("color: gray; font-size: 9pt;")
    return label



# =====================================================================
# 🟦 TOAST NOTIFICATION (slide + fade)
# =====================================================================

class ToastNotification(QLabel):
    SLIDE_OFFSET = 25
    VERTICAL_MARGIN = 40

    COLOR_MAP = {
        "success": "rgba(46, 204, 113, 230)",
        "warning": "rgba(241, 196, 15, 230)",
        "error":   "rgba(231, 76, 60, 230)",
    }

    def __init__(self, parent, message, duration=4000, type="success"):
        super().__init__(parent)

        bg_color = self.COLOR_MAP.get(type, "rgba(50, 50, 50, 220)")

        self.setText(message)
        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: bold;
        """)

        self.setAlignment(Qt.AlignCenter)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.adjustSize()

        # --- Posição relativa à janela
        parent_rect = parent.rect()
        window_pos = parent.mapToGlobal(parent_rect.topLeft())

        x = window_pos.x() + (parent_rect.width() - self.width()) // 2
        base_y = window_pos.y() + parent_rect.height() - self.height() - self.VERTICAL_MARGIN
        start_y = base_y + self.SLIDE_OFFSET

        self.move(x, start_y)
        self.base_y = base_y
        self.x = x

        # --- Fade-in
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        self.show()

        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)

        # --- Slide-up
        self.slide_in = QPropertyAnimation(self, b"pos")
        self.slide_in.setDuration(300)
        self.slide_in.setStartValue(QPoint(x, start_y))
        self.slide_in.setEndValue(QPoint(x, base_y))
        self.slide_in.setEasingCurve(QEasingCurve.OutQuad)

        self.fade_in.start()
        self.slide_in.start()

        QTimer.singleShot(duration, self._fade_and_slide_out)

    # -----------------------------------------
    # Saída (Fade-out + Slide-down)
    # -----------------------------------------
    def _fade_and_slide_out(self):
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(450)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)

        self.slide_out = QPropertyAnimation(self, b"pos")
        self.slide_out.setDuration(450)
        self.slide_out.setStartValue(QPoint(self.x, self.base_y))
        self.slide_out.setEndValue(QPoint(self.x, self.base_y + self.SLIDE_OFFSET))
        self.slide_out.setEasingCurve(QEasingCurve.InQuad)

        self.fade_out.finished.connect(self.close)
        self.fade_out.start()
        self.slide_out.start()
