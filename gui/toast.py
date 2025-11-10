# mogno_app/gui/toast.py
from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve


class ToastNotification(QLabel):
    """
    Exibe uma notificação leve (toast) no canto inferior direito da janela principal.
    Suporta tipos: 'success', 'warning', 'error'.
    Desaparece automaticamente após alguns segundos.
    """

    COLOR_MAP = {
        "success": "rgba(46, 204, 113, 230)",   # verde suave
        "warning": "rgba(241, 196, 15, 230)",   # amarelo/laranja
        "error":   "rgba(231, 76, 60, 230)",    # vermelho
    }

    def __init__(self, parent, message, duration=3000, type="success"):
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

        # Posição: canto inferior direito com margem
        parent_rect = parent.frameGeometry()
        x = parent_rect.width() - self.width() - 30
        y = parent_rect.height() - self.height() - 40
        self.move(x, y)

        # Efeito de transparência
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        self.show()
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.raise_()
        self.activateWindow()
        
        # Animação de fade-in
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.start()

        # Timer para fade-out automático
        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out.start()
        self.fade_out.finished.connect(self.close)
