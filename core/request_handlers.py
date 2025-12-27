# core/request_handlers.py
"""
Gerenciador centralizado de requisições (API, Redis, Consumo de Dados).
Responsável por orquestrar chamadas assíncronas, logs, progressos e sinais.
"""

import traceback
from threading import Thread, Lock
from utils.logger import adicionar_log
from services.api_requests import modo_requisitar_lotes
from services.redis_service import ultima_posicao_tipo, status_equipamento, obter_dados_consumo
from services.events_api import requisitar_eventos_lote

class RequestHandler:
    """Gerencia todas as requisições da aplicação (API e Redis) de forma otimizada."""

    def __init__(self, app_state, signal_manager):
        self.app_state = app_state
        self.signal_manager = signal_manager
        self._lock = Lock()
        self._active_count = 0

        # Mapeamento genérico de tipos → funções e sinais correspondentes
        self.REQ_MAP = {
            "last_position_api": (modo_requisitar_lotes, self.signal_manager.last_position_completed),
            "last_position_redis": (ultima_posicao_tipo, self.signal_manager.last_position_completed),
            "status_equipment": (status_equipamento, self.signal_manager.status_equipment_completed),
            "data_consumption": (obter_dados_consumo, self.signal_manager.data_consumption_completed),
            "events": (requisitar_eventos_lote, self.signal_manager.events_request_completed),
        }

        # Conecta sinais
        self.signal_manager.last_position_completed.connect(self._handle_finished)
        self.signal_manager.status_equipment_completed.connect(self._handle_finished)
        self.signal_manager.data_consumption_completed.connect(self._handle_finished)
        self.signal_manager.events_request_completed.connect(self._handle_finished)


    # ------------------------------------------------------------------
    # Controle de requisições ativas
    # ------------------------------------------------------------------
    def _inc(self):
        with self._lock:
            self._active_count += 1

    def _dec(self):
        with self._lock:
            if self._active_count > 0:
                self._active_count -= 1
            if self._active_count == 0:
                self.signal_manager.all_requests_finished.emit()

    def _handle_finished(self, *_):
        """Chamado quando uma requisição específica emite seu sinal de término."""
        self._dec()

    # ------------------------------------------------------------------
    # Execução genérica com threading
    # ------------------------------------------------------------------
    def _exec_async(self, tipo, func, *args, **kwargs):
        """Executa função de requisição em thread separada."""
        self._inc()

        def run():
            try:
                result = func(*args, **kwargs)
                self.app_state["dados_atuais"][tipo] = result
                self.REQ_MAP[tipo][1].emit(result)
                adicionar_log(f"✅ Requisição [{tipo}] concluída ({len(result) if result else 0} registros).")
            except Exception as e:
                adicionar_log(f"❌ Erro em [{tipo}]: {e}")
                adicionar_log(traceback.format_exc())
                self.REQ_MAP[tipo][1].emit([])
                self.signal_manager.show_toast_error.emit(f"Erro em {tipo}: {e}")

        Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # Chamadas públicas específicas
    # ------------------------------------------------------------------
    def execute_last_position_api(self, api_type, serials, config=None):
        """Executa requisição de últimas posições via API Mogno."""
        step = config.get("step", 20) if config else 20
        max_workers = config.get("max_workers", 4) if config else 4

        self._exec_async(
            "last_position_api",
            modo_requisitar_lotes,
            serials,
            self.app_state,
            tipo_api=api_type,
            step=step,
            max_workers=max_workers,
            ajuste_step=10,
            tentativas_timeout=3,
            progress_callback=lambda cur, tot: self.signal_manager.equipment_progress_updated.emit(
                cur, tot, f"API Mogno ({api_type}) - {cur}/{tot}"
            ),
        )

    def execute_last_position_redis(self, serials):
        """Executa requisição de últimas posições via Redis."""
        self._exec_async("last_position_redis", ultima_posicao_tipo, serials)

    def execute_status_equipment(self, serials):
        """Executa requisição de status de equipamentos via Redis."""
        self._exec_async("status_equipment", status_equipamento, serials)

    def execute_data_consumption(self, month, year):
        """Executa requisição de consumo de dados (não requer seriais)."""
        self._exec_async("data_consumption", obter_dados_consumo, month, year)

    def execute_events_request(self, serials, start_datetime, end_datetime, event_filters, max_workers=20):
        """
        Executa requisição de eventos via API Mogno com multithread.

        Args:
            serials (list): Lista de seriais
            start_datetime (str): Data/hora início
            end_datetime (str): Data/hora fim
            event_filters (str): Filtros de eventos (IDs separados por vírgula)
            max_workers (int): Número de threads simultâneas (padrão: 20)
        """
        self._exec_async(
            "events",
            requisitar_eventos_lote,
            serials,
            start_datetime,
            end_datetime,
            event_filters,
            self.app_state,
            max_workers=max_workers,  # Parâmetro de workers
            progress_callback=lambda cur, tot, lbl: self.signal_manager.events_progress_updated.emit(
                cur, tot, lbl
            ),
        )