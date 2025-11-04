# mogno_app/core/scheduler.py

"""
Módulo de backend para agendamento de tarefas.
Responsável por:
- Persistência de agendamentos
- Execução periódica
- Execução em background
"""

import json
import os
from datetime import datetime, timedelta
from threading import Thread, Lock
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from utils.logger import adicionar_log

SCHEDULES_FILE = "config/schedules.json"

class Scheduler(QObject):
    task_executed = pyqtSignal(str, dict)
    scheduler_triggered = pyqtSignal(str)
    execution_error = pyqtSignal(str, str)
    schedules_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.schedules = {}
        self.task_registry = {}
        self.lock = Lock()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_pending_executions)
        self.timer.start(60000)  # Verifica a cada 60s
        self.load_schedules()
        adicionar_log("✅ Scheduler iniciado")

    def register_task(self, task_id, function):
        self.task_registry[task_id] = function
        adicionar_log(f"📋 Tarefa registrada: {task_id}")

    def load_schedules(self):
        if not os.path.exists(SCHEDULES_FILE):
            self.schedules = {}
            return
        try:
            with open(SCHEDULES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for sid, cfg in data.items():
                if "datetime" in cfg:
                    cfg["datetime"] = datetime.fromisoformat(cfg["datetime"])
            self.schedules = data
            adicionar_log(f"📅 {len(self.schedules)} agendamentos carregados")
        except Exception as e:
            adicionar_log(f"❌ Erro ao carregar agendamentos: {e}")
            self.schedules = {}

    def save_schedules(self):
        try:
            data = {}
            for sid, cfg in self.schedules.items():
                cfg_copy = cfg.copy()
                if isinstance(cfg_copy.get("datetime"), datetime):
                    cfg_copy["datetime"] = cfg_copy["datetime"].isoformat()
                data[sid] = cfg_copy
            with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            adicionar_log("💾 Agendamentos salvos")
        except Exception as e:
            adicionar_log(f"❌ Erro ao salvar agendamentos: {e}")

    def add_schedule(self, scheduler_id, config):
        with self.lock:
            self.schedules[scheduler_id] = config
            self.save_schedules()
            self.schedules_updated.emit()

    def remove_schedule(self, scheduler_id):
        with self.lock:
            if scheduler_id in self.schedules:
                del self.schedules[scheduler_id]
                self.save_schedules()
                self.schedules_updated.emit()

    def get_all_schedules(self):
        return self.schedules.copy()

    def check_pending_executions(self):
        now = datetime.now()
        for sid, cfg in self.schedules.items():
            if not cfg.get("enabled", False):
                continue
            next_exec = self._calculate_next_execution(cfg)
            if next_exec and next_exec <= now:
                self._execute_schedule(sid, cfg)

    def _calculate_next_execution(self, cfg):
        dt = cfg.get("datetime")
        if not dt:
            return None
        now = datetime.now()
        tipo = cfg.get("type")
        if tipo == "once":
            return dt if dt > now else None
        elif tipo == "daily":
            return datetime.combine(now.date(), dt.time()) + timedelta(days=1)
        elif tipo == "weekly":
            dow = cfg.get("day_of_week", 0)
            days_ahead = (dow - now.weekday()) % 7
            if days_ahead == 0 and now.time() > dt.time():
                days_ahead = 7
            return datetime.combine(now.date() + timedelta(days=days_ahead), dt.time())
        elif tipo == "monthly":
            dom = cfg.get("day_of_month", 1)
            try:
                next_date = now.replace(day=dom)
                if next_date < now:
                    if now.month == 12:
                        next_date = next_date.replace(year=now.year+1, month=1)
                    else:
                        next_date = next_date.replace(month=now.month+1)
                return datetime.combine(next_date.date(), dt.time())
            except:
                return None
        return None

    def _execute_schedule(self, scheduler_id, config):
        adicionar_log(f"🚀 Executando agendamento '{scheduler_id}'")
        self.scheduler_triggered.emit(scheduler_id)
        for task_id in config.get("tasks", []):
            if task_id in self.task_registry:
                try:
                    Thread(target=self.task_registry[task_id], args=(config,), daemon=True).start()
                    adicionar_log(f"✅ Tarefa '{task_id}' executada")
                except Exception as e:
                    adicionar_log(f"❌ Erro ao executar '{task_id}': {e}")
                    self.execution_error.emit(scheduler_id, str(e))
