# mogno_app/gui/widgets.py

from PyQt5.QtWidgets import (
    QLabel, QGroupBox, QFrame, QPushButton,
    QGraphicsOpacityEffect, QDialog, QDialogButtonBox, 
    QVBoxLayout, QHBoxLayout, QCheckBox, QScrollArea, QWidget
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

# -----------------------------------------
#   Diálogo para seleção de períodos (abas) em relatórios de últimas posições.
# -----------------------------------------
class SheetSelectionDialog(QDialog):
    """Diálogo para escolher quais períodos e tipos de comunicação incluir no relatório."""

    def __init__(self, app_state, parent=None):
        super().__init__(parent)

        # Armazena referência ao app_state
        self.app_state = app_state

        self.setWindowTitle("📊 Selecionar Períodos e Tipos de Comunicação")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)

        self._setup_ui()
        self._update_periods_state()  # Atualiza estado inicial dos períodos
        self._update_ok_button_state()  # ← NOVO: Atualiza estado inicial do botão OK

    def _setup_ui(self):
        """Constrói a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # =====================================================================
        # TÍTULO PRINCIPAL
        # =====================================================================
        title = QLabel("Configure as abas a serem incluídas no relatório:")
        title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(title)

        # =====================================================================
        # LAYOUT DE DUAS COLUNAS: TIPOS DE COMUNICAÇÃO + PERÍODOS
        # =====================================================================
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(15)

        # ─────────────────────────────────────────────────────────────────────
        # COLUNA 1: TIPOS DE COMUNICAÇÃO
        # ─────────────────────────────────────────────────────────────────────
        comm_group = QGroupBox("📡 Tipos de Comunicação")
        comm_group.setFont(QFont("Segoe UI", 9, QFont.Bold))
        comm_layout = QVBoxLayout(comm_group)

        self.chk_gsm = QCheckBox("📶 GSM")
        self.chk_lorawan = QCheckBox("🛜 LoRaWAN")
        self.chk_p2p = QCheckBox("🔗 LoRaP2P")

        # Todos desmarcados por padrão
        for chk in [self.chk_gsm, self.chk_lorawan, self.chk_p2p]:
            chk.setChecked(False)
            comm_layout.addWidget(chk)
            # Conecta mudança de estado
            chk.stateChanged.connect(self._update_periods_state)
            chk.stateChanged.connect(self._update_ok_button_state)  # ← NOVO

        comm_layout.addStretch()
        columns_layout.addWidget(comm_group)

        # ─────────────────────────────────────────────────────────────────────
        # COLUNA 2: PERÍODOS
        # ─────────────────────────────────────────────────────────────────────
        self.period_group = QGroupBox("📅 Períodos (por tipo de comunicação)")
        self.period_group.setFont(QFont("Segoe UI", 9, QFont.Bold))
        period_layout = QVBoxLayout(self.period_group)

        self.chk_hoje = QCheckBox("📅 Hoje")
        self.chk_1_7 = QCheckBox("📆 1-7 dias")
        self.chk_8_15 = QCheckBox("📆 8-15 dias")
        self.chk_16_plus = QCheckBox("📆 +16 dias")

        # Todos desmarcados por padrão
        for chk in [self.chk_hoje, self.chk_1_7, self.chk_8_15, self.chk_16_plus]:
            chk.setChecked(False)
            period_layout.addWidget(chk)
            chk.stateChanged.connect(self._update_ok_button_state)  # ← NOVO

        period_layout.addStretch()
        columns_layout.addWidget(self.period_group)

        layout.addLayout(columns_layout)

        # =====================================================================
        # NOTA INFORMATIVA
        # =====================================================================
        note = QLabel(
            "ℹ️ <i>Se nenhum tipo de comunicação for selecionado, apenas as abas fixas serão geradas: "
            "<b>'Resumo_Tipos'</b>, <b>'Equip_sem_posicao'</b> e "
            "<b>detalhadas</b> (GSM_Detalhado, LoRaWAN_Detalhado, P2P_Detalhado).</i>"
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            "color: #666; font-size: 9pt; padding: 10px; "
            "background-color: #f0f0f0; border-radius: 5px;"
        )
        layout.addWidget(note)

        # =====================================================================
        # BOTÕES DE AÇÃO RÁPIDA
        # =====================================================================
        button_layout = QHBoxLayout()

        btn_select_all = QPushButton("✅ Marcar Todos")
        btn_select_all.setToolTip("Marca todos os tipos de comunicação e períodos")
        btn_select_all.clicked.connect(self._select_all)

        btn_deselect_all = QPushButton("❌ Desmarcar Todos")
        btn_deselect_all.setToolTip("Desmarca todos os tipos de comunicação e períodos")
        btn_deselect_all.clicked.connect(self._deselect_all)

        self.btn_only_periods = QPushButton("📅 Apenas Períodos")
        self.btn_only_periods.setToolTip("Marca todos os períodos (requer tipo de comunicação selecionado)")
        self.btn_only_periods.clicked.connect(self._select_all_periods)

        button_layout.addWidget(btn_select_all)
        button_layout.addWidget(btn_deselect_all)
        button_layout.addWidget(self.btn_only_periods)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # =====================================================================
        # BOTÕES OK/CANCELAR
        # =====================================================================
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # ✅ Armazena referência ao botão OK
        self.btn_ok = self.button_box.button(QDialogButtonBox.Ok)

    # =========================================================================
    # ATUALIZAÇÃO DE ESTADO DOS PERÍODOS
    # =========================================================================

    def _update_periods_state(self):
        """
        Habilita/desabilita checkboxes de períodos e botão 'Apenas Períodos'
        baseado na seleção de tipos de comunicação.
        """
        # Verifica se pelo menos um tipo de comunicação está marcado
        has_comm_type = any([
            self.chk_gsm.isChecked(),
            self.chk_lorawan.isChecked(),
            self.chk_p2p.isChecked()
        ])

        # Habilita/desabilita grupo de períodos
        self.period_group.setEnabled(has_comm_type)

        # Habilita/desabilita checkboxes individuais
        for chk in [self.chk_hoje, self.chk_1_7, self.chk_8_15, self.chk_16_plus]:
            chk.setEnabled(has_comm_type)

        # Habilita/desabilita botão "Apenas Períodos"
        self.btn_only_periods.setEnabled(has_comm_type)

        # Se desabilitado, desmarca todos os períodos
        if not has_comm_type:
            for chk in [self.chk_hoje, self.chk_1_7, self.chk_8_15, self.chk_16_plus]:
                chk.setChecked(False)

    # =========================================================================
    # ✅ NOVO: ATUALIZAÇÃO DE ESTADO DO BOTÃO OK
    # =========================================================================

    def _update_ok_button_state(self):
        """
        Habilita/desabilita o botão OK baseado nas regras:
        1. OK habilitado se NENHUM tipo de comunicação estiver marcado (gera apenas abas fixas)
        2. OK habilitado se PELO MENOS UM tipo de comunicação E PELO MENOS UM período estiverem marcados
        3. OK desabilitado se houver tipo de comunicação marcado MAS nenhum período
        """
        # Verifica tipos de comunicação marcados
        has_comm_type = any([
            self.chk_gsm.isChecked(),
            self.chk_lorawan.isChecked(),
            self.chk_p2p.isChecked()
        ])

        # Verifica períodos marcados
        has_period = any([
            self.chk_hoje.isChecked(),
            self.chk_1_7.isChecked(),
            self.chk_8_15.isChecked(),
            self.chk_16_plus.isChecked()
        ])

        # ✅ Lógica de habilitação:
        # - Se não tem tipo de comunicação → OK (gera apenas abas fixas)
        # - Se tem tipo de comunicação E tem período → OK
        # - Se tem tipo de comunicação MAS não tem período → BLOQUEADO

        if not has_comm_type:
            # Caso 1: Nenhum tipo de comunicação → OK habilitado
            self.btn_ok.setEnabled(True)
            self.btn_ok.setToolTip("Gerar relatório apenas com abas fixas")
        elif has_comm_type and has_period:
            # Caso 2: Tipo de comunicação E período → OK habilitado
            self.btn_ok.setEnabled(True)
            self.btn_ok.setToolTip("Gerar relatório com tipos e períodos selecionados")
        else:
            # Caso 3: Tipo de comunicação SEM período → OK desabilitado
            self.btn_ok.setEnabled(False)
            self.btn_ok.setToolTip("⚠️ Selecione pelo menos um período para os tipos de comunicação marcados")

    # =========================================================================
    # MÉTODOS DE SELEÇÃO RÁPIDA
    # =========================================================================

    def _select_all(self):
        """Marca todos os checkboxes (tipos de comunicação e períodos)."""
        # Marca tipos de comunicação primeiro
        for chk in [self.chk_gsm, self.chk_lorawan, self.chk_p2p]:
            chk.setChecked(True)

        # Marca períodos (agora habilitados)
        for chk in [self.chk_hoje, self.chk_1_7, self.chk_8_15, self.chk_16_plus]:
            chk.setChecked(True)

    def _deselect_all(self):
        """Desmarca todos os checkboxes (tipos de comunicação e períodos)."""
        # Desmarca períodos primeiro
        for chk in [self.chk_hoje, self.chk_1_7, self.chk_8_15, self.chk_16_plus]:
            chk.setChecked(False)

        # Desmarca tipos de comunicação (desabilita períodos automaticamente)
        for chk in [self.chk_gsm, self.chk_lorawan, self.chk_p2p]:
            chk.setChecked(False)

    def _select_all_periods(self):
        """Marca todos os períodos (só funciona se houver tipo de comunicação selecionado)."""
        has_comm_type = any([
            self.chk_gsm.isChecked(),
            self.chk_lorawan.isChecked(),
            self.chk_p2p.isChecked()
        ])

        if has_comm_type:
            for chk in [self.chk_hoje, self.chk_1_7, self.chk_8_15, self.chk_16_plus]:
                chk.setChecked(True)

    # =========================================================================
    # MÉTODOS DE OBTENÇÃO DE SELEÇÕES
    # =========================================================================

    def get_selected_comm_types(self):
        """
        Retorna lista de tipos de comunicação selecionados.

        Returns:
            list: Nomes dos tipos (ex: ["GSM", "LoRaWAN", "P2P"])
        """
        comm_types = []

        if self.chk_gsm.isChecked():
            comm_types.append("GSM")
        if self.chk_lorawan.isChecked():
            comm_types.append("LoRaWAN")
        if self.chk_p2p.isChecked():
            comm_types.append("P2P")

        return comm_types

    def get_selected_periods(self):
        """
        Retorna lista de períodos selecionados.

        Returns:
            list: Nomes dos períodos (ex: ["Hoje", "1-7", "8-15", "+16"])
        """
        periods = []

        if self.chk_hoje.isChecked():
            periods.append("Hoje")
        if self.chk_1_7.isChecked():
            periods.append("1-7")
        if self.chk_8_15.isChecked():
            periods.append("8-15")
        if self.chk_16_plus.isChecked():
            periods.append("+16")

        return periods

    def get_selections(self):
        """
        Retorna dicionário completo com todas as seleções.

        Returns:
            dict: {
                "comm_types": ["GSM", "LoRaWAN", "P2P"],
                "periods": ["Hoje", "1-7", "8-15", "+16"]
            }
        """
        return {
            "comm_types": self.get_selected_comm_types(),
            "periods": self.get_selected_periods()
        }

    # =========================================================================
    # MÉTODO ESTÁTICO PARA USO SIMPLIFICADO
    # =========================================================================

    @staticmethod
    def get_sheet_config(app_state, parent=None):
        """
        Método estático para uso simplificado.

        Args:
            app_state: Instância do AppState (obrigatório)
            parent: Widget pai (opcional)

        Returns:
            tuple: (config_dict, accepted_bool)

        Exemplo:
            config, accepted = SheetSelectionDialog.get_sheet_config(self.app_state, self)
            if accepted:
                comm_types = config["comm_types"]
                periods = config["periods"]
        """
        dialog = SheetSelectionDialog(app_state, parent)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            # Lê a configuração recém-salva do app_state
            config = app_state.get("sheet_config", {})
            return config, True
        else:
            return {"comm_types": [], "periods": []}, False



    """Executado quando o usuário clica em "OK"."""
    # Coleta tipos de comunicação selecionados
    def accept(self):

        selected_comm = []
        if self.chk_gsm.isChecked():
            selected_comm.append("GSM")
        if self.chk_lorawan.isChecked():
            selected_comm.append("LoRaWAN")
        if self.chk_p2p.isChecked():
            selected_comm.append("P2P")

        # Coleta períodos selecionados
        selected_periods = []
        if self.chk_hoje.isChecked():
            selected_periods.append("Hoje")
        if self.chk_1_7.isChecked():
            selected_periods.append("1-7")
        if self.chk_8_15.isChecked():
            selected_periods.append("8-15")
        if self.chk_16_plus.isChecked():
            selected_periods.append("+16")

        # ✅ SALVA DIRETAMENTE NO APP_STATE
        self.app_state.set("sheet_config", {
            "comm_types": selected_comm,
            "periods": selected_periods
        })

        #adicionar_log(f"✅ Config salva: Tipos={selected_comm}, Períodos={selected_periods}")

        super().accept()





# =========================================================================
# 🟦 EventsSheetSelectionDialog (EXCLUSIVO DA ABA DE EVENTOS)
# =========================================================================

class EventsSheetSelectionDialog(QDialog):
    """
    Diálogo para selecionar quais abas gerar no relatório de eventos.
    - Resumo_Eventos: obrigatório
    - Seriais_sem_evento: opcional
    - Tipos de eventos: dinâmicos (baseados nos filtros usados)
    """

    def __init__(self, app_state, event_types, parent=None):
        super().__init__(parent)

        self.app_state = app_state
        self.event_types = sorted(event_types)

        self.setWindowTitle("📊 Selecionar Abas do Relatório de Eventos")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMinimumHeight(500)

        self._build_ui()
        self._update_ok_button()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Escolha as abas que deseja gerar no relatório:")
        title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(title)

        # Grupo principal
        self.group = QGroupBox("📑 Abas Disponíveis")
        self.group_layout = QVBoxLayout(self.group)

        # Aba obrigatória
        self.chk_resumo = QCheckBox("✅ Resumo_Eventos (obrigatória)")
        self.chk_resumo.setChecked(True)
        self.chk_resumo.setEnabled(False)
        self.group_layout.addWidget(self.chk_resumo)

        # Aba seriais sem evento
        self.chk_sem_evento = QCheckBox("📋 Seriais_sem_evento")
        self.chk_sem_evento.setChecked(True)
        self.group_layout.addWidget(self.chk_sem_evento)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.group_layout.addWidget(separator)

        # --- Área de Scroll para Tipos de Eventos Dinâmicos ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.event_types_layout = QVBoxLayout(scroll_content) # Layout para os checkboxes de eventos
        self.event_types_layout.setContentsMargins(0, 0, 0, 0) # Remover margens extras
        self.event_types_layout.setSpacing(5) # Espaçamento entre os checkboxes

        self.event_type_checks = {}
        if self.event_types:
            label = QLabel("📌 Tipos de Eventos:")
            label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.event_types_layout.addWidget(label)

            for et in self.event_types:
                chk = QCheckBox(f"📊 {et}")
                chk.setChecked(True)
                self.event_type_checks[et] = chk
                self.event_types_layout.addWidget(chk)
        else:
            label_info = QLabel("ℹ️ Nenhum tipo de evento foi filtrado.")
            label_info.setStyleSheet("color: #666; font-style: italic;")
            self.event_types_layout.addWidget(label_info)

        self.event_types_layout.addStretch() # Empurra os checkboxes para cima
        scroll_area.setWidget(scroll_content)
        self.group_layout.addWidget(scroll_area) # Adiciona a área de scroll ao grupo principal

        self.group_layout.addStretch()
        layout.addWidget(self.group)


        # Botões de ação rápida
        btns = QHBoxLayout()
        bt_all = QPushButton("Marcar Todos")
        bt_all.clicked.connect(self._select_all)

        bt_none = QPushButton("Desmarcar Todos")
        bt_none.clicked.connect(self._deselect_all)

        btns.addWidget(bt_all)
        btns.addWidget(bt_none)
        btns.addStretch()
        layout.addLayout(btns)

        # Ok/Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.btn_ok = self.button_box.button(QDialogButtonBox.Ok)

    # ------------------------------
    # LÓGICA DE SELEÇÃO
    # ------------------------------

    def _select_all(self):
        self.chk_sem_evento.setChecked(True)
        for chk in self.event_type_checks.values():
            chk.setChecked(True)

    def _deselect_all(self):
        self.chk_sem_evento.setChecked(False)
        for chk in self.event_type_checks.values():
            chk.setChecked(False)

    def _update_ok_button(self):
        # Sempre habilitado (Resumo_Eventos é obrigatório)
        self.btn_ok.setEnabled(True)

    # ------------------------------
    # LEITURA DAS SELEÇÕES
    # ------------------------------

    def get_sheet_config(self):
        sheets = ["Resumo_Eventos"]

        if self.chk_sem_evento.isChecked():
            sheets.append("Seriais_sem_evento")

        for evt, chk in self.event_type_checks.items():
            if chk.isChecked():
                sheets.append(evt)

        return {
            "sheets": sheets,
            "include_seriais_sem_evento": self.chk_sem_evento.isChecked(),
            "include_event_types": [
                evt for evt, chk in self.event_type_checks.items() if chk.isChecked()
            ]
        }

    @staticmethod
    def get_sheet_config_dialog(app_state, event_types, parent=None):
        dialog = EventsSheetSelectionDialog(app_state, event_types, parent)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            return dialog.get_sheet_config(), True

        return {
            "sheets": ["Resumo_Eventos"],
            "include_seriais_sem_evento": False,
            "include_event_types": []
        }, False

    def accept(self):
        config = self.get_sheet_config()
        self.app_state.set("events_sheet_config", config)
        super().accept()
