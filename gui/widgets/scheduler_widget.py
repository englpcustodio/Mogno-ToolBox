# mogno_app/gui/widgets/scheduler_widget.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, QDateEdit,
    QTimeEdit, QComboBox, QLabel, QCheckBox, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTime, QDateTime
from datetime import datetime

class SchedulerWidget(QWidget):
    scheduler_saved = pyqtSignal(str, dict)
    scheduler_deleted = pyqtSignal(str)

    def __init__(self, available_tasks=None, parent=None):
        super().__init__(parent)
        self.available_tasks = available_tasks or []
        self.current_scheduler_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Tipo
        type_group = QGroupBox("Tipo de Agendamento")
        type_layout = QVBoxLayout(type_group)
        self.radio_once = QRadioButton("Única vez")
        self.radio_daily = QRadioButton("Diariamente")
        self.radio_weekly = QRadioButton("Semanalmente")
        self.radio_monthly = QRadioButton("Mensalmente")
        self.radio_once.setChecked(True)
        for rb in [self.radio_once, self.radio_daily, self.radio_weekly, self.radio_monthly]:
            type_layout.addWidget(rb)
        layout.addWidget(type_group)

        # Data e hora
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.time_edit = QTimeEdit(QTime.currentTime())
        layout.addWidget(QLabel("Data:"))
        layout.addWidget(self.date_edit)
        layout.addWidget(QLabel("Hora:"))
        layout.addWidget(self.time_edit)

        # Campos específicos
        self.weekly_day_combo = QComboBox()
        self.weekly_day_combo.addItems(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"])
        self.monthly_day_combo = QComboBox()
        self.monthly_day_combo.addItems([f"{i:02d}" for i in range(1, 32)])
        layout.addWidget(QLabel("Dia da semana (semanal):"))
        layout.addWidget(self.weekly_day_combo)
        layout.addWidget(QLabel("Dia do mês (mensal):"))
        layout.addWidget(self.monthly_day_combo)

        # Tarefas
        self.task_checkboxes = {}
        layout.addWidget(QLabel("Tarefas:"))
        for task in self.available_tasks:
            chk = QCheckBox(task["name"])
            self.task_checkboxes[task["id"]] = chk
            layout.addWidget(chk)

        # Botões
        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self.save_schedule)
        layout.addWidget(btn_save)

    def save_schedule(self):
        selected_tasks = [tid for tid, chk in self.task_checkboxes.items() if chk.isChecked()]
        if not selected_tasks:
            QMessageBox.warning(self, "Aviso", "Selecione ao menos uma tarefa.")
            return

        scheduler_type = "once"
        if self.radio_daily.isChecked():
            scheduler_type = "daily"
        elif self.radio_weekly.isChecked():
            scheduler_type = "weekly"
        elif self.radio_monthly.isChecked():
            scheduler_type = "monthly"

        dt = QDateTime(self.date_edit.date(), self.time_edit.time()).toPyDateTime()
        config = {
            "enabled": True,
            "type": scheduler_type,
            "datetime": dt,
            "tasks": selected_tasks
        }

        if scheduler_type == "weekly":
            config["day_of_week"] = self.weekly_day_combo.currentIndex()
        elif scheduler_type == "monthly":
            config["day_of_month"] = self.monthly_day_combo.currentIndex() + 1

        scheduler_id = self.current_scheduler_id or f"scheduler_{int(datetime.now().timestamp())}"
        self.scheduler_saved.emit(scheduler_id, config)
