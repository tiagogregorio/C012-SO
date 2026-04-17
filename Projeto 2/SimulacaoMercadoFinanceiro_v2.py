import tkinter as tk
from tkinter import ttk
import threading
import random
import time
import os
from collections import deque
from datetime import datetime
import queue

#  DETECÇÃO DE RESOLUÇÃO
def _detectar():
    tmp = tk.Tk(); tmp.withdraw()
    sw = tmp.winfo_screenwidth(); sh = tmp.winfo_screenheight()
    tmp.destroy()
    f = max(0.60, min(sh / 1080.0, 2.0))
    return f, sw, sh, min(int(1560 * f), sw - 30), min(int(980 * f), sh - 50)

SCALE, SCR_W, SCR_H, WIN_W, WIN_H = _detectar()
def S(x): return max(1, int(x * SCALE))
def F(x): return max(7, int(x * SCALE))

LIMITE_AVISO, LIMITE_PERIGO, LIMITE_MAXIMO = 9, 15, 20

#  DADOS DO MERCADO
ACOES = {
    "VALE3": {"nome": "Vale S.A.",      "preco": 68.50, "cor": "#4FC3F7"},
    "PETR4": {"nome": "Petrobras PN",   "preco": 38.20, "cor": "#FF8A65"},
    "ITUB4": {"nome": "Itaú Unibanco",  "preco": 34.80, "cor": "#A5D6A7"},
    "BBDC4": {"nome": "Bradesco PN",    "preco": 14.90, "cor": "#CE93D8"},
    "B3SA3": {"nome": "B3 S.A.",        "preco": 11.40, "cor": "#FFD54F"},
    "ABEV3": {"nome": "Ambev S.A.",     "preco": 12.80, "cor": "#80DEEA"},
    "MGLU3": {"nome": "Magazine Luiza", "preco": 9.10,  "cor": "#F48FB1"},
    "WEGE3": {"nome": "WEG S.A.",       "preco": 51.30, "cor": "#BCAAA4"},
    "RENT3": {"nome": "Localiza",       "preco": 43.60, "cor": "#EF9A9A"},
    "SUZB3": {"nome": "Suzano S.A.",    "preco": 57.20, "cor": "#B39DDB"},
}
TICKERS = list(ACOES.keys())

BANCO_NOTICIAS = [
    {"data": "2019-01-25", "titulo": "Rompimento da Barragem de Brumadinho", "impacto": {"VALE3": -24.5}, "intensidade": "CRÍTICA", "cor": "#FF1744", "fonte": "Reuters"},
    {"data": "2021-03-10", "titulo": "China anuncia pacote de US$ 1,4 tri", "impacto": {"VALE3": +8.3, "SUZB3": +2.1}, "intensidade": "CRÍTICA", "cor": "#69F0AE", "fonte": "Bloomberg"},
    {"data": "2022-02-24", "titulo": "Petróleo Brent ultrapassa US$ 100", "impacto": {"PETR4": +9.2, "VALE3": +2.3}, "intensidade": "CRÍTICA", "cor": "#FF8C00", "fonte": "WSJ"},
    {"data": "2020-03-18", "titulo": "COVID-19: Ibovespa aciona circuit breaker", "impacto": {"PETR4": -12.3, "VALE3": -9.8, "ITUB4": -11.2, "BBDC4": -10.5, "MGLU3": -13.1, "ABEV3": -8.4, "WEGE3": -9.6, "RENT3": -12.8, "B3SA3": -11.0, "SUZB3": -7.2}, "intensidade": "CRÍTICA", "cor": "#FF1744", "fonte": "B3"},
    {"data": "2024-09-18", "titulo": "Fed corta juros em 0,5 p.p.", "impacto": {"ITUB4": +3.2, "B3SA3": +3.8, "MGLU3": +5.1}, "intensidade": "ALTA", "cor": "#69F0AE", "fonte": "Reuters"},
    {"data": "GERADA", "titulo": "[IA] Guerra escala no Oriente Médio", "impacto": {"PETR4": +8.9, "ABEV3": -1.5, "MGLU3": -2.3}, "intensidade": "CRÍTICA", "cor": "#FF8C00", "fonte": "IA"},
]

BG, BG2, BG3, BG4 = "#0A0E17", "#0D1220", "#111827", "#1C2333"
VERDE, VERD2, VERM, VERM2 = "#00E676", "#00C853", "#FF1744", "#D50000"
AMAR, AZUL, LARA, CIAN, ROXO = "#FFD740", "#40C4FF", "#FF8A65", "#80DEEA", "#CE93D8"
TEXTO, TEXT2, TEXT3, GRADE = "#E2E8F0", "#64748B", "#94A3B8", "#1E293B"
FM = "Courier New"

ESTADOS = {
    "NOVA": ("#607D8B", "Thread criada, não iniciada"),
    "PRONTA": ("#90A4AE", "Aguardando CPU (RUNNABLE)"),
    "DISPUTANDO": (AMAR, "Tentando adquirir o MUTEX"),
    "EXECUTANDO": (VERDE, "Acesso exclusivo (MUTEX OK)"),
    "CALCULANDO": (AZUL, "Lendo Data Section"),
    "APLICANDO": (LARA, "Escrevendo na Seção Crítica"),
    "LIBERANDO": (CIAN, "Liberando o MUTEX"),
    "TERMINADA": (TEXT2, "Thread encerrada"),
    "RACE": (VERM, "⚠ RACE CONDITION (S/ Mutex)"),
}

class Candle:
    def __init__(self, o): self.o = self.h = self.l = self.c = o
    def update(self, p): self.c = p; self.h = max(self.h, p); self.l = min(self.l, p)

#  ALGORITMOS DE ESCALONAMENTO E FILA
class Processo:
    _cnt = 0
    _lock = threading.Lock()
    def __init__(self, noticia):
        with Processo._lock: Processo._cnt += 1; self.pid = Processo._cnt
        self.burst_time = len(noticia["impacto"]) * random.uniform(0.8, 1.5) 
        self.arrival_time = time.time()
        self.nome = f"P{self.pid}"
        self.noticia = noticia

def fcfs(processos):
    if not processos: return 0.0, 0.0
    fila = sorted(processos, key=lambda p: p.arrival_time)
    tempo_atual, esperas, respostas = fila[0].arrival_time, [], []
    for p in fila:
        tempo_atual = max(tempo_atual, p.arrival_time)
        esperas.append(tempo_atual - p.arrival_time)
        respostas.append(tempo_atual - p.arrival_time)
        tempo_atual += p.burst_time
    return sum(esperas) / len(esperas), sum(respostas) / len(respostas)

def sjf(processos):
    if not processos: return 0.0, 0.0
    fila = sorted(processos, key=lambda p: p.arrival_time)
    tempo_atual, prontos, restantes, esperas, respostas = fila[0].arrival_time, [], list(fila), [], []
    while restantes or prontos:
        novos = [p for p in restantes if p.arrival_time <= tempo_atual]
        for p in novos: prontos.append(p); restantes.remove(p)
        if not prontos: tempo_atual = restantes[0].arrival_time; continue
        prontos.sort(key=lambda p: p.burst_time)
        escolhido = prontos.pop(0)
        esperas.append(tempo_atual - escolhido.arrival_time)
        respostas.append(tempo_atual - escolhido.arrival_time)
        tempo_atual += escolhido.burst_time
    return sum(esperas) / len(esperas), sum(respostas) / len(respostas)

def round_robin(processos, quantum=1.5):
    if not processos: return 0.0, 0.0
    fila = sorted(processos, key=lambda p: p.arrival_time)
    tempo_atual = fila[0].arrival_time
    restantes = {p.pid: p.burst_time for p in fila}
    chegadas = {p.pid: p.arrival_time for p in fila}
    inicio_exec, fila_rr, esperas, respostas = {}, list(fila), {}, {}
    while fila_rr:
        p = fila_rr.pop(0)
        if p.pid not in inicio_exec: 
            inicio_exec[p.pid] = tempo_atual
            respostas[p.pid] = tempo_atual - chegadas[p.pid] 
            
        fatia = min(quantum, restantes[p.pid])
        tempo_atual += fatia
        restantes[p.pid] -= fatia
        
        if restantes[p.pid] > 0.001: fila_rr.append(p)
        else: esperas[p.pid] = (tempo_atual - chegadas[p.pid]) - p.burst_time 
            
    return sum(esperas.values()) / len(esperas), sum(respostas.values()) / len(respostas)

#  ESTADO GLOBAL
class EstadoMercado:
    def __init__(self):
        self.lock = threading.Lock() 
        self.precos = {t: d["preco"] for t, d in ACOES.items()}
        self.candles = {t: [] for t in ACOES}
        self.candle_cur = {t: Candle(d["preco"]) for t, d in ACOES.items()}
        self.noticias = deque(maxlen=8)
        self.colisoes, self.total, self.travamentos, self.races = 0, 0, 0, 0
        self.rodando = False
        self.pausar_noticias = False 
        self.num_threads = 4
        self.volatilidade = 1.0
        self.candle_secs = 2.0
        self.ui_q = queue.Queue()
        self.threads_vivas = []
        self.threads_lock = threading.Lock()
        self.modo_sync = True  
        self.fila_processos = []
        
        self.historico_fcfs = []; self.resp_fcfs = []
        self.historico_sjf = [];  self.resp_sjf = []
        self.historico_rr = [];   self.resp_rr = []
        
        self.sched_lock = threading.Lock()
        self.quantum_rr = 1.5
        
        self.evento_fila = threading.Event()
        self.evento_fila.set() 

estado = EstadoMercado()
PID = os.getpid()

#  THREAD DE NOTÍCIA
class ThreadNoticia(threading.Thread):
    _cnt = 0
    _cnt_lock = threading.Lock()

    def __init__(self):
        super().__init__(daemon=True)
        with ThreadNoticia._cnt_lock: ThreadNoticia._cnt += 1; self.tid = ThreadNoticia._cnt
        self.noticia = random.choice(BANCO_NOTICIAS); self.nome = f"P{self.tid}"
        self.estado_thr = "NOVA"; self.ts_inicio = time.time(); self.so_ident = None; self.impactos = {}
        try: self.processo = Processo(self.noticia)
        except Exception: self.processo = None

    def _log(self, estado_thr, detalhe=""):
        self.estado_thr = estado_thr
        try: estado.ui_q.put({"tid": self.tid, "nome": self.nome, "estado": estado_thr, "detalhe": detalhe, "ts": time.time(), "noticia": self.noticia["titulo"][:48]})
        except: pass

    def _executar_com_lock(self):
        self._log("DISPUTANDO", "Tentando adquirir o mutex...")
        with estado.lock:
            self._log("EXECUTANDO", f"Mutex adquirido! [colisão #{estado.colisoes+1}]")
            estado.colisoes += 1; estado.total += 1
            self._log("CALCULANDO", f"Ações: {list(self.noticia['impacto'].keys())}"); self.impactos = {}
            for ticker, pct in self.noticia["impacto"].items():
                if ticker in estado.precos:
                    var = (pct + random.gauss(0, 0.7)) * estado.volatilidade
                    novo = max(0.50, estado.precos[ticker] * (1 + var / 100))
                    estado.precos[ticker] = novo; estado.candle_cur[ticker].update(novo); self.impactos[ticker] = var
            time.sleep(0.015)
            self._log("APLICANDO", "  ".join(f"{t}:{v:+.1f}%" for t, v in self.impactos.items()))
            estado.noticias.appendleft({"texto": self.noticia["titulo"], "cor": self.noticia["cor"], "intensidade": self.noticia["intensidade"], "ts": time.time(), "data": self.noticia["data"], "fonte": self.noticia["fonte"], "tickers": list(self.noticia["impacto"].keys())})
        self._log("LIBERANDO", "Mutex liberado")

    def _executar_sem_lock(self):
        self._log("RACE", "⚠ SEM LOCK — Seção crítica desprotegida!")
        estado.total += 1
        for ticker, pct in self.noticia["impacto"].items():
            if ticker in estado.precos:
                preco_lido = estado.precos[ticker] 
                time.sleep(0.01) # Força Race Condition
                var = (pct + random.gauss(0, 0.7)) * estado.volatilidade
                novo = max(0.50, preco_lido * (1 + var / 100))
                estado.precos[ticker] = novo; estado.candle_cur[ticker].update(novo); self.impactos[ticker] = var
        with estado.threads_lock: estado.races += 1
        self._log("APLICANDO", "⚠ Dados corrompidos por Race Condition")
        estado.noticias.appendleft({"texto": "⚠ RACE: " + self.noticia["titulo"], "cor": VERM, "intensidade": "RACE", "ts": time.time(), "data": self.noticia["data"], "fonte": self.noticia["fonte"], "tickers": list(self.noticia["impacto"].keys())})

    def run(self):
        try:
            self.so_ident = self.ident
            with estado.threads_lock: estado.threads_vivas.append(self)
            comparar, snap = False, None
            
            if self.processo is not None:
                with estado.sched_lock:
                    estado.fila_processos.append(self.processo)
                    if estado.evento_fila.is_set() and len(estado.fila_processos) >= 8:
                        snap = list(estado.fila_processos); estado.fila_processos.clear(); comparar = True

            if comparar and snap: _comparar_escalonadores(snap)
            self._log("PRONTA", f"Notícia: {self.noticia['titulo'][:42]}")
            
            if not estado.evento_fila.is_set():
                estado.evento_fila.wait()
                time.sleep(random.uniform(0.1, 1.5))
            
            if estado.modo_sync: self._executar_com_lock()
            else: self._executar_sem_lock()

            dur = time.time() - self.ts_inicio
            self._log("TERMINADA", f"Duração: {dur:.3f}s")
        except Exception as e: print(f"Erro: {e}")
        finally:
            with estado.threads_lock:
                if self in estado.threads_vivas: estado.threads_vivas.remove(self)

def _comparar_escalonadores(processos):
    try:
        w_f, r_f = fcfs(processos); w_s, r_s = sjf(processos); w_rr, r_rr = round_robin(processos, quantum=estado.quantum_rr)
        with estado.sched_lock:
            estado.historico_fcfs.append(w_f); estado.resp_fcfs.append(r_f)
            estado.historico_sjf.append(w_s);  estado.resp_sjf.append(r_s)
            estado.historico_rr.append(w_rr);  estado.resp_rr.append(r_rr)
            if len(estado.historico_fcfs) > 20: 
                estado.historico_fcfs.pop(0); estado.resp_fcfs.pop(0)
                estado.historico_sjf.pop(0); estado.resp_sjf.pop(0)
                estado.historico_rr.pop(0); estado.resp_rr.pop(0)
    except: pass

#  LOOPS BACKGROUND
def loop_candles():
    while True:
        time.sleep(estado.candle_secs)
        if not estado.rodando or estado.pausar_noticias: 
            continue
        with estado.lock:
            for t in ACOES:
                estado.candles[t].append(estado.candle_cur[t])
                if len(estado.candles[t]) > 60: estado.candles[t] = estado.candles[t][-60:]
                estado.candle_cur[t] = Candle(estado.precos[t])

def loop_ruido():
    while True:
        if not estado.rodando: 
            time.sleep(0.3); continue
        n = estado.num_threads; intervalo = max(0.10, 0.35 - n * 0.012)
        time.sleep(random.uniform(intervalo * 0.6, intervalo))
        with estado.lock:
            amp = (0.18 + n * 0.025) * estado.volatilidade
            for t in estado.precos:
                r = random.gauss(0, amp); novo = max(0.50, estado.precos[t] * (1 + r / 100))
                estado.precos[t] = novo; estado.candle_cur[t].update(novo)

def loop_noticias():
    while True:
        if not estado.rodando or estado.pausar_noticias or threading.active_count() > 35: 
            time.sleep(0.5); continue
            
        n = estado.num_threads; qtd = random.randint(n, n + random.randint(0, max(1, n // 2)))
        for _ in range(qtd): ThreadNoticia().start()
        
        if n <= 4: pausa = random.uniform(2.0, 3.0)
        elif n <= 8: pausa = random.uniform(1.0, 1.8)
        elif n <= 13: pausa = random.uniform(0.5, 1.0)
        elif n <= 17: pausa = random.uniform(0.2, 0.5)
        else: pausa = random.uniform(0.10, 0.25)
        time.sleep(pausa)

def loop_espontaneo():
    while True:
        if not estado.rodando or estado.pausar_noticias or threading.active_count() > 35: 
            time.sleep(0.5); continue
        n = estado.num_threads; time.sleep(random.uniform(0.3, max(0.4, 3.5 - n * 0.15)))
        for _ in range(random.randint(1, max(1, n // 2))): ThreadNoticia().start()

def threads_so(): return threading.active_count()

#  UI (INTERFACE GRÁFICA)
def draw_candles(cv, ticker):
    cv.delete("all"); w = cv.winfo_width(); h = cv.winfo_height()
    if w < 20 or h < 10: return
    all_c = list(estado.candles[ticker]) + [estado.candle_cur[ticker]]
    if not all_c: return
    ml, mr, mt, mb = S(50), S(4), S(4), S(14); aw = w - ml - mr; ah = h - mt - mb
    for i in range(5): cv.create_line(ml, mt + i*ah//4, w-mr, mt + i*ah//4, fill=GRADE, dash=(2,4))
    prices = [p for c in all_c for p in (c.h, c.l)]; mn = min(prices)*0.999; mx = max(prices)*1.001
    rng = mx - mn if mx != mn else 1.0
    def py(v): return mt + int((1-(v-mn)/rng)*ah)
    vis = all_c[-max(1, aw//S(8)):]; step = aw / max(len(vis), 1); cw = max(2, min(int(step*0.6), S(12)))
    for i, c in enumerate(vis):
        xc = ml + int(i*step + step/2); cor = VERD2 if c.c >= c.o else VERM2
        cv.create_line(xc, py(c.h), xc, py(c.l), fill=cor, width=1)
        y0 = min(py(c.o), py(c.c)); y1 = max(py(c.o), py(c.c))
        cv.create_rectangle(xc-cw//2, y0, xc+cw//2, max(y1, y0+1), fill=cor, outline=cor)
    for i in range(5): cv.create_text(ml-2, mt+i*ah//4, text=f"{mx-(i/4)*rng:.2f}", font=(FM, F(6)), fill=TEXT2, anchor="e")
    p = estado.precos[ticker]
    cv.create_line(ml, py(p), w-mr, py(p), fill=ACOES[ticker]["cor"], dash=(3,4), width=1)

class HomeBroker:
    def __init__(self, root):
        self.root = root
        root.title(f"MERCADO FINANCEIRO — Escalonamento + Sincronização")
        root.configure(bg=BG); root.geometry(f"{WIN_W}x{WIN_H}"); root.minsize(S(1050), S(700))
        self.acao_sel = tk.StringVar(value="VALE3"); self.prev_p = {t: d["preco"] for t, d in ACOES.items()}
        self.flash = {}; self.var_visual_algo = tk.StringVar(value="FCFS") 
        self._build(); self._update()

    def _build(self):
        self.root.grid_rowconfigure(2, weight=1); self.root.grid_columnconfigure(0, weight=1)
        self._header(); self._controles()
        tk.Frame(self.root, bg=GRADE, height=1).grid(row=1, column=0, sticky="sew")
        self._corpo(); self._footer()

    def _header(self):
        h = tk.Frame(self.root, bg=BG, height=S(46)); h.grid(row=0, column=0, sticky="ew"); h.grid_propagate(False); h.grid_columnconfigure(1, weight=1)
        tk.Label(h, text="MERCADO FINANCEIRO — Escalonamento de CPU + Sincronização", font=(FM, F(10), "bold"), bg=BG, fg=AMAR).grid(row=0, column=0, padx=S(10), pady=S(7), sticky="w")
        info = tk.Frame(h, bg=BG); info.grid(row=0, column=2, padx=S(8), sticky="e")
        self.lbl_stats = tk.Label(info, text="", font=(FM, F(8)), bg=BG, fg=TEXT3); self.lbl_stats.pack(side="left", padx=S(6))
        tk.Label(info, text=f"PID:{PID}", font=(FM, F(9), "bold"), bg=BG, fg=CIAN).pack(side="left", padx=S(6))
        self.lbl_so = tk.Label(info, text="SO: — thr", font=(FM, F(9), "bold"), bg=BG, fg=VERDE); self.lbl_so.pack(side="left", padx=S(6))
        self.lbl_hora = tk.Label(info, text="", font=(FM, F(8)), bg=BG, fg=TEXT2); self.lbl_hora.pack(side="left", padx=S(6))

    def _controles(self):
        c = tk.Frame(self.root, bg=BG2, height=S(54)); c.grid(row=1, column=0, sticky="ew"); c.grid_propagate(False)
        col = 0
        def nxt(): nonlocal col; col += 1; return col - 1

        tk.Label(c, text="THREADS:", font=(FM, F(8), "bold"), bg=BG2, fg=TEXT3).grid(row=0, column=nxt(), padx=(S(4),S(2)), pady=S(14))
        self.var_thr = tk.IntVar(value=4); self.lbl_thr = tk.Label(c, text=" 4", font=(FM, F(12), "bold"), bg=BG2, fg=AMAR, width=3); self.lbl_thr.grid(row=0, column=nxt())
        ttk.Scale(c, from_=1, to=LIMITE_MAXIMO, orient="horizontal", length=S(90), variable=self.var_thr, command=self._on_thr).grid(row=0, column=nxt(), padx=(S(2), S(4)))

        self.lbl_aviso = tk.Label(c, text="", font=(FM, F(8), "bold"), bg=BG2, fg=VERDE, width=15, anchor="w"); self.lbl_aviso.grid(row=0, column=nxt(), padx=S(2))

        tk.Label(c, text="VOL:", font=(FM, F(8), "bold"), bg=BG2, fg=TEXT3).grid(row=0, column=nxt(), padx=(S(2),S(2)))
        self.var_vol = tk.DoubleVar(value=1.0); self.lbl_vol = tk.Label(c, text="1.0×", font=(FM, F(9), "bold"), bg=BG2, fg=LARA, width=4); self.lbl_vol.grid(row=0, column=nxt())
        ttk.Scale(c, from_=0.2, to=5.0, orient="horizontal", length=S(70), variable=self.var_vol, command=lambda v: [setattr(estado, "volatilidade", float(v)), self.lbl_vol.config(text=f"{float(v):.1f}×")]).grid(row=0, column=nxt(), padx=(S(2), S(4)))

        # BOTÃO DO RR VOLTOU AQUI!
        tk.Label(c, text="RR-Q:", font=(FM, F(8), "bold"), bg=BG2, fg=TEXT3).grid(row=0, column=nxt(), padx=(S(2),S(2)))
        self.var_rr = tk.DoubleVar(value=1.5); self.lbl_rr = tk.Label(c, text="1.5s", font=(FM, F(9), "bold"), bg=BG2, fg=ROXO, width=4); self.lbl_rr.grid(row=0, column=nxt())
        ttk.Scale(c, from_=0.5, to=5.0, orient="horizontal", length=S(70), variable=self.var_rr, command=lambda v: [setattr(estado, "quantum_rr", float(v)), self.lbl_rr.config(text=f"{float(v):.1f}s")]).grid(row=0, column=nxt(), padx=(S(2), S(4)))

        self.btn_play = tk.Button(c, text="▶  INICIAR", font=(FM, F(8), "bold"), bg=VERD2, fg=BG, relief="flat", padx=S(4), command=self._toggle_play); self.btn_play.grid(row=0, column=nxt(), padx=S(4))
        self.btn_noticias = tk.Button(c, text="🛑 PARAR NOTÍCIAS", font=(FM, F(8), "bold"), bg="#5D0000", fg=TEXTO, relief="flat", padx=S(4), command=self._toggle_noticias); self.btn_noticias.grid(row=0, column=nxt(), padx=S(4))
        self.btn_sync = tk.Button(c, text="🔒 COM SYNC", font=(FM, F(8), "bold"), bg="#1A3A2A", fg=VERDE, relief="flat", padx=S(4), command=self._toggle_sync); self.btn_sync.grid(row=0, column=nxt(), padx=S(4))
        tk.Button(c, text="↺ RESET", font=(FM, F(8)), bg=BG4, fg=TEXT3, relief="flat", padx=S(2), command=self._reset).grid(row=0, column=nxt(), padx=S(2))

    def _toggle_play(self):
        estado.rodando = not estado.rodando; self.btn_play.config(text="⏸  PAUSAR" if estado.rodando else "▶  INICIAR", bg=AMAR if estado.rodando else VERD2, fg=BG)

    def _toggle_noticias(self):
        estado.pausar_noticias = not estado.pausar_noticias
        self.btn_noticias.config(text="🟢 VOLTAR NOTÍCIAS" if estado.pausar_noticias else "🛑 PARAR NOTÍCIAS", bg=VERD2 if estado.pausar_noticias else "#5D0000", fg=BG if estado.pausar_noticias else TEXTO)

    def _toggle_sync(self):
        estado.modo_sync = not estado.modo_sync; self.btn_sync.config(text="🔒 COM SYNC" if estado.modo_sync else "⚠ SEM SYNC", bg="#1A3A2A" if estado.modo_sync else "#3A1A1A", fg=VERDE if estado.modo_sync else VERM)

    def _on_thr(self, v):
        n = int(float(v)); estado.num_threads = n; self.lbl_thr.config(text=f"{n:2d}")
        self.lbl_aviso.config(text="🔴 PÂNICO!" if n>=LIMITE_PERIGO else "🟡 CAOS!" if n>=LIMITE_AVISO else "🟢 Estável", fg=VERM if n>=LIMITE_PERIGO else AMAR if n>=LIMITE_AVISO else VERDE)

    def _corpo(self):
        corpo = tk.Frame(self.root, bg=BG); corpo.grid(row=2, column=0, sticky="nsew")
        corpo.grid_rowconfigure(0, weight=1); corpo.grid_columnconfigure(0, weight=0); corpo.grid_columnconfigure(1, weight=1); corpo.grid_columnconfigure(2, weight=0)
        self._painel_acoes(corpo); self._painel_central(corpo); self._painel_direito(corpo)

    def _painel_acoes(self, parent):
        f = tk.Frame(parent, bg=BG3, width=S(170)); f.grid(row=0, column=0, sticky="nsew"); f.grid_propagate(False)
        tk.Label(f, text="CARTEIRA", font=(FM, F(8), "bold"), bg=BG3, fg=TEXT2).pack(pady=(S(8), S(4))); self.fa = {}
        for ticker, dados in ACOES.items():
            fr = tk.Frame(f, bg=BG3, cursor="hand2"); fr.pack(fill="x", padx=S(4), pady=S(2)); fr.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            l1 = tk.Label(fr, text=ticker, font=(FM, F(9), "bold"), bg=BG3, fg=dados["cor"], anchor="w"); l1.pack(fill="x", padx=S(4)); l1.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            l2 = tk.Label(fr, text="R$—", font=(FM, F(8)), bg=BG3, fg=TEXT2, anchor="w"); l2.pack(fill="x", padx=S(4)); l2.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            lv = tk.Label(fr, text="—", font=(FM, F(7)), bg=BG3, fg=TEXT2, anchor="w"); lv.pack(fill="x", padx=S(4)); lv.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            self.fa[ticker] = {"f": fr, "l1": l1, "lp": l2, "lv": lv, "ref": dados["preco"]}

    def _painel_central(self, parent):
        f = tk.Frame(parent, bg=BG); f.grid(row=0, column=1, sticky="nsew")
        f.grid_rowconfigure(0, weight=3); f.grid_rowconfigure(1, weight=0); f.grid_rowconfigure(2, weight=1); f.grid_columnconfigure(0, weight=1)

        gf = tk.Frame(f, bg=BG2); gf.grid(row=0, column=0, sticky="nsew", padx=S(4), pady=(S(4), S(2)))
        gf.grid_rowconfigure(1, weight=1); gf.grid_columnconfigure(0, weight=1)
        hdr = tk.Frame(gf, bg=BG2); hdr.grid(row=0, column=0, sticky="ew", padx=S(4))
        self.lbl_hdr = tk.Label(hdr, text="VALE3 — Vale S.A.", font=(FM, F(11), "bold"), bg=BG2, fg=AZUL); self.lbl_hdr.pack(side="left")
        self.lbl_pgrande = tk.Label(hdr, text="R$ —", font=(FM, F(13), "bold"), bg=BG2, fg=VERDE); self.lbl_pgrande.pack(side="right", padx=S(8))
        self.lbl_vgrande = tk.Label(hdr, text="—", font=(FM, F(10)), bg=BG2, fg=TEXT2); self.lbl_vgrande.pack(side="right")
        self.lbl_ohlc = tk.Label(hdr, text="", font=(FM, F(7)), bg=BG2, fg=TEXT2); self.lbl_ohlc.pack(side="right", padx=S(8))
        self.cv_main = tk.Canvas(gf, bg=BG2, highlightthickness=0); self.cv_main.grid(row=1, column=0, sticky="nsew")

        # ─── PAINEL DE ESCALONAMENTO E VISUALIZADOR ───
        sf = tk.Frame(f, bg=BG4, height=S(160)); sf.grid(row=1, column=0, sticky="ew", padx=S(4), pady=S(2)); sf.grid_propagate(False)
        sf.grid_columnconfigure(0, weight=1); sf.grid_columnconfigure(1, weight=1); sf.grid_columnconfigure(2, weight=1)
        
        hdr_sf = tk.Frame(sf, bg=BG4); hdr_sf.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(S(4),0))
        tk.Label(hdr_sf, text="ALGORITMOS DE ESCALONAMENTO", font=(FM, F(8), "bold"), bg=BG4, fg=AMAR).pack(side="left", padx=S(8))
        
        tk.Label(hdr_sf, text="Legenda Fila:  🟩 Rápido   🟨 Médio   🟥 Lento", font=(FM, F(7), "bold"), bg=BG4, fg=TEXT2).pack(side="left", padx=S(10))
        
        for txt, val in [("FCFS", "FCFS"), ("SJF", "SJF"), ("Round Robin", "RR")]:
            tk.Radiobutton(hdr_sf, text=txt, variable=self.var_visual_algo, value=val, bg=BG4, fg=TEXTO, selectcolor=BG2, font=(FM, F(7))).pack(side="left", padx=S(4))
            
        self.btn_pausa_fila = tk.Button(hdr_sf, text="⏸ CONGELAR FILA", font=(FM, F(7), "bold"), bg=AMAR, fg=BG, command=self._toggle_pausa_fila)
        self.btn_pausa_fila.pack(side="right", padx=S(8))
        
        fila_container = tk.Frame(sf, bg=BG3)
        fila_container.grid(row=1, column=0, columnspan=3, sticky="ew", padx=S(8), pady=S(4))
        
        self.cv_fila = tk.Canvas(fila_container, bg=BG3, height=S(35), highlightthickness=0)
        self.scroll_fila = ttk.Scrollbar(fila_container, orient="horizontal", command=self.cv_fila.xview)
        self.cv_fila.configure(xscrollcommand=self.scroll_fila.set)
        
        self.cv_fila.pack(side="top", fill="x", expand=True)
        self.scroll_fila.pack(side="bottom", fill="x")

        f_med = tk.Frame(sf, bg=BG4); f_med.grid(row=2, column=0, columnspan=3, sticky="ew", padx=S(8))
        f_med.grid_columnconfigure(0, weight=1); f_med.grid_columnconfigure(1, weight=1); f_med.grid_columnconfigure(2, weight=1); f_med.grid_columnconfigure(3, weight=0)
        
        fcfs_f = tk.Frame(f_med, bg="#0D1F2D", bd=1, relief="solid"); fcfs_f.grid(row=0, column=0, padx=S(4), pady=S(2), sticky="nsew")
        tk.Label(fcfs_f, text="FCFS", font=(FM, F(9), "bold"), bg="#0D1F2D", fg=AZUL).pack(pady=(S(2),0)); self.lbl_fcfs_esp = tk.Label(fcfs_f, text="Espera Méd: —", font=(FM, F(7), "bold"), bg="#0D1F2D", fg=TEXT2); self.lbl_fcfs_esp.pack(pady=1)
        self.lbl_fcfs_rsp = tk.Label(fcfs_f, text="Resposta Méd: —", font=(FM, F(7), "bold"), bg="#0D1F2D", fg=AZUL); self.lbl_fcfs_rsp.pack(pady=(1, S(2)))
        
        sjf_f = tk.Frame(f_med, bg="#0D2D0D", bd=1, relief="solid"); sjf_f.grid(row=0, column=1, padx=S(4), pady=S(2), sticky="nsew")
        tk.Label(sjf_f, text="SJF", font=(FM, F(9), "bold"), bg="#0D2D0D", fg=VERDE).pack(pady=(S(2),0)); self.lbl_sjf_esp = tk.Label(sjf_f, text="Espera Méd: —", font=(FM, F(7), "bold"), bg="#0D2D0D", fg=VERDE); self.lbl_sjf_esp.pack(pady=1)
        self.lbl_sjf_rsp = tk.Label(sjf_f, text="Resposta Méd: —", font=(FM, F(7), "bold"), bg="#0D2D0D", fg=TEXT2); self.lbl_sjf_rsp.pack(pady=(1, S(2)))
        
        rr_f = tk.Frame(f_med, bg="#2D1A0D", bd=1, relief="solid"); rr_f.grid(row=0, column=2, padx=S(4), pady=S(2), sticky="nsew")
        tk.Label(rr_f, text="Round Robin", font=(FM, F(9), "bold"), bg="#2D1A0D", fg=LARA).pack(pady=(S(2),0)); self.lbl_rr_esp = tk.Label(rr_f, text="Espera Méd: —", font=(FM, F(7), "bold"), bg="#2D1A0D", fg=TEXT2); self.lbl_rr_esp.pack(pady=1)
        self.lbl_rr_rsp = tk.Label(rr_f, text="Resposta Méd: —", font=(FM, F(7), "bold"), bg="#2D1A0D", fg=LARA); self.lbl_rr_rsp.pack(pady=(1, S(2)))
        
        venc_f = tk.Frame(f_med, bg=BG4); venc_f.grid(row=0, column=3, padx=S(6), pady=S(2), sticky="nsew")
        tk.Label(venc_f, text="VENCEDORES:", font=(FM, F(7), "bold"), bg=BG4, fg=TEXT2).pack(pady=(S(2),0))
        self.lbl_venc_esp = tk.Label(venc_f, text="Espera: —", font=(FM, F(8), "bold"), bg=BG4, fg=AMAR); self.lbl_venc_esp.pack()
        self.lbl_venc_rsp = tk.Label(venc_f, text="Respos: —", font=(FM, F(8), "bold"), bg=BG4, fg=AMAR); self.lbl_venc_rsp.pack()

        # Feed
        ff = tk.Frame(f, bg=BG3); ff.grid(row=2, column=0, sticky="nsew", padx=S(4), pady=(S(2), S(4))); ff.grid_columnconfigure(1, weight=1)
        tk.Label(ff, text="FEED DE NOTÍCIAS", font=(FM, F(7), "bold"), bg=BG3, fg=TEXT2).grid(row=0, column=0, columnspan=3, sticky="w", padx=S(6), pady=(S(4), S(2)))
        self.feed = []
        for i in range(5):
            fn = tk.Frame(ff, bg=BG2); fn.grid(row=i+1, column=0, columnspan=3, sticky="ew", padx=S(4), pady=1); fn.grid_columnconfigure(2, weight=1)
            li = tk.Label(fn, text="", font=(FM, F(7), "bold"), bg=BG2, fg=TEXT2, width=7); li.grid(row=0, column=0, padx=S(2))
            ld = tk.Label(fn, text="", font=(FM, F(7)), bg=BG2, fg=TEXT2, width=10); ld.grid(row=0, column=1)
            lt = tk.Label(fn, text="—", font=(FM, F(7)), bg=BG2, fg=TEXT2, anchor="w"); lt.grid(row=0, column=2, sticky="ew", padx=S(2))
            self.feed.append((li, ld, lt, fn))

    def _toggle_pausa_fila(self):
        if estado.evento_fila.is_set(): 
            estado.evento_fila.clear()
            self.btn_pausa_fila.config(text="▶ LIBERAR FILA", bg=VERD2, fg=BG)
        else: 
            estado.evento_fila.set()
            self.btn_pausa_fila.config(text="⏸ CONGELAR FILA", bg=AMAR, fg=BG)
            copia = []
            with estado.sched_lock:
                if len(estado.fila_processos) > 0:
                    copia = list(estado.fila_processos)
                    estado.fila_processos.clear()
            if copia:
                _comparar_escalonadores(copia)

    def _painel_direito(self, parent):
        f = tk.Frame(parent, bg=BG, width=S(310)); f.grid(row=0, column=2, sticky="nsew"); f.grid_propagate(False); f.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style(); style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG3, foreground=TEXT3, font=(FM, F(8), "bold"), padding=[S(10), S(5)])
        style.map("TNotebook.Tab", background=[("selected",BG2)], foreground=[("selected",AMAR)])
        
        nb = ttk.Notebook(f); nb.grid(row=0, column=0, sticky="nsew", padx=S(4), pady=S(4))
        
        # Aba 1: Log Normal
        tab_log = tk.Frame(nb, bg=BG2); nb.add(tab_log, text="⚙️ LOG DO SISTEMA")
        tab_log.grid_rowconfigure(1, weight=1); tab_log.grid_columnconfigure(0, weight=1)
        
        hdr = tk.Frame(tab_log, bg=BG2); hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(hdr, text="ESTADOS (Cap 4)", font=(FM, F(7), "bold"), bg=BG2, fg=TEXT2).pack(side="left", padx=S(4), pady=S(4))
        self.lbl_race = tk.Label(hdr, text="RACE: 0", font=(FM, F(8), "bold"), bg=BG2, fg=TEXT2); self.lbl_race.pack(side="right", padx=S(4))

        self.log_txt = tk.Text(tab_log, font=(FM, F(7)), bg=BG, fg=TEXT3, state="disabled", wrap="none")
        self.log_txt.grid(row=1, column=0, sticky="nsew", padx=S(4), pady=S(4))
        for est, (cor, _) in ESTADOS.items(): self.log_txt.tag_config(est, foreground=cor)
        self.log_txt.tag_config("ts", foreground=TEXT2); self.log_txt.tag_config("tid", foreground=ROXO); self.log_txt.tag_config("det", foreground=TEXT3)

        pf = tk.Frame(tab_log, bg=BG3); pf.grid(row=2, column=0, sticky="ew", padx=S(4), pady=(0, S(4)))
        tk.Label(pf, text="PROCESS VIEWER", font=(FM, F(7), "bold"), bg=BG3, fg=TEXT2).pack(anchor="w", padx=S(4), pady=(S(4), S(2)))
        thr_f = tk.Frame(pf, bg=BG3); thr_f.pack(fill="x", padx=S(4), pady=(0, S(4)))
        
        self.thr_rows = []; cols = ["Thread", "SO-Id", "Estado", "Tmp"]
        for j, h_txt in enumerate(cols): tk.Label(thr_f, text=h_txt, font=(FM, F(6), "bold"), bg=BG3, fg=TEXT2).grid(row=0, column=j, padx=S(2), sticky="w")
        for i in range(5):
            bg_row = BG4 if i % 2 == 0 else BG3
            row = {"bg": bg_row}; cells = {}
            for j, key in enumerate(["tid","so_id","estado","dur"]):
                lbl = tk.Label(thr_f, text="", font=(FM, F(6)), bg=bg_row, fg=TEXT2, anchor="w", width=9); lbl.grid(row=i+1, column=j, padx=S(2), sticky="w"); cells[key] = lbl
            self.thr_rows.append((row, cells))

        # Aba 2: Manual TP2
        tab_ajuda = tk.Frame(nb, bg=BG2); nb.add(tab_ajuda, text="❔ MANUAL TP2")
        tab_ajuda.grid_rowconfigure(0, weight=1); tab_ajuda.grid_columnconfigure(0, weight=1)
        
        ajuda_txt = tk.Text(tab_ajuda, font=(FM, F(8)), bg=BG, fg=TEXTO, wrap="word", padx=S(10), pady=S(10))
        sb = tk.Scrollbar(tab_ajuda, command=ajuda_txt.yview, bg=BG3); ajuda_txt.configure(yscrollcommand=sb.set)
        ajuda_txt.grid(row=0, column=0, sticky="nsew"); sb.grid(row=0, column=1, sticky="ns")
        
        ajuda_txt.tag_config("titulo", font=(FM, F(10), "bold"), foreground=AMAR, spacing1=S(10), spacing3=S(5))
        ajuda_txt.tag_config("sub", font=(FM, F(8), "bold"), foreground=AZUL)
        ajuda_txt.tag_config("verde", foreground=VERDE); ajuda_txt.tag_config("verm", foreground=VERM)
        
        texto_ajuda = [
            ("Ajuda\n\n", "titulo"),
            ("1. SINCRONISMO E RACE CONDITION\n", "sub"),
            ("Por quê corrompe? ", "verde"), ("Sem Mutex, a Thread A lê o preço, mas a Thread B altera antes da A salvar. A salva o preço defasado. (Condição de Corrida).\n", ""),
            ("Solução: ", "verde"), ("O 'COM SYNC' usa `threading.Lock()`. Apenas uma thread domina a Seção Crítica por vez.\n\n", ""),
            
            ("2. ALGORITMOS DE ESCALONAMENTO E MÉTRICAS\n", "sub"),
            ("Por que usar FCFS se ele perde nos tempos? ", "verde"), ("Porque ele garante ZERO Starvation (ninguém morre de fome na fila) e impõe ordem absoluta. Usado no mundo real para Filas de Impressão e Batch bancário (onde interatividade não importa, mas a ordem e certeza de execução sim).\n", ""),
            ("Qual vence? ", "verde"), ("SJF sempre vence no 'Tempo de Espera' (tira os rápidos da frente). Mas o Round Robin salva o 'Tempo de Resposta' (tempo até o programa responder).\n\n", ""),
            
            ("3. TAXA DE CHEGADA E LIMITES (O SO não trava)\n", "sub"),
            ("Long-Term Scheduler: ", "verde"), ("Se o número de Threads bater 35 (limite estipulado), o SO proíbe a criação de novas threads. Isso evita que a RAM estoure e o SO trave.\n\n", ""),
            
            ("4. ESTADOS DA THREAD\n", "sub"),
            ("• DISPUTANDO (Amarelo): ", "sub"), ("Aguardando Mutex.\n", ""),
            ("• EXECUTANDO (Verde): ", "sub"), ("Adquiriu Mutex.\n", ""),
            ("• CALCULANDO (Azul): ", "sub"), ("Na Seção Crítica.\n", ""),
            ("• RACE (Vermelho): ", "sub"), ("Violação! Entrou sem autorização.\n\n", ""),
            ("-------------------------\nFIM DO MANUAL.", "TEXT2")
        ]
        
        for t, tag in texto_ajuda: ajuda_txt.insert("end", t, tag if tag else None)
        ajuda_txt.config(state="disabled")

    def _footer(self):
        ff = tk.Frame(self.root, bg=BG4, height=S(22)); ff.grid(row=3, column=0, sticky="ew"); ff.grid_propagate(False)
        self.lbl_fl = tk.Label(ff, text="", font=(FM, F(7)), bg=BG4, fg=TEXT2); self.lbl_fl.pack(side="left", padx=S(8))
        self.lbl_fr = tk.Label(ff, text="", font=(FM, F(7)), bg=BG4, fg=TEXT2); self.lbl_fr.pack(side="right", padx=S(8))

    def _reset(self):
        estado.rodando = False; self.btn_play.config(text="▶  INICIAR", bg=VERD2, fg=BG)
        estado.pausar_noticias = False; self.btn_noticias.config(text="🛑 PARAR NOTÍCIAS", bg="#5D0000", fg=TEXTO)
        for t in ACOES: 
            estado.precos[t] = ACOES[t]["preco"]; estado.candles[t] = []; estado.candle_cur[t] = Candle(ACOES[t]["preco"])
        estado.colisoes = 0; estado.total = 0; estado.travamentos = 0; estado.races = 0
        with estado.sched_lock: 
            estado.fila_processos.clear(); estado.historico_fcfs.clear(); estado.historico_sjf.clear(); estado.historico_rr.clear()
            estado.resp_fcfs.clear(); estado.resp_sjf.clear(); estado.resp_rr.clear()
        for t in self.fa: self.fa[t]["ref"] = ACOES[t]["preco"]
        self.log_txt.config(state="normal"); self.log_txt.delete("1.0", "end"); self.log_txt.config(state="disabled")
        ThreadNoticia._cnt = 0; Processo._cnt = 0

    def _sel(self, t): self.acao_sel.set(t); self.lbl_hdr.config(text=f"{t} — {ACOES[t]['nome']}")

    def _flush_log(self):
        processados = 0
        try:
            while not estado.ui_q.empty() and processados < 50:
                e = estado.ui_q.get_nowait()
                self.log_txt.config(state="normal")
                ts = datetime.fromtimestamp(e["ts"]).strftime("%H:%M:%S.%f")[:-3]
                est = e["estado"]
                self.log_txt.insert("end", f"[{ts}] ", "ts"); self.log_txt.insert("end", f"{e['nome']:<12}", "tid")
                tag = est if est in ESTADOS else "det"
                self.log_txt.insert("end", f"► {est:<12}", tag)
                if e["detalhe"]: self.log_txt.insert("end", f"  {e['detalhe'][:50]}", "det")
                self.log_txt.insert("end", "\n")
                self.log_txt.config(state="disabled")
                processados += 1
        except queue.Empty: pass
        if processados > 0:
            self.log_txt.config(state="normal"); self.log_txt.see("end")
            if int(self.log_txt.index("end-1c").split(".")[0]) > 400: self.log_txt.delete("1.0", "80.0") 
            self.log_txt.config(state="disabled")

    def _update_proc(self):
        with estado.threads_lock: vivas = list(estado.threads_vivas)
        for i, (row, cells) in enumerate(self.thr_rows):
            if i < len(vivas):
                t = vivas[i]; dur = time.time() - t.ts_inicio
                cor_e, _ = ESTADOS.get(t.estado_thr, (TEXT2, ""))
                cells["tid"].config(text=t.nome, fg=ROXO); cells["so_id"].config(text=str(t.so_ident or "—")[:12], fg=TEXT3)
                cells["estado"].config(text=t.estado_thr, fg=cor_e); cells["dur"].config(text=f"{dur:.2f}s", fg=TEXT2)
                for cv in cells.values(): cv.config(bg=row["bg"])
            else:
                for cv in cells.values(): cv.config(text="")

    def _update_sched(self):
        with estado.sched_lock:
            fila = list(estado.fila_processos)
            h_fcfs = list(estado.historico_fcfs); r_fcfs = list(estado.resp_fcfs)
            h_sjf = list(estado.historico_sjf);   r_sjf = list(estado.resp_sjf)
            h_rr = list(estado.historico_rr);     r_rr = list(estado.resp_rr)

        self.cv_fila.delete("all")
        w = self.cv_fila.winfo_width(); h = self.cv_fila.winfo_height()
        
        if fila:
            algo_sel = self.var_visual_algo.get()
            fatias_visuais = []
            
            if algo_sel in ["FCFS", "SJF"]:
                if algo_sel == "FCFS": fila.sort(key=lambda p: p.arrival_time)
                elif algo_sel == "SJF": fila.sort(key=lambda p: p.burst_time)
                
                for p in fila:
                    fatias_visuais.append({"nome": p.nome, "burst": p.burst_time, "cor": VERD2 if p.burst_time < 3.0 else (AMAR if p.burst_time < 5.0 else VERM2)})
                    
            elif algo_sel == "RR":
                fila.sort(key=lambda p: p.arrival_time)
                fila_sim = [{"nome": p.nome, "restante": p.burst_time, "cor": VERD2 if p.burst_time < 3.0 else (AMAR if p.burst_time < 5.0 else VERM2)} for p in fila]
                q = estado.quantum_rr
                loop_infinito = 0
                
                # BUGFIX: Limite de laço aumentado para 1000 para não cortar os processos no meio!
                while fila_sim and loop_infinito < 1000: 
                    loop_infinito += 1; p = fila_sim.pop(0)
                    fatias_visuais.append({"nome": p["nome"], "burst": min(q, p["restante"]), "cor": p["cor"]})
                    p["restante"] -= q
                    if p["restante"] > 0.001: fila_sim.append(p)

            bx_min_w = S(40)
            espaco_necessario = len(fatias_visuais) * (bx_min_w + S(4))
            
            scroll_w = max(w, espaco_necessario + S(20))
            self.cv_fila.configure(scrollregion=(0, 0, scroll_w, h))

            for i, p in enumerate(fatias_visuais):
                x0 = S(10) + i * (bx_min_w + S(4))
                self.cv_fila.create_rectangle(x0, S(5), x0+bx_min_w, h-S(5), fill=p["cor"], outline=BG2)
                self.cv_fila.create_text(x0+bx_min_w/2, h/2-S(6), text=p["nome"], font=(FM, F(7), "bold"), fill=BG)
                self.cv_fila.create_text(x0+bx_min_w/2, h/2+S(6), text=f"{p['burst']:.1f}t", font=(FM, F(6)), fill=BG2)

        n = len(h_fcfs)
        if n == 0: return
        
        mw_f, mr_f = sum(h_fcfs)/n, sum(r_fcfs)/n
        mw_s, mr_s = sum(h_sjf)/n, sum(r_sjf)/n
        mw_rr, mr_rr = sum(h_rr)/n, sum(r_rr)/n
        
        self.lbl_fcfs_esp.config(text=f"Espera Méd: {mw_f:.3f}s"); self.lbl_fcfs_rsp.config(text=f"Resposta Méd: {mr_f:.3f}s")
        self.lbl_sjf_esp.config(text=f"Espera Méd: {mw_s:.3f}s");  self.lbl_sjf_rsp.config(text=f"Resposta Méd: {mr_s:.3f}s")
        self.lbl_rr_esp.config(text=f"Espera Méd: {mw_rr:.3f}s");  self.lbl_rr_rsp.config(text=f"Resposta Méd: {mr_rr:.3f}s")
        
        medias_esp = {"FCFS": mw_f, "SJF": mw_s, "RR": mw_rr}; medias_rsp = {"FCFS": mr_f, "SJF": mr_s, "RR": mr_rr}
        venc_esp = min(medias_esp, key=medias_esp.get); cores = {"FCFS": AZUL, "SJF": VERDE, "RR": LARA}
        venc_rsp = min(medias_rsp, key=medias_rsp.get)
        
        self.lbl_venc_esp.config(text=f"Espera: {venc_esp}", fg=cores[venc_esp]); self.lbl_venc_rsp.config(text=f"Respos: {venc_rsp}", fg=cores[venc_rsp])

    def _update(self):
        now = time.time(); sel = self.acao_sel.get()
        if not hasattr(self, "_frame"): self._frame = 0
        self._frame += 1
        self._flush_log()
        
        if self._frame % 3 == 0: self._update_proc(); self._update_sched()

        cor_r = VERM if (estado.races > 0 and self._frame % 2 == 0) else TEXT2
        font_r = (FM, F(9), "bold") if estado.races > 0 else (FM, F(8), "bold")
        self.lbl_race.config(text=f"RACE: {estado.races}", fg=cor_r, font=font_r)
        
        self.lbl_hora.config(text=datetime.now().strftime("%d/%m  %H:%M:%S"))
        n_so = threads_so(); cor_so = VERM if n_so >= LIMITE_PERIGO else (AMAR if n_so >= LIMITE_AVISO else VERDE)
        self.lbl_so.config(text=f"SO:{n_so}thr", fg=cor_so)
        modo_txt = "SYNC✓" if estado.modo_sync else "⚠NO-SYNC"; cor_modo = VERDE if estado.modo_sync else VERM
        self.lbl_stats.config(text=(f"SIM:{estado.num_threads}t  COL:{estado.colisoes}  VOL:{estado.volatilidade:.1f}×  [{modo_txt}]"), fg=cor_modo)

        for ticker, comp in self.fa.items():
            p = estado.precos.get(ticker, 0); var = (p - comp["ref"]) / comp["ref"] * 100
            cor = VERDE if var >= 0 else VERM; sig = "▲" if var >= 0 else "▼"
            comp["lp"].config(text=f"R${p:.2f}", fg=cor); comp["lv"].config(text=f"{sig}{abs(var):.1f}%", fg=cor)
            bg = ("#0D2218" if (ticker in self.flash and now < self.flash[ticker] and var >= 0) else "#220A0A" if (ticker in self.flash and now < self.flash[ticker]) else "#111C2E" if ticker == sel else BG3)
            comp["f"].config(bg=bg); comp["l1"].config(bg=bg); comp["lp"].config(bg=bg); comp["lv"].config(bg=bg)

        p = estado.precos.get(sel, 0); ref = ACOES[sel]["preco"]; var = (p - ref) / ref * 100; cor = VERDE if var >= 0 else VERM
        self.lbl_pgrande.config(text=f"R$ {p:.2f}", fg=cor); self.lbl_vgrande.config(text=f"{'▲' if var>=0 else '▼'} {abs(var):.2f}%", fg=cor)
        cd = estado.candle_cur.get(sel)
        if cd: self.lbl_ohlc.config(text=f"O:{cd.o:.2f}  H:{cd.h:.2f}  L:{cd.l:.2f}  C:{cd.c:.2f}")

        for ticker in estado.precos:
            if abs(estado.precos[ticker] - self.prev_p.get(ticker, 0)) > 0.01: self.flash[ticker] = now + 0.35
        self.prev_p = dict(estado.precos)
        draw_candles(self.cv_main, sel)

        noticias = list(estado.noticias)
        for i, (li, ld, lt, fn) in enumerate(self.feed):
            if i < len(noticias):
                n = noticias[i]; idade = now - n["ts"]; cor_n = n["cor"] if idade < 4 else TEXT2
                li.config(text=f"[{n['intensidade'][:4]}]", fg=cor_n); ld.config(text=n.get("data", "")); lt.config(text=n["texto"], fg=cor_n)
                fn.config(bg=BG4 if idade < 0.5 else BG3)
            else:
                li.config(text=""); ld.config(text=""); lt.config(text="—", fg=TEXT2); fn.config(bg=BG2)

        n = estado.num_threads; bar = "█" * n + "░" * max(0, LIMITE_MAXIMO - n)
        self.lbl_fl.config(text=f"SIM [{bar}] {n}t")
        self.lbl_fr.config(text=f"↯ {estado.total} notícias  |  {estado.colisoes} colisões  |  {estado.races} races")

        n_thr = estado.num_threads
        ms = 80 if n_thr <= 8 else (100 if n_thr <= 14 else 120)
        self.root.after(ms, self._update)

def main():
    for fn in [loop_ruido, loop_noticias, loop_candles, loop_espontaneo]: threading.Thread(target=fn, daemon=True).start()
    root = tk.Tk()
    HomeBroker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
