# services/events_api.py
"""
Requisições de eventos via API Mogno com suporte a multithread e retry automático.
Busca eventos de rastreadores em um período específico com filtros.
"""

import requests
import traceback
from datetime import datetime
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from utils.logger import adicionar_log
from config.settings import MOGNO_BASE_URL, MOGNO_EVENTS_ENDPOINT, MOGNO_EVENTS_REFERER

def requisitar_eventos_serial(serial, start_datetime, end_datetime, event_filters, app_state, page=1, timeout=30):
    """
    Requisita eventos de um único serial em um período específico.

    Args:
        serial (str): Número de série do rastreador
        start_datetime (str): Data/hora início no formato "dd/MM/yyyy HH:mm:ss"
        end_datetime (str): Data/hora fim no formato "dd/MM/yyyy HH:mm:ss"
        event_filters (str): String com IDs dos eventos separados por vírgula (ex: "0,1,2,6,7")
        app_state: Instância do AppState com token JWT
        page (int): Número da página (padrão: 1)
        timeout (int): Timeout da requisição em segundos

    Returns:
        tuple: (success: bool, data: list)
            - success: True se sucesso, False se timeout/erro
            - data: Lista de eventos encontrados (vazia se erro)
    """
    try:
        token = app_state.get("jwt_token")
        cookie_dict = app_state.get("cookie_dict", {})

        if not token:
            adicionar_log("❌ Token JWT não encontrado. Faça login primeiro.")
            return False, []

        # Converte formato de data: "27/11/2025 00:00:00" → "27-11-2025 00:00:00"
        start_formatted = start_datetime.replace("/", "-")
        end_formatted = end_datetime.replace("/", "-")

        # Codifica apenas o espaço (não os dois pontos)
        start_encoded = quote(start_formatted, safe=':')
        end_encoded = quote(end_formatted, safe=':')

        # Monta a URL do endpoint
        endpoint = MOGNO_EVENTS_ENDPOINT.format(
            serial=serial,
            start_date=start_encoded,
            end_date=end_encoded,
            page=page
        )
        url = f"{MOGNO_BASE_URL}{endpoint}"

        # Headers da requisição
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"Bearer {token}",
            "Referer": f"{MOGNO_BASE_URL}{MOGNO_EVENTS_REFERER}",
            "Origin": MOGNO_BASE_URL,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }

        # Cookies
        cookies = {
            "Authorization": f"Bearer {token}",
            "login": cookie_dict.get("login", ""),
            "userId": cookie_dict.get("userId", ""),
        }

        # Payload com filtros de eventos
        payload = {
            "filtro": event_filters
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                adicionar_log(f"✅ Serial {serial}: {len(data)} eventos encontrados")
                return True, data
            else:
                adicionar_log(f"⚠️ Serial {serial}: resposta não é uma lista")
                return True, []
        else:
            adicionar_log(f"❌ Serial {serial}: Status {response.status_code}")
            return False, []

    except requests.exceptions.Timeout:
        adicionar_log(f"⏱️ Timeout: {serial}")
        return False, []  # ✅ Retorna False para indicar timeout
    except requests.exceptions.RequestException as e:
        adicionar_log(f"❌ Erro de rede ({serial}): {e}")
        return False, []
    except Exception as e:
        adicionar_log(f"❌ Erro inesperado ({serial}): {e}")
        return False, []


def requisitar_eventos_lote(serials, start_datetime, end_datetime, event_filters, app_state,
                           max_workers=20, progress_callback=None):
    """
    Requisita eventos de múltiplos seriais usando multithread com retry automático.

    Args:
        serials (list): Lista de números de série
        start_datetime (str): Data/hora início
        end_datetime (str): Data/hora fim
        event_filters (str): Filtros de eventos
        app_state: Instância do AppState
        max_workers (int): Número máximo de threads simultâneas (padrão: 20)
        progress_callback (callable): Função para atualizar progresso (current, total, label)

    Returns:
        list: Lista consolidada de todos os eventos encontrados
    """
    todos_eventos = []
    total_serials = len(serials)
    processados = 0
    lock = Lock()

    # ✅ NOVO: Lista para armazenar seriais com timeout
    serials_com_timeout = []

    adicionar_log(f"🚀 Iniciando requisição de eventos para {total_serials} seriais (multithread)...")
    adicionar_log(f"📅 Período: {start_datetime} até {end_datetime}")
    adicionar_log(f"🔍 Filtros: {event_filters}")
    adicionar_log(f"🧵 Workers: {max_workers}")

    def processar_serial(serial, is_retry=False):
        """Função auxiliar para processar um serial."""
        nonlocal processados

        try:
            # Requisita eventos do serial
            success, eventos = requisitar_eventos_serial(
                serial,
                start_datetime,
                end_datetime,
                event_filters,
                app_state,
                page=1
            )

            # ✅ NOVO: Se deu timeout, adiciona à lista
            if not success and not is_retry:
                with lock:
                    serials_com_timeout.append(serial)

            # Adiciona informações extras a cada evento
            for evento in eventos:
                evento['serial_requisitado'] = serial
                evento['data_requisicao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # Atualiza progresso (thread-safe)
            with lock:
                processados += 1
                if progress_callback:
                    retry_label = " (retry)" if is_retry else ""
                    progress_callback(processados, total_serials, f"Processado: {serial}{retry_label}")

            return success, eventos

        except Exception as e:
            adicionar_log(f"❌ Erro ao processar serial {serial}: {e}")

            # Atualiza progresso mesmo em caso de erro
            with lock:
                processados += 1
                if progress_callback:
                    progress_callback(processados, total_serials, f"Erro: {serial}")

            return False, []

    # ========================================================================
    # FASE 1: REQUISIÇÕES INICIAIS
    # ========================================================================
    adicionar_log("📡 Fase 1: Requisições iniciais...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submete todas as tarefas
        futures = {executor.submit(processar_serial, serial, False): serial for serial in serials}

        # Coleta resultados conforme vão completando
        for future in as_completed(futures):
            serial = futures[future]
            try:
                success, eventos = future.result()
                if success:
                    todos_eventos.extend(eventos)
            except Exception as e:
                adicionar_log(f"❌ Exceção ao processar {serial}: {e}")
                adicionar_log(traceback.format_exc())

    # ========================================================================
    # FASE 2: RETRY AUTOMÁTICO PARA SERIAIS COM TIMEOUT
    # ========================================================================
    if serials_com_timeout:
        adicionar_log(f"🔄 Fase 2: Retry para {len(serials_com_timeout)} seriais com timeout...")
        adicionar_log(f"📋 Seriais com timeout: {', '.join(serials_com_timeout)}")

        # Reseta contador para o retry
        processados = 0
        total_retry = len(serials_com_timeout)
        serials_falharam_retry = []

        # Atualiza callback de progresso para indicar retry
        if progress_callback:
            progress_callback(0, total_retry, "Iniciando retry...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submete tarefas de retry
            futures_retry = {
                executor.submit(processar_serial, serial, True): serial 
                for serial in serials_com_timeout
            }

            # Coleta resultados do retry
            for future in as_completed(futures_retry):
                serial = futures_retry[future]
                try:
                    success, eventos = future.result()
                    if success:
                        todos_eventos.extend(eventos)
                        adicionar_log(f"✅ Retry bem-sucedido: {serial}")
                    else:
                        serials_falharam_retry.append(serial)
                        adicionar_log(f"❌ Retry falhou: {serial}")
                except Exception as e:
                    serials_falharam_retry.append(serial)
                    adicionar_log(f"❌ Exceção no retry de {serial}: {e}")

        # ========================================================================
        # RELATÓRIO FINAL DE TIMEOUTS
        # ========================================================================
        if serials_falharam_retry:
            adicionar_log("=" * 70)
            adicionar_log(f"⚠️ ATENÇÃO: {len(serials_falharam_retry)} seriais falharam mesmo após retry:")
            adicionar_log("=" * 70)
            for serial in serials_falharam_retry:
                adicionar_log(f"   ❌ {serial}")
            adicionar_log("=" * 70)
            adicionar_log("💡 Sugestões:")
            adicionar_log("   • Verifique a conexão de rede")
            adicionar_log("   • Tente novamente com período menor")
            adicionar_log("   • Verifique se os seriais estão ativos")
            adicionar_log("=" * 70)
        else:
            adicionar_log("✅ Todos os seriais com timeout foram recuperados no retry!")
    else:
        adicionar_log("✅ Nenhum timeout detectado. Todas as requisições foram bem-sucedidas!")

    # ========================================================================
    # RESUMO FINAL
    # ========================================================================
    adicionar_log("=" * 70)
    adicionar_log(f"📊 RESUMO FINAL:")
    adicionar_log(f"   • Total de seriais: {total_serials}")
    adicionar_log(f"   • Eventos encontrados: {len(todos_eventos)}")
    adicionar_log(f"   • Timeouts (1ª tentativa): {len(serials_com_timeout)}")
    if serials_com_timeout:
        adicionar_log(f"   • Recuperados no retry: {len(serials_com_timeout) - len(serials_falharam_retry)}")
        adicionar_log(f"   • Falharam após retry: {len(serials_falharam_retry)}")
    adicionar_log("=" * 70)

    return todos_eventos
