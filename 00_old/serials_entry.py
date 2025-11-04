## serials_entry.py
#
#import os
#import pandas as pd
#from tkinter import filedialog, messagebox
#from logs import adicionar_log
#
## Estado global da lista de seriais e status do CSV
#serials_list = []
#csv_carregado = False
#
#
## Lê um arquivo CSV contendo seriais e atualiza a lista global e o nome do arquivo
#def ler_csv(var, btn_iniciar, login_realizado_cb, verificar_entrada_serial_cb):
#    """
#    - var: dicionário de widgets/variáveis, p.ex. var['entry_csv_nome']
#    - btn_iniciar: botão de iniciar (liberado se login já realizado)
#    - login_realizado_cb: função/flag que retorna True se login já feito
#    - verificar_entrada_serial_cb: função para atualizar a interface
#    """
#    global serials_list, csv_carregado
#    filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
#    nome_arquivo = os.path.basename(filepath)
#    if filepath:
#        try:
#            df = pd.read_csv(filepath, header=None)
#            serials = df.iloc[:, 0].dropna().astype(str).tolist()
#            serials_list = serials
#            adicionar_log(f"📄 Arquivo \"{nome_arquivo}\", carregado com {len(serials)} seriais.")
#            atualizar_nome_arquivo(var['entry_csv_nome'], os.path.basename(filepath))
#            csv_carregado = True
#            if login_realizado_cb():
#                btn_iniciar.config(state="normal")
#            verificar_entrada_serial_cb()
#        except Exception as e:
#            messagebox.showerror("Erro", f"Erro ao ler CSV: {str(e)}")
#
#def atualizar_nome_arquivo(entry_widget, nome_arquivo):
#    entry_widget.config(state="normal")
#    entry_widget.delete(0, "end")
#    entry_widget.insert(0, nome_arquivo)
#    entry_widget.config(state="disabled")
#
## Retorna a lista de seriais com base no modo de entrada selecionado
#def obter_seriais(modo_entrada, entry_serial_manual=None): # csv" ou "manual | campo Entry, necessário se for manual
#    if modo_entrada == "csv": 
#        return serials_list
#    elif modo_entrada == "manual" and entry_serial_manual:
#        texto = entry_serial_manual.get().strip()
#        seriais = [s.strip() for s in texto.split(";") if s.strip()]
#        return seriais
#    return []
#
## Retorna se um CSV já foi carregado
#def get_csv_status():
#    return csv_carregado
#
## Retorna a lista bruta de seriais carregados
#def get_serials():
#    return serials_list
#


# serials_entry.py (versão PyQt)
import os
import pandas as pd
from PyQt5.QtWidgets import QMessageBox
from logs import adicionar_log

# Estado global da lista de seriais e status do CSV
serials_list = []
csv_carregado = False

def ler_csv_qt(window, filepath):
    """
    Lê um arquivo CSV contendo seriais e atualiza a lista global
    
    Args:
        window: Instância da janela principal
        filepath: Caminho do arquivo CSV
    """
    global serials_list, csv_carregado
    
    if not filepath:
        return
        
    nome_arquivo = os.path.basename(filepath)
    
    try:
        df = pd.read_csv(filepath, header=None)
        serials = df.iloc[:, 0].dropna().astype(str).tolist()
        serials_list = serials
        adicionar_log(f"📄 Arquivo \"{nome_arquivo}\", carregado com {len(serials)} seriais.")
        
        # Atualizar a interface
        window.entry_csv_nome.setText(nome_arquivo)
        csv_carregado = True
        
        # Habilitar o botão iniciar se estivermos no modo CSV
        if window.radio_csv.isChecked():
            window.btn_iniciar.setEnabled(True)
        
    except Exception as e:
        QMessageBox.critical(window, "Erro", f"Erro ao ler CSV: {str(e)}")
        adicionar_log(f"Erro ao ler arquivo CSV: {e}")

def obter_seriais_qt(modo_entrada, entry_serial_manual=None):
    """
    Retorna a lista de seriais com base no modo de entrada selecionado
    
    Args:
        modo_entrada: "csv" ou "manual"
        entry_serial_manual: QLineEdit contendo os seriais, necessário se for manual
    
    Returns:
        Lista de seriais
    """
    if modo_entrada == "csv": 
        return serials_list
    elif modo_entrada == "manual" and entry_serial_manual:
        texto = entry_serial_manual.text().strip()
        seriais = [s.strip() for s in texto.split(";") if s.strip()]
        return seriais
    return []

def get_csv_status():
    """Retorna se um CSV já foi carregado"""
    return csv_carregado

def get_serials():
    """Retorna a lista bruta de seriais carregados"""
    return serials_list
