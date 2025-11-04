# df_to_excel.py (correção para remover a coluna data_datetime)
import os
import re
import json
import datetime
import pandas as pd
from PyQt5.QtWidgets import QMessageBox
from logs import adicionar_log
from utils import flatten_json, formatar_tempo

OUTPUT_DIR = "output_files_mogno"

def preparar_dataframe(dados):
    df = pd.DataFrame(dados)
    # Corrigir o campo "logitude" que vem errado da API
    if "logitude" in df.columns:
        df.rename(columns={"logitude": "longitude"}, inplace=True)

    # Extrair versao_hardware
    if "proto" in df.columns:
        df = inserir_versao_hardware(df)
    # Tratar colunas de data/hora
    if "horario" in df.columns:
        df = tratar_colunas_datahora(df)
    return df

def inserir_versao_hardware(df):
    versoes_hw = []
    for item in df["proto"]:
        if pd.isna(item):
            versoes_hw.append(None)
        else:
            try:
                parsed = json.loads(item)
                versao = parsed.get("rastreador", {}).get("versao_hardware")
                versoes_hw.append(versao)
            except Exception:
                versoes_hw.append(None)
    idx_fix = df.columns.get_loc("fix") + 1 if "fix" in df.columns else len(df.columns)
    df.insert(idx_fix, "versao_hardware", versoes_hw)
    return df

def tratar_colunas_datahora(df):
    df["horario"] = pd.to_datetime(df["horario"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df.insert(3, "data", df["horario"].dt.strftime("%d/%m/%Y"))
    df.insert(4, "horario_formatado", df["horario"].dt.strftime("%H:%M:%S"))
    df.drop(columns=["horario"], inplace=True)
    df.rename(columns={"horario_formatado": "horario"}, inplace=True)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    df.sort_values(by="data", ascending=False, inplace=True)
    df["data"] = df["data"].dt.strftime("%d/%m/%Y")
    return df

def extrair_seriais_faltantes(dados, serials_list):
    seriais_ok = {item.get("serial") for item in dados if "serial" in item}
    faltantes = set(serials_list) - seriais_ok
    return list(faltantes)

def gerar_proto_colunas(df):
    registros = []
    for linha in df["proto"].dropna():
        try:
            d = json.loads(linha)
            registros.append(flatten_json(d))
        except Exception:
            continue
    if registros:
        return pd.DataFrame(registros)
    return None

def tratar_nome_abas_excel(nome):
    nome = str(nome).strip()
    nome = re.sub(r'[\\/*?:\[\]]', '_', nome)
    nome = re.sub(r'\s+', '_', nome)
    if not nome:
        nome = "versao_desconhecida"
    return nome[:31]

def criar_abas_por_hw(writer, df):
    for versao, grupo in df.groupby("versao_hardware"):
        nome_aba = str(versao) if pd.notna(versao) else "versao_NULA"
        nome_aba = tratar_nome_abas_excel(nome_aba)
        
        # Remover coluna data_datetime se existir
        if 'data_datetime' in grupo.columns:
            grupo = grupo.drop(columns=['data_datetime'])
            
        grupo.to_excel(writer, index=False, sheet_name=nome_aba)

def salvar_resultado_excel(
    dados,
    serials_list,
    opcoes_relatorio_personalizado=None,
    progress_text=None,
    tempo_inicio=None
):
    if not dados:
        QMessageBox.warning(None, "Aviso", "Nenhum dado retornado.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    nome = f"request_last_position_mogno_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(OUTPUT_DIR, nome)

    # --- OPÇÕES RELATÓRIO PERSONALIZADO ---
    usar_relatorio_personalizado = opcoes_relatorio_personalizado.get("usar") if opcoes_relatorio_personalizado else False
    incluir_proto_colunas = opcoes_relatorio_personalizado.get("incluir_proto_colunas", False) if usar_relatorio_personalizado else False
    abas_por_hw = opcoes_relatorio_personalizado.get("abas_por_hw", False) if usar_relatorio_personalizado else False
    periodo_hoje = opcoes_relatorio_personalizado.get("periodo_hoje", False) if usar_relatorio_personalizado else False
    periodo_0_7 = opcoes_relatorio_personalizado.get("periodo_0_7", False) if usar_relatorio_personalizado else False
    periodo_7_15 = opcoes_relatorio_personalizado.get("periodo_7_15", False) if usar_relatorio_personalizado else False
    periodo_15_30 = opcoes_relatorio_personalizado.get("periodo_15_30", False) if usar_relatorio_personalizado else False
    periodo_30_cima = opcoes_relatorio_personalizado.get("periodo_30_cima", False) if usar_relatorio_personalizado else False
    gerar_mapa = opcoes_relatorio_personalizado.get("gerar_mapa", False) if usar_relatorio_personalizado else False

    # Preparar DataFrame principal
    df = preparar_dataframe(dados)
    faltantes = extrair_seriais_faltantes(dados, serials_list)

    # --- PERIODIZAÇÃO ---
    periodos = []
    temp_data_datetime = None
    
    if any([periodo_hoje, periodo_0_7, periodo_7_15, periodo_15_30, periodo_30_cima]):
        # Criar coluna temporária para filtragem
        df['data_datetime'] = pd.to_datetime(df['data'], format="%d/%m/%Y", errors="coerce")
        temp_data_datetime = 'data_datetime'  # Marcar para remoção posterior
        
        hoje = pd.Timestamp.now().normalize()
        if periodo_hoje:
            periodos.append({
                "nome_aba": "hoje",
                "mask": (df['data_datetime'] == hoje)
            })
        if periodo_0_7:
            periodos.append({
                "nome_aba": "ate_7_dias",
                "mask": (df['data_datetime'] <= hoje) & (df['data_datetime'] >= hoje - pd.Timedelta(days=6))
            })
        if periodo_7_15:
            periodos.append({
                "nome_aba": "7_a_15_dias",
                "mask": (df['data_datetime'] < hoje - pd.Timedelta(days=6)) & (df['data_datetime'] >= hoje - pd.Timedelta(days=14))
            })
        if periodo_15_30:
            periodos.append({
                "nome_aba": "15_a_30_dias",
                "mask": (df['data_datetime'] < hoje - pd.Timedelta(days=14)) & (df['data_datetime'] >= hoje - pd.Timedelta(days=29))
            })
        if periodo_30_cima:
            periodos.append({
                "nome_aba": "acima_30_dias",
                "mask": (df['data_datetime'] < hoje - pd.Timedelta(days=29))
            })

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        # Remover a coluna temporária data_datetime do DataFrame principal antes de salvar
        if temp_data_datetime and temp_data_datetime in df.columns:
            df_principal = df.drop(columns=[temp_data_datetime])
        else:
            df_principal = df
            
        # Aba padrão com todos os dados
        df_principal.to_excel(writer, index=False, sheet_name="request_OK")
        
        # Seriais não encontrados
        pd.DataFrame({"Seriais não encontrados": faltantes}).to_excel(writer, index=False, sheet_name="no-position_serials")
        
        # Aba de proto-colunas personalizada
        if incluir_proto_colunas and "proto" in df.columns:
            df_proto_colunas = gerar_proto_colunas(df)
            if df_proto_colunas is not None:
                df_proto_colunas.to_excel(writer, index=False, sheet_name="proto-colunas")
        
        # Abas por versão de hardware personalizadas
        if abas_por_hw and "versao_hardware" in df.columns:
            # Garantir que df_hw não contenha a coluna data_datetime
            df_hw = df.drop(columns=[temp_data_datetime]) if temp_data_datetime and temp_data_datetime in df.columns else df
            criar_abas_por_hw(writer, df_hw)
        
        # Abas por período (caso algum filtro de período tenha sido marcado)
        for periodo in periodos:
            # Filtrar os dados conforme o período
            aba_df = df.loc[periodo['mask']]
            
            # Remover a coluna data_datetime antes de salvar
            if temp_data_datetime and temp_data_datetime in aba_df.columns:
                aba_df = aba_df.drop(columns=[temp_data_datetime])
                
            if not aba_df.empty:
                nome_aba = tratar_nome_abas_excel(periodo['nome_aba'])
                aba_df.to_excel(writer, index=False, sheet_name=nome_aba)

    adicionar_log(f"📄 Arquivo salvo em: {path}")

    # Opcional: salvar log textual também
    if progress_text is not None:
        log_path = path.replace(".xlsx", ".txt")
        try:
            # Obter texto do QTextEdit
            text_content = progress_text.toPlainText()
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            adicionar_log(f"📃 Log salvo em: {log_path}")
        except Exception as e:
            adicionar_log(f"Erro ao salvar arquivo de log: {e}")

    print("[DEBUG] Fim da execução do processo de requisitar última posição.")
    return path
