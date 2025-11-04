# mogno_app/services/api_requests.py

import json
import requests
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import adicionar_log, log_inicio # Importa o logger da nova localização
from utils.helpers import ( # Importa helpers da nova localização
    dividir_lotes,
    step_autoajustar,
    lotes_total,
    calcular_tempo_medio_entre_requisicoes,
    formatar_tempo
)
from config.settings import ( # Importa configurações da nova localização
    MOGNO_BASE_URL,
    MOGNO_RASTREADORES_ENDPOINT,
    MOGNO_RASTREADORES_REFERER,
    MOGNO_ISCAS_ENDPOINT,
    MOGNO_ISCAS_REFERER,
    DEFAULT_REQUEST_TIMEOUT
)

def preparar_requisicao(tipo_api, serials, jwt_token, user_login, user_id, cookie_dict=None):
    """
    Prepara a URL, headers e payload para a requisição da API Mogno.
    """
    endpoints = {
        "rastreadores": (MOGNO_RASTREADORES_ENDPOINT, MOGNO_RASTREADORES_REFERER),
        "iscas": (MOGNO_ISCAS_ENDPOINT, MOGNO_ISCAS_REFERER)
    }
    endpoint, referer = endpoints.get(tipo_api, (None, None))
    if not endpoint:
        raise ValueError("tipo_api inválido")
    url = MOGNO_BASE_URL + endpoint
    cookie_items = [
        f"login={user_login}",
        f"userId={user_id}",
        f"Authorization=Bearer {jwt_token}"
    ]
    if cookie_dict:
        for k, v in cookie_dict.items():
            # Evita duplicar cookies que já estão sendo definidos explicitamente
            if not any(item.startswith(f"{k}=") for item in cookie_items):
                cookie_items.append(f"{k}={v}")
    if tipo_api == "iscas" and ("ztype=2" not in ";".join(cookie_items)):
        cookie_items.append("ztype=2")
    cookie_header = "; ".join(cookie_items)
    headers = {
        "Cookie": cookie_header,
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": referer,
        "Accept": "application/json, text/plain, */*"
    }
    if tipo_api == "iscas":
        payload = ";".join(serials)
    else:
        payload = json.dumps({"serial": ";".join(serials), "filtro": ""})
    return url, headers, payload

def requisitar_lote(serials, tipo_api, estado, lote_idx=1, total_lotes=1, timeout=DEFAULT_REQUEST_TIMEOUT, tentativas_timeout=3):
    """
    Realiza a requisição para um lote de seriais.
    Retorna (sucesso, dados_retornados, seriais_usados_no_lote).
    """
    jwt_token = estado['jwt_token']
    user_login = estado['user_login']
    user_id = estado['user_id']
    cookie_dict = estado.get('cookie_dict', None)
    url, headers, payload = preparar_requisicao(
        tipo_api, serials, jwt_token, user_login, user_id, cookie_dict
    )
    for tentativa in range(1, tentativas_timeout + 1):
        try:
            r = requests.post(url, headers=headers, data=payload, timeout=timeout)
            if r.status_code == 200:
                dados = r.json()
                adicionar_log(
                    f"Lote {lote_idx}/{total_lotes} [{len(serials)}] ✅ OK - "
                    f"{len(dados) if isinstance(dados, list) else 0}/{len(serials)} seriais válidos"
                )
                return True, dados, len(serials)
            else:
                adicionar_log(
                    f"Lote {lote_idx}/{total_lotes} [{len(serials)}] ❌ falhou: status {r.status_code} ({r.text[:100]})"
                )
                if r.status_code in [400, 413, 500]: # Erros que indicam problema com o payload ou servidor
                    return False, [], len(serials)
        except requests.Timeout:
            adicionar_log(
                f"Lote {lote_idx}/{total_lotes} [{len(serials)}] ❌ timeout (tentativa {tentativa}/{tentativas_timeout})"
            )
            if tentativa == tentativas_timeout:
                adicionar_log(f"Lote {lote_idx}/{total_lotes} [{len(serials)}] cancelado após {tentativas_timeout} timeouts.")
        except Exception as e:
            adicionar_log(f"Erro no lote {lote_idx}: {e}")
            sleep(2) # Pequena pausa antes de tentar novamente em caso de erro genérico
    return False, [], len(serials)

def tentar_requisicao_bloco(serials_originais, tipo_api, estado, start_idx, end_idx, lote_idx, qtd_lotes, timeout=DEFAULT_REQUEST_TIMEOUT, tentativas_timeout=3):
    """
    Função auxiliar para tentar requisitar um bloco de seriais.
    Retorna (sucesso, dados_retornados, seriais_usados_no_bloco).
    """
    tentativas = 0
    while tentativas < 1: # A lógica original tentava apenas 1 vez aqui, o loop de tentativas está em requisitar_lote
        success, data, usados = requisitar_lote(
            serials_originais[start_idx:end_idx], tipo_api, estado, lote_idx=lote_idx, total_lotes=qtd_lotes, timeout=timeout, tentativas_timeout=tentativas_timeout
        )
        tentativas += 1
        if success:
            return True, data, usados
    return False, [], end_idx - start_idx # Retorna a quantidade de seriais que foram tentados

def modo_requisitar_lotes(
    serials,
    estado,
    tipo_api,
    step,
    max_workers,
    ajuste_step,
    tentativas_timeout,
    timeout=DEFAULT_REQUEST_TIMEOUT,
    progress_callback=None,
    modo='sequencial'
):
    """
    Orquestra as requisições de lotes em modo sequencial ou paralelo.
    """
    import time

    total = len(serials)
    modo_legivel = "Sequencial" if modo == "sequencial" else "Paralelo"
    resultados = []
    step_atual = step
    start = 0
    log_inicio(tipo_api, modo_legivel, total, step, lotes_total) # Passa lotes_total como argumento
    lote_timestamps = []
    seriais_processados = 0

    while start < total:
        lote_timestamps.append(time.time())

        if modo == "sequencial":
            lote_idx = (start // step_atual) + 1
            end = min(total, start + step_atual)
            qtd_lotes = lotes_total(total, step_atual)
            success, data, usados = tentar_requisicao_bloco(
                serials, tipo_api, estado, start, end, lote_idx, qtd_lotes,
                timeout=timeout, tentativas_timeout=tentativas_timeout
            )
            if success:
                resultados.extend(data)
                start += usados
                seriais_processados += usados
                if progress_callback:
                    progress_callback(min(seriais_processados, total), total)
            else:
                if step_atual > 1:
                    step_atual = step_autoajustar(step_atual, ajuste_step)
                    adicionar_log(f"[Auto-Ajuste] Reduzindo lote para {step_atual} seriais.")
                else:
                    adicionar_log(
                        f"Lote {start+1}-{end} falhou mesmo com step mínimo (1 serial); pulando esse serial."
                    )
                    start += 1
                    seriais_processados += 1
                    if progress_callback:
                        progress_callback(min(seriais_processados, total), total)

        else:  # modo == "paralelo"
            # Gerar lotes para a iteração atual
            current_serials_chunk = serials[start:]
            lotes_para_processar = dividir_lotes(current_serials_chunk, step_atual)
            qtd_lotes_chunk = len(lotes_para_processar)
            
            # Mapear os índices de início dos lotes no array original de seriais
            indices_ini_originais = [start + i * step_atual for i in range(qtd_lotes_chunk)]
            
            lotes_falhados_indices = []
            ret_lotes_temp = [[] for _ in lotes_para_processar]
            lote_processados_count = [0 for _ in lotes_para_processar]

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for idx_chunk, ini_original in enumerate(indices_ini_originais):
                    end_original = min(total, ini_original + step_atual)
                    futures.append(
                        (executor.submit(
                            tentar_requisicao_bloco, serials, tipo_api, estado,
                            ini_original, end_original, idx_chunk + 1, qtd_lotes_chunk,
                            timeout, tentativas_timeout
                        ), idx_chunk)
                    )

                for future, idx_chunk in futures:
                    try:
                        success, data, usados = future.result()
                        if success:
                            ret_lotes_temp[idx_chunk] = data
                            lote_processados_count[idx_chunk] = usados
                        else:
                            lotes_falhados_indices.append(idx_chunk)
                            # Mesmo quando falha, considerar como processados para fins de progresso
                            tamanho_lote_real = min(step_atual, total - indices_ini_originais[idx_chunk])
                            lote_processados_count[idx_chunk] = tamanho_lote_real
                    except Exception as exc:
                        adicionar_log(f"Lote {idx_chunk+1} gerou exception: {exc}")
                        lotes_falhados_indices.append(idx_chunk)
                        tamanho_lote_real = min(step_atual, total - indices_ini_originais[idx_chunk])
                        lote_processados_count[idx_chunk] = tamanho_lote_real
                    
                    # Atualizar o progresso após cada lote ser concluído (seja sucesso ou falha)
                    seriais_processados += lote_processados_count[idx_chunk]
                    if progress_callback:
                        progress_callback(min(seriais_processados, total), total)

            # Consolidar resultados e ajustar 'start'
            for idx_chunk, data in enumerate(ret_lotes_temp):
                if idx_chunk not in lotes_falhados_indices: # Adicionar apenas lotes bem-sucedidos
                    resultados.extend(data)
            
            # Avançar 'start' pelo total de seriais que foram *tentados* nesta iteração
            # Isso garante que o loop eventualmente termine, mesmo com falhas
            start += sum(lote_processados_count)

            if lotes_falhados_indices and step_atual > 1:
                step_atual = step_autoajustar(step_atual, ajuste_step)
                adicionar_log(f"[Auto-Ajuste] Reduzindo lote para {step_atual} seriais.")
            elif lotes_falhados_indices and step_atual == 1:
                for idx_chunk in lotes_falhados_indices:
                    ini_original = indices_ini_originais[idx_chunk]
                    end_original = min(total, ini_original + step_atual)
                    adicionar_log(
                        f"Lote {ini_original+1}-{end_original} falhou mesmo com step mínimo (1 serial); pulando esses seriais."
                    )
            
    # Garantir que o progresso seja 100% ao final
    if progress_callback:
        progress_callback(total, total)

    # **CORREÇÃO:** Removido adicionar_log como argumento
    calcular_tempo_medio_entre_requisicoes(lote_timestamps, formatar_tempo)
    return resultados