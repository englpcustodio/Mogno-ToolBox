import traceback
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from config.settings import LOGO_CEABS_PATH, BACKGROUND_IMAGE_PATH 
from utils.logger import adicionar_log

class LoginTab(QWidget):
    login_requested = pyqtSignal(str, str, bool)  # user, pass, keep_browser_open
    show_password_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configura os widgets da aba de login com fundo e centralização."""

        # === Label de background ===
        self.background_label = QLabel(self)
        pixmap_bg = QPixmap(BACKGROUND_IMAGE_PATH)
        if pixmap_bg.isNull():
            adicionar_log(f"⚠️ [DEBUG] Background não encontrado em: {BACKGROUND_IMAGE_PATH}")
        else:
            self.background_label.setPixmap(pixmap_bg)
            self.background_label.setScaledContents(True)
        self.background_label.lower()  # garante que fique atrás de todos os widgets

        # === Layout principal ===
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(40, 40, 40, 40)

        main_layout.addSpacerItem(QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Container central com todo o conteúdo
        container = QWidget()
        # Container levemente translúcido
        container.setStyleSheet("background: rgba(255, 255, 255, 0.7); border-radius: 12px;")
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(15)

        # === Logo CEABS ===
        try:
            pixmap = QPixmap(LOGO_CEABS_PATH)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(360, Qt.SmoothTransformation)
            lbl_logo = QLabel()
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(lbl_logo)
        except Exception as e:
            adicionar_log(f"⚠️ [DEBUG] Erro ao carregar logo: {e}")
            lbl_logo = QLabel("[Logo CEABS não encontrada]")
            lbl_logo.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(lbl_logo)

        # === Texto de instrução ===
        lbl_instrucao = QLabel("Para iniciar, insira seu login e senha do servidor Mogno-CEABS:")
        lbl_instrucao.setFont(QFont("Segoe UI", 10))
        lbl_instrucao.setStyleSheet("font-style: italic; color: #333;")
        lbl_instrucao.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(lbl_instrucao)

        # === Campos de Login ===
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignCenter)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)

        self.entry_login = QLineEdit()
        self.entry_login.setFixedWidth(250)
        self.entry_login.setPlaceholderText("Usuário")
        form_layout.addRow("Usuário:", self.entry_login)

        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.Password)
        self.entry_senha.setFixedWidth(250)
        self.entry_senha.setPlaceholderText("Senha")
        self.entry_senha.returnPressed.connect(self._emit_login_request)
        form_layout.addRow("Senha:", self.entry_senha)

        container_layout.addLayout(form_layout)

        # === Opções ===
        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignCenter)
        options_layout.setContentsMargins(0, 0, 0, 0)

        self.chk_show_password = QCheckBox("Mostrar senha")
        self.chk_show_password.toggled.connect(self.toggle_senha)
        options_layout.addWidget(self.chk_show_password)

        self.chk_manter_navegador = QCheckBox("Manter janela do navegador aberta após login")
        options_layout.addWidget(self.chk_manter_navegador)

        self.chk_login_automatico = QCheckBox("Login automático")
        self.chk_login_automatico.setChecked(True)
        options_layout.addWidget(self.chk_login_automatico)

        container_layout.addLayout(options_layout)

        # === Botão de Login ===
        self.btn_login = QPushButton("Realizar Login")
        self.btn_login.setFixedWidth(200)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover { background-color: #005EA6; }
            QPushButton:disabled { background-color: #999; }
        """)
        self.btn_login.clicked.connect(self._emit_login_request)
        container_layout.addWidget(self.btn_login, alignment=Qt.AlignCenter)

        # === Status do Token ===
        self.lbl_token_status = QLabel("Realize o login.")
        self.lbl_token_status.setStyleSheet("color: #0044cc; font-style: italic;")
        self.lbl_token_status.setWordWrap(True)
        self.lbl_token_status.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.lbl_token_status)

        # Ajusta a largura do container dinamicamente
        container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        # Adiciona o container centralizado
        main_layout.addWidget(container)
        main_layout.addSpacerItem(QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    # Ajusta o tamanho do background quando o widget for redimensionado
    def resizeEvent(self, event):
        self.background_label.setGeometry(self.rect())
        super().resizeEvent(event)

    # === Funções internas ===
    def toggle_senha(self, checked):
        self.entry_senha.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.show_password_toggled.emit(checked)

    def _emit_login_request(self):
        login = self.entry_login.text().strip()
        senha = self.entry_senha.text().strip()
        manter_aberto = self.chk_manter_navegador.isChecked()

        if not login or not senha:
            self.update_token_status("Por favor, preencha usuário e senha.", "red")
            return

        try:
            self.update_token_status("Realizando o login, por favor aguarde...", "orange")
            self.set_login_button_enabled(False)
            self.login_requested.emit(login, senha, manter_aberto)
        except Exception as e:
            adicionar_log(f"❌ [DEBUG] Erro ao emitir sinal login_requested: {e}")
            adicionar_log(traceback.format_exc())

    def update_token_status(self, text, color):
        try:
            self.lbl_token_status.setText(text)
            self.lbl_token_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        except Exception as e:
            adicionar_log(f"❌ [DEBUG] Erro em update_token_status: {e}")
            adicionar_log(traceback.format_exc())

    def set_login_button_enabled(self, enabled):
        self.btn_login.setEnabled(enabled)
        self.btn_login.setText("Realizar Login" if enabled else "⏳ Autenticando...")

    def registrar_login_sucesso(self):
        hora = datetime.now().strftime("%H:%M:%S")
        self.update_token_status(f"✅ Login realizado com sucesso às {hora}.", "green")

    def get_login_credentials(self):
        return self.entry_login.text().strip(), self.entry_senha.text().strip(), self.chk_manter_navegador.isChecked()

    def is_auto_login_checked(self):
        return self.chk_login_automatico.isChecked()
