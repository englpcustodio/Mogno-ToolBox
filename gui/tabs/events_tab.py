# gui/tabs/events_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QGroupBox, QGridLayout, QCheckBox,
    QScrollArea, QDateTimeEdit, QProgressBar, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal, QTime, QTimer

from config.settings import EVENT_NAMES
from core import serial_management # Importar o módulo de gerenciamento de seriais
from gui.widgets import EventsSheetSelectionDialog
from utils.logger import adicionar_log

class EventsTab(QWidget):
    """
    Aba para análise de eventos de rastreadores.
    Permite inserir seriais, selecionar um período e filtrar por tipo de evento.
    """
    # Sinal para iniciar a requisição de eventos
    start_events_request = pyqtSignal(list, str, str, str) # serials, start_datetime, end_datetime, event_filters
    # Sinal para gerar o relatório de eventos (será conectado ao ReportHandler)
    generate_events_report = pyqtSignal(list) # Passa os dados dos eventos para o ReportHandler

    def __init__(self, app_state, signal_manager):
        super().__init__()
        self.app_state = app_state
        self.signal_manager = signal_manager
        self.event_filters_map = self._get_event_filters_map() # Mapeamento de eventos
        self.filter_checkboxes = {} # Dicionário para armazenar os checkboxes
        self.last_events_data = [] # Para armazenar os dados da última requisição de eventos
        self.auto_generate_report = False  # Flag para geração automática
        self._report_generation_triggered = False # Flag para evitar geração duplicada
        self._setup_ui()
        self._connect_signals()
        self._reset_progress()
        self._update_serial_count_label() # Atualiza a contagem inicial de seriais
        self._check_enable_start_button() # Garante que o botão de iniciar esteja no estado correto

    def _setup_ui(self):
        """Configura a interface do usuário para a aba de eventos."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # --- Grupo de Seriais ---
        serials_group = QGroupBox("Seriais para Análise")
        serials_layout = QVBoxLayout(serials_group)

        # Entrada manual de seriais
        self.serials_text_edit = QTextEdit()
        self.serials_text_edit.setPlaceholderText("Insira seriais separados por ';' ou nova linha...")
        self.serials_text_edit.setFixedHeight(100)
        serials_layout.addWidget(self.serials_text_edit)

        # Botões de arquivo e limpeza
        file_buttons_layout = QHBoxLayout()
        self.btn_select_file = QPushButton("📁 Carregar do Arquivo (.csv/.xlsx)")
        self.btn_clear_serials = QPushButton("🧹 Limpar Seriais")
        file_buttons_layout.addWidget(self.btn_select_file)
        file_buttons_layout.addWidget(self.btn_clear_serials)
        serials_layout.addLayout(file_buttons_layout)

        self.serial_count_label = QLabel("Seriais carregados: 0")
        serials_layout.addWidget(self.serial_count_label)
        main_layout.addWidget(serials_group)

        # --- Grupo de Período ---
        period_group = QGroupBox("Período de Análise")
        period_layout = QGridLayout(period_group)

        # DATA/HORA INÍCIO: Dia atual às 00:00:00
        period_layout.addWidget(QLabel("Data/Hora Início:"), 0, 0)
        self.datetime_start = QDateTimeEdit()
        self.datetime_start.setCalendarPopup(True)
        self.datetime_start.setDisplayFormat("dd/MM/yyyy HH:mm:ss")

        # Define data de início: hoje às 00:00:00
        today_start = QDateTime.currentDateTime()
        today_start.setTime(QTime(0, 0, 0))  # 00:00:00
        self.datetime_start.setDateTime(today_start)
        period_layout.addWidget(self.datetime_start, 0, 1)

        # DATA/HORA FIM: Dia atual às 23:59:59
        period_layout.addWidget(QLabel("Data/Hora Fim:"), 1, 0)
        self.datetime_end = QDateTimeEdit()
        self.datetime_end.setCalendarPopup(True)
        self.datetime_end.setDisplayFormat("dd/MM/yyyy HH:mm:ss")

        # Define data de fim: hoje às 23:59:59
        today_end = QDateTime.currentDateTime()
        today_end.setTime(QTime(23, 59, 59))  # 23:59:59
        self.datetime_end.setDateTime(today_end)
        period_layout.addWidget(self.datetime_end, 1, 1)

        main_layout.addWidget(period_group)

        # --- Grupo de Filtros de Eventos ---
        filters_group = QGroupBox("Filtros de Eventos")
        filters_layout = QVBoxLayout(filters_group)

        # Botões de seleção rápida
        filter_action_layout = QHBoxLayout()
        self.btn_select_all_filters = QPushButton("Selecionar Todos")
        self.btn_deselect_all_filters = QPushButton("Deselecionar Todos")
        filter_action_layout.addWidget(self.btn_select_all_filters)
        filter_action_layout.addWidget(self.btn_deselect_all_filters)
        filters_layout.addLayout(filter_action_layout)

        # Área de scroll para os checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.filters_grid_layout = QGridLayout(scroll_content)
        self.filters_grid_layout.setSpacing(5)
        scroll_area.setWidget(scroll_content)
        filters_layout.addWidget(scroll_area)

        self._populate_event_filters() # Preenche os checkboxes
        main_layout.addWidget(filters_group)

        # --- Checkbox: Gerar Relatório Automático ---
        auto_report_layout = QHBoxLayout()
        self.chk_auto_generate_report = QCheckBox("✅ Gerar Relatório após as Requisições")
        self.chk_auto_generate_report.setChecked(False)
        self.chk_auto_generate_report.setToolTip(
            "Se marcado, o relatório será gerado automaticamente após as requisições finalizarem"
        )
        self.chk_auto_generate_report.stateChanged.connect(self._on_auto_report_checkbox_changed)
        auto_report_layout.addWidget(self.chk_auto_generate_report)
        auto_report_layout.addStretch()
        main_layout.addLayout(auto_report_layout)

        # --- Botões de Ação ---
        action_buttons_layout = QHBoxLayout()
        self.btn_start_request = QPushButton("🚀 Iniciar Requisição de Eventos")
        self.btn_start_request.setFixedHeight(40)
        self.btn_start_request.setStyleSheet("font-weight: bold;")
        self.btn_generate_report = QPushButton("📊 Gerar Relatório Excel")
        self.btn_generate_report.setFixedHeight(40)
        self.btn_generate_report.setEnabled(False) # Desabilitado por padrão
        action_buttons_layout.addWidget(self.btn_start_request)
        action_buttons_layout.addWidget(self.btn_generate_report)
        main_layout.addLayout(action_buttons_layout)

        # --- Barra de Progresso ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        self.progress_status_label = QLabel("Aguardando requisição...")
        self.progress_status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.progress_status_label)

        # Espaçador para empurrar tudo para cima
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _on_report_generation_completed(self, message: str):
        """Restaura botão quando o relatório é gerado com sucesso."""
        if "Relatório de eventos gerado" in message:
            self._restore_generate_button()

    def _connect_signals(self):
        """Conecta os sinais dos widgets aos seus respectivos slots."""
        self.serials_text_edit.textChanged.connect(self._handle_manual_serials_input)
        self.btn_select_file.clicked.connect(self._on_select_file_clicked)
        self.btn_clear_serials.clicked.connect(self._on_clear_serials_clicked)
        self.btn_select_all_filters.clicked.connect(lambda: self._set_all_filters(True))
        self.btn_deselect_all_filters.clicked.connect(lambda: self._set_all_filters(False))
        self.btn_start_request.clicked.connect(self._on_start_request_clicked)
        self.btn_generate_report.clicked.connect(self._on_generate_report_clicked)

        # Conectar sinais do SignalManager para atualização de progresso
        self.signal_manager.events_progress_updated.connect(self.update_progress)
        self.signal_manager.events_request_completed.connect(self._handle_request_completed)

        # Conecta sinal de conclusão de geração de relatório
        self.signal_manager.show_toast_success.connect(self._on_report_generation_completed)

    def _on_auto_report_checkbox_changed(self):
        """Captura mudança do checkbox de geração automática."""
        self.auto_generate_report = self.chk_auto_generate_report.isChecked()
        adicionar_log(f"🔄 Geração automática de relatório: {'ATIVADA' if self.auto_generate_report else 'DESATIVADA'}")

    def _get_event_filters_map(self):
        """Retorna um dicionário com os IDs e nomes dos eventos."""
        return {name: id for id, name in EVENT_NAMES}

    def _populate_event_filters(self):
        """Preenche o layout de filtros com checkboxes para cada evento."""
        self.filter_checkboxes = {}
        col = 0
        row = 0
        sorted_events = sorted(self.event_filters_map.items(), key=lambda item: item[1])
        for event_name, event_id in sorted_events:
            checkbox = QCheckBox(f"{event_id} - {event_name}")
            checkbox.setChecked(False)
            self.filters_grid_layout.addWidget(checkbox, row, col)
            self.filter_checkboxes[event_id] = checkbox
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _set_all_filters(self, checked: bool):
        """Marca ou desmarca todos os checkboxes de filtro."""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(checked)

    def _get_selected_event_filters(self) -> str:
        """Retorna uma string formatada com os IDs dos eventos selecionados."""
        selected_ids = []
        for event_id in sorted(self.filter_checkboxes.keys()):
            checkbox = self.filter_checkboxes[event_id]
            if checkbox.isChecked():
                selected_ids.append(str(event_id))
        return ",".join(selected_ids)

    def _handle_manual_serials_input(self):
        """Processa a entrada manual de seriais e atualiza a contagem."""
        text = self.serials_text_edit.toPlainText()
        info = serial_management.carregar_seriais_manualmente(text)
        self._update_serial_count_label(info)
        self._check_enable_start_button()

    def _handle_file_selected(self, filepath):
        """Lida com a seleção de um arquivo de seriais."""
        info = serial_management.ler_arquivo_serials(filepath)
        self._update_serial_count_label(info)
        self._check_enable_start_button()

    def _on_select_file_clicked(self):
        """Abre diálogo para selecionar arquivo de seriais."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Seriais",
            "",
            "Arquivos CSV/Excel (*.csv *.xlsx);;Todos os Arquivos (*)"
        )

        if filepath:
            self._handle_file_selected(filepath)

    def _on_clear_serials_clicked(self):
        """Limpa a área de texto de seriais e a lista interna."""
        serial_management.limpar_seriais()
        self.serials_text_edit.clear()
        self._update_serial_count_label()
        self._check_enable_start_button()

    def _update_serial_count_label(self, info=None):
        """Atualiza o label com a contagem de seriais carregados."""
        if info is None:
            current_serials_info = serial_management.get_info_serials()
            total_serials = current_serials_info.get('quantidade_total', 0)
            self.serial_count_label.setText(f"Seriais carregados: {total_serials}")
        else:
            total_lidos = info.get('total_lidos', 0)
            duplicados = info.get('duplicados', 0)
            unicos = info.get('unicos', [])
            self.serial_count_label.setText(
                f"Seriais carregados: {len(unicos)} (Total lidos: {total_lidos}, Duplicados removidos: {duplicados})"
            )
        self._check_enable_start_button()

    def _check_enable_start_button(self):
        """Verifica se há seriais carregados para habilitar o botão de iniciar."""
        serials_list = serial_management.get_seriais()
        has_serials = len(serials_list) > 0

        self.btn_start_request.setEnabled(has_serials)
        if not has_serials:
            self.progress_status_label.setText("Insira seriais para iniciar a requisição.")
            self.progress_bar.setValue(0)
        self.btn_generate_report.setEnabled(False)

    def _on_start_request_clicked(self):
        """Lida com o clique no botão 'Iniciar Requisição de Eventos'."""
        try:
            serials = serial_management.get_seriais()
            if not serials:
                self.signal_manager.show_toast_warning.emit("Por favor, carregue seriais antes de iniciar a requisição.")
                return

            start_dt = self.datetime_start.dateTime().toString("dd/MM/yyyy HH:mm:ss")
            end_dt = self.datetime_end.dateTime().toString("dd/MM/yyyy HH:mm:ss")
            event_filters = self._get_selected_event_filters()

            if not event_filters:
                self.signal_manager.show_toast_warning.emit("Por favor, selecione pelo menos um tipo de evento para filtrar.")
                return

            # SALVA CONFIGURAÇÃO NO APP_STATE
            self.app_state.set("eventos_config", {
                "start_datetime": start_dt,
                "end_datetime": end_dt,
                "filtros": event_filters,
                "serials": serials
            })

            # Se geração automática está ativada, abre diálogo ANTES da requisição
            if self.auto_generate_report:
                adicionar_log("🤖 Geração automática de relatório ativada. Abrindo diálogo de seleção de abas ANTES da requisição...")
                self._open_sheet_selection_dialog(start_request_on_accept=True)
            else:
                # Fluxo normal: inicia requisição
                adicionar_log(f"Iniciando requisição de eventos para {len(serials)} seriais de {start_dt} a {end_dt} com filtros: {event_filters}")
                self._reset_progress()
                self.btn_start_request.setEnabled(False)
                self.btn_generate_report.setEnabled(False)
                self.start_events_request.emit(serials, start_dt, end_dt, event_filters)

        except Exception as e:
            adicionar_log(f"❌ Erro ao iniciar requisição: {e}")
            self.signal_manager.show_toast_error.emit(f"Erro ao iniciar requisição: {e}")

    def _open_sheet_selection_dialog(self, start_request_on_accept: bool):
        """Abre diálogo para seleção de abas do relatório."""
        try:
            selected_event_names_for_dialog = []
            for event_name, event_id in self.event_filters_map.items():
                if self.filter_checkboxes.get(event_id) and self.filter_checkboxes[event_id].isChecked():
                    selected_event_names_for_dialog.append(event_name)

            config, accepted = EventsSheetSelectionDialog.get_sheet_config_dialog(
                self.app_state,
                self._get_selected_event_names_for_dialog(),
                self
            )

            if accepted:
                adicionar_log(f"📊 Abas selecionadas: {config['sheets']}")

                if start_request_on_accept:
                    serials = serial_management.get_seriais()
                    start_dt = self.datetime_start.dateTime().toString("dd/MM/yyyy HH:mm:ss")
                    end_dt = self.datetime_end.dateTime().toString("dd/MM/yyyy HH:mm:ss")
                    event_filters = self._get_selected_event_filters()

                    adicionar_log(f"Iniciando requisição de eventos para {len(serials)} seriais de {start_dt} a {end_dt} com filtros: {event_filters}")
                    self._reset_progress()
                    self.btn_start_request.setEnabled(False)
                    self.btn_generate_report.setEnabled(False)
                    self.start_events_request.emit(serials, start_dt, end_dt, event_filters)
                else:
                    # ✅ CORRETO: Emite apenas a lista
                    self.btn_generate_report.setText("⏳ Gerando Relatório... Aguarde...")
                    self.btn_generate_report.setEnabled(False)
                    self.generate_events_report.emit(self.last_events_data)
            else:
                adicionar_log("❌ Geração de relatório cancelada pelo usuário")
                if start_request_on_accept:
                    self.btn_start_request.setEnabled(True)
                    self.progress_status_label.setText("Requisição cancelada.")

        except Exception as e:
            adicionar_log(f"❌ Erro ao abrir diálogo de seleção: {e}")
            self.signal_manager.show_toast_error.emit(f"Erro ao abrir diálogo: {e}")

    def _on_generate_report_clicked(self):
        """Lida com o clique no botão 'Gerar Relatório Excel'."""
        if not self.last_events_data:
            self.signal_manager.show_toast_warning.emit("Nenhum dado de evento para gerar relatório.")
            return

        self._open_sheet_selection_dialog(start_request_on_accept=False)

    def update_progress(self, current: int, total: int, label: str):
        """Atualiza a barra de progresso e o label de status."""
        try:
            if total > 0:
                percentage = int((current / total) * 100)
                self.progress_bar.setValue(percentage)
                self.progress_status_label.setText(f"{label} ({current}/{total})")
            else:
                self.progress_bar.setValue(0)
                self.progress_status_label.setText(label)
        except Exception as e:
            adicionar_log(f"⚠️ Erro ao atualizar progresso na aba de eventos: {e}")

    def _reset_progress(self):
        """Reseta a barra de progresso e o label de status."""
        self.progress_bar.setValue(0)
        self.progress_status_label.setText("Aguardando requisição...")
        self.last_events_data = []
        self.btn_generate_report.setEnabled(False)
        self._report_generation_triggered = False

    def _handle_request_completed(self, data: list):
        """Lida com a conclusão da requisição de eventos."""
        adicionar_log(f"✅ Requisição de eventos concluída. {len(data)} registros recebidos.")
        self.btn_start_request.setEnabled(True)
        self.last_events_data = data

        if data:
            self.btn_generate_report.setEnabled(True)
            self.progress_status_label.setText(f"Requisição concluída. {len(data)} eventos encontrados.")

            # ✅ CORRETO: Geração automática emite apenas a lista
            if self.auto_generate_report and not self._report_generation_triggered:
                self._report_generation_triggered = True
                adicionar_log("🤖 Geração automática de relatório: Requisição concluída. Iniciando geração do relatório...")
                self.btn_generate_report.setText("⏳ Gerando Relatório... Aguarde...")
                self.btn_generate_report.setEnabled(False)
                self.generate_events_report.emit(self.last_events_data)
            elif self.auto_generate_report and self._report_generation_triggered:
                adicionar_log("ℹ️ Geração automática de relatório já disparada. Ignorando segunda chamada.")
        else:
            self.btn_generate_report.setEnabled(False)
            self.progress_status_label.setText("Requisição concluída. Nenhum evento encontrado.")

    def _restore_generate_button(self):
        """Restaura o botão de gerar relatório ao estado original."""
        self.btn_generate_report.setText("📊 Gerar Relatório Excel")
        self.btn_generate_report.setEnabled(True)
        self._report_generation_triggered = False

    def _get_selected_event_names_for_dialog(self):
        """Retorna os nomes dos eventos selecionados nos filtros."""
        selected = []
        for event_name, event_id in self.event_filters_map.items():
            chk = self.filter_checkboxes.get(event_id)
            if chk and chk.isChecked():
                selected.append(event_name)
        return selected
