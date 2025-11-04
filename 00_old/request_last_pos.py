## request_last_pos.py
#
#import json
#import requests
#from time import sleep
#from concurrent.futures import ThreadPoolExecutor, as_completed
#from logs import adicionar_log, log_inicio
#from utils import (
#    dividir_lotes,
#    step_autoajustar,
#    lotes_total,
#    calcular_tempo_medio_entre_requisicoes,
#    formatar_tempo
#)
#
#def preparar_requisicao(tipo_api, serials, jwt_token, user_login, user_id, cookie_dict=None):
#    base_url = "https://mognotst.ceabs.com.br"
#    endpoints = {
#        "rastreadores": ("/api/tools/getLastPosition/2", "/paginas/gps/pesquisaultimoevento.html"),
#        "iscas": ("/api/tools/rf/getLastPosition/2", "/paginas/rf/pesquisaultimoeventorf.html")
#    }
#    endpoint, referer = endpoints.get(tipo_api, (None, None))
#    if not endpoint:
#        raise ValueError("tipo_api inválido")
#    url = base_url + endpoint
#    cookie_items = [
#        f"login={user_login}",
#        f"userId={user_id}",
#        f"Authorization=Bearer {jwt_token}"
#    ]
#    if cookie_dict:
#        for k, v in cookie_dict.items():
#            if f"{k}=" not in "".join(cookie_items):
#                cookie_items.append(f"{k}={v}")
#    if tipo_api == "iscas" and ("ztype=2" not in ";".join(cookie_items)):
#        cookie_items.append("ztype=2")
#    cookie_header = "; ".join(cookie_items)
#    headers = {
#        "Cookie": cookie_header,
#        "Content-Type": "application/json;charset=UTF-8",
#        "Referer": referer,
#        "Accept": "application/json, text/plain, */*"
#    }
#    if tipo_api == "iscas":
#        payload = ";".join(serials)
#    else:
#        payload = json.dumps({"serial": ";".join(serials), "filtro": ""})
#    return url, headers, payload
#
#def requisitar_lote(serials, tipo_api, estado, lote_idx=1, total_lotes=1, timeout=15, tentativas_timeout=3):
#    jwt_token = estado['jwt_token']
#    user_login = estado['user_login']
#    user_id = estado['user_id']
#    cookie_dict = estado.get('cookie_dict', None)
#    url, headers, payload = preparar_requisicao(
#        tipo_api, serials, jwt_token, user_login, user_id, cookie_dict
#    )
#    for tentativa in range(1, tentativas_timeout + 1):
#        try:
#            r = requests.post(url, headers=headers, data=payload, timeout=timeout)
#            if r.status_code == 200:
#                dados = r.json()
#                adicionar_log(
#                    f"Lote {lote_idx}/{total_lotes} [{len(serials)}] ✅ OK - "
#                    f"{len(dados) if isinstance(dados, list) else 0}/{len(serials)} seriais válidos"
#                )
#                return True, dados, len(serials)
#            else:
#                adicionar_log(
#                    f"Lote {lote_idx}/{total_lotes} [{len(serials)}] ❌ falhou: status {r.status_code} ({r.text[:100]})"
#                )
#                if r.status_code in [400, 413, 500]:
#                    return False, [], len(serials)
#        except requests.Timeout:
#            adicionar_log(
#                f"Lote {lote_idx}/{total_lotes} [{len(serials)}] ❌ timeout (tentativa {tentativa}/{tentativas_timeout})"
#            )
#            if tentativa == tentativas_timeout:
#                adicionar_log(f"Lote {lote_idx}/{total_lotes} [{len(serials)}] cancelado após {tentativas_timeout} timeouts.")
#        except Exception as e:
#            adicionar_log(f"Erro no lote {lote_idx}: {e}")
#            sleep(2)
#    return False, [], len(serials)
#
#def tentar_requisicao_bloco(serials, tipo_api, estado, start, end, lote_idx, qtd_lotes, timeout=15, tentativas_timeout=3):
#    tentativas = 0
#    while tentativas < 1:
#        success, data, usados = requisitar_lote(
#            serials[start:end], tipo_api, estado, lote_idx=lote_idx, total_lotes=qtd_lotes, timeout=timeout, tentativas_timeout=tentativas_timeout
#        )
#        tentativas += 1
#        if success:
#            return True, data, usados
#    return False, [], end - start
#
#def modo_requisitar_lotes(
#    serials,
#    estado,
#    tipo_api,
#    step=40,
#    max_workers=4,
#    ajuste_step=10,
#    tentativas_timeout=3,
#    timeout=15,
#    progress_callback=None,
#    modo='sequencial'  # aceita 'sequencial' ou 'paralelo'
#):
#    """
#    Requisita lotes em modo sequencial ou paralelo.
#    Parâmetros:
#        - serials: lista de seriais
#        - estado/tipo_api: conforme original
#        - step: tamanho do bloco inicial
#        - max_workers: apenas para modo paralelo
#        - ajuste_step: decremento no auto-ajuste
#        - tentativas_timeout: tentativas por lote
#        - timeout: timeout de requisição
#        - progress_callback: função de progresso
#        - modo: 'sequencial' ou 'paralelo'
#    """
#    import time  # apenas para lote_timestamps (compatibilidade original)
#
#    total = len(serials)
#    modo_legivel = "Sequencial" if modo == "sequencial" else "Paralelo"
#    resultados = []
#    step_atual = step
#    start = 0
#    log_inicio(tipo_api, modo_legivel, total, step, adicionar_log)
#    lote_timestamps = []
#
#    while start < total:
#        lote_timestamps.append(time.time())
#
#        if modo == "sequencial":
#            lote_idx = (start // step_atual) + 1
#            end = min(total, start + step_atual)
#            qtd_lotes = lotes_total(total, step_atual)
#            success, data, usados = tentar_requisicao_bloco(
#                serials, tipo_api, estado, start, end, lote_idx, qtd_lotes,
#                timeout=timeout, tentativas_timeout=tentativas_timeout
#            )
#            if success:
#                resultados.extend(data)
#                start += usados
#                if progress_callback:
#                    progress_callback(min(start, total), total)
#            else:
#                if step_atual > 1:
#                    step_atual = step_autoajustar(step_atual, ajuste_step)
#                    adicionar_log(f"[Auto-Ajuste] Reduzindo lote para {step_atual} seriais.")
#                else:
#                    adicionar_log(
#                        f"Lote {start+1}-{end} falhou mesmo com step mínimo (1 serial); pulando esse serial."
#                    )
#                    start += 1
#                    if progress_callback:
#                        progress_callback(min(start, total), total)
#
#        else:  # modo == "paralelo"
#            lotes = dividir_lotes(serials[start:], step_atual)
#            qtd_lotes = len(lotes)
#            indices_ini = [start + i*step_atual for i in range(qtd_lotes)]
#            lotes_falhados = []
#            ret_lotes = [[] for _ in lotes]
#
#            with ThreadPoolExecutor(max_workers=max_workers) as executor:
#                future_to_idx = {
#                    executor.submit(
#                        tentar_requisicao_bloco, serials, tipo_api, estado,
#                        ini, min(total, ini+step_atual), idx+1, qtd_lotes,
#                        timeout, tentativas_timeout
#                    ): idx
#                    for idx, ini in enumerate(indices_ini)
#                }
#                for future in as_completed(future_to_idx):
#                    idx = future_to_idx[future]
#                    try:
#                        success, data, *_ = future.result()
#                        if success:
#                            ret_lotes[idx] = data
#                        else:
#                            lotes_falhados.append(idx)
#                    except Exception as exc:
#                        adicionar_log(f"Lote {idx+1} gerou exception: {exc}")
#                        lotes_falhados.append(idx)
#
#            if not lotes_falhados:
#                for idx, data in enumerate(ret_lotes):
#                    resultados.extend(data)
#                    start = min(total, start + step_atual)
#                    if progress_callback:
#                        progress_callback(min(start, total), total)
#            else:
#                if step_atual > 1:
#                    step_atual = step_autoajustar(step_atual, ajuste_step)
#                    adicionar_log(f"[Auto-Ajuste] Reduzindo lote para {step_atual} seriais.")
#                else:
#                    for idx in lotes_falhados:
#                        ini = indices_ini[idx]
#                        end = min(total, ini + step_atual)
#                        adicionar_log(
#                            f"Lote {ini+1}-{end} falhou mesmo com step mínimo (1 serial); pulando esses seriais."
#                        )
#                    start = min(total, start + (qtd_lotes * step_atual))
#                    if progress_callback:
#                        progress_callback(min(start, total), total)
#
#    if progress_callback:
#        progress_callback(total, total)
#
#    calcular_tempo_medio_entre_requisicoes(lote_timestamps, adicionar_log, formatar_tempo)
#    return resultados
#
## -- Uso fica assim:
## Para modo sequencial:
##    modo_requisitar_lotes(serials, estado, tipo_api, step=20, modo='sequencial')
## Para modo paralelo:
##    modo_requisitar_lotes(serials, estado, tipo_api, step=40, max_workers=6, modo='paralelo')





# request_last_pos.py (correção para atualização da barra de progresso no modo paralelo)

import json
import requests
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from logs import adicionar_log, log_inicio
from utils import (
    dividir_lotes,
    step_autoajustar,
    lotes_total,
    calcular_tempo_medio_entre_requisicoes,
    formatar_tempo
)

def preparar_requisicao(tipo_api, serials, jwt_token, user_login, user_id, cookie_dict=None):
    base_url = "https://mognotst.ceabs.com.br"
    endpoints = {
        "rastreadores": ("/api/tools/getLastPosition/2", "/paginas/gps/pesquisaultimoevento.html"),
        "iscas": ("/api/tools/rf/getLastPosition/2", "/paginas/rf/pesquisaultimoeventorf.html")
    }
    endpoint, referer = endpoints.get(tipo_api, (None, None))
    if not endpoint:
        raise ValueError("tipo_api inválido")
    url = base_url + endpoint
    cookie_items = [
        f"login={user_login}",
        f"userId={user_id}",
        f"Authorization=Bearer {jwt_token}"
    ]
    if cookie_dict:
        for k, v in cookie_dict.items():
            if f"{k}=" not in "".join(cookie_items):
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

def requisitar_lote(serials, tipo_api, estado, lote_idx=1, total_lotes=1, timeout=15, tentativas_timeout=3):
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
                if r.status_code in [400, 413, 500]:
                    return False, [], len(serials)
        except requests.Timeout:
            adicionar_log(
                f"Lote {lote_idx}/{total_lotes} [{len(serials)}] ❌ timeout (tentativa {tentativa}/{tentativas_timeout})"
            )
            if tentativa == tentativas_timeout:
                adicionar_log(f"Lote {lote_idx}/{total_lotes} [{len(serials)}] cancelado após {tentativas_timeout} timeouts.")
        except Exception as e:
            adicionar_log(f"Erro no lote {lote_idx}: {e}")
            sleep(2)
    return False, [], len(serials)

def tentar_requisicao_bloco(serials, tipo_api, estado, start, end, lote_idx, qtd_lotes, timeout=15, tentativas_timeout=3):
    tentativas = 0
    while tentativas < 1:
        success, data, usados = requisitar_lote(
            serials[start:end], tipo_api, estado, lote_idx=lote_idx, total_lotes=qtd_lotes, timeout=timeout, tentativas_timeout=tentativas_timeout
        )
        tentativas += 1
        if success:
            return True, data, usados
    return False, [], end - start

def modo_requisitar_lotes(
    serials,
    estado,
    tipo_api,
    step=40,
    max_workers=4,
    ajuste_step=10,
    tentativas_timeout=3,
    timeout=15,
    progress_callback=None,
    modo='sequencial'  # aceita 'sequencial' ou 'paralelo'
):
    """
    Requisita lotes em modo sequencial ou paralelo.
    Parâmetros:
        - serials: lista de seriais
        - estado/tipo_api: conforme original
        - step: tamanho do bloco inicial
        - max_workers: apenas para modo paralelo
        - ajuste_step: decremento no auto-ajuste
        - tentativas_timeout: tentativas por lote
        - timeout: timeout de requisição
        - progress_callback: função de progresso
        - modo: 'sequencial' ou 'paralelo'
    """
    import time  # apenas para lote_timestamps (compatibilidade original)

    total = len(serials)
    modo_legivel = "Sequencial" if modo == "sequencial" else "Paralelo"
    resultados = []
    step_atual = step
    start = 0
    log_inicio(tipo_api, modo_legivel, total, step, adicionar_log)
    lote_timestamps = []
    seriais_processados = 0  # Contador para acompanhar o progresso

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
                seriais_processados += usados  # Atualizar contador de processados
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
                    seriais_processados += 1  # Contar como processado mesmo com falha
                    if progress_callback:
                        progress_callback(min(seriais_processados, total), total)

        else:  # modo == "paralelo"
            lotes = dividir_lotes(serials[start:], step_atual)
            qtd_lotes = len(lotes)
            indices_ini = [start + i*step_atual for i in range(qtd_lotes)]
            lotes_falhados = []
            ret_lotes = [[] for _ in lotes]
            lote_processados = [0 for _ in lotes]  # Armazenar quantidade de seriais processados por lote

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                # Submeter todas as tarefas primeiro
                for idx, ini in enumerate(indices_ini):
                    futures.append(
                        (executor.submit(
                            tentar_requisicao_bloco, serials, tipo_api, estado,
                            ini, min(total, ini+step_atual), idx+1, qtd_lotes,
                            timeout, tentativas_timeout
                        ), idx)
                    )
                
                # Processar os resultados à medida que são concluídos
                for future, idx in futures:
                    try:
                        success, data, usados = future.result()
                        if success:
                            ret_lotes[idx] = data
                            lote_processados[idx] = usados
                            # Incrementar contador e atualizar barra de progresso a cada lote concluído
                            seriais_processados += usados
                            if progress_callback:
                                progress_callback(min(seriais_processados, total), total)
                        else:
                            lotes_falhados.append(idx)
                            # Mesmo quando falha, considerar como processados para fins de progresso
                            tamanho_lote = min(step_atual, total-indices_ini[idx])
                            lote_processados[idx] = tamanho_lote
                            seriais_processados += tamanho_lote
                            if progress_callback:
                                progress_callback(min(seriais_processados, total), total)
                    except Exception as exc:
                        adicionar_log(f"Lote {idx+1} gerou exception: {exc}")
                        lotes_falhados.append(idx)
                        # Em caso de exceção, também considerar como processados
                        tamanho_lote = min(step_atual, total-indices_ini[idx])
                        lote_processados[idx] = tamanho_lote
                        seriais_processados += tamanho_lote
                        if progress_callback:
                            progress_callback(min(seriais_processados, total), total)

            if not lotes_falhados:
                for idx, data in enumerate(ret_lotes):
                    resultados.extend(data)
                start = min(total, start + sum(lote_processados))  # Avançar pelo total processado
            else:
                if step_atual > 1:
                    step_atual = step_autoajustar(step_atual, ajuste_step)
                    adicionar_log(f"[Auto-Ajuste] Reduzindo lote para {step_atual} seriais.")
                else:
                    for idx in lotes_falhados:
                        ini = indices_ini[idx]
                        end = min(total, ini + step_atual)
                        adicionar_log(
                            f"Lote {ini+1}-{end} falhou mesmo com step mínimo (1 serial); pulando esses seriais."
                        )
                    # Avançar pelo que foi processado, independente de sucesso ou falha
                    start = min(total, start + sum(lote_processados))

    # Garantir que o progresso seja 100% ao final
    if progress_callback:
        progress_callback(total, total)

    calcular_tempo_medio_entre_requisicoes(lote_timestamps, adicionar_log, formatar_tempo)
    return resultados
