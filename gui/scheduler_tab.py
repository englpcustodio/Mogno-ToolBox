# mogno_app/gui/scheduler_tab.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QCheckBox, QLabel
from PyQt5.QtCore import pyqtSignal
from gui.widgets.scheduler_widget import SchedulerWidget
from utils.gui_utils import log_message

class SchedulerTab(QWidget):
    scheduler_saved = pyqtSignal(str, dict)
    scheduler_deleted = pyqtSignal(str)
    scheduler_enabled_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.chk_enable = QCheckBox("Habilitar Agendador")
        self.chk_enable.toggled.connect(self.scheduler_enabled_changed.emit)
        layout.addWidget(self.chk_enable)

        self.scheduler_widget = SchedulerWidget(available_tasks=[
            {"id": "last_position_api", "name": "Últimas Posições (API)", "enabled": True},
            {"id": "status_equipment", "name": "Status Equipamentos", "enabled": True},
        ])
        self.scheduler_widget.scheduler_saved.connect(self.scheduler_saved.emit)
        self.scheduler_widget.scheduler_deleted.connect(self.scheduler_deleted.emit)
        layout.addWidget(self.scheduler_widget)

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.logs_text)

    def log(self, message):
        log_message(self.logs_text, message)
