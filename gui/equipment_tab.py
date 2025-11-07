# mogno_app/gui/equipment_tab.py
"""
Aba "Análise de Equipamentos" - Versão otimizada e modular.
"""
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox, QRadioButton, QProgressBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QGroupBox,
    QTextEdit, QFileDialog, QMessageBox, QStackedWidget,
    QDateEdit, QScrollArea, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont

from core.serial_management import ler_arquivo_serials

from utils.logger import adicionar_log
from utils.ui_helpers import (
    create_group_box, create_column_frame, create_section_title,
    create_separator, create_styled_button, create_info_label
)
from utils.styles import (
    BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE, BUTTON_WARNING_STYLE,
    BUTTON_DANGER_STYLE, PROGRESS_BAR_STYLE
)
from config.settings import OUTPUT_DIR
from utils.gui_utils import (
    log_message, update_progress, set_execution_complete,
    parse_serials, toggle_widget_enabled
)


class EquipmentTab(QWidget):
    """Aba de Análise de Equipamentos com layout otimizado."""
    # Sinais
    start_last_position_api = pyqtSignal(str, list)
    start_last_position_redis = pyqtSignal(list)
    start_status_equipment = pyqtSignal(list)
    start_data_consumption = pyqtSignal(list, str, str)
    generate_consolidated_report = pyqtSignal(dict)
    generate_separate_reports = pyqtSignal(dict)
    file_selected = pyqtSignal(str)
    serial_entry_changed = pyqtSignal()
    pause_requests = pyqtSignal()
    cancel_requests = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_serials = []
        self.csv_filepath = None
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface completa."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Seções
        content_layout.addWidget(self._create_serial_input_section())
        content_layout.addWidget(self._create_queries_section())
        content_layout.addWidget(self._create_actions_section())
        content_layout.addWidget(self._create_progress_section())
        content_layout.addStretch(1)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        self.update_interface_serial()

    def _create_serial_input_section(self):
        """Cria seção de entrada de seriais."""
        group = create_group_box("📋 Entrada de Seriais")
        layout = QVBoxLayout(group)

        # Modo de entrada
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Modo de Entrada:"))
        self.radio_csv = QRadioButton("Arquivo CSV/Excel")
        self.radio_manual = QRadioButton("Inserir Manualmente")
        self.radio_csv.setChecked(True)
        mode_layout.addWidget(self.radio_csv)
        mode_layout.addWidget(self.radio_manual)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        self.radio_csv.toggled.connect(self.update_interface_serial)

        # Container empilhado
        self.entry_container = QStackedWidget()
        self.entry_container.addWidget(self._create_csv_input())
        self.entry_container.addWidget(self._create_manual_input())
        layout.addWidget(self.entry_container)

        # Status
        self.serial_status_label = QLabel("Selecione um modo de entrada")
        self.serial_status_label.setStyleSheet("color: gray; font-style: italic;")
        self.serial_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.serial_status_label)
        return group

    def _create_csv_input(self):
        """Cria input CSV."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.entry_csv_nome = QLineEdit()
        self.entry_csv_nome.setReadOnly(True)
        self.entry_csv_nome.setPlaceholderText("Nenhum arquivo selecionado")
        self.btn_select_file = QPushButton("📁 Selecionar Arquivo")
        self.btn_select_file.clicked.connect(self.select_file)
        layout.addWidget(QLabel("Arquivo:"))
        layout.addWidget(self.entry_csv_nome, 1)
        layout.addWidget(self.btn_select_file)
        return widget

    def _create_manual_input(self):
        """Cria input manual."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.entry_serials = QLineEdit()
        self.entry_serials.setPlaceholderText("Ex: 123456789;987654321")
        self.entry_serials.textChanged.connect(self.update_serial_count)
        self.entry_serials.textChanged.connect(self.update_serial_status)
        self.lbl_serial_count = QLabel("0 seriais")
        self.lbl_serial_count.setStyleSheet("color: gray;")
        layout.addWidget(QLabel("Seriais (separados por ;):"))
        layout.addWidget(self.entry_serials, 1)
        layout.addWidget(self.lbl_serial_count)
        return widget

    def _create_queries_section(self):
        """Cria seção de consultas em 3 colunas."""
        group = create_group_box("🔎 Consultas Disponíveis")
        layout = QVBoxLayout(group)
        grid = QGridLayout()
        grid.setSpacing(15)
        grid.addWidget(self._create_last_position_column(), 0, 0)
        grid.addWidget(self._create_status_consumption_column(), 0, 1)
        grid.addWidget(self._create_line_lorawan_column(), 0, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        layout.addLayout(grid)
        return group

    def _create_last_position_column(self):
        """Cria coluna de últimas posições."""
        col = create_column_frame()
        layout = QVBoxLayout(col)
        self.chk_last_position = QCheckBox("📍 Últimas Posições")
        self.chk_last_position.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.chk_last_position.setChecked(True)
        layout.addWidget(self.chk_last_position)
        self.last_pos_options = QFrame()
        opt_layout = QVBoxLayout(self.last_pos_options)
        self.radio_redis = QRadioButton("Redis")
        self.radio_api_mogno = QRadioButton("API Mogno")
        self.radio_redis.setChecked(True)
        opt_layout.addWidget(self.radio_redis)
        opt_layout.addWidget(self.radio_api_mogno)
        self.api_mogno_frame = QFrame()
        api_layout = QVBoxLayout(self.api_mogno_frame)
        self.radio_rastreadores = QRadioButton("Rastreadores")
        self.radio_iscas = QRadioButton("Iscas")
        self.radio_rastreadores.setChecked(True)
        self.radio_rastreadores.setEnabled(False)
        self.radio_iscas.setEnabled(False)
        api_layout.addWidget(self.radio_rastreadores)
        api_layout.addWidget(self.radio_iscas)
        opt_layout.addWidget(self.api_mogno_frame)
        self.radio_api_mogno.toggled.connect(lambda checked: toggle_widget_enabled([self.radio_rastreadores, self.radio_iscas], checked))
        self.chk_last_position.toggled.connect(lambda checked: toggle_widget_enabled([self.last_pos_options], checked))
        layout.addWidget(self.last_pos_options)
        layout.addStretch()
        return col

    def _create_status_consumption_column(self):
        """Cria coluna de status e consumo."""
        col = create_column_frame()
        layout = QVBoxLayout(col)
        self.chk_status_equipment = QCheckBox("⚙️ Status dos Equipamentos")
        self.chk_status_equipment.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(self.chk_status_equipment)
        layout.addWidget(create_info_label("Somente equipamentos Maxtrack"))
        layout.addSpacing(15)
        self.chk_data_consumption = QCheckBox("📊 Consumo de Dados")
        self.chk_data_consumption.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(self.chk_data_consumption)
        self.data_consumption_options = QFrame()
        cons_layout = QVBoxLayout(self.data_consumption_options)
        period_layout = QHBoxLayout()
        period_layout.setSpacing(10)
        period_label = QLabel("Período:")
        period_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        period_layout.addWidget(period_label)
        self.consumption_month = QComboBox()
        self.consumption_month.addItems([
            "01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril",
            "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto",
            "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"
        ])
        self.consumption_month.setCurrentIndex(QDate.currentDate().month() - 1)
        self.consumption_month.setFixedWidth(150)
        period_layout.addWidget(self.consumption_month)
        self.consumption_year = QComboBox()
        current_year = QDate.currentDate().year()
        for year in range(current_year - 2, current_year + 3):
            self.consumption_year.addItem(str(year))
        self.consumption_year.setCurrentText(str(current_year))
        self.consumption_year.setFixedWidth(90)
        period_layout.addWidget(self.consumption_year)
        period_layout.addStretch()
        cons_layout.addLayout(period_layout)
        self.data_consumption_options.setEnabled(False)
        layout.addWidget(self.data_consumption_options)
        self.chk_data_consumption.toggled.connect(
            lambda c: toggle_widget_enabled([self.data_consumption_options], c)
        )
        layout.addStretch()
        return col

    def _create_line_lorawan_column(self):
        """Cria coluna de linha e LoraWAN."""
        col = create_column_frame()
        layout = QVBoxLayout(col)
        self.chk_line_status = QCheckBox("📞 Status de Linha")
        self.chk_line_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.chk_line_status.setEnabled(True)
        layout.addWidget(self.chk_line_status)
        self.line_status_options = QFrame()
        line_layout = QHBoxLayout(self.line_status_options)
        line_layout.setSpacing(15)
        line_layout.setContentsMargins(15, 5, 0, 0)
        self.chk_claro = QCheckBox("Claro")
        self.chk_tim = QCheckBox("TIM")
        self.chk_vivo = QCheckBox("Vivo")
        self.chk_algar = QCheckBox("Algar")
        for chk in [self.chk_claro, self.chk_tim, self.chk_vivo, self.chk_algar]:
            chk.setEnabled(False)
            line_layout.addWidget(chk)
        self.line_status_options.setEnabled(True)
        layout.addWidget(self.line_status_options)
        self.chk_lorawan_status = QCheckBox("🌐 Status LoraWAN")
        self.chk_lorawan_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.chk_lorawan_status.setEnabled(True)
        layout.addWidget(self.chk_lorawan_status)
        layout.addWidget(create_info_label("(Everynet - Em breve)"))
        layout.addStretch()
        return col

    def _create_actions_section(self):
        """Cria seção de ações."""
        group = create_group_box("⚡ Ações")
        layout = QHBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)
        self.btn_start_requests = create_styled_button(
            "🚀 Iniciar Requisições", BUTTON_PRIMARY_STYLE, 180, 40
        )
        self.btn_start_requests.setEnabled(False)
        self.btn_start_requests.clicked.connect(self.start_requests)
        self.btn_pause_requests = create_styled_button(
            "⏸️ Pausar", BUTTON_WARNING_STYLE, 120, 40
        )
        self.btn_pause_requests.setEnabled(False)
        self.btn_pause_requests.clicked.connect(self.pause_requests.emit)
        self.btn_cancel_requests = create_styled_button(
            "❌ Cancelar", BUTTON_DANGER_STYLE, 120, 40
        )
        self.btn_cancel_requests.setEnabled(False)
        self.btn_cancel_requests.clicked.connect(self.cancel_requests.emit)
        self.btn_generate_report = create_styled_button(
            "📊 Gerar Relatório", BUTTON_SECONDARY_STYLE, 160, 40
        )
        self.btn_generate_report.setEnabled(False)
        self.btn_generate_report.clicked.connect(self.generate_report)
        layout.addWidget(self.btn_start_requests)
        layout.addWidget(self.btn_pause_requests)
        layout.addWidget(self.btn_cancel_requests)
        layout.addSpacing(30)
        layout.addWidget(self.btn_generate_report)
        self.radio_consolidated = QRadioButton("Consolidado")
        self.radio_separate = QRadioButton("Separado")
        self.radio_consolidated.setChecked(True)
        layout.addWidget(QLabel("Formato:"))
        layout.addWidget(self.radio_consolidated)
        layout.addWidget(self.radio_separate)
        layout.addStretch()
        return group

    def _create_progress_section(self):
        """Cria seção de progresso."""
        group = create_group_box("📊 Progresso da Execução")
        layout = QVBoxLayout(group)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        layout.addWidget(self.progress_bar)
        self.progress_status_label = QLabel("Aguardando início da execução...")
        self.progress_status_label.setAlignment(Qt.AlignCenter)
        self.progress_status_label.setStyleSheet("font-style: italic; color: #666666;")
        layout.addWidget(self.progress_status_label)
        return group

    # ========== MÉTODOS DE CONTROLE ==========
    def select_file(self):
        """Seleciona arquivo de seriais."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo de seriais", "",
            "Arquivos (*.csv *.xlsx);;Todos (*.*)"
        )
        if filepath:
            self.csv_filepath = filepath
            self.entry_csv_nome.setText(os.path.basename(filepath))
            self.file_selected.emit(filepath)

    def update_serial_count(self):
        """Atualiza contagem de seriais manuais, removendo duplicados."""
        text = self.entry_serials.text().strip()
        serials = [s.strip() for s in text.split(";") if s.strip()]
        total_lidos = len(serials)
        label_text = f"Total de {total_lidos} seriais inseridos"
        self.lbl_serial_count.setText(label_text)
        self.lbl_serial_count.setStyleSheet("color: green; font-weight: bold;")
        self.update_serial_status()

    def update_interface_serial(self):
        """Atualiza interface de entrada de seriais."""
        self.entry_container.setCurrentIndex(0 if self.radio_csv.isChecked() else 1)
        self.update_serial_status()

    def update_serial_status(self):
        """Atualiza status de seriais."""
        if self.radio_csv.isChecked():
            if self.csv_filepath and self.current_serials:
                self.serial_status_label.setText(f"📄 {len(self.current_serials)} seriais carregados")
                self.serial_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.btn_start_requests.setEnabled(True)
            else:
                self.serial_status_label.setText("Selecione um arquivo CSV/Excel")
                self.serial_status_label.setStyleSheet("color: gray; font-style: italic;")
                self.btn_start_requests.setEnabled(False)
        else:
            text = self.entry_serials.text().strip()
            serials = [s.strip() for s in text.split(";") if s.strip()]
            total_lidos = len(serials)
            unique_serials = list(set(serials))
            count_unique = len(unique_serials)
            duplicados = total_lidos - count_unique
            if count_unique > 0:
                status_text = f"📄 {count_unique} seriais únicos inseridos"
                if duplicados > 0:
                    status_text += f" ({duplicados} duplicados removidos)"
                self.serial_status_label.setText(status_text)
                self.serial_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.btn_start_requests.setEnabled(True)
            else:
                self.serial_status_label.setText("Digite os seriais separados por ';'")
                self.serial_status_label.setStyleSheet("color: gray; font-style: italic;")
                self.btn_start_requests.setEnabled(False)

    def get_selected_serials(self):
        """Retorna lista de seriais selecionados, removendo duplicados."""
        if self.radio_csv.isChecked():
            return self.current_serials.copy()
        text = self.entry_serials.text().strip()
        serials = [s.strip() for s in text.split(";") if s.strip()]
        return list(set(serials))

    def start_requests(self):
        """Inicia requisições selecionadas."""
        serials = self.get_selected_serials()
        if not serials:
            QMessageBox.warning(self, "Aviso", "Nenhum serial selecionado.")
            return
        enabled_queries = []
        if self.chk_last_position.isChecked():
            if self.radio_api_mogno.isChecked():
                api_type = "rastreadores" if self.radio_rastreadores.isChecked() else "iscas"
                self.start_last_position_api.emit(api_type, serials)
                enabled_queries.append("last_position_api")
            else:
                self.start_last_position_redis.emit(serials)
                enabled_queries.append("last_position_redis")
        if self.chk_status_equipment.isChecked():
            self.start_status_equipment.emit(serials)
            enabled_queries.append("status_equipment")
        if self.chk_data_consumption.isChecked():
            month = self.consumption_month.currentText().split(" - ")[0]
            year = self.consumption_year.currentText()
            self.start_data_consumption.emit(serials, month, year)
            enabled_queries.append("data_consumption")
        if not enabled_queries:
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos uma consulta.")
            return
        self.btn_start_requests.setEnabled(False)
        self.btn_pause_requests.setEnabled(True)
        self.btn_cancel_requests.setEnabled(True)

    def generate_report(self):
        """Gera relatório baseado nas opções."""
        main_window = self.window()
        if hasattr(main_window, "requisicoes_concluidas") and not main_window.requisicoes_concluidas:
            QMessageBox.warning(self, "Aviso", "As requisições ainda não foram concluídas.")
            return
        serials = self.get_selected_serials()
        if not serials:
            QMessageBox.warning(self, "Aviso", "Nenhum serial selecionado.")
            return
        opcoes = {
            "serials": serials,
            "consolidated": self.radio_consolidated.isChecked(),
            "enabled_queries": []
        }
        if self.chk_last_position.isChecked():
            opcoes["enabled_queries"].append("last_position")
        if self.chk_status_equipment.isChecked():
            opcoes["enabled_queries"].append("status_equipment")
        if self.chk_data_consumption.isChecked():
            opcoes["enabled_queries"].append("data_consumption")
        if not opcoes["enabled_queries"]:
            QMessageBox.warning(self, "Aviso", "Nenhuma consulta executada.")
            return
        if self.radio_consolidated.isChecked():
            self.generate_consolidated_report.emit(opcoes)
        else:
            self.generate_separate_reports.emit(opcoes)

    def handle_file_selected(self, filepath):
        """Processa seleção de arquivo CSV com seriais"""
        try:
            result = ler_arquivo_serials(filepath)
            self.current_serials = result["unicos"]
            self.update_serial_status()
        except Exception as e:
            adicionar_log(f"❌ Erro ao carregar arquivo: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar arquivo:\n{e}")