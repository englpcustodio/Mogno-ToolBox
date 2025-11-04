# mogno_app/core/report_generation.py

import os
import re
import json
import datetime
import pandas as pd
# from PyQt5.QtWidgets import QMessageBox # REMOVIDO: Lógica de GUI não deve estar aqui
from core.map_generation import gerar_mapa # Importa a função de geração de mapa
from utils.helpers import flatten_json, formatar_tempo
from utils.logger import adicionar_log # Importa o logger da nova localização
from config.settings import OUTPUT_DIR # Importa o diretório de saída das configurações

def preparar_dataframe(dados):
    """
    Prepara um DataFrame a partir dos dados brutos da API.
    Realiza renomeação de colunas, extração de versão de hardware e tratamento de datas.
    """
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


def extrair_coordenadas_do_excel(caminho_arquivo, aba="request_OK"):
    """
    Extrai as coordenadas válidas de um arquivo Excel para uso no mapa.
    Esta função é mantida aqui no main.py pois é uma ponte entre o resultado
    do Excel e a geração do mapa, e pode precisar de tratamento de erros na GUI.
    """
    try:
        df = pd.read_excel(caminho_arquivo, sheet_name=aba)
        if not {'latitude', 'longitude'}.issubset(df.columns):
            adicionar_log(f"⚠️ Colunas 'latitude' ou 'longitude' não encontradas na aba '{aba}'.")
            return []

        result = df[
            df['latitude'].notnull() & df['longitude'].notnull() &
            (df['latitude'] != 0) & (df['longitude'] != 0)
        ]
        return result.to_dict('records')
    except Exception as e:
        adicionar_log(f"Erro ao extrair coordenadas do Excel da aba '{aba}': {e}")
        return []


def inserir_versao_hardware(df):
    """
    Extrai a versão de hardware do campo 'proto' e insere como nova coluna.
    """
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
    """
    Converte a coluna 'horario' para datetime, extrai 'data' e 'horario_formatado',
    e remove a coluna original 'horario'.
    """
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
    """
    Compara a lista de seriais requisitados com os seriais retornados
    e identifica os que não tiveram posição.
    """
    seriais_ok = {item.get("serial") for item in dados if "serial" in item}
    faltantes = set(serials_list) - seriais_ok
    return list(faltantes)

def gerar_proto_colunas(df):
    """
    Achata o JSON da coluna 'proto' em novas colunas no DataFrame.
    """
    registros = []
    for linha in df["proto"].dropna():
        try:
            d = json.loads(linha)
            registros.append(flatten_json(d))
        except Exception as e:
            adicionar_log(f"Erro ao achatar JSON do proto: {e}")
            continue
    if registros:
        return pd.DataFrame(registros)
    return None

def tratar_nome_abas_excel(nome):
    """
    Limpa e formata o nome da aba do Excel para garantir compatibilidade.
    """
    nome = str(nome).strip()
    nome = re.sub(r'[\\/*?:\[\]]', '_', nome)
    nome = re.sub(r'\s+', '_', nome)
    if not nome:
        nome = "versao_desconhecida"
    return nome[:31] # Limita o nome da aba a 31 caracteres

def criar_abas_por_hw(writer, df):
    """
    Cria abas separadas no Excel para cada versão de hardware.
    """
    for versao, grupo in df.groupby("versao_hardware"):
        nome_aba = str(versao) if pd.notna(versao) else "versao_NULA"
        nome_aba = tratar_nome_abas_excel(nome_aba)

        # Remover coluna data_datetime se existir (garantir que não vá para o Excel)
        if 'data_datetime' in grupo.columns:
            grupo = grupo.drop(columns=['data_datetime'])

        grupo.to_excel(writer, index=False, sheet_name=nome_aba)

def salvar_resultado_excel(
    dados,
    serials_list,
    opcoes_relatorio_personalizado=None,
    log_content_to_save=None # Novo parâmetro para o conteúdo do log
):
    """
    Salva os dados processados em um arquivo Excel, aplicando opções de relatório.
    Retorna o caminho do arquivo salvo ou None em caso de erro.
    """
    if not dados:
        adicionar_log("Aviso: Nenhum dado retornado para salvar no Excel.")
        return None

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    nome = f"request_last_position_mogno_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(OUTPUT_DIR, nome)

    # --- OPÇÕES RELATÓRIO PERSONALIZADO ---
    usar_relatorio_personalizado = opcoes_relatorio_personalizado.get("usar", False)
    incluir_proto_colunas = opcoes_relatorio_personalizado.get("incluir_proto_colunas", False)
    abas_por_hw = opcoes_relatorio_personalizado.get("abas_por_hw", False)
    periodo_hoje = opcoes_relatorio_personalizado.get("periodo_hoje", False)
    periodo_0_7 = opcoes_relatorio_personalizado.get("periodo_0_7", False)
    periodo_7_15 = opcoes_relatorio_personalizado.get("periodo_7_15", False)
    periodo_15_30 = opcoes_relatorio_personalizado.get("periodo_15_30", False)
    periodo_30_cima = opcoes_relatorio_personalizado.get("periodo_30_cima", False)
    gerar_log_file = opcoes_relatorio_personalizado.get("gerar_log", False) # Nova opção

    # Preparar DataFrame principal
    df = preparar_dataframe(dados)
    faltantes = extrair_seriais_faltantes(dados, serials_list)

    # --- PERIODIZAÇÃO ---
    periodos = []
    temp_data_datetime_col = None

    if any([periodo_hoje, periodo_0_7, periodo_7_15, periodo_15_30, periodo_30_cima]):
        # Criar coluna temporária para filtragem
        df['data_datetime'] = pd.to_datetime(df['data'], format="%d/%m/%Y", errors="coerce")
        temp_data_datetime_col = 'data_datetime'  # Marcar para remoção posterior

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

    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            # Remover a coluna temporária data_datetime do DataFrame principal antes de salvar
            if temp_data_datetime_col and temp_data_datetime_col in df.columns:
                df_principal = df.drop(columns=[temp_data_datetime_col])
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
                df_hw = df.drop(columns=[temp_data_datetime_col]) if temp_data_datetime_col and temp_data_datetime_col in df.columns else df
                criar_abas_por_hw(writer, df_hw)

            # Abas por período (caso algum filtro de período tenha sido marcado)
            for periodo in periodos:
                # Filtrar os dados conforme o período
                aba_df = df.loc[periodo['mask']]

                # Remover a coluna data_datetime antes de salvar
                if temp_data_datetime_col and temp_data_datetime_col in aba_df.columns:
                    aba_df = aba_df.drop(columns=[temp_data_datetime_col])

                if not aba_df.empty:
                    nome_aba = tratar_nome_abas_excel(periodo['nome_aba'])
                    aba_df.to_excel(writer, index=False, sheet_name=nome_aba)

        adicionar_log(f"📄 Arquivo Excel salvo em: {path}")

        # Opcional: salvar log textual também
        if gerar_log_file and log_content_to_save:
            log_path = path.replace(".xlsx", ".txt")
            try:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(log_content_to_save)
                adicionar_log(f"📃 Log salvo em: {log_path}")
            except Exception as e:
                adicionar_log(f"Erro ao salvar arquivo de log: {e}")

        return path

    except Exception as e:
        adicionar_log(f"Erro crítico ao salvar arquivo Excel: {e}")
        return None

