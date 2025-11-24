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
from core.credential_manager import CredentialManager # Importar o novo manager

class LoginTab(QWidget):
    login_requested = pyqtSignal(str, str, bool, bool, bool)  # user, pass, keep_browser_open, remember_user, remember_password
    show_password_toggled = pyqtSignal(bool)

    def __init__(self, signal_manager, app_state=None, parent=None):
        super().__init__(parent)
        self.signal_manager = signal_manager
        self.app_state = app_state
        self.first_load = True
        self.credential_manager = CredentialManager() # Instanciar o CredentialManager
        self.setup_ui()
        self._connect_internal_signals() # Conectar sinais internos e do SignalManager
        self._load_saved_credentials() # Carregar credenciais ao iniciar

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
        self.entry_login.setFixedWidth(180)
        self.entry_login.setPlaceholderText("Usuário")
        form_layout.addRow("Usuário:", self.entry_login)

        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.Password)
        self.entry_senha.setFixedWidth(180)
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

        self.chk_remember_user = QCheckBox("Lembrar usuário")
        self.chk_remember_user.setChecked(True) # Padrão para lembrar usuário
        options_layout.addWidget(self.chk_remember_user)

        self.chk_remember_password = QCheckBox("Lembrar senha")
        self.chk_remember_password.setChecked(False) # Padrão para NÃO lembrar senha
        options_layout.addWidget(self.chk_remember_password)

        self.chk_auto_login = QCheckBox("Login automático")
        self.chk_auto_login.setChecked(True) # Padrão para login automático
        options_layout.addWidget(self.chk_auto_login)

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
        # Login é iniciado ao clicar no botão, emitindo o sinal [self.login_requested.emit(login, senha, manter_aberto)]
        self.btn_login.clicked.connect(self._emit_login_request)
        container_layout.addWidget(self.btn_login, alignment=Qt.AlignCenter)

        # === Status do Token ===
        self.lbl_token_status = QLabel("Realize o login para acessar as funcionalidades.")
        self.lbl_token_status.setStyleSheet("color: #0044cc; font-style: italic;")
        self.lbl_token_status.setWordWrap(True)
        self.lbl_token_status.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.lbl_token_status)

        # Ajusta a largura do container dinamicamente
        container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        # Adiciona o container centralizado
        main_layout.addWidget(container)
        main_layout.addSpacerItem(QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _connect_internal_signals(self):
        """Conecta sinais internos e do SignalManager."""
        self.signal_manager.token_status_updated.connect(self.update_token_status)
        self.signal_manager.enable_start_button.connect(self.set_login_button_enabled)
        # Adicionar conexão para reauthentication_required para resetar a UI de login
        self.signal_manager.reauthentication_required.connect(self._handle_reauthentication_required)

        # Conectar chk_remember_user para desabilitar chk_remember_password se desmarcado
        self.chk_remember_user.toggled.connect(self._toggle_remember_password_checkbox)

    def _toggle_remember_password_checkbox(self, checked):
        """Desabilita/habilita o checkbox de lembrar senha com base no lembrar usuário."""
        self.chk_remember_password.setEnabled(checked)
        if not checked:
            self.chk_remember_password.setChecked(False) # Desmarcar se usuário não for lembrado

    def _load_saved_credentials(self):
        """Carrega credenciais salvas e preenche os campos."""
        username, password, remember_user, remember_password = self.credential_manager.load_credentials()

        if username:
            self.entry_login.setText(username)
            self.chk_remember_user.setChecked(remember_user)
            self.chk_remember_password.setChecked(remember_password)
            if password and remember_password:
                self.entry_senha.setText(password)

            adicionar_log("📂 Credenciais pré-preenchidas na tela de login.")
        else:
            # Primeira execução → mostrar mensagem azul normal
            self.lbl_token_status.setText("Realize o login para acessar as funcionalidades.")
            self.lbl_token_status.setStyleSheet("color: #0044cc; font-style: italic;")

            self.chk_remember_user.setChecked(False)
            self.chk_remember_password.setChecked(False)
            self.chk_remember_password.setEnabled(False)

        # Finaliza o carregamento inicial
        self.first_load = False


    # Ajusta o tamanho do background quando o widget for redimensionado
    def resizeEvent(self, event):
        self.background_label.setGeometry(self.rect())
        super().resizeEvent(event)

    # === Funções internas ===
    def toggle_senha(self, checked):
        self.entry_senha.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.show_password_toggled.emit(checked)

    # Função que é chamada para iniciar o login
    def _emit_login_request(self):
        login = self.entry_login.text().strip()
        senha = self.entry_senha.text().strip()
        manter_aberto = self.chk_manter_navegador.isChecked()
        remember_user = self.chk_remember_user.isChecked()
        remember_password = self.chk_remember_password.isChecked()

        if not login or not senha:
            self.update_token_status("Por favor, preencha usuário e senha.", "red")
            self.signal_manager.show_toast_error.emit("Por favor, preencha usuário e senha.")
            return

        try:
            self.update_token_status("Realizando o login, por favor aguarde...", "orange")
            self.set_login_button_enabled(False)
            # Emitir o sinal com as novas opções de salvamento
            self.login_requested.emit(login, senha, manter_aberto, remember_user, remember_password)
        except Exception as e:
            adicionar_log(f"❌ [DEBUG] Erro ao emitir sinal login_requested: {e}")
            adicionar_log(traceback.format_exc())
            self.update_token_status("Erro ao iniciar o login.", "red")
            self.set_login_button_enabled(True)
            self.signal_manager.show_toast_error.emit("Erro ao iniciar o login.")

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

    def _handle_reauthentication_required(self):
        """Reseta a UI de login quando a reautenticação é necessária."""
    
        # Se for primeira execução → NÃO mostrar erro de sessão expirada
        if self.first_load:
            adicionar_log("Ignorando reauthentication_required na primeira inicialização.")
            return
    
        self.update_token_status("Sessão expirada ou inválida. Por favor, faça login novamente.", "red")
        self.set_login_button_enabled(True)
    
        if not self.chk_remember_password.isChecked():
            self.entry_senha.clear()
    
        adicionar_log("UI de login resetada devido à necessidade de reautenticação.")


    # Métodos para obter o estado dos checkboxes (agora usados pelo AuthManager)
    def get_login_credentials(self):
        return self.entry_login.text().strip(), self.entry_senha.text().strip()

    def is_auto_login_checked(self):
        return self.chk_auto_login.isChecked()

    def get_remember_options(self):
        return self.chk_remember_user.isChecked(), self.chk_remember_password.isChecked()
