"""
Estado global compartilhado entre todas as threads (class G).
Cada recurso compartilhado tem seu próprio mutex.
"""
import threading
import queue
from collections import deque

from config import ACOES
from models import Candle, Processo

class G:
    # — Escalonamento —
    mutex_fila  = threading.Lock()
    ready_queue = []
    historico   = []          # histórico COMPLETO para cálculo de métricas (sem limite)
    historico_vis = []        # histórico visual limitado (últimos 20 para exibição)
    mutex_hist  = threading.Lock()
    mutex_cpu   = threading.Lock()
    no_cpu      = None
    cpu_livre   = threading.Event()   # set = CPU livre; clear = CPU ocupada

    # Resultados das simulações (recalculados a cada processo concluído)
    res_fcfs  = None
    res_sjf   = None
    res_rr    = None
    mutex_res = threading.Lock()

    # Contador de tempo simulado (unidades inteiras)
    t_sim      = 0
    mutex_tsim = threading.Lock()

    # — Mercado (seção crítica dos preços) —
    mutex_mkt  = threading.Lock()
    precos     = {t: d["preco"] for t, d in ACOES.items()}
    candles    = {t: [] for t in ACOES}
    candle_cur = {t: Candle(d["preco"]) for t, d in ACOES.items()}
    feed_exec  = deque(maxlen=5)
    colisoes   = 0
    races      = 0
    total_exec = 0

    # — Configurações —
    algoritmo    = "FCFS"
    quantum_rr   = 3
    taxa_chegada = 5.0
    limite_fila  = 8
    volatilidade = 1.0
    rodando      = False
    modo_sync    = True

    # — Threads executoras —
    mutex_thr = threading.Lock()
    threads_ex = []

    # — Fila de eventos para a UI —
    ui_q = queue.Queue()

    @classmethod
    def reset(cls):
        with cls.mutex_fila: cls.ready_queue.clear()
        with cls.mutex_hist: cls.historico.clear(); cls.historico_vis.clear()
        with cls.mutex_cpu:  cls.no_cpu = None
        with cls.mutex_res:  cls.res_fcfs = cls.res_sjf = cls.res_rr = None
        with cls.mutex_tsim: cls.t_sim = 0
        with cls.mutex_mkt:
            for t, d in ACOES.items():
                cls.precos[t]     = d["preco"]
                cls.candles[t]    = []
                cls.candle_cur[t] = Candle(d["preco"])
            cls.feed_exec  = deque(maxlen=5)
            cls.colisoes   = 0; cls.races = 0; cls.total_exec = 0
        cls.cpu_livre.set()
        Processo._cnt = 0
