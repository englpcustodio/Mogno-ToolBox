# mogno_app/core/equipment_analysis.py

"""
Módulo para coordenar e consolidar consultas de análise de equipamentos.
Integra dados de múltiplas fontes (API Mogno, Redis, etc.).
"""

import pandas as pd
from utils.logger import adicionar_log

def consolidar_dados_equipamentos(
    ultimas_posicoes=None,
    status_equipamentos=None,
    consumo_dados=None,
    status_linhas=None,
    status_lorawan=None
):
    """
    Consolida dados de diferentes fontes em um único DataFrame ou dict de DataFrames.
    
    Args:
        ultimas_posicoes: Lista de dicts com últimas posições (API ou Redis)
        status_equipamentos: Lista de dicts com status Maxtrack (Redis)
        consumo_dados: Dict com consumo de dados por serial (Redis)
        status_linhas: Lista de dicts com status de linhas (futuro)
        status_lorawan: Lista de dicts com status LoraWAN (futuro)
    
    Returns:
        DataFrame consolidado ou dict de DataFrames por tipo de consulta
    """
    try:
        dataframes = {}
        
        # Processar últimas posições
        if ultimas_posicoes:
            adicionar_log(f"📊 Consolidando {len(ultimas_posicoes)} registros de últimas posições")
            
            # Se for uma lista de dicts (da API Mogno)
            if isinstance(ultimas_posicoes, list) and ultimas_posicoes:
                df_posicoes = pd.DataFrame(ultimas_posicoes)
                
                # Renomear "logitude" para "longitude" se existir
                if "logitude" in df_posicoes.columns:
                    df_posicoes.rename(columns={"logitude": "longitude"}, inplace=True)
                
                dataframes["Ultimas_Posicoes"] = df_posicoes
                adicionar_log(f"✅ DataFrame de últimas posições criado: {len(df_posicoes)} linhas")
        
        # Processar status dos equipamentos
        if status_equipamentos:
            adicionar_log(f"📊 Consolidando {len(status_equipamentos)} registros de status")
            
            # Extrair informações relevantes do proto
            status_data = []
            for item in status_equipamentos:
                serial = item.get("Serial", "")
                dados_proto = item.get("Dados")
                
                if dados_proto:
                    # Aqui você pode extrair campos específicos do proto
                    # Por enquanto, vamos criar um registro básico
                    status_data.append({
                        "Serial": serial,
                        "Status": str(dados_proto)[:100]  # Limitar tamanho para visualização
                    })
            
            if status_data:
                df_status = pd.DataFrame(status_data)
                dataframes["Status_Equipamentos"] = df_status
                adicionar_log(f"✅ DataFrame de status criado: {len(df_status)} linhas")
        
        # Processar consumo de dados
        if consumo_dados:
            adicionar_log(f"📊 Consolidando {len(consumo_dados)} registros de consumo")
            
            # Converter dict para DataFrame
            consumo_list = [
                {"Serial": serial, "Consumo_MB": consumo}
                for serial, consumo in consumo_dados.items()
            ]
            
            if consumo_list:
                df_consumo = pd.DataFrame(consumo_list)
                dataframes["Consumo_Dados"] = df_consumo
                adicionar_log(f"✅ DataFrame de consumo criado: {len(df_consumo)} linhas")
        
        # Processar status de linhas (placeholder para futuro)
        if status_linhas:
            adicionar_log(f"📊 Consolidando {len(status_linhas)} registros de status de linhas")
            df_linhas = pd.DataFrame(status_linhas)
            dataframes["Status_Linhas"] = df_linhas
        
        # Processar status LoraWAN (placeholder para futuro)
        if status_lorawan:
            adicionar_log(f"📊 Consolidando {len(status_lorawan)} registros de status LoraWAN")
            df_lorawan = pd.DataFrame(status_lorawan)
            dataframes["Status_LoraWAN"] = df_lorawan
        
        # Se houver apenas um DataFrame, retornar diretamente
        if len(dataframes) == 1:
            return list(dataframes.values())[0]
        
        # Se houver múltiplos DataFrames, retornar dict
        if len(dataframes) > 1:
            adicionar_log(f"✅ Consolidação concluída: {len(dataframes)} DataFrames criados")
            return dataframes
        
        # Se não houver dados, retornar None
        adicionar_log("⚠️ Nenhum dado disponível para consolidação")
        return None
        
    except Exception as e:
        adicionar_log(f"❌ Erro ao consolidar dados de equipamentos: {e}")
        return None

def merge_dataframes_by_serial(dataframes_dict):
    """
    Faz merge de múltiplos DataFrames usando a coluna 'Serial' como chave.
    
    Args:
        dataframes_dict: Dict com nome_aba: DataFrame
        
    Returns:
        DataFrame consolidado com merge de todos os dados
    """
    try:
        if not dataframes_dict:
            return None
        
        # Começar com o primeiro DataFrame
        df_list = list(dataframes_dict.values())
        df_merged = df_list[0].copy()
        
        # Fazer merge com os demais
        for df in df_list[1:]:
            if "Serial" in df.columns and "Serial" in df_merged.columns:
                df_merged = pd.merge(
                    df_merged,
                    df,
                    on="Serial",
                    how="outer",  # Outer join para manter todos os seriais
                    suffixes=("", "_dup")
                )
        
        adicionar_log(f"✅ Merge de DataFrames concluído: {len(df_merged)} linhas")
        return df_merged
        
    except Exception as e:
        adicionar_log(f"❌ Erro ao fazer merge de DataFrames: {e}")
        return None

def filtrar_por_seriais(df, serials_list):
    """
    Filtra um DataFrame para incluir apenas os seriais especificados.
    
    Args:
        df: DataFrame a ser filtrado
        serials_list: Lista de seriais para manter
        
    Returns:
        DataFrame filtrado
    """
    try:
        if df is None or "Serial" not in df.columns:
            return df
        
        df_filtrado = df[df["Serial"].isin(serials_list)]
        adicionar_log(f"✅ DataFrame filtrado: {len(df_filtrado)} de {len(df)} linhas mantidas")
        return df_filtrado
        
    except Exception as e:
        adicionar_log(f"❌ Erro ao filtrar DataFrame: {e}")
        return df
