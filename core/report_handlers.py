# core/report_handlers.py
"""
═══════════════════════════════════════════════════════════════════════════════
ORQUESTRADOR CENTRAL DE GERAÇÃO DE RELATÓRIOS
═══════════════════════════════════════════════════════════════════════════════

Este módulo faz a ponte entre a GUI e os geradores específicos de cada tipo
de relatório, centralizando a lógica de validação, criação de diretórios e
tratamento de erros.

ARQUITETURA UNIFICADA:
────────────────────────────────────────────────────────────────────────────────
ReportHandler (orquestrador principal)
│
├─ generate_reports()                    [MÉTODO UNIFICADO]
│  ├─ Detecta tipo de fluxo (eventos vs gerais)
│  ├─ Valida dados de entrada
│  ├─ Cria estrutura de diretórios
│  ├─ Gera timestamp único
│  ├─ Delega para método interno apropriado
│  └─ Emite toast de sucesso/erro
│
├─ generate_events_report()              [WRAPPER PÚBLICO]
│  ├─ Recebe list (compatível com signal)
│  ├─ Constrói dict internamente
│  └─ Chama generate_reports()
│
├─ _generate_general_reports_internal()  [FLUXO GERAL]
│  ├─ Loop sobre enabled_queries
│  └─ Chama _generate_single_report()
│
├─ _generate_events_report_internal()    [FLUXO EVENTOS]
│  └─ Chama _generate_single_report() com data_override
│
└─ _generate_single_report()             [GERADOR INDIVIDUAL]
   ├─ Obtém módulo correto via REPORT_MAP
   ├─ Valida existência de dados
   ├─ Define output_path com subdiretório apropriado
   ├─ Chama module.gerar_relatorio() com parâmetros específicos
   └─ Trata retorno (sucesso/erro)

MAPEAMENTOS:
────────────────────────────────────────────────────────────────────────────────
REPORT_MAP      → Tipo de requisição → Módulo gerador
REPORT_LABELS   → Tipo de requisição → Label amigável para logs
SUBDIRS         → Tipo de requisição → Subdiretório de saída

FLUXOS DE USO:
────────────────────────────────────────────────────────────────────────────────
1. RELATÓRIOS GERAIS (Últimas Posições, Status, Consumo):
   MainWindow → generate_reports(options) → _generate_general_reports_internal()
   → _generate_single_report() → módulo específico

2. RELATÓRIO DE EVENTOS:
   EventsTab → generate_events_report(list) → generate_reports(dict)
   → _generate_events_report_internal() → _generate_single_report() → report_events.py

DEPENDÊNCIAS:
────────────────────────────────────────────────────────────────────────────────
- app_state: Armazena dados das requisições e configurações
- signal_manager: Emite toasts de sucesso/erro/aviso
- reports.*: Módulos geradores específicos de cada tipo de relatório
═══════════════════════════════════════════════════════════════════════════════
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
    """
    Gerencia a geração de relatórios por tipo de requisição.

    Responsabilidades:
    - Validar dados de entrada
    - Criar estrutura de diretórios
    - Rotear para o módulo gerador correto
    - Tratar erros e emitir feedbacks
    """

    # ═══════════════════════════════════════════════════════════════════════
    # MAPEAMENTOS ESTÁTICOS
    # ═══════════════════════════════════════════════════════════════════════

    # Tipo de requisição → Módulo gerador
    REPORT_MAP = {
        "last_position_api": report_last_position,
        "last_position_redis": report_last_position,
        "status_equipment": report_device_status_maxtrack_redis,
        "data_consumption": report_traffic_data_redis,
        "events": report_events
    }

    # Tipo de requisição → Label amigável para logs
    REPORT_LABELS = {
        "last_position_api": "📡 Últimas Posições - API Mogno",
        "last_position_redis": "📍 Últimas Posições - Redis",
        "status_equipment": "⚙️ Status dos Equipamentos",
        "data_consumption": "📶 Consumo de Dados no Servidor",
        "events": "📋 Análise de Eventos"
    }

    # Tipo de requisição → Subdiretório de saída
    SUBDIRS = {
        "last_position_api": "ultimas_posicoes",
        "last_position_redis": "ultimas_posicoes",
        "status_equipment": "status_equipamentos",
        "data_consumption": "consumo_dados",
        "events": "analise_eventos"
    }

    # ═══════════════════════════════════════════════════════════════════════
    # INICIALIZAÇÃO
    # ═══════════════════════════════════════════════════════════════════════

    def __init__(self, app_state, signal_manager, main_window):
        """
        Inicializa o orquestrador de relatórios.

        Args:
            app_state: Instância do AppState (armazena dados e configurações)
            signal_manager: Instância do SignalManager (emite toasts)
            main_window: Referência à janela principal
        """
        self.app_state = app_state
        self.signal_manager = signal_manager
        self.main_window = main_window

    # ═══════════════════════════════════════════════════════════════════════
    # WRAPPER PÚBLICO: RELATÓRIO DE EVENTOS
    # ═══════════════════════════════════════════════════════════════════════

    def generate_events_report(self, eventos_data: list):
        """
        Wrapper público para geração de relatório de eventos.

        Mantém compatibilidade com a interface do signal (recebe list),
        mas internamente chama o método unificado generate_reports().

        Args:
            eventos_data (list): Lista de eventos retornados pela API

        Emite:
            - show_toast_warning: Se não houver eventos
            - show_toast_error: Se houver erro na geração
            - show_toast_success: Se gerado com sucesso
        """
        try:
            # Validação rápida
            if not eventos_data:
                self.signal_manager.show_toast_warning.emit("⚠️ Nenhum evento para gerar relatório")
                return

            # Constrói o dicionário de opções internamente
            options = {
                "report_type": "events",
                "eventos_data": eventos_data
            }

            # Chama o método unificado
            self.generate_reports(options)

        except Exception as e:
            adicionar_log(f"❌ Erro ao gerar relatório de eventos: {e}")
            adicionar_log(traceback.format_exc())
            self.signal_manager.show_toast_error.emit(f"❌ Erro ao gerar relatório: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # MÉTODO UNIFICADO: GERAÇÃO DE RELATÓRIOS
    # ═══════════════════════════════════════════════════════════════════════

    def generate_reports(self, options: dict):
        """
        Método unificado para gerar qualquer tipo de relatório.

        Suporta dois fluxos:
        1. Relatórios gerais (últimas posições, status, consumo)
        2. Relatório de eventos (com seleção de abas)

        Args:
            options (dict): Dicionário com parâmetros específicos do fluxo
                ┌─────────────────────────────────────────────────────────────┐
                │ PARA RELATÓRIOS GERAIS:                                     │
                ├─────────────────────────────────────────────────────────────┤
                │ - serials (list): Lista de números de série                 │
                │ - enabled_queries (list): Tipos habilitados                 │
                │   Ex: ["last_position_api", "status_equipment"]             │
                │ - sheet_config (dict): Config de abas (opcional)            │
                ├─────────────────────────────────────────────────────────────┤
                │ PARA RELATÓRIO DE EVENTOS:                                  │
                ├─────────────────────────────────────────────────────────────┤
                │ - report_type (str): "events"                               │
                │ - eventos_data (list): Dados dos eventos                    │
                └─────────────────────────────────────────────────────────────┘

        Emite:
            - show_toast_warning: Se validação falhar
            - show_toast_error: Se houver erros na geração
            - show_toast_success: Se tudo for gerado com sucesso
        """
        try:
            adicionar_log("📁 Iniciando geração de relatórios...")

            # ─────────────────────────────────────────────────────────────────
            # DETECÇÃO DO TIPO DE FLUXO
            # ─────────────────────────────────────────────────────────────────
            if options.get("report_type") == "events":
                # Fluxo de eventos: delegado ao método interno
                return self._generate_events_report_internal(options)

            # ─────────────────────────────────────────────────────────────────
            # FLUXO DE RELATÓRIOS GERAIS
            # ─────────────────────────────────────────────────────────────────
            return self._generate_general_reports_internal(options)

        except Exception as e:
            adicionar_log(f"❌ Erro inesperado em generate_reports: {e}")
            adicionar_log(traceback.format_exc())
            self.signal_manager.show_toast_error.emit(f"❌ Erro ao gerar relatórios: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # MÉTODO INTERNO: RELATÓRIOS GERAIS
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_general_reports_internal(self, options: dict):
        """
        Lógica interna para geração de relatórios gerais.

        Args:
            options (dict): Opções de geração (serials, enabled_queries, sheet_config)
        """
        # Extração de parâmetros
        serials = options.get("serials", [])
        enabled_queries = options.get("enabled_queries", [])
        sheet_config = options.get("sheet_config")

        # Validações
        if not serials and "data_consumption" not in enabled_queries:
            adicionar_log("⚠️ Nenhum serial fornecido para gerar relatórios.")
            self.signal_manager.show_toast_warning.emit("⚠️ Nenhum serial selecionado!")
            return

        if not enabled_queries:
            adicionar_log("⚠️ Nenhum tipo de relatório habilitado.")
            self.signal_manager.show_toast_warning.emit("⚠️ Selecione ao menos um tipo de relatório!")
            return

        # Configuração de abas
        if sheet_config:
            self.app_state.set("sheet_config", sheet_config)
            comm_types = sheet_config.get("comm_types", [])
            periods = sheet_config.get("periods", [])
            adicionar_log(f"📊 Config de abas: Tipos={comm_types}, Períodos={periods}")

        # Preparação
        base_dir = os.path.join(os.getcwd(), "relatorios_gerados")
        os.makedirs(base_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Geração de relatórios
        erros_encontrados = []

        for query_type in enabled_queries:
            try:
                self._generate_single_report(
                    query_type=query_type,
                    serials=serials,
                    base_dir=base_dir,
                    timestamp=timestamp,
                    data_override=None  # Busca do app_state
                )
            except Exception as e:
                erros_encontrados.append((query_type, str(e)))
                adicionar_log(f"❌ Erro ao gerar relatório '{query_type}': {e}")
                adicionar_log(traceback.format_exc())

        # Feedback final
        if erros_encontrados:
            msg_erro = f"⚠️ {len(erros_encontrados)} relatório(s) falharam. Verifique o log."
            self.signal_manager.show_toast_error.emit(msg_erro)
            adicionar_log(f"⚠️ Relatórios com erro: {[q for q, _ in erros_encontrados]}")
        else:
            adicionar_log("✅ Todos os relatórios foram gerados com sucesso!")
            self.signal_manager.show_toast_success.emit("✅ Relatórios gerados com sucesso!")

    # ═══════════════════════════════════════════════════════════════════════
    # MÉTODO INTERNO: RELATÓRIO DE EVENTOS
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_events_report_internal(self, options: dict):
        """
        Lógica interna para geração de relatório de eventos.

        Args:
            options (dict): Dicionário com:
                - report_type: "events"
                - eventos_data: lista de eventos
        """
        # Extração de parâmetros
        eventos_data = options.get("eventos_data", [])

        # Preparação
        base_dir = os.path.join(os.getcwd(), "relatorios_gerados")
        os.makedirs(base_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Recupera parâmetros do app_state
        eventos_config = self.app_state.get("eventos_config", {})
        serials = eventos_config.get("serials", [])

        # Chama geração única
        try:
            self._generate_single_report(
                query_type="events",
                serials=serials,
                base_dir=base_dir,
                timestamp=timestamp,
                data_override=eventos_data  # Passa dados diretamente
            )

            adicionar_log(f"✅ Relatório de eventos gerado com sucesso!")
            self.signal_manager.show_toast_success.emit("✅ Relatório de eventos gerado com sucesso!")

        except Exception as e:
            adicionar_log(f"❌ Erro ao gerar relatório de eventos: {e}")
            adicionar_log(traceback.format_exc())
            self.signal_manager.show_toast_error.emit(f"❌ Erro ao gerar relatório: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # MÉTODO AUXILIAR: GERAÇÃO DE RELATÓRIO INDIVIDUAL
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_single_report(self, query_type, serials, base_dir, timestamp, data_override=None):
        """
        Gera um único relatório de um tipo específico.

        Este método é chamado tanto por relatórios gerais quanto por eventos.
        A única diferença é que eventos passa 'data_override' diretamente.

        Fluxo:
        1. Obtém módulo gerador via REPORT_MAP
        2. Valida existência de dados (do app_state ou data_override)
        3. Define output_path com subdiretório apropriado
        4. Chama module.gerar_relatorio() com parâmetros corretos
        5. Valida retorno

        Args:
            query_type (str): Tipo de requisição (ex: "events", "last_position_api")
            serials (list): Lista de números de série
            base_dir (str): Diretório base para relatórios
            timestamp (str): Timestamp único para o arquivo
            data_override (list, optional): Dados a usar em vez de buscar do app_state

        Raises:
            Exception: Se o gerador retornar None ou falhar
        """
        adicionar_log(f"📄 Gerando relatório: {self.REPORT_LABELS.get(query_type, query_type)}")

        # ─────────────────────────────────────────────────────────────────────
        # OBTENÇÃO DO MÓDULO GERADOR
        # ─────────────────────────────────────────────────────────────────────
        module = self.REPORT_MAP.get(query_type)
        if not module:
            adicionar_log(f"⚠️ Tipo de relatório desconhecido: {query_type}")
            return

        if not hasattr(module, "gerar_relatorio"):
            adicionar_log(f"⚠️ Módulo '{module.__name__}' não possui função gerar_relatorio()")
            return

        # ─────────────────────────────────────────────────────────────────────
        # OBTENÇÃO DOS DADOS
        # ─────────────────────────────────────────────────────────────────────
        if data_override is not None:
            # Eventos: usa dados passados diretamente
            resultados = data_override
        else:
            # Relatórios gerais: busca do app_state
            resultados = self.app_state.get("dados_atuais", {}).get(query_type, [])

        if not resultados:
            adicionar_log(f"⚠️ Nenhum dado disponível para {query_type}. Pulando...")
            return

        # ─────────────────────────────────────────────────────────────────────
        # DEFINIÇÃO DO CAMINHO DE SAÍDA
        # ─────────────────────────────────────────────────────────────────────
        subdir = self.SUBDIRS.get(query_type, "outros")
        output_dir = os.path.join(base_dir, subdir)
        os.makedirs(output_dir, exist_ok=True)

        filename = f"report_{query_type}_{timestamp}.xlsx"
        output_path = os.path.join(output_dir, filename)

        adicionar_log(f"📁 Salvando em: {os.path.relpath(output_path)}")

        # ─────────────────────────────────────────────────────────────────────
        # CHAMADA DO GERADOR (com parâmetros específicos por tipo)
        # ─────────────────────────────────────────────────────────────────────
        if query_type == "events":
            # Parâmetros específicos de eventos
            eventos_config = self.app_state.get("eventos_config", {})
            sheet_config = self.app_state.get("events_sheet_config", {})

            start_datetime = eventos_config.get("start_datetime", "N/A")
            end_datetime = eventos_config.get("end_datetime", "N/A")
            filtros_str = eventos_config.get("filtros", "")

            selected_sheets = sheet_config.get("sheets", ["Resumo_Eventos"])
            include_seriais_sem_evento = sheet_config.get("include_seriais_sem_evento", True)
            include_event_types = sheet_config.get("include_event_types", [])

            modo_rapido = len(resultados) > 5000
            adicionar_log(f"⚡ Modo rápido: {'ATIVADO' if modo_rapido else 'DESATIVADO'} ({len(resultados)} eventos)")
            adicionar_log(f"📊 Abas a gerar: {selected_sheets}")

            result_path = module.gerar_relatorio(
                serials=serials,
                eventos_data=resultados,
                output_path=output_path,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                filtros_str=filtros_str,
                modo_rapido=modo_rapido,
                selected_sheets=selected_sheets,
                include_seriais_sem_evento=include_seriais_sem_evento,
                include_event_types=include_event_types
            )

        elif query_type in ["last_position_redis", "last_position_api"]:
            # Parâmetros específicos de últimas posições
            origem = 'redis' if query_type == "last_position_redis" else 'api'
            result_path = module.gerar_relatorio(
                serials,
                resultados,
                output_path,
                origem=origem
            )

        else:
            # Parâmetros padrão para outros tipos
            result_path = module.gerar_relatorio(serials, resultados, output_path)

        # ─────────────────────────────────────────────────────────────────────
        # VALIDAÇÃO DO RETORNO
        # ─────────────────────────────────────────────────────────────────────
        if result_path:
            adicionar_log(f"✅ Relatório '{filename}' gerado com sucesso!")
        else:
            adicionar_log(f"⚠️ Relatório '{filename}' retornou None (possível erro interno)")
            raise Exception(f"Gerador de '{query_type}' retornou None")
