# mogno_app/core/request_handlers.py

"""
Handlers para processamento de requisições de equipamentos.
Encapsula toda a lógica de execução de consultas (API, Redis, etc.).
"""

import time
from threading import Thread
from services.api_requests import modo_requisitar_lotes
from services.redis_service import ultima_posicao_tipo, status_equipamento, obter_dados_consumo
from utils.logger import adicionar_log
from utils.helpers import formatar_tempo

class RequestHandler:
    """Gerenciador de requisições de equipamentos"""
    
    def __init__(self, app_state, signal_manager):
        self.app_state = app_state
        self.signal_manager = signal_manager
        
    def execute_last_position_api(self, api_type, serials, config=None):
        """Executa requisição de últimas posições via API Mogno"""
        adicionar_log(f"🚀 Iniciando requisição via API ({api_type})")
        
        def execute_thread():
            try:
                step = config.get("step", 20) if config else 20
                max_workers = config.get("max_workers", 4) if config else 4
                modo = config.get("mode", "paralelo") if config else "paralelo"
                
                resultados = modo_requisitar_lotes(
                    serials,
                    self.app_state,
                    tipo_api=api_type,
                    step=step,
                    max_workers=max_workers,
                    ajuste_step=10,
                    tentativas_timeout=3,
                    progress_callback=lambda current, total: self.signal_manager.equipment_progress_updated.emit(
                        current, total, f"API Mogno ({api_type}) - {current}/{total}"
                    ),
                    modo=modo
                )
                
                self.app_state["dados_atuais"]["last_position_api"] = resultados
                self.signal_manager.last_position_completed.emit(resultados)
                adicionar_log(f"✅ {len(resultados)} posições obtidas via API")
                
            except Exception as e:
                error_msg = f"Erro na requisição API: {e}"
                adicionar_log(f"❌ {error_msg}")
                self.signal_manager.request_failed.emit(error_msg)
        
        Thread(target=execute_thread, daemon=True).start()
        
    def execute_last_position_redis(self, serials):
        self.execute_redis_generic(
            serials,
            tipo="last_position_redis",
            redis_func=ultima_posicao_tipo,
            signal_complete=self.signal_manager.last_position_completed,
            progress_label="Últimas Posições Redis"
        )
    
    def execute_status_equipment(self, serials):
        self.execute_redis_generic(
            serials,
            tipo="status_equipment",
            redis_func=status_equipamento,
            signal_complete=self.signal_manager.status_equipment_completed,
            progress_label="Status Maxtrack"
        )
    
        
    def execute_data_consumption(self, serials, month, year):
        """Executa requisição de consumo de dados"""
        adicionar_log(f"🚀 Iniciando requisição de consumo ({month}/{year})")
        
        def execute_thread():
            try:
                # obter_dados_consumo conecta ao Redis internamente
                all_consumption = obter_dados_consumo(month, year)
                
                # Filtrar apenas os seriais solicitados
                filtered_consumption = {
                    serial: consumo for serial, consumo in all_consumption.items() 
                    if serial in serials
                }
                
                self.app_state["dados_atuais"]["data_consumption"] = filtered_consumption
                self.signal_manager.data_consumption_completed.emit(filtered_consumption)
                adicionar_log(f"✅ {len(filtered_consumption)} registros de consumo obtidos")
                
            except Exception as e:
                error_msg = f"Erro na requisição de consumo: {e}"
                adicionar_log(f"❌ {error_msg}")
                self.signal_manager.request_failed.emit(error_msg)
        
        Thread(target=execute_thread, daemon=True).start()

    def execute_redis_generic(self, serials, tipo, redis_func, signal_complete, progress_label):
        adicionar_log(f"🚀 Iniciando requisição Redis ({tipo})")
    
        def execute_thread():
            try:
                total = len(serials)
                batch_size = 50
                batches = [serials[i:i+batch_size] for i in range(0, len(serials), batch_size)]
                all_results = []
                current = 0
    
                for i, batch in enumerate(batches):
                    self.signal_manager.equipment_progress_updated.emit(
                        current, total, f"{progress_label} - Lote {i+1}/{len(batches)}"
                    )
                    batch_results = redis_func(batch)
                    all_results.extend(batch_results)
                    current += len(batch)
                    time.sleep(0.5)
    
                self.app_state["dados_atuais"][tipo] = all_results
                signal_complete.emit(all_results)
                adicionar_log(f"✅ {len(all_results)} registros obtidos via Redis ({tipo})")
    
            except Exception as e:
                error_msg = f"Erro na requisição Redis ({tipo}): {e}"
                adicionar_log(f"❌ {error_msg}")
                self.signal_manager.request_failed.emit(error_msg)
    
        Thread(target=execute_thread, daemon=True).start()
    