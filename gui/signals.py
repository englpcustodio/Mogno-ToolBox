# gui/signals.py

from PyQt5.QtCore import pyqtSignal, QObject

class SignalManager(QObject):
    """
    Gerenciador de sinais (Event Bus) centralizado.
    """

    # ========== Gerais / UI ==========
    progress_updated = pyqtSignal(int, int)
    equipment_progress_updated = pyqtSignal(int, int, str)  # current, total, label
    login_successful = pyqtSignal(str, str, str, dict)   # token, user_login, user_id, cookie_dict
    login_failed = pyqtSignal(str)
    token_status_updated = pyqtSignal(str, str)         # texto, cor
    request_failed = pyqtSignal(str)
    log_message = pyqtSignal(str)
    enable_start_button = pyqtSignal(bool)              # compatibilidade com o código existente
    update_start_button_text = pyqtSignal(str)
    update_timer_label = pyqtSignal(str)
    csv_file_selected = pyqtSignal(str)

    # ========== Requisições de equipamentos ==========
    request_last_position_api = pyqtSignal(str, list)       # tipo_api, serials
    request_last_position_redis = pyqtSignal(list)          # serials
    request_status_equipment = pyqtSignal(list)             # serials
    request_data_consumption = pyqtSignal(int, int)         # mes, ano

    # ========== Relatórios ==========
    generate_consolidated_report = pyqtSignal(dict)
    generate_separate_reports = pyqtSignal(dict)

    # ========== Agendador ==========
    scheduler_saved = pyqtSignal(dict)
    scheduler_deleted = pyqtSignal(str)

    # ========== Conclusões específicas (emitidas por RequestHandler) ==========
    last_position_completed = pyqtSignal(list)
    status_equipment_completed = pyqtSignal(list)
    data_consumption_completed = pyqtSignal(dict)
    all_requests_finished = pyqtSignal()

    # ========== Toasters / mensagens ==========
    show_toast = pyqtSignal(str, str)          # mensagem, tipo ("success"/"warning"/"error")
    show_toast_success = pyqtSignal(str)
    show_toast_warning = pyqtSignal(str)
    show_toast_error = pyqtSignal(str)
