"""
Loops daemon: gerador de processos, escalonador de CPU e loops de mercado.
"""
import time
import random

from config import ACOES, BANCO_NOTICIAS
from models import Processo, Candle
from state import G
from threads import ThreadExecutora
from schedulers import simular_fcfs, simular_sjf, simular_rr

def loop_escalonador():
    """Despacha processos da ready_queue para a CPU ."""
    while True:
        time.sleep(0.2)
        if not G.rodando: continue
        G.cpu_livre.wait(timeout=1.0)
        if not G.cpu_livre.is_set(): continue

        with G.mutex_fila:
            if not G.ready_queue: continue

            if G.algoritmo == "FCFS":
                G.ready_queue.sort(key=lambda p: p.t_chegada_sim)
            elif G.algoritmo == "SJF":
                G.ready_queue.sort(key=lambda p: p.restante)
            # RR: ordem de inserção (não reordena)

            proc = G.ready_queue.pop(0)

        # Marca entrada no CPU
        G.cpu_livre.clear()
        with G.mutex_cpu: G.no_cpu = proc
        proc.estado = "CPU"
        proc.t_inicio_real = time.time()
        if proc.t_inicio_cpu_sim is None:
            with G.mutex_tsim:
                proc.t_inicio_cpu_sim = G.t_sim

        G.ui_q.put({"tipo":"sched","acao":"CPU","proc":proc.nome,
                    "burst":proc.burst_time,"restante":proc.restante,
                    "algo":G.algoritmo,"ts":time.time()})

        t_ini_real = time.time()

        if G.algoritmo in ("FCFS", "SJF"):
            thr = ThreadExecutora(proc)
            thr.start(); thr.join()
            proc.restante = 0

        elif G.algoritmo == "RR":
            thr = ThreadExecutora(proc)
            thr.start()
            # Converte quantum em tempo real (1 unidade = taxa_chegada/3 segundos)
            tempo_real_q = G.quantum_rr * (G.taxa_chegada / 3.0)
            thr.join(timeout=max(0.3, tempo_real_q))
            consumido_real = time.time() - t_ini_real
            # Converte tempo real em unidades simuladas
            unidades_consumidas = max(1, round(consumido_real / (G.taxa_chegada/3.0)))
            proc.restante = max(0, proc.restante - unidades_consumidas)

        t_fim_real = time.time()
        proc.fatias_gantt.append((t_ini_real, t_fim_real))

        if G.algoritmo == "RR" and proc.restante > 0:
            proc.estado = "FILA"
            with G.mutex_fila: G.ready_queue.append(proc)
            G.ui_q.put({"tipo":"sched","acao":"RR_VOLTA","proc":proc.nome,
                        "restante":proc.restante,"ts":time.time()})
        else:
            proc.estado     = "CONCLUÍDO"
            proc.t_fim_real = t_fim_real
            proc.restante   = 0

            with G.mutex_hist:
                G.historico.append(proc)          # sem limite — usado para cálculo
                G.historico_vis.append(proc)
                if len(G.historico_vis) > 20:     # limite apenas para exibição
                    G.historico_vis.pop(0)

            _recalcular_resultados()

            G.ui_q.put({"tipo":"sched","acao":"CONCLUIU","proc":proc.nome,
                        "espera":proc.tempo_espera_sim,"ts":time.time()})

        with G.mutex_cpu: G.no_cpu = None
        G.cpu_livre.set()


def _recalcular_resultados():
    """Recalcula FCFS, SJF e RR sobre o histórico atual (sem limite de processos)."""
    with G.mutex_hist: h = list(G.historico)
    if len(h) < 2: return
    try:
        rf = simular_fcfs(h)
        rs = simular_sjf(h)
        rr = simular_rr(h, G.quantum_rr)
        with G.mutex_res:
            G.res_fcfs = rf
            G.res_sjf  = rs
            G.res_rr   = rr
    except Exception as e:
        print(f"[_recalcular] {e}")

def loop_gerador():
    """Gera novos processos (notícias) na taxa configurada."""
    while True:
        time.sleep(0.3)
        if not G.rodando: continue

        with G.mutex_fila: n = len(G.ready_queue)
        with G.mutex_hist: n_hist = len(G.historico)
        if n >= G.limite_fila: time.sleep(1.0); continue

        noticia = random.choice(BANCO_NOTICIAS)

        with G.mutex_tsim:
            G.t_sim += random.randint(0, 3)
            t_chegada = G.t_sim

        proc = Processo(noticia, t_chegada)
        with G.mutex_fila: G.ready_queue.append(proc)

        G.ui_q.put({"tipo":"sched","acao":"CHEGOU","proc":proc.nome,
                    "burst":proc.burst_time,"chegada":t_chegada,
                    "cat":proc.categoria(),"n_acoes":proc.n_acoes,"ts":time.time()})

        with G.mutex_tsim:
            G.t_sim += random.randint(1, 2)

        time.sleep(G.taxa_chegada * random.uniform(0.7, 1.3))

def loop_candles():
    """Fecha o candle atual e abre um novo a cada 3 segundos."""
    while True:
        time.sleep(3.0)
        if not G.rodando: continue
        with G.mutex_mkt:
            for t in ACOES:
                G.candles[t].append(G.candle_cur[t])
                if len(G.candles[t]) > 60: G.candles[t] = G.candles[t][-60:]
                G.candle_cur[t] = Candle(G.precos[t])

def loop_ruido():
    """Adiciona ruído gaussiano aos preços independente das notícias."""
    while True:
        if not G.rodando: time.sleep(0.5); continue
        time.sleep(random.uniform(0.5, 1.5))
        with G.mutex_mkt:
            for t in G.precos:
                r = random.gauss(0, 0.10 * G.volatilidade)
                G.precos[t] = max(0.50, G.precos[t]*(1+r/100))
                G.candle_cur[t].update(G.precos[t])
