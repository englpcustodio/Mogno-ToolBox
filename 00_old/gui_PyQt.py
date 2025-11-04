# gui_qt.py (com ajustes de centralização)
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QRadioButton, QProgressBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QFrame, QGroupBox, QTextEdit, QFileDialog, QMessageBox,
    QSpinBox, QSizePolicy, QStackedWidget 
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette
from logs import configurar_componente_logs_qt, limpar_logs
from utils import get_resource_path

class MognoMainWindow(QMainWindow):
    def __init__(self, signal_manager):
        super().__init__()
        
        self.signal_manager = signal_manager
        
        # Configurar a janela principal
        self.setWindowTitle("Mogno API Client Application - CEABS v1.2")
        self.setFixedSize(800, 700)
        
        # Criar o widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Criar o notebook (abas)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Criar as abas
        self.aba_login = QWidget()
        self.aba_requisicoes = QWidget()
        self.aba_logs = QWidget()
        self.aba_sobre = QWidget()
        
        # Inicialmente, apenas a aba de login é visível
        self.tab_widget.addTab(self.aba_login, "Login Mogno")
        
        # Configurar cada aba
        self.setup_aba_login()
        self.setup_aba_requisicoes()
        self.setup_aba_logs()
        self.setup_aba_sobre()
        
        # Inicializar estado da interface
        self.update_interface_serial()
    
    def show_tabs_after_login(self):
        """Exibe as outras abas após o login bem-sucedido"""
        # Remover todas as abas
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
            
        # Adicionar todas as abas na ordem correta
        self.tab_widget.addTab(self.aba_login, "Login Mogno")
        self.tab_widget.addTab(self.aba_requisicoes, "Requisitar Últimas Posições")
        self.tab_widget.addTab(self.aba_logs, "Logs")
        self.tab_widget.addTab(self.aba_sobre, "Sobre")
        
        # Habilitar o botão de requisições
        self.btn_iniciar.setEnabled(True)
        
        # Mudar para a aba de requisições
        self.tab_widget.setCurrentIndex(1)
    
    def setup_aba_login(self):
        """Configura os widgets da aba de login com centralização"""
        # Usamos VBoxLayout para centralizar verticalmente
        main_layout = QVBoxLayout(self.aba_login)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Container central para os elementos
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout = QGridLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        
        # Título e instrução (centralizado)
        lbl_instrucao = QLabel(
            "Para iniciar, insira seu login e senha do servidor Mogno-CEABS [VPN ligada/Cabo de rede]:"
        )
        lbl_instrucao.setFont(QFont("Segoe UI", 10))
        lbl_instrucao.setStyleSheet("font-style: italic;")
        lbl_instrucao.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_instrucao, 0, 0, 1, 2, Qt.AlignCenter)
        
        # Logo CEABS (centralizado)
        try:
            caminho_logo = get_resource_path("logo_CEABS.png")
            pixmap = QPixmap(caminho_logo).scaled(360, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo = QLabel()
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_logo, 1, 0, 1, 2, Qt.AlignCenter)
        except Exception as e:
            layout.addWidget(QLabel("[Logo CEABS não encontrada]"), 1, 0, 1, 2, Qt.AlignCenter)
        
        # Form layout para campos de entrada (para melhor alinhamento)
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignCenter)
        form_layout.setContentsMargins(20, 10, 20, 10)
        
        # Login
        self.entry_login = QLineEdit()
        self.entry_login.setFixedWidth(250)
        form_layout.addRow("Usuário:", self.entry_login)
        
        # Senha
        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.Password)
        self.entry_senha.setFixedWidth(250)
        form_layout.addRow("Senha:", self.entry_senha)
        
        layout.addWidget(form_container, 2, 0, 1, 2, Qt.AlignCenter)
        
        # Opções (centralizado)
        options_container = QWidget()
        options_layout = QVBoxLayout(options_container)
        options_layout.setAlignment(Qt.AlignCenter)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # Mostrar senha
        self.chk_show_password = QCheckBox("Mostrar senha")
        self.chk_show_password.setStyleSheet("margin-left: 50px;")
        options_layout.addWidget(self.chk_show_password)
        self.chk_show_password.toggled.connect(self.toggle_senha)
        
        # Manter navegador aberto
        self.chk_manter_navegador = QCheckBox("Manter janela do navegador aberta após login")
        self.chk_manter_navegador.setStyleSheet("margin-left: 50px;")
        options_layout.addWidget(self.chk_manter_navegador)
        
        # Login automático
        self.chk_login_automatico = QCheckBox("Login automático")
        self.chk_login_automatico.setStyleSheet("margin-left: 50px;")
        self.chk_login_automatico.setChecked(True)
        options_layout.addWidget(self.chk_login_automatico)
        
        layout.addWidget(options_container, 3, 0, 1, 2, Qt.AlignCenter)
        
        # Botão login (centralizado)
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 10)
        button_layout.setAlignment(Qt.AlignCenter)
        
        self.btn_login = QPushButton("Realizar Login")
        self.btn_login.setFixedWidth(180)
        button_layout.addWidget(self.btn_login)
        
        layout.addWidget(button_container, 4, 0, 1, 2, Qt.AlignCenter)
        
        # Status token (centralizado)
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
        
        # Adicionar container principal ao layout da aba
        main_layout.addWidget(container)
        
        # Espaçador flexível para manter a centralização vertical
        main_layout.addStretch(1)
    
    def setup_aba_requisicoes(self):
        """Configura os widgets da aba de requisições com centralização"""
        # Layout principal centralizado
        main_layout = QVBoxLayout(self.aba_requisicoes)
        main_layout.setAlignment(Qt.AlignCenter)

        # Container centralizado
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout = QGridLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(10)

        # ======== Tipo de Equipamento ========
        # Label para Tipo de Equipamento
        lbl_tipo = QLabel("Tipo de Equipamento:")
        lbl_tipo.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_tipo, 0, 0, Qt.AlignLeft)

        # RadioButtons para Tipo de Equipamento
        radio_container_tipo = QWidget()
        radio_layout_tipo = QHBoxLayout(radio_container_tipo)
        radio_layout_tipo.setContentsMargins(0, 0, 0, 0)
        radio_layout_tipo.setSpacing(20)

        self.radio_rastreadores = QRadioButton("Rastreadores")
        self.radio_rastreadores.setChecked(True)
        radio_layout_tipo.addWidget(self.radio_rastreadores)

        self.radio_iscas = QRadioButton("Iscas")
        radio_layout_tipo.addWidget(self.radio_iscas)

        radio_layout_tipo.addStretch(1)  # Espaçador para alinhar à esquerda
        layout.addWidget(radio_container_tipo, 0, 1, 1, 2, Qt.AlignLeft)

        # ======== Modo de Entrada dos Seriais ========
        # Label para Modo de Entrada
        lbl_modo = QLabel("Modo de Entrada dos Seriais:")
        lbl_modo.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_modo, 1, 0, Qt.AlignLeft)

        # RadioButtons para Modo de Entrada
        radio_container_modo = QWidget()
        radio_layout_modo = QHBoxLayout(radio_container_modo)
        radio_layout_modo.setContentsMargins(0, 0, 0, 0)
        radio_layout_modo.setSpacing(26) # Ajustado manualmente para ficar visualmente melhor

        self.radio_csv = QRadioButton("Arquivo CSV")
        self.radio_csv.setChecked(True)
        radio_layout_modo.addWidget(self.radio_csv)

        self.radio_manual = QRadioButton("Inserir Manualmente")
        radio_layout_modo.addWidget(self.radio_manual)

        radio_layout_modo.addStretch(1)  # Espaçador para alinhar à esquerda
        layout.addWidget(radio_container_modo, 1, 1, 1, 2, Qt.AlignLeft)

        # Conexão para alternar entre os modos
        self.radio_csv.toggled.connect(self.update_interface_serial)
        self.radio_manual.toggled.connect(self.update_interface_serial)

        # Linha horizontal para separar as seções
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setFrameShadow(QFrame.Sunken)
        linha.setStyleSheet("background-color: #CCCCCC;")
        layout.addWidget(linha, 2, 0, 1, 3)

        # ======== Container para Entrada de Dados (CSV ou Manual) ========
        self.entrada_container = QStackedWidget()

        # ======== Campo CSV ========
        self.csv_container = QWidget()
        csv_layout = QHBoxLayout(self.csv_container)
        csv_layout.setContentsMargins(0, 10, 0, 0)  # Espaço acima para separar da linha
        csv_layout.setSpacing(10)

        self.lbl_csv = QLabel("Nome do Arquivo .CSV:")
        self.lbl_csv.setFixedWidth(180)
        self.lbl_csv.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        csv_layout.addWidget(self.lbl_csv)

        self.entry_csv_nome = QLineEdit()
        self.entry_csv_nome.setReadOnly(True)
        self.entry_csv_nome.setFixedWidth(250)
        csv_layout.addWidget(self.entry_csv_nome)

        self.btn_csv = QPushButton("Selecionar Arquivo")
        self.btn_csv.setFixedWidth(140)
        csv_layout.addWidget(self.btn_csv)

        csv_layout.addStretch(1)  # Espaçador para alinhar à esquerda

        # ======== Campo Manual ========
        self.manual_container = QWidget()
        manual_layout = QHBoxLayout(self.manual_container)
        manual_layout.setContentsMargins(0, 10, 0, 0)  # Espaço acima para separar da linha
        manual_layout.setSpacing(10)

        self.lbl_manual = QLabel("Inserir seriais (separados por ;):")
        self.lbl_manual.setFixedWidth(180)
        self.lbl_manual.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        manual_layout.addWidget(self.lbl_manual)

        self.entry_serial_manual = QLineEdit()
        self.entry_serial_manual.setFixedWidth(250)
        manual_layout.addWidget(self.entry_serial_manual)

        self.lbl_contagem_seriais = QLabel("📦 Seriais inseridos: 0")
        self.lbl_contagem_seriais.setStyleSheet("color: blue;")
        self.lbl_contagem_seriais.setFixedWidth(140)
        manual_layout.addWidget(self.lbl_contagem_seriais)

        manual_layout.addStretch(1)  # Espaçador para alinhar à esquerda

        # Configurar evento de atualização da contagem
        self.entry_serial_manual.textChanged.connect(self.update_contagem_seriais)

        # Adicionar os containers ao QStackedWidget
        self.entrada_container.addWidget(self.csv_container)
        self.entrada_container.addWidget(self.manual_container)

        # Adicionar o QStackedWidget ao layout principal
        layout.addWidget(self.entrada_container, 3, 0, 1, 3)

        # Configurar evento de atualização da contagem
        self.entry_serial_manual.textChanged.connect(self.update_contagem_seriais)

        # Botão configurações avançadas (centralizado)        
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 10)
        btn_layout.setAlignment(Qt.AlignCenter)
        self.btn_avancadas = QPushButton("Mostrar Configurações Avançadas")
        self.btn_avancadas.setFixedWidth(300)
        btn_layout.addWidget(self.btn_avancadas)
        layout.addWidget(btn_container, 4, 0, 1, 3, Qt.AlignCenter)
        self.btn_avancadas.clicked.connect(self.toggle_avancadas)

        # Frame configurações avançadas (centralizado)
        self.frame_avancadas = QFrame()
        self.frame_avancadas.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        avancadas_layout = QVBoxLayout(self.frame_avancadas)
        avancadas_layout.setAlignment(Qt.AlignCenter)
        
        # Grupo de configurações avançadas
        avancadas_form = QWidget()
        form_layout = QFormLayout(avancadas_form)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        form_layout.setContentsMargins(10, 5, 10, 5)
        
        # Modo de Requisição
        modo_group = QWidget()
        modo_hbox = QHBoxLayout(modo_group)
        modo_hbox.setContentsMargins(0, 0, 0, 0)
        
        self.radio_sequencial = QRadioButton("Sequencial")
        self.radio_paralelo = QRadioButton("Paralelo")
        self.radio_paralelo.setChecked(True)
        
        modo_hbox.addWidget(self.radio_sequencial)
        modo_hbox.addWidget(self.radio_paralelo)
        
        form_layout.addRow("Modo de Requisição:", modo_group)
        
        # Quantidade de seriais por lote
        self.entry_step = QLineEdit("20")
        self.entry_step.setFixedWidth(70)
        form_layout.addRow("Quantidade de seriais por lote:", self.entry_step)
        
        # Max Workers
        self.entry_max_workers = QLineEdit("4")
        self.entry_max_workers.setFixedWidth(70)
        form_layout.addRow("Max Workers (Modo Paralelo):", self.entry_max_workers)
        
        # Step de ajuste
        self.entry_ajuste_step = QLineEdit("10")
        self.entry_ajuste_step.setFixedWidth(70)
        form_layout.addRow("Step de ajuste (diminuição):", self.entry_ajuste_step)
        
        # Tentativas timeout
        self.entry_tentativas_timeout = QLineEdit("3")
        self.entry_tentativas_timeout.setFixedWidth(70)
        form_layout.addRow("Tentativas em Timeout:", self.entry_tentativas_timeout)
        
        avancadas_layout.addWidget(avancadas_form)
        
        layout.addWidget(self.frame_avancadas, 5, 0, 1, 3)
        self.frame_avancadas.hide()  # Inicialmente oculto
        
        # Opções de relatório personalizado (centralizado)
        relatorio_container = QWidget()
        relatorio_layout = QVBoxLayout(relatorio_container)
        relatorio_layout.setAlignment(Qt.AlignCenter)
        relatorio_layout.setContentsMargins(0, 10, 0, 0)
        
        self.chk_gerar_relatorio = QCheckBox("Gerar relatório personalizado")
        self.chk_gerar_relatorio.setStyleSheet("font-weight: bold;")
        relatorio_layout.addWidget(self.chk_gerar_relatorio, Qt.AlignCenter)
        
        layout.addWidget(relatorio_container, 6, 0, 1, 3, Qt.AlignCenter)
        
        # Frame de opções de relatório (centralizado)
        self.frame_relatorio = QFrame()
        self.frame_relatorio.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        relatorio_options_layout = QVBoxLayout(self.frame_relatorio)
        relatorio_options_layout.setAlignment(Qt.AlignCenter)
        relatorio_options_layout.setSpacing(8)
        relatorio_options_layout.setContentsMargins(15, 10, 15, 10)
        
        # Adicionar checkboxes em duas colunas para economizar espaço
        options_grid = QGridLayout()
        options_grid.setAlignment(Qt.AlignCenter)
        options_grid.setHorizontalSpacing(20)
        options_grid.setVerticalSpacing(8)
        
        self.chk_incluir_proto = QCheckBox("Informações de proto em colunas")
        self.chk_abas_hw = QCheckBox("Criar aba separada por modelo de equipamento")
        self.chk_periodo_hoje = QCheckBox("Aba: posição hoje (data mais recente)")
        self.chk_periodo_0_7 = QCheckBox("Aba: posição entre hoje até 7 dias")
        self.chk_periodo_7_15 = QCheckBox("Aba: posição entre 7 dias até 15 dias")
        self.chk_periodo_15_30 = QCheckBox("Aba: posição entre 15 até 30 dias")
        self.chk_periodo_30_cima = QCheckBox("Aba: posição há mais de 30 dias")
        self.chk_gerar_mapa = QCheckBox("Gerar mapa de posições")
        
        # Primeira coluna
        options_grid.addWidget(self.chk_incluir_proto, 0, 0)
        options_grid.addWidget(self.chk_abas_hw, 1, 0)
        options_grid.addWidget(self.chk_periodo_hoje, 2, 0)
        options_grid.addWidget(self.chk_periodo_7_15, 3, 0)
        
        # Segunda coluna
        options_grid.addWidget(self.chk_gerar_mapa, 0, 1)
        options_grid.addWidget(self.chk_periodo_0_7, 1, 1)
        options_grid.addWidget(self.chk_periodo_15_30, 2, 1)
        options_grid.addWidget(self.chk_periodo_30_cima, 3, 1)
        
        relatorio_options_layout.addLayout(options_grid)
        
        layout.addWidget(self.frame_relatorio, 7, 0, 1, 3)
        self.frame_relatorio.hide()  # Inicialmente oculto
        
        self.chk_gerar_relatorio.toggled.connect(
            lambda checked: self.frame_relatorio.show() if checked else self.frame_relatorio.hide()
        )
        
        # Botão iniciar requisições (centralizado)
        iniciar_container = QWidget()
        iniciar_layout = QHBoxLayout(iniciar_container)
        iniciar_layout.setAlignment(Qt.AlignCenter)
        iniciar_layout.setContentsMargins(0, 15, 0, 5)
        
        self.btn_iniciar = QPushButton("Iniciar Requisições")
        self.btn_iniciar.setFixedWidth(200)
        self.btn_iniciar.setStyleSheet("font-weight: bold;")
        self.btn_iniciar.setEnabled(False)  # Inicialmente desabilitado
        iniciar_layout.addWidget(self.btn_iniciar)
        
        layout.addWidget(iniciar_container, 8, 0, 1, 3, Qt.AlignCenter)
        
        # Timer (cronômetro) (centralizado)
        timer_container = QWidget()
        timer_layout = QHBoxLayout(timer_container)
        timer_layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_timer = QLabel("⏱️ Tempo decorrido: 00:00:00")
        self.lbl_timer.setStyleSheet("color: darkgreen; font-weight: bold;")
        timer_layout.addWidget(self.lbl_timer)
        
        layout.addWidget(timer_container, 9, 0, 1, 3, Qt.AlignCenter)
        
        # Barra de progresso (centralizada, mas ocupando toda a largura)
        progress_container = QWidget()
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(20, 5, 20, 10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFormat("%p%")
        
        # Estilo personalizado para a barra de progresso (cor verde)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                text-align: center;
                background-color: #F5F5F5;
                color: #333333;
                font-weight: bold;
                padding: 1px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2979FF, 
                    stop:0.5 #42A5F5, 
                    stop:1 #2979FF
                );
                border-radius: 10px;
            }
        """)       
                  
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container, 10, 0, 1, 3)
        
        # Adicionar container principal ao layout da aba
        main_layout.addWidget(container)
        
        # Adicionar espaço flexível no final para centralização vertical
        main_layout.addStretch(1)
    
    def setup_aba_logs(self):
        """Configura os widgets da aba de logs com centralização"""
        layout = QVBoxLayout(self.aba_logs)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Barra superior (centralizada)
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 5, 0, 5)
        
        self.chk_gerar_log = QCheckBox("Gerar arquivo de logs (.txt)")
        self.chk_gerar_log.setChecked(True)
        top_layout.addWidget(self.chk_gerar_log, 1)
        
        btn_limpar_logs = QPushButton("Limpar Logs")
        btn_limpar_logs.setFixedWidth(120)
        btn_limpar_logs.clicked.connect(self.limpar_logs)
        top_layout.addWidget(btn_limpar_logs, 0, Qt.AlignRight)
        
        layout.addWidget(top_bar)
        
        # Área de texto para logs (centralizada em relação à largura disponível)
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMinimumHeight(400)  # Altura mínima para melhor visualização
        layout.addWidget(self.progress_text)
        
        # Configurar o componente de logs
        configurar_componente_logs_qt(self.progress_text)
    
    def setup_aba_sobre(self):
        """Configura os widgets da aba sobre com centralização"""
        layout = QVBoxLayout(self.aba_sobre)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setAlignment(Qt.AlignCenter)
        
        # Container para informações (centralizado)
        info_container = QWidget()
        info_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        info_layout = QVBoxLayout(info_container)
        info_layout.setAlignment(Qt.AlignCenter)
        
        # Informações básicas (centralizadas)
        info_label = QLabel(
            "Mogno API Client Application - CEABS\n"
            "Data do 1º Lançamento: 13/07/2025\n"
            "Desenvolvedor: M.Eng. Luis P. Custodio\n"
            "Contatos: luis.custodio@ceabs.com.br | engenharia@ceabs.com.br\n\n"
            "Versão Atual: v1.2 - Liberada em: 11/08/2025"
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 11pt;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_container)
        
        # Release notes (centralizado)
        release_notes = QTextEdit()
        release_notes.setReadOnly(True)
        release_notes.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        try:
            with open(get_resource_path("Release_Notes.txt"), "r", encoding="utf-8") as f:
                conteudo = f.read()
        except Exception as e:
            conteudo = "Erro ao carregar informações do Sobre: " + str(e)
        
        release_notes.setText(conteudo)
        layout.addWidget(release_notes)
        
        # Logo (centralizado)
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)
        
        try:
            logo_path = get_resource_path("mogno100x100.png")
            pixmap = QPixmap(logo_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo = QLabel()
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(lbl_logo)
        except Exception:
            lbl_logo = QLabel("[Logo não encontrada]")
            lbl_logo.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(lbl_logo)
        
        layout.addWidget(logo_container)
    
    def toggle_senha(self, checked):
        """Alterna a visibilidade da senha"""
        self.entry_senha.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
    
    def toggle_avancadas(self):
        """Alterna a visibilidade das configurações avançadas"""
        if self.frame_avancadas.isVisible():
            self.frame_avancadas.hide()
            self.btn_avancadas.setText("Mostrar Configurações Avançadas")
        else:
            self.frame_avancadas.show()
            self.btn_avancadas.setText("Recolher Configurações Avançadas")
    
    def update_interface_serial(self):
        """Atualiza a interface baseada no modo de entrada de seriais"""
        if self.radio_csv.isChecked():
            # Modo CSV - mostrar primeiro widget no stack
            self.entrada_container.setCurrentIndex(0)
            # Atualizar o estado do botão iniciar baseado no arquivo CSV
            self.btn_iniciar.setEnabled(bool(self.entry_csv_nome.text()))
        else:
            # Modo Manual - mostrar segundo widget no stack
            self.entrada_container.setCurrentIndex(1)
            # Atualizar contagem e verificar se há seriais
            self.update_contagem_seriais()

    def update_contagem_seriais(self):
        """Atualiza a contagem de seriais inseridos manualmente"""
        texto = self.entry_serial_manual.text().strip()
        seriais = [s.strip() for s in texto.split(";") if s.strip()]
        qtd = len(seriais)

        if qtd > 0:
            self.lbl_contagem_seriais.setText(f"📦 Seriais inseridos: {qtd}")
            # Habilitar botão de iniciar se tiver seriais
            if self.radio_manual.isChecked():  # Verificar se estamos no modo manual
                self.btn_iniciar.setEnabled(True)
        else:
            self.lbl_contagem_seriais.setText("📦 Seriais inseridos: 0")
            # Desabilitar botão se não tiver seriais e estivermos no modo manual
            if self.radio_manual.isChecked():
                self.btn_iniciar.setEnabled(False)

    
    def configure_file_selection(self, ler_csv_func):
        """Configura a seleção de arquivo CSV"""
        def selecionar_arquivo():
            arquivo = QFileDialog.getOpenFileName(
                self, "Selecionar arquivo CSV", "", "Arquivos CSV (*.csv)"
            )[0]
            if arquivo:
                ler_csv_func(self, arquivo)
                # Habilitar o botão iniciar se estivermos no modo CSV
                if self.radio_csv.isChecked():
                    self.btn_iniciar.setEnabled(True)

        self.btn_csv.clicked.connect(selecionar_arquivo)

    
    def update_token_status(self, texto, cor):
        """Atualiza o status do token com texto e cor específicos"""
        self.lbl_token_status.setText(texto)
        self.lbl_token_status.setStyleSheet(f"color: {cor}; font-weight: bold;")
    
    def limpar_logs(self):
        """Limpa o conteúdo da área de logs"""
        self.progress_text.clear()
        limpar_logs()
    
    def get_tipo_api(self):
        """Retorna o tipo de API selecionado"""
        return "rastreadores" if self.radio_rastreadores.isChecked() else "iscas"
    
    def get_modo_entrada_serial(self):
        """Retorna o modo de entrada de seriais selecionado"""
        return "csv" if self.radio_csv.isChecked() else "manual"
    
    def get_modo_lote(self):
        """Retorna o modo de requisição selecionado"""
        return "sequencial" if self.radio_sequencial.isChecked() else "paralelo"
    
    def get_opcoes_relatorio(self):
        """Retorna as opções de relatório personalizado"""
        return {
            "usar": self.chk_gerar_relatorio.isChecked(),
            "incluir_proto_colunas": self.chk_incluir_proto.isChecked(),
            "abas_por_hw": self.chk_abas_hw.isChecked(),
            "periodo_hoje": self.chk_periodo_hoje.isChecked(),
            "periodo_0_7": self.chk_periodo_0_7.isChecked(),
            "periodo_7_15": self.chk_periodo_7_15.isChecked(),
            "periodo_15_30": self.chk_periodo_15_30.isChecked(),
            "periodo_30_cima": self.chk_periodo_30_cima.isChecked(),
            "gerar_mapa": self.chk_gerar_mapa.isChecked(),
            "gerar_log": self.chk_gerar_log.isChecked()
        }
