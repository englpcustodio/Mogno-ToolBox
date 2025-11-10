# mogno_app/gui/signals.py

from PyQt5.QtCore import pyqtSignal, QObject

class SignalManager(QObject):
    """
    Gerenciador de sinais para comunicação entre diferentes partes da aplicação.
    """
    # ========== Sinais Existentes (manter) ==========
    progress_updated = pyqtSignal(int, int)
    login_successful = pyqtSignal(str, str, str, dict)
    login_failed = pyqtSignal(str)
    token_status_updated = pyqtSignal(str, str)
    request_completed = pyqtSignal(list, str)
    request_failed = pyqtSignal(str)
    log_message = pyqtSignal(str)
    enable_start_button = pyqtSignal(bool)
    update_start_button_text = pyqtSignal(str)
    update_timer_label = pyqtSignal(str)
    csv_file_selected = pyqtSignal(str)
    
    # ========== Novos Sinais para Análise de Equipamentos ==========
    # Requisições de últimas posições
    request_last_position_api = pyqtSignal(str, list)       # (tipo_api, serials)
    request_last_position_redis = pyqtSignal(list)          # (serials)
    
    # Requisições de status e consumo
    request_status_equipment = pyqtSignal(list)             # (serials)
    request_data_consumption = pyqtSignal(list, str, str)   # (serials, mes, ano)
    
    # Requisições futuras (placeholders)
    request_line_status = pyqtSignal(list)                  # (serials)
    request_lorawan_status = pyqtSignal(list)               # (serials)
    
    # Geração de relatórios consolidados
    generate_consolidated_report = pyqtSignal(dict)         # (opcoes_relatorio)
    generate_separate_reports = pyqtSignal(dict)            # (opcoes_relatorio)
    
    # Agendamento de tarefas
    schedule_saved = pyqtSignal(dict)                       # (schedule_config)
    schedule_deleted = pyqtSignal(str)                      # (schedule_id)
    
    # Conclusão de requisições específicas
    last_position_completed = pyqtSignal(list)              # (resultados)
    status_equipment_completed = pyqtSignal(list)           # (resultados)
    data_consumption_completed = pyqtSignal(dict)           # (resultados)

    # Progresso detalhado de execução
    equipment_progress_updated = pyqtSignal(int, int, str)  # (current, total, status_text)

    # ========== TOAST NOTIFICATIONS ==========
    show_toast = pyqtSignal(str, str)
    show_toast_success = pyqtSignal(str)                    # mensagem de sucesso
    show_toast_warning = pyqtSignal(str)                    # mensagem de aviso
    show_toast_error = pyqtSignal(str)                      # mensagem de erro

    