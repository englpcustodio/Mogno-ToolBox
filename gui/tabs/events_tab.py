# gui/tabs/events_tab.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QGroupBox, QGridLayout, QCheckBox,
    QScrollArea, QDateTimeEdit, QProgressBar, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from utils.logger import adicionar_log
from core import serial_management # Importar o módulo de gerenciamento de seriais

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

        period_layout.addWidget(QLabel("Data/Hora Início:"), 0, 0)
        self.datetime_start = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_start.setCalendarPopup(True)
        self.datetime_start.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        # Definir a data de hoje (27/11/2025) às 00:00:00
        today = QDateTime(2025, 11, 27, 0, 0, 0)
        self.datetime_start.setDateTime(today)
        period_layout.addWidget(self.datetime_start, 0, 1)

        period_layout.addWidget(QLabel("Data/Hora Fim:"), 1, 0)
        self.datetime_end = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_end.setCalendarPopup(True)
        self.datetime_end.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        # Definir a data de hoje (27/11/2025) às 23:59:59
        end_of_today = QDateTime(2025, 11, 27, 23, 59, 59)
        self.datetime_end.setDateTime(end_of_today)
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

    def _connect_signals(self):
        """Conecta os sinais dos widgets aos seus respectivos slots."""
        self.serials_text_edit.textChanged.connect(self._handle_manual_serials_input)
        self.btn_select_file.clicked.connect(self._handle_file_selected)
        self.btn_clear_serials.clicked.connect(self._on_clear_serials_clicked)
        self.btn_select_all_filters.clicked.connect(lambda: self._set_all_filters(True))
        self.btn_deselect_all_filters.clicked.connect(lambda: self._set_all_filters(False))
        self.btn_start_request.clicked.connect(self._on_start_request_clicked)
        self.btn_generate_report.clicked.connect(self._on_generate_report_clicked)

        # Conectar sinais do SignalManager para atualização de progresso
        self.signal_manager.events_progress_updated.connect(self.update_progress)
        self.signal_manager.events_request_completed.connect(self._handle_request_completed)
        # Reutilizar para habilitar/desabilitar o botão de iniciar (se necessário, embora _check_enable_start_button já faça isso)
        # self.signal_manager.enable_start_button.connect(self._set_start_button_enabled)
        # Para reabilitar o botão de gerar relatório (já tratado em _handle_request_completed)
        # self.signal_manager.all_requests_finished.connect(self._handle_all_requests_finished)

    def _get_event_filters_map(self):
        """Retorna um dicionário com os IDs e nomes dos eventos."""
        # A lista de eventos fornecida pelo usuário
        events_data = [
            (0, "POSICAO"), (1, "PANICO"), (2, "FAKE_VIOLADO"), (3, "FAKE_RESTAURADO"), (4, "ANTENA_GPS_CORTADA"),
            (5, "ANTENA_GPS_RECONECTADA"), (6, "IGNICAO_ON"), (7, "IGNICAO_OFF"), (8, "BATERIA_EXTERNA_PERDIDA"),
            (9, "BATERIA_EXTERNA_RECONECTADA"), (10, "BATERIA_EXTERNA_BAIXA"), (11, "BATERIA_INTERNA_PERDIDA"),
            (12, "BATERIA_INTERNA_RECONECTADA"), (13, "BATERIA_INTERNA_BAIXA"), (14, "BATERIA_INTERNA_ERRO"),
            (15, "INICIO_SLEEP"), (16, "RESET_RASTREADOR"), (17, "INICIO_SUPER_SLEEP"), (18, "BLOQUEIO_ANTIFURTO"),
            (19, "DESBLOQUEIO_ANTIFURTO"), (20, "RESPOSTA_POSICAO_SOLICITADA"), (21, "POSICAO_EM_SLEEP"),
            (22, "POSICAO_EM_SUPER_SLEEP"), (23, "OPERADORA_CELULAR"), (24, "ALARME_ANTIFURTO"), (25, "DADOS_VIAGEM"),
            (26, "DADOS_ESTACIONAMENTO"), (27, "PAINEL_VIOLADO"), (28, "PAINEL_RESTAURADO"), (29, "TECLADO_CONECTADO"),
            (30, "TECLADO_DESCONECTADO"), (31, "SENSOR_LIVRE_RESTAURADO"), (32, "MACRO"), (33, "MENSAGEM_NUMERICA"),
            (34, "TERMINO_SLEEP"), (35, "TERMINO_SUPER_SLEEP"), (36, "INICIO_DEEP_SLEEP"), (37, "TERMINO_DEEP_SLEEP"),
            (38, "BATERIA_BACKUP_RECONECTADA"), (39, "BATERIA_BACKUP_DESCONECTADA"), (40, "ANTENA_GPS_EM_CURTO"),
            (41, "ANTIFURTO_RESTAURADO"), (42, "ANTIFURTO_VIOLADO"), (43, "INICIO_MODO_PANICO"), (44, "FIM_MODO_PANICO"),
            (45, "ALERTA_ACELERACAO_FORA_PADRAO"), (46, "ALERTA_FREADA_BRUSCA"), (47, "ALERTA_CURVA_AGRESSIVA"),
            (48, "ALERTA_DIRECAO_ACIMA_VELOCIDADE_PADRAO"), (49, "JAMMING_DETECTADO"), (50, "PLATAFORMA_ACIONADA"),
            (51, "BOTAO_ANTIFURTO_PRESSIONADO"), (52, "EVENTO_GENERICO"), (53, "CARCACA_VIOLADA"),
            (54, "JAMMING_RESTAURADO"), (55, "GPS_FALHA"), (56, "IDENTIFICACAO_CONDUTOR"), (57, "BLOQUEADOR_VIOLADO"),
            (58, "BLOQUEADOR_RESTAURADO"), (59, "COLISAO"), (60, "ECU_VIOLADA"), (61, "ECU_INSTALADA"),
            (62, "IDENTIFICACAO_CONDUTOR_NAO_CADASTRADO"), (63, "FREQ_CONT_PULSOS_ACIMA_LIMITE"),
            (64, "PLATAFORMA_DESACIONADA"), (65, "BETONEIRA_CARREGANDO"), (66, "BETONEIRA_DESCARREGANDO"),
            (67, "PORTA_ABERTA"), (68, "PORTA_FECHADA"), (69, "ALERTA_FREADA_BRUSCA_ACELERACAO_FORA_PADRAO"),
            (70, "TIMEOUT_IDENTIFICADOR_CONDUTOR"), (71, "BAU_ABERTO"), (72, "BAU_FECHADO"), (73, "CARRETA_ENGATADA"),
            (74, "CARRETA_DESENGATADA"), (75, "TECLADO_MENSAGEM"), (76, "ACAO_EMBARCADA_ACIONADA"),
            (77, "ACAO_EMBARCADA_DESACIONADA"), (78, "FIM_VELOCIDADE_ACIMA_DO_PADRAO"), (79, "ENTRADA_EM_BANGUELA"),
            (80, "SAIDA_DE_BANGUELA"), (81, "RPM_EXCEDIDO"),
            (82, "ALERTA_DE_DIRECAO_COM_VELOCIDADE_EXCESSIVA_NA_CHUVA"),
            (83, "FIM_DE_VELOCIDADE_ACIMA_DO_PADRAO_NA_CHUVA"),
            (84, "VEICULO_PARADO_COM_MOTOR_FUNCIONANDO"), (85, "VEICULO_PARADO"),
            (86, "CALIBRACAO_AUTOMATICA_DO_RPM_REALIZADA"),
            (87, "CALIBRACAO_DO_ODOMETRO_FINALIZADA"), (88, "MODO_ERB"),
            (89, "EMERGENCIA_OU_POSICAO_DE_DISPOSITIVO_RF_EM_MODO_ERB"), (90, "EMERGENCIA_POR_PRESENCA"),
            (91, "EMERGENCIA_POR_RF"), (92, "DISPOSITIVO_PRESENCA_AUSENTE"),
            (93, "BATERIA_VEICULO_ABAIXO_LIMITE_PRE_DEFINIDO"), (94, "LEITURA_OBD"),
            (95, "VEICULO_PARADO_COM_RPM"), (96, "MODO_EMERGENCIA_POR_JAMMING"), (97, "EMERGENCIA_POR_GPRS"),
            (98, "DETECCAO_RF"), # Adicionado DETECCAO_RF com ID 98
            (99, "DISPOSITIVO_PRESENCA_RECUPERADO"), (100, "ENTRADA_MODO_EMERGENCIA"),
            (101, "SAIDA_MODO_EMERGENCIA"), (102, "EMERGENCIA"), (103, "INICIO_DE_MOVIMENTO"),
            (104, "FIM_DE_MOVIMENTO"), (105, "VEICULO_PARADO_COM_IGNICAO_LIGADA"),
            (106, "REGRA_GEOGRAFICO"), (107, "ALERTA_DE_IGNICAO_SEM_FAROL"),
            (108, "FIM_DE_IGNICAO_SEM_FAROL"), (109, "INICIO_MOVIMENTO_SEM_BATERIA_EXTERNA"),
            (110, "FIM_MOVIMENTO_SEM_BATERIA_EXTERNA"), (111, "RASTREAMENTO_ATIVADO"),
            (112, "RASTREAMENTO_DESATIVADO"), (113, "ALERTA_DE_MOTORISTA_COM_SONOLENCIA"),
            (114, "ALERTA_DE_MOTORISTA_COM_DISTRACAO"), (115, "ALERTA_DE_MOTORISTA_BOCEJANDO"),
            (116, "ALERTA_DE_MOTORISTA_AO_TELEFONE"), (117, "ALERTA_DE_MOTORISTA_FUMANDO")
        ]
        return {name: id for id, name in events_data} # Inverte para ter nome -> ID

    def _populate_event_filters(self):
        """Preenche o layout de filtros com checkboxes para cada evento."""
        self.filter_checkboxes = {}
        col = 0
        row = 0
        # Ordena os eventos pelo ID para exibição consistente
        sorted_events = sorted(self.event_filters_map.items(), key=lambda item: item[1])
        for event_name, event_id in sorted_events:
            checkbox = QCheckBox(f"{event_id} - {event_name}")
            checkbox.setChecked(True) # Todos selecionados por padrão
            self.filters_grid_layout.addWidget(checkbox, row, col)
            self.filter_checkboxes[event_id] = checkbox
            col += 1
            if col >= 3: # 3 colunas por linha
                col = 0
                row += 1

    def _set_all_filters(self, checked: bool):
        """Marca ou desmarca todos os checkboxes de filtro."""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(checked)

    def _get_selected_event_filters(self) -> str:
        """Retorna uma string formatada com os IDs dos eventos selecionados."""
        selected_ids = []
        # Ordena os IDs para garantir uma string de filtro consistente
        for event_id in sorted(self.filter_checkboxes.keys()):
            checkbox = self.filter_checkboxes[event_id]
            if checkbox.isChecked():
                selected_ids.append(str(event_id))
        return ",".join(selected_ids)

    def _handle_manual_serials_input(self):
        """Processa a entrada manual de seriais e atualiza a contagem."""
        text = self.serials_text_edit.toPlainText()
        info = serial_management.carregar_seriais_manualmente(text)
        # O dicionário 'info' retornado por carregar_seriais_manualmente contém 'unicos', 'total_lidos', 'duplicados'
        # Precisamos passar a informação de quantidade para _update_serial_count_label
        self._update_serial_count_label(info) # <--- Ajuste aqui: info já contém os dados necessários
        self._check_enable_start_button()

    def _handle_file_selected(self, filepath):
        """Lida com a seleção de um arquivo de seriais."""
        info = serial_management.ler_arquivo_serials(filepath)
        # O dicionário 'info' retornado por ler_arquivo_serials contém 'unicos', 'total_lidos', 'duplicados'
        # Precisamos passar a informação de quantidade para _update_serial_count_label
        self._update_serial_count_label(info) # <--- Ajuste aqui: info já contém os dados necessários
        self._check_enable_start_button()

    def _on_clear_serials_clicked(self):
        """Limpa a área de texto de seriais e a lista interna."""
        serial_management.limpar_seriais()
        self.serials_text_edit.clear()
        self._update_serial_count_label() # Chamada sem argumentos para resetar
        self._check_enable_start_button()

    def _update_serial_count_label(self, info=None): # <--- Adicionado info=None como argumento opcional
        """Atualiza o label com a contagem de seriais carregados."""
        if info is None:
            # Se info não for fornecido, pega do serial_management (para inicialização ou limpeza)
            current_serials_info = serial_management.get_info_serials()
            total_serials = current_serials_info.get('quantidade_total', 0) # <--- Usar 'quantidade_total'
            # 'origem' e 'arquivo_carregado' também estão em current_serials_info, mas não são usados aqui
            self.serial_count_label.setText(f"Seriais carregados: {total_serials}")
        else:
            # Se info for fornecido (de _handle_manual_serials_input ou _handle_file_selected)
            total_lidos = info.get('total_lidos', 0)
            duplicados = info.get('duplicados', 0)
            unicos = info.get('unicos', [])
            self.serial_count_label.setText(
                f"Seriais carregados: {len(unicos)} (Total lidos: {total_lidos}, Duplicados removidos: {duplicados})"
            )
        self._check_enable_start_button() # Re-verifica o estado do botão após a atualização


    def _check_enable_start_button(self):
        """Verifica se há seriais carregados para habilitar o botão de iniciar."""
        # A forma mais robusta de verificar se há seriais é pegar a lista de seriais
        # e verificar seu tamanho, em vez de depender de uma chave específica no dicionário de info.
        serials_list = serial_management.get_seriais()
        has_serials = len(serials_list) > 0

        self.btn_start_request.setEnabled(has_serials)
        if not has_serials:
            self.progress_status_label.setText("Insira seriais para iniciar a requisição.")
            self.progress_bar.setValue(0)
        # Também desabilita o botão de relatório se não houver seriais
        self.btn_generate_report.setEnabled(False)

    def _on_start_request_clicked(self):
        """Lida com o clique no botão 'Iniciar Requisição de Eventos'."""
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

        adicionar_log(f"Iniciando requisição de eventos para {len(serials)} seriais de {start_dt} a {end_dt} com filtros: {event_filters}")
        self._reset_progress()
        self.btn_start_request.setEnabled(False)
        self.btn_generate_report.setEnabled(False) # Desabilita o botão de relatório ao iniciar nova requisição

        # Emite o sinal para o RequestHandler iniciar a requisição
        self.start_events_request.emit(serials, start_dt, end_dt, event_filters)

    def _on_generate_report_clicked(self):
        """Lida com o clique no botão 'Gerar Relatório Excel'."""
        if not self.last_events_data:
            self.signal_manager.show_toast_warning.emit("Nenhum dado de evento para gerar relatório.")
            return

        adicionar_log("Gerando relatório de eventos...")
        self.signal_manager.show_toast_info.emit("Gerando relatório de eventos... Por favor, aguarde.")
        self.btn_generate_report.setEnabled(False) # Desabilita enquanto gera o relatório
        # Emite o sinal para o ReportHandler com os dados coletados
        self.generate_events_report.emit(self.last_events_data)


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
        self.last_events_data = [] # Limpa os dados anteriores
        self.btn_generate_report.setEnabled(False) # Garante que o botão de relatório esteja desabilitado

    def _set_start_button_enabled(self, enabled: bool):
        """Habilita ou desabilita o botão de iniciar requisição."""
        # Esta função pode ser usada se houver uma lógica externa que precise controlar o botão
        # No entanto, _check_enable_start_button e _on_start_request_clicked já gerenciam isso internamente.
        self.btn_start_request.setEnabled(enabled)

    def _handle_request_completed(self, data: list):
        """Lida com a conclusão da requisição de eventos."""
        adicionar_log(f"Requisição de eventos concluída. {len(data)} registros recebidos.")
        self.btn_start_request.setEnabled(True) # Reabilita o botão de iniciar
        self.last_events_data = data # Armazena os dados para o relatório

        if data:
            self.btn_generate_report.setEnabled(True) # Habilita o botão de relatório se houver dados
            self.progress_status_label.setText(f"Requisição concluída. {len(data)} eventos encontrados.")
        else:
            self.btn_generate_report.setEnabled(False)
            self.progress_status_label.setText("Requisição concluída. Nenhum evento encontrado.")

    def _handle_all_requests_finished(self):
        """Lida com o sinal de que todas as requisições foram finalizadas."""
        # Este sinal é mais genérico e pode ser usado para lógicas globais.
        # A habilitação do botão de relatório já é tratada por _handle_request_completed,
        # que é mais específico para a conclusão da requisição de eventos.
        pass

