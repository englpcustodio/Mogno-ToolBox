# mogno_app/core/serial_management.py
import os
import pandas as pd
from utils.logger import adicionar_log

_serials_list = []
_arquivo_carregado = False

def ler_arquivo_serials(filepath):
    """
    Lê um arquivo .csv ou .xlsx contendo seriais, identifica a coluna relevante por palavras-chave,
    remove duplicados e atualiza a lista global.
    """
    global _serials_list, _arquivo_carregado
    if not filepath:
        adicionar_log("Nenhum arquivo selecionado.")
        return {'unicos': [], 'total_lidos': 0, 'duplicados': 0}

    nome_arquivo = os.path.basename(filepath)
    extensao = os.path.splitext(filepath)[1].lower()

    try:
        if extensao == ".csv":
            df = pd.read_csv(filepath)
        elif extensao == ".xlsx":
            df = pd.read_excel(filepath)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {extensao}")

        if df.empty:
            raise ValueError("Arquivo vazio ou sem dados válidos.")

        # Procura no cabeçalho por palavras-chaves para identificar qual pertence aos números de série para as consultas
        palavras_chave = ["seriais", "serial", "numero_serial", "serial_device", "serial_number", "rastreador_numero_serie"]
        coluna_serial = next((col for col in df.columns if any(kw in str(col).lower() for kw in palavras_chave)), df.columns[0])

        serials = df[coluna_serial].dropna().astype(str).str.strip().tolist()
        total_lidos = len(serials)
        serials_unicos = list(set(serials))
        duplicados = total_lidos - len(serials_unicos)

        _serials_list = serials_unicos
        _arquivo_carregado = True

        adicionar_log(f"📄 '{nome_arquivo}' carregado: {total_lidos} lidos, {duplicados} duplicados removidos.")
        return {'unicos': serials_unicos, 'total_lidos': total_lidos, 'duplicados': duplicados}

    except Exception as e:
        adicionar_log(f"❌ Erro ao ler '{nome_arquivo}': {e}")
        _serials_list = []
        _arquivo_carregado = False
        return {'unicos': [], 'total_lidos': 0, 'duplicados': 0}
