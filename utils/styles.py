# mogno_app/utils/styles.py

"""
Estilos CSS centralizados para a aplicação.
"""

# ========== ESTILOS DE GROUPBOX ==========
GROUPBOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        font-size: 11pt;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 15px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
"""

# ========== ESTILOS DE BOTÕES ==========
BUTTON_PRIMARY_STYLE = """
    QPushButton {
        font-weight: bold;
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 10pt;
    }
    QPushButton:hover:enabled {
        background-color: #45a049;
    }
    QPushButton:disabled {
        background-color: #cccccc;
        color: #666666;
    }
"""

BUTTON_SECONDARY_STYLE = """
    QPushButton {
        font-weight: bold;
        background-color: #2196F3;
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 10pt;
    }
    QPushButton:hover:enabled {
        background-color: #1976D2;
    }
    QPushButton:disabled {
        background-color: #cccccc;
        color: #666666;
    }
"""

BUTTON_WARNING_STYLE = """
    QPushButton {
        font-weight: bold;
        background-color: #FF9800;
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 10pt;
    }
    QPushButton:hover:enabled {
        background-color: #F57C00;
    }
    QPushButton:disabled {
        background-color: #cccccc;
        color: #666666;
    }
"""

BUTTON_DANGER_STYLE = """
    QPushButton {
        font-weight: bold;
        background-color: #F44336;
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 10pt;
    }
    QPushButton:hover:enabled {
        background-color: #D32F2F;
    }
    QPushButton:disabled {
        background-color: #cccccc;
        color: #666666;
    }
"""

# ========== ESTILOS DE PROGRESS BAR ==========
PROGRESS_BAR_STYLE = """
    QProgressBar {
        border: 2px solid #E0E0E0;
        border-radius: 10px;
        text-align: center;
        background-color: #F5F5F5;
        color: #333333;
        font-weight: bold;
        padding: 2px;
        height: 30px;
    }
    QProgressBar::chunk {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #4CAF50,
            stop:0.5 #8BC34A,
            stop:1 #4CAF50
        );
        border-radius: 8px;
    }
"""

# ========== ESTILOS DE TEXTEDIT (LOGS) ==========
LOGS_TEXTEDIT_STYLE = """
    QTextEdit {
        border: 1px solid #CCCCCC;
        border-radius: 5px;
        padding: 8px;
        background-color: #FAFAFA;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 9pt;
    }
"""

# ========== ESTILOS DE FRAME (COLUNAS) ==========
COLUMN_FRAME_STYLE = """
    QFrame {
        border: 1px solid #DDDDDD;
        border-radius: 5px;
        padding: 10px;
    }
"""

# ========== ESTILOS DE DATEEDIT (CALENDÁRIO MODERNO) ==========
DATEEDIT_MODERN_STYLE = """
    QDateEdit {
        border: 2px solid #2196F3;
        border-radius: 8px;
        padding: 10px 15px;
        background-color: white;
        font-size: 11pt;
        font-weight: bold;
        color: #333;
        min-height: 35px;
    }
    QDateEdit:hover {
        border: 2px solid #1976D2;
        background-color: #E3F2FD;
    }
    QDateEdit:focus {
        border: 2px solid #0D47A1;
        background-color: #BBDEFB;
    }
    QDateEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 35px;
        border-left: 1px solid #2196F3;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        background-color: #2196F3;
    }
    QDateEdit::down-arrow {
        image: url(none);
        width: 0px;
        height: 0px;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 10px solid white;
        margin-right: 10px;
    }
    QDateEdit::down-arrow:hover {
        border-top: 10px solid #FFEB3B;
    }
    QCalendarWidget QWidget {
        background-color: white;
        border: 1px solid #CCCCCC;
        border-radius: 10px;
    }
    QCalendarWidget QToolButton {
        color: white;
        background-color: #2196F3;
        border: none;
        border-radius: 5px;
        padding: 8px;
        font-weight: bold;
        font-size: 12pt;
    }
    QCalendarWidget QToolButton:hover {
        background-color: #1976D2;
    }
    QCalendarWidget QAbstractItemView:enabled {
        color: #333;
        background-color: white;
        selection-background-color: #2196F3;
        selection-color: white;
    }
    QCalendarWidget QAbstractItemView::item:selected {
        background-color: #2196F3;
        color: white;
        border-radius: 3px;
    }
    QCalendarWidget QAbstractItemView::item:hover {
        background-color: #E3F2FD;
        color: #1976D2;
        border-radius: 3px;
    }
"""
