# mogno_app/core/report_handlers.py

"""
Handlers para geração de relatórios consolidados e separados.
"""

import os
import datetime
import pandas as pd
from threading import Thread
from PyQt5.QtWidgets import QMessageBox
from core.equipment_analysis import consolidar_dados_equipamentos
from core.report_generation import salvar_resultado_excel
from utils.logger import adicionar_log
from config.settings import OUTPUT_DIR

class ReportHandler:
    """Gerenciador de geração de relatórios"""
    
    def __init__(self, app_state, signal_manager, main_window):
        self.app_state = app_state
        self.signal_manager = signal_manager
        self.main_window = main_window
        
    def generate_consolidated_report(self, opcoes):
        """Gera relatório consolidado"""
        adicionar_log(f"📊 Gerando relatório consolidado")
        
        def generate_thread():
            try:
                serials = opcoes.get("serials", [])
                if not serials:
                    raise ValueError("Nenhum serial para o relatório")
                
                dados_disponiveis = {}
                
                if "last_position" in opcoes.get("enabled_queries", []):
                    if "last_position_api" in self.app_state["dados_atuais"]:
                        dados_disponiveis["ultimas_posicoes"] = self.app_state["dados_atuais"]["last_position_api"]
                    elif "last_position_redis" in self.app_state["dados_atuais"]:
                        dados_disponiveis["ultimas_posicoes"] = self.app_state["dados_atuais"]["last_position_redis"]
                
                if "status_equipment" in opcoes.get("enabled_queries", []):
                    if "status_equipment" in self.app_state["dados_atuais"]:
                        dados_disponiveis["status_equipamentos"] = self.app_state["dados_atuais"]["status_equipment"]
                
                if "data_consumption" in opcoes.get("enabled_queries", []):
                    if "data_consumption" in self.app_state["dados_atuais"]:
                        dados_disponiveis["consumo_dados"] = self.app_state["dados_atuais"]["data_consumption"]
                
                df_consolidado = consolidar_dados_equipamentos(
                    ultimas_posicoes=dados_disponiveis.get("ultimas_posicoes"),
                    status_equipamentos=dados_disponiveis.get("status_equipamentos"),
                    consumo_dados=dados_disponiveis.get("consumo_dados")
                )
                
                if df_consolidado is None:
                    raise ValueError("Falha na consolidação dos dados")
                
                nome_arquivo = f"relatorio_consolidado_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                caminho_arquivo = os.path.join(OUTPUT_DIR, nome_arquivo)
                
                with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
                    if isinstance(df_consolidado, pd.DataFrame):
                        df_consolidado.to_excel(writer, index=False, sheet_name="Consolidado")
                    else:
                        for aba_nome, df_aba in df_consolidado.items():
                            aba_nome_limpo = aba_nome[:31]
                            df_aba.to_excel(writer, index=False, sheet_name=aba_nome_limpo)
                    
                    pd.DataFrame({"Seriais Processados": serials}).to_excel(
                        writer, index=False, sheet_name="Seriais_Processados"
                    )
                
                adicionar_log(f"✅ Relatório consolidado gerado: {caminho_arquivo}")
                
                resposta = QMessageBox.question(
                    self.main_window,
                    "Relatório Gerado",
                    f"Relatório consolidado criado:\n{caminho_arquivo}\n\nDeseja abrir o arquivo?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if resposta == QMessageBox.Yes:
                    try:
                        os.startfile(caminho_arquivo)
                    except Exception as e:
                        QMessageBox.critical(self.main_window, "Erro", f"Não foi possível abrir:\n{e}")
                        
            except Exception as e:
                error_msg = f"Erro ao gerar relatório consolidado: {e}"
                adicionar_log(f"❌ {error_msg}")
                QMessageBox.critical(self.main_window, "Erro", error_msg)
        
        Thread(target=generate_thread, daemon=True).start()
        
    def generate_separate_reports(self, opcoes):
        """Gera relatórios separados"""
        adicionar_log(f"📊 Gerando relatórios separados")
        
        def generate_thread():
            try:
                serials = opcoes.get("serials", [])
                if not serials:
                    raise ValueError("Nenhum serial para os relatórios")
                
                enabled_queries = opcoes.get("enabled_queries", [])
                arquivos_gerados = []
                
                for query_type in enabled_queries:
                    try:
                        if query_type == "last_position":
                            if "last_position_api" in self.app_state["dados_atuais"]:
                                dados = self.app_state["dados_atuais"]["last_position_api"]
                                arquivo = salvar_resultado_excel(
                                    dados=dados,
                                    serials_list=serials,
                                    opcoes_relatorio_personalizado=opcoes
                                )
                            elif "last_position_redis" in self.app_state["dados_atuais"]:
                                dados = self.app_state["dados_atuais"]["last_position_redis"]
                                arquivo = salvar_resultado_excel(
                                    dados=dados,
                                    serials_list=serials,
                                    opcoes_relatorio_personalizado=opcoes
                                )
                            else:
                                continue
                                
                        elif query_type == "status_equipment":
                            if "status_equipment" in self.app_state["dados_atuais"]:
                                dados = self.app_state["dados_atuais"]["status_equipment"]
                                nome_arquivo = f"status_equipamentos_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                df_status = pd.DataFrame([{
                                    "Serial": item.get("Serial", ""),
                                    "Status": str(item.get("Dados", ""))
                                } for item in dados])
                                arquivo = os.path.join(OUTPUT_DIR, nome_arquivo)
                                df_status.to_excel(arquivo, index=False)
                            else:
                                continue
                                
                        elif query_type == "data_consumption":
                            if "data_consumption" in self.app_state["dados_atuais"]:
                                dados = self.app_state["dados_atuais"]["data_consumption"]
                                nome_arquivo = f"consumo_dados_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                df_consumo = pd.DataFrame([
                                    {"Serial": serial, "Consumo": consumo}
                                    for serial, consumo in dados.items()
                                ])
                                arquivo = os.path.join(OUTPUT_DIR, nome_arquivo)
                                df_consumo.to_excel(arquivo, index=False)
                            else:
                                continue
                                
                        if arquivo:
                            arquivos_gerados.append(arquivo)
                            adicionar_log(f"✅ Relatório {query_type} gerado")
                            
                    except Exception as e:
                        adicionar_log(f"❌ Erro ao gerar relatório {query_type}: {e}")
                        continue
                
                if arquivos_gerados:
                    mensagem = f"Relatórios gerados:\n\n"
                    for arquivo in arquivos_gerados:
                        mensagem += f"• {os.path.basename(arquivo)}\n"
                    
                    resposta = QMessageBox.question(
                        self.main_window,
                        "Relatórios Gerados",
                        mensagem + "\nDeseja abrir todos?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if resposta == QMessageBox.Yes:
                        for arquivo in arquivos_gerados:
                            try:
                                os.startfile(arquivo)
                            except Exception as e:
                                adicionar_log(f"Erro ao abrir {arquivo}: {e}")
                else:
                    adicionar_log("❌ Nenhum relatório foi gerado")
                    
            except Exception as e:
                error_msg = f"Erro ao gerar relatórios separados: {e}"
                adicionar_log(f"❌ {error_msg}")
                QMessageBox.critical(self.main_window, "Erro", error_msg)
        
        Thread(target=generate_thread, daemon=True).start()
