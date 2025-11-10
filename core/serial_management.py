# mogno_app/core/serial_management.py
import os
import pandas as pd
from utils.logger import adicionar_log

# Estado global (cache temporário dos seriais)
_serials_list = []
_arquivo_carregado = False
_origem_serials = None  # 'arquivo' ou 'manual'


def ler_arquivo_serials(filepath):
    """
    Lê um arquivo .csv ou .xlsx contendo seriais, identifica a coluna relevante,
    remove duplicados e atualiza a lista global.
    """
    global _serials_list, _arquivo_carregado, _origem_serials

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

        # Identifica a coluna com números de série
        palavras_chave = [
            "serial", "seriais", "numero_serial", "serial_device",
            "serial_number", "rastreador_numero_serie"
        ]
        coluna_serial = next(
            (col for col in df.columns if any(kw in str(col).lower() for kw in palavras_chave)),
            df.columns[0]
        )

        serials = df[coluna_serial].dropna().astype(str).str.strip().tolist()
        total_lidos = len(serials)
        serials_unicos = list(set(serials))
        duplicados = total_lidos - len(serials_unicos)

        _serials_list = serials_unicos
        _arquivo_carregado = True
        _origem_serials = "arquivo"

        adicionar_log(f"📄 '{nome_arquivo}' carregado: {total_lidos} lidos, {duplicados} duplicados removidos.")
        return {'unicos': serials_unicos, 'total_lidos': total_lidos, 'duplicados': duplicados}

    except Exception as e:
        adicionar_log(f"❌ Erro ao ler '{nome_arquivo}': {e}")
        _serials_list = []
        _arquivo_carregado = False
        _origem_serials = None
        return {'unicos': [], 'total_lidos': 0, 'duplicados': 0}


def carregar_seriais_manualmente(texto):
    """
    Processa uma string com seriais separados por ';' ou nova linha,
    remove duplicados e atualiza a lista global.
    """
    global _serials_list, _arquivo_carregado, _origem_serials

    if not texto:
        adicionar_log("⚠️ Nenhum serial manual inserido.")
        return {'unicos': [], 'total_lidos': 0, 'duplicados': 0}

    # Divide por ';' ou quebra de linha
    partes = [s.strip() for s in texto.replace("\n", ";").split(";") if s.strip()]
    total_lidos = len(partes)
    serials_unicos = list(set(partes))
    duplicados = total_lidos - len(serials_unicos)

    _serials_list = serials_unicos
    _arquivo_carregado = False
    _origem_serials = "manual"

    adicionar_log(f"✍️ Inserção manual: {total_lidos} lidos, {duplicados} duplicados removidos.")
    return {'unicos': serials_unicos, 'total_lidos': total_lidos, 'duplicados': duplicados}


def get_seriais():
    """Retorna a lista atual de seriais únicos."""
    return _serials_list.copy()


def limpar_seriais():
    """Limpa a lista de seriais carregada."""
    global _serials_list, _arquivo_carregado, _origem_serials
    _serials_list = []
    _arquivo_carregado = False
    _origem_serials = None
    adicionar_log("🧹 Lista de seriais limpa.")


def get_info_serials():
    """Retorna um resumo da situação atual dos seriais."""
    return {
        "quantidade": len(_serials_list),
        "origem": _origem_serials,
        "arquivo_carregado": _arquivo_carregado,
    }
