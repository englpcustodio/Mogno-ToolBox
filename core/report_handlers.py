# core/report_handlers.py
"""
Orquestrador central de geração de relatórios.
Faz a ponte entre a GUI e os geradores específicos de cada tipo de relatório.

ReportHandler (orquestrador)
│
├─ generate_reports()
│  ├─ Valida opções
│  ├─ Cria diretórios
│  ├─ Gera timestamp
│  ├─ Loop sobre enabled_queries
│  │  └─ Chama _generate_single_report() para cada tipo
│  ├─ Coleta erros
│  └─ Emite toast de sucesso/erro
│
└─ _generate_single_report(query_type, serials, ...)
   ├─ Obtém módulo correto via REPORT_MAP
   ├─ Valida dados disponíveis
   ├─ Define output_path
   ├─ Chama module.gerar_relatorio(...)
   └─ Trata retorno (sucesso/erro)
"""

import os
import traceback
from datetime import datetime
from utils.logger import adicionar_log
from reports import (
    report_device_status_maxtrack_redis,
    report_last_position, 
    report_traffic_data_redis,
    report_events
)

class ReportHandler:
    """Gerencia a geração de relatórios por tipo de requisição."""

    # Mapeamento: tipo de requisição → módulo gerador
    REPORT_MAP = {
        "last_position_api": report_last_position,
        "last_position_redis": report_last_position,
        "status_equipment": report_device_status_maxtrack_redis,
        "data_consumption": report_traffic_data_redis,
        "events": report_events
    }

    # Labels amigáveis
    REPORT_LABELS = {
        "last_position_api": "📡 Últimas Posições - API Mogno",
        "last_position_redis": "📍 Últimas Posições - Redis",
        "status_equipment": "⚙️ Status dos Equipamentos",
        "data_consumption": "📶 Consumo de Dados no Servidor",
        "events": "📋 Análise de Eventos"
    }

    # Subdiretórios
    SUBDIRS = {
        "last_position_api": "ultimas_posicoes",
        "last_position_redis": "ultimas_posicoes",
        "status_equipment": "status_equipamentos",
        "data_consumption": "consumo_dados",
        "events": "analise_eventos"
    }

    def __init__(self, app_state, signal_manager, main_window):
        self.app_state = app_state
        self.signal_manager = signal_manager
        self.main_window = main_window

    def generate_reports(self, options: dict):
        """
        Gera relatórios separados para cada tipo de requisição habilitado.
        """
        try:
            adicionar_log("📁 Iniciando geração de relatórios...")

            serials = options.get("serials", [])
            enabled_queries = options.get("enabled_queries", [])
            #selected_periods = options.get("selected_periods")
            sheet_config = options.get("sheet_config")

            if not serials and not any(q == "data_consumption" for q in enabled_queries):
                adicionar_log("⚠️ Nenhum serial fornecido para gerar relatórios.")
                self.signal_manager.show_toast_warning.emit("⚠️ Nenhum serial selecionado!")
                return

            if not enabled_queries:
                adicionar_log("⚠️ Nenhum tipo de relatório habilitado.")
                self.signal_manager.show_toast_warning.emit("⚠️ Selecione ao menos um tipo de relatório!")
                return
#
#            # Armazena configuração de abas no app_state
            if sheet_config:
                self.app_state.set("sheet_config", sheet_config)
                comm_types = sheet_config.get("comm_types", [])
                periods = sheet_config.get("periods", [])
                adicionar_log(f"📊 Config de abas: Tipos={comm_types}, Períodos={periods}")

            # ✅ LOGA A CONFIGURAÇÃO ATUAL (debug)
            config = self.app_state.get("sheet_config", {})
            if config:
                adicionar_log(f"📊 Config de abas: {config}")

            # Diretório base
            base_dir = os.path.join(os.getcwd(), "relatorios_gerados")
            os.makedirs(base_dir, exist_ok=True)

            # Timestamp único
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Rastreia erros
            erros_encontrados = []

            # Gera cada relatório
            for query_type in enabled_queries:
                try:
                    self._generate_single_report(
                        query_type=query_type,
                        serials=serials,
                        base_dir=base_dir,
                        timestamp=timestamp
                    )
                except Exception as e:
                    erros_encontrados.append((query_type, str(e)))
                    adicionar_log(f"❌ Erro ao gerar relatório '{query_type}': {e}")
                    adicionar_log(traceback.format_exc())

            # Emite toast apropriado
            if erros_encontrados:
                msg_erro = f"⚠️ {len(erros_encontrados)} relatório(s) falharam. Verifique o log."
                self.signal_manager.show_toast_error.emit(msg_erro)
                adicionar_log(f"⚠️ Relatórios com erro: {[q for q, _ in erros_encontrados]}")
            else:
                adicionar_log("✅ Todos os relatórios foram gerados com sucesso!")
                self.signal_manager.show_toast_success.emit("✅ Relatórios gerados com sucesso!")

        except Exception as e:
            adicionar_log(f"❌ Erro inesperado em generate_reports: {e}")
            adicionar_log(traceback.format_exc())
            self.signal_manager.show_toast_error.emit(f"❌ Erro ao gerar relatórios: {e}")

    def _generate_single_report(self, query_type, serials, base_dir, timestamp):
        """
        Gera um único relatório de um tipo específico.
        """
        try:
            adicionar_log(f"📄 Gerando relatório: {self.REPORT_LABELS.get(query_type, query_type)}")

            # Obtém módulo gerador
            module = self.REPORT_MAP.get(query_type)
            if not module:
                adicionar_log(f"⚠️ Tipo de relatório desconhecido: {query_type}")
                return

            # Verifica função
            if not hasattr(module, "gerar_relatorio"):
                adicionar_log(f"⚠️ Módulo '{module.__name__}' não possui função gerar_relatorio()")
                return

            # Obtém dados
            resultados = self.app_state.get("dados_atuais", {}).get(query_type, [])
            if not resultados:
                adicionar_log(f"⚠️ Nenhum dado disponível para {query_type}. Pulando...")
                return

            # Define output_path
            subdir = self.SUBDIRS.get(query_type, "outros")
            output_dir = os.path.join(base_dir, subdir)
            os.makedirs(output_dir, exist_ok=True)

            filename = f"report_{query_type}_{timestamp}.xlsx"
            output_path = os.path.join(output_dir, filename)

            # Chama o gerador
            adicionar_log(f"📁 Salvando em: {os.path.relpath(output_path)}")

                # CHAMA O GERADOR (ele lê app_state internamente)
            if query_type in ["last_position_redis", "last_position_api"]:
                origem = 'redis' if query_type == "last_position_redis" else 'api'

                result_path = module.gerar_relatorio(
                    serials, 
                    resultados, 
                    output_path,
                    origem=origem
                )
            else:
                result_path = module.gerar_relatorio(serials, resultados, output_path)

            if result_path:
                adicionar_log(f"✅ Relatório '{filename}' gerado com sucesso!")
            else:
                adicionar_log(f"⚠️ Relatório '{filename}' retornou None (possível erro interno)")
                raise Exception(f"Gerador de '{query_type}' retornou None")

        except Exception as e:
            adicionar_log(f"❌ Erro ao gerar relatório '{query_type}': {e}")
            adicionar_log(traceback.format_exc())
            raise

    def generate_events_report(self, eventos_data):
        """Gera relatório específico de eventos."""
        try:
            if not eventos_data:
                self.signal_manager.show_toast_warning.emit("⚠️ Nenhum evento para gerar relatório")
                return

            from datetime import datetime
            import os

            # Diretório base
            base_dir = os.path.join(os.getcwd(), "relatorios_gerados", "analise_eventos")
            os.makedirs(base_dir, exist_ok=True)

            # Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"report_events_{timestamp}.xlsx"
            output_path = os.path.join(base_dir, filename)

            # Recupera parâmetros da requisição
            eventos_config = self.app_state.get("eventos_config", {})
            start_datetime = eventos_config.get("start_datetime", "N/A")
            end_datetime = eventos_config.get("end_datetime", "N/A")
            filtros_str = eventos_config.get("filtros", "")
            serials = eventos_config.get("serials", [])

            # ✅ MODO RÁPIDO: Ativado por padrão para grandes volumes
            modo_rapido = len(eventos_data) > 10000

            adicionar_log(f"📁 Salvando relatório de eventos em: {os.path.relpath(output_path)}")
            adicionar_log(f"⚡ Modo rápido: {'ATIVADO' if modo_rapido else 'DESATIVADO'} ({len(eventos_data)} eventos)")

            result_path = report_events.gerar_relatorio(
                serials=serials,
                eventos_data=eventos_data,
                output_path=output_path,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                filtros_str=filtros_str,
                modo_rapido=modo_rapido  # ✅ TOGGLE
            )

            if result_path:
                adicionar_log(f"✅ Relatório de eventos gerado com sucesso!")
                self.signal_manager.show_toast_success.emit("✅ Relatório de eventos gerado com sucesso!")
            else:
                raise Exception("Gerador retornou None")

        except Exception as e:
            adicionar_log(f"❌ Erro ao gerar relatório de eventos: {e}")
            adicionar_log(traceback.format_exc())
            self.signal_manager.show_toast_error.emit(f"❌ Erro ao gerar relatório: {e}")