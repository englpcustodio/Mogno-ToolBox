# mogno_app/gui/login_tab.py
import traceback
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QFont
from config.settings import LOGO_CEABS_PATH # Importa o caminho da logo das configurações
from utils.logger import adicionar_log

class LoginTab(QWidget):
    # Sinais para comunicação com a janela principal ou outras partes da aplicação
    login_requested = pyqtSignal(str, str, bool) # user, pass, keep_browser_open
    show_password_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura os widgets da aba de login com centralização."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout = QGridLayout(container)
        layout.setAlignment(Qt.AlignCenter)

        lbl_instrucao = QLabel(
            "Para iniciar, insira seu login e senha do servidor Mogno-CEABS [VPN ligada/Cabo de rede]:"
        )
        lbl_instrucao.setFont(QFont("Segoe UI", 10))
        lbl_instrucao.setStyleSheet("font-style: italic;")
        lbl_instrucao.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_instrucao, 0, 0, 1, 2, Qt.AlignCenter)

        try:
            pixmap = QPixmap(LOGO_CEABS_PATH).scaled(360, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo = QLabel()
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_logo, 1, 0, 1, 2, Qt.AlignCenter)
        except Exception as e:
            adicionar_log(f"⚠️ [DEBUG] Erro ao carregar logo: {e}")
            layout.addWidget(QLabel("[Logo CEABS não encontrada]"), 1, 0, 1, 2, Qt.AlignCenter)

        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignCenter)
        form_layout.setContentsMargins(20, 10, 20, 10)

        self.entry_login = QLineEdit()
        self.entry_login.setFixedWidth(250)
        form_layout.addRow("Usuário:", self.entry_login)

        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.Password)
        self.entry_senha.setFixedWidth(250)
        # Permitir login ao pressionar Enter no campo de senha
        self.entry_senha.returnPressed.connect(self._emit_login_request)
        form_layout.addRow("Senha:", self.entry_senha)

        layout.addWidget(form_container, 2, 0, 1, 2, Qt.AlignCenter)

        options_container = QWidget()
        options_layout = QVBoxLayout(options_container)
        options_layout.setAlignment(Qt.AlignCenter)
        options_layout.setContentsMargins(0, 0, 0, 0)

        self.chk_show_password = QCheckBox("Mostrar senha")
        self.chk_show_password.setStyleSheet("margin-left: 50px;")
        options_layout.addWidget(self.chk_show_password)
        self.chk_show_password.toggled.connect(self.toggle_senha)

        self.chk_manter_navegador = QCheckBox("Manter janela do navegador aberta após login")
        self.chk_manter_navegador.setStyleSheet("margin-left: 50px;")
        options_layout.addWidget(self.chk_manter_navegador)

        self.chk_login_automatico = QCheckBox("Login automático")
        self.chk_login_automatico.setStyleSheet("margin-left: 50px;")
        self.chk_login_automatico.setChecked(True)
        options_layout.addWidget(self.chk_login_automatico)

        layout.addWidget(options_container, 3, 0, 1, 2, Qt.AlignCenter)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 10)
        button_layout.setAlignment(Qt.AlignCenter)

        self.btn_login = QPushButton("Realizar Login")
        self.btn_login.setFixedWidth(180)
        button_layout.addWidget(self.btn_login)

        # TESTE: Conectar com lambda para verificar se o botão funciona

        self.btn_login.clicked.connect(self._emit_login_request)


        layout.addWidget(button_container, 4, 0, 1, 2, Qt.AlignCenter)

        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setAlignment(Qt.AlignCenter)

        self.lbl_token_status = QLabel("Gerar token ao realizar Login.")
        self.lbl_token_status.setStyleSheet("color: blue; font-style: italic;")
        self.lbl_token_status.setWordWrap(True)
        self.lbl_token_status.setFixedWidth(350)
        self.lbl_token_status.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.lbl_token_status)

        layout.addWidget(status_container, 5, 0, 1, 2, Qt.AlignCenter)

        main_layout.addWidget(container)
        main_layout.addStretch(1)

        
    def toggle_senha(self, checked):
        """Alterna a visibilidade da senha e emite sinal."""
        self.entry_senha.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.show_password_toggled.emit(checked) # Emite sinal para a janela principal se necessário
        
    def _emit_login_request(self):
        """Emite o sinal de requisição de login com os dados dos campos."""      
        login = self.entry_login.text().strip()
        senha = self.entry_senha.text().strip()
        manter_aberto = self.chk_manter_navegador.isChecked()
        adicionar_log(f"🔍 [DEBUG] Login: {login}, Senha: {'*' * len(senha)}, Manter aberto: {manter_aberto}")
        
        try:
            self.login_requested.emit(login, senha, manter_aberto)

        except Exception as e:
            adicionar_log(f"❌ [DEBUG] Erro ao emitir sinal login_requested: {e}")
           
            adicionar_log(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
        
    def update_token_status(self, text, color):
        """Atualiza o status do token na UI."""      
        try:
            self.lbl_token_status.setText(text)
            self.lbl_token_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        except Exception as e:
            print(f"❌ [CONSOLE] Erro em update_token_status: {e}")
            print(traceback.format_exc())

        
    def set_login_button_enabled(self, enabled):
        """Habilita/desabilita o botão de login."""
        self.btn_login.setEnabled(enabled)
        if enabled:
            self.btn_login.setText("Realizar Login")
        else:
            self.btn_login.setText("⏳ Autenticando...")
        
    def get_login_credentials(self):
        """Retorna as credenciais de login e a opção de manter navegador."""
        return self.entry_login.text().strip(), self.entry_senha.text().strip(), self.chk_manter_navegador.isChecked()
        
    def is_auto_login_checked(self):
        """Retorna se o login automático está marcado."""
        return self.chk_login_automatico.isChecked()
