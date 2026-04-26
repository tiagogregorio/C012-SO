"""
Modelos de dados: Candle, Processo e ResultadoSimulacao.
"""
import threading
import random
import time

from config import PALETA_PROCESSOS, VERD2, AMAR, VERM2

class Candle:
    def __init__(self, o): self.o = self.h = self.l = self.c = o
    def update(self, p):
        self.c = p; self.h = max(self.h, p); self.l = min(self.l, p)

class Processo:
    """Representa uma notícia que entra no sistema como processo."""
    _cnt  = 0
    _lock = threading.Lock()

    def __init__(self, noticia, t_chegada_simulado):
        with Processo._lock:
            Processo._cnt += 1
            self.pid = Processo._cnt

        self.nome      = f"N{self.pid}"
        self.noticia   = noticia
        self.n_acoes   = len(noticia["impacto"])
        self.cor_gantt = PALETA_PROCESSOS[(self.pid - 1) % len(PALETA_PROCESSOS)]

        # Burst time em unidades inteiras (cada ação impactada = 2-3 unidades de CPU)
        self.burst_time = self.n_acoes * random.randint(2, 3)

        self.t_chegada_sim  = t_chegada_simulado
        self.t_chegada_real = time.time()

        # Preenchidos pelo escalonador
        self.t_inicio_cpu_sim = None
        self.t_fim_sim        = None
        self.restante         = self.burst_time
        self.fatias_gantt     = []
        self.estado           = "FILA"

        self.t_inicio_real = None
        self.t_fim_real    = None

    @property
    def tempo_espera_sim(self):
        if self.t_inicio_cpu_sim is None: return 0
        return max(0, self.t_inicio_cpu_sim - self.t_chegada_sim)

    @property
    def turnaround_sim(self):
        if self.t_fim_sim is None: return 0
        return max(0, self.t_fim_sim - self.t_chegada_sim)

    def categoria(self):
        if self.burst_time <= 4:  return "curto"
        if self.burst_time <= 10: return "medio"
        return "longo"

    def cor_categoria(self):
        c = self.categoria()
        if c == "curto": return VERD2
        if c == "medio": return AMAR
        return VERM2

class ResultadoSimulacao:
    """Resultado de uma simulação de escalonamento."""
    def __init__(self, algo, processos, gantt, esperas, turnarounds, media_espera):
        self.algo         = algo
        self.processos    = processos
        self.gantt        = gantt        # [(nome, t_ini, t_fim, cor)]
        self.esperas      = esperas      # {nome: espera}
        self.turnarounds  = turnarounds  # {nome: turnaround}
        self.media_espera = media_espera
        self.formula      = ""           # "(e1+e2+...)/n = X"
