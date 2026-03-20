"""SIMULAÇÃO CAÓTICA DO MERCADO FINANCEIRO — utilizando Threads
"""

#IMPORTAÇÕES
import tkinter as tk
from tkinter import ttk, font as tkfont
import threading
import random
import time
import os
import sys
from collections import deque
from datetime import datetime
import queue

# DETECÇÃO DE RESOLUÇÃO — escala automática

def _detectar():
    #criando janela adaptavel ao monitor
    tmp = tk.Tk(); tmp.withdraw() #criação de janela
    sw, sh = tmp.winfo_screenwidth(), tmp.winfo_screenheight() #mede a tela
    tmp.destroy()
    f = max(0.60, min(sh / 1080.0, 2.0)) #zoom janela de 60% até 200%
    return f, sw, sh, min(int(1560*f), sw-30), min(int(940*f), sh-50)

SCALE, SCR_W, SCR_H, WIN_W, WIN_H = _detectar() #largura monitor + janela
def S(x): return max(1, int(x * SCALE)) #escala = nunca menor que 1
def F(x): return max(7, int(x * SCALE)) # textos = nunca menor que 7


# LIMITE SEGURO DE THREADS

LIMITE_AVISO   = 9    # amarelo: mercado caótico, UI começa a sentir
LIMITE_PERIGO  = 15   # vermelho: pânico total, UI visivelmente lenta
LIMITE_MAXIMO  = 22   # travamento garantido acima de ~19

# AÇÕES, aqueles que vão influenciar no mercado financeiro
#dicionario chave-valor; chave {nome,valor_ação_inicial,cor_no_grafico}
ACOES = {
    "VALE3": {"nome": "Vale S.A.",       "preco": 68.50, "cor": "#4FC3F7"},
    "PETR4": {"nome": "Petrobras PN",    "preco": 38.20, "cor": "#FF8A65"},
    "ITUB4": {"nome": "Itaú Unibanco",   "preco": 34.80, "cor": "#A5D6A7"},
    "BBDC4": {"nome": "Bradesco PN",     "preco": 14.90, "cor": "#CE93D8"},
    "B3SA3": {"nome": "B3 S.A.",         "preco": 11.40, "cor": "#FFD54F"},
    "ABEV3": {"nome": "Ambev S.A.",      "preco": 12.80, "cor": "#80DEEA"},
    "MGLU3": {"nome": "Magazine Luiza",  "preco": 9.10,  "cor": "#F48FB1"},
    "WEGE3": {"nome": "WEG S.A.",        "preco": 51.30, "cor": "#BCAAA4"},
    "RENT3": {"nome": "Localiza",        "preco": 43.60, "cor": "#EF9A9A"},
    "SUZB3": {"nome": "Suzano S.A.",     "preco": 57.20, "cor": "#B39DDB"},
}
#cria uma lista só com as chaves do nosso dicionário 
TICKERS = list(ACOES.keys())

# BANCO DE NOTÍCIAS REAIS
#cada noticia tem data real, mexe no preço da açao, intensidade e cor de alerta.
BANCO_NOTICIAS = [
    {"data":"2019-01-25","titulo":"Rompimento da Barragem de Brumadinho — Vale suspende operações",
     "impacto":{"VALE3":-24.5},"intensidade":"CRÍTICA","cor":"#FF1744","fonte":"Reuters/B3"},
    {"data":"2021-03-10","titulo":"China anuncia pacote de US$ 1,4 tri — minério de ferro dispara",
     "impacto":{"VALE3":+8.3,"SUZB3":+2.1},"intensidade":"CRÍTICA","cor":"#69F0AE","fonte":"Bloomberg"},
    {"data":"2022-07-14","titulo":"Vale reporta produção recorde de minério no 2T22",
     "impacto":{"VALE3":+5.2},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Infomoney"},
    {"data":"2023-04-19","titulo":"Minério de ferro cai 6% em Dalian — estoques elevados",
     "impacto":{"VALE3":-4.8},"intensidade":"ALTA","cor":"#FF5252","fonte":"Reuters"},
    {"data":"2024-01-10","titulo":"Vale anuncia dividendos extraordinários de R$ 2,79/ação",
     "impacto":{"VALE3":+6.1},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Valor Econômico"},
    {"data":"2022-02-24","titulo":"Rússia invade Ucrânia — petróleo Brent ultrapassa US$ 100",
     "impacto":{"PETR4":+9.2,"VALE3":+2.3},"intensidade":"CRÍTICA","cor":"#FF8C00","fonte":"Reuters/WSJ"},
    {"data":"2022-06-22","titulo":"Petrobras corta preço do diesel por pressão do governo",
     "impacto":{"PETR4":-7.8},"intensidade":"CRÍTICA","cor":"#FF1744","fonte":"Folha de SP"},
    {"data":"2023-02-16","titulo":"Petrobras suspende dividendos extraordinários — Lula",
     "impacto":{"PETR4":-11.3},"intensidade":"CRÍTICA","cor":"#FF1744","fonte":"O Globo"},
    {"data":"2023-08-03","titulo":"OPEP+ anuncia corte adicional de 1 mi de barris/dia",
     "impacto":{"PETR4":+5.7},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Reuters"},
    {"data":"2024-03-14","titulo":"Petrobras descobre campo pré-sal com 700 mi de barris",
     "impacto":{"PETR4":+6.4},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Petrobras IR"},
    {"data":"2021-10-27","titulo":"COPOM sobe Selic em 1,5 p.p. — maior alta em décadas",
     "impacto":{"ITUB4":+3.2,"BBDC4":+2.8,"B3SA3":-3.1,"MGLU3":-4.2},"intensidade":"ALTA","cor":"#FFD740","fonte":"Banco Central"},
    {"data":"2022-08-03","titulo":"Itaú reporta lucro de R$ 7,7 bi no 2T22 — recorde",
     "impacto":{"ITUB4":+5.8},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Itaú RI"},
    {"data":"2022-11-10","titulo":"Bradesco provisiona R$ 5 bi para crédito ruim",
     "impacto":{"BBDC4":-8.2,"ITUB4":-2.1},"intensidade":"CRÍTICA","cor":"#FF1744","fonte":"Estadão"},
    {"data":"2023-01-13","titulo":"Americanas: R$ 43 bi em passivos ocultos — crise sistêmica",
     "impacto":{"BBDC4":-5.5,"ITUB4":-3.8,"B3SA3":-4.2},"intensidade":"CRÍTICA","cor":"#FF1744","fonte":"Reuters"},
    {"data":"2024-05-08","titulo":"COPOM reduz Selic para 10,50% — ciclo de corte continua",
     "impacto":{"ITUB4":+2.1,"BBDC4":+1.9,"MGLU3":+3.5,"B3SA3":+2.8},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Banco Central"},
    {"data":"2020-03-18","titulo":"COVID-19: Ibovespa aciona circuit breaker — queda de 15%",
     "impacto":{"PETR4":-12.3,"VALE3":-9.8,"ITUB4":-11.2,"BBDC4":-10.5,"MGLU3":-13.1,
                "ABEV3":-8.4,"WEGE3":-9.6,"RENT3":-12.8,"B3SA3":-11.0,"SUZB3":-7.2},
     "intensidade":"CRÍTICA","cor":"#FF1744","fonte":"B3/Bloomberg"},
    {"data":"2022-10-30","titulo":"Lula vence eleição presidencial — mercado reage",
     "impacto":{"B3SA3":-6.2,"PETR4":+3.1,"ITUB4":-3.5,"BBDC4":-3.1},"intensidade":"CRÍTICA","cor":"#FFD740","fonte":"TSE/Reuters"},
    {"data":"2025-01-15","titulo":"Dólar bate R$ 6,18 — Banco Central intervém com swap",
     "impacto":{"VALE3":+5.1,"PETR4":+3.4,"MGLU3":-6.2,"ITUB4":-1.8,"ABEV3":-3.3},
     "intensidade":"CRÍTICA","cor":"#FF1744","fonte":"Bloomberg/BC"},
    {"data":"2024-09-18","titulo":"Fed corta juros em 0,5 p.p. — emergentes sobem forte",
     "impacto":{"ITUB4":+3.2,"B3SA3":+3.8,"MGLU3":+5.1,"BBDC4":+2.7},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Fed/Reuters"},
    {"data":"2021-11-19","titulo":"Magazine Luiza: lucro cai 72% — pressão de custos",
     "impacto":{"MGLU3":-9.4},"intensidade":"CRÍTICA","cor":"#FF1744","fonte":"MGLU RI"},
    {"data":"2022-06-01","titulo":"WEG bate recorde: maior contrato de exportação da história",
     "impacto":{"WEGE3":+7.2},"intensidade":"ALTA","cor":"#69F0AE","fonte":"WEG RI"},
    {"data":"2023-05-30","titulo":"Suzano faz oferta de US$ 15 bi pela International Paper",
     "impacto":{"SUZB3":+12.3},"intensidade":"CRÍTICA","cor":"#69F0AE","fonte":"Bloomberg"},
    {"data":"2024-02-28","titulo":"Localiza conclui fusão com Unidas — nova gigante de frotas",
     "impacto":{"RENT3":+8.1},"intensidade":"ALTA","cor":"#69F0AE","fonte":"RENT RI"},
    {"data":"GERADA","titulo":"[IA] China suspende importações de minério — disputa comercial",
     "impacto":{"VALE3":-6.3,"SUZB3":-2.8},"intensidade":"ALTA","cor":"#FF5252","fonte":"Gerada por IA"},
    {"data":"GERADA","titulo":"[IA] BC anuncia alta surpresa de 0,75 p.p. na Selic",
     "impacto":{"ITUB4":+3.9,"BBDC4":+3.2,"MGLU3":-5.2,"B3SA3":-3.8},"intensidade":"CRÍTICA","cor":"#FFD740","fonte":"Gerada por IA"},
    {"data":"GERADA","titulo":"[IA] Guerra escala no Oriente Médio — petróleo atinge US$ 120",
     "impacto":{"PETR4":+8.9,"ABEV3":-1.5,"MGLU3":-2.3},"intensidade":"CRÍTICA","cor":"#FF8C00","fonte":"Gerada por IA"},
    {"data":"GERADA","titulo":"[IA] Escândalo contábil atinge setor bancário — pânico",
     "impacto":{"BBDC4":-7.1,"ITUB4":-4.3,"B3SA3":-5.2},"intensidade":"CRÍTICA","cor":"#FF1744","fonte":"Gerada por IA"},
    {"data":"GERADA","titulo":"[IA] Reforma fiscal aprovada — mercado reage positivamente",
     "impacto":{"B3SA3":+4.1,"ITUB4":+2.8,"BBDC4":+2.4},"intensidade":"ALTA","cor":"#69F0AE","fonte":"Gerada por IA"},
]


# CORES USADAS NA TELA
BG    = "#0A0E17"
BG2   = "#0D1220"
BG3   = "#111827"
BG4   = "#1C2333"
VERDE = "#00E676"
VERD2 = "#00C853"
VERM  = "#FF1744"
VERM2 = "#D50000"
AMAR  = "#FFD740"
AZUL  = "#40C4FF"
LARA  = "#FF8A65"
CIAN  = "#80DEEA"
ROXO  = "#CE93D8"
TEXTO = "#E2E8F0"
TEXT2 = "#64748B"
TEXT3 = "#94A3B8"
GRADE = "#1E293B"
FM    = "Courier New"

# Estados das threads para visualização no gráfico
ESTADOS = {
    # Etapa                  Cor         Significado
    "NOVA"       : ("#607D8B", "Thread criada, ainda não iniciada"),
    "PRONTA"     : ("#90A4AE", "Na fila, aguardando CPU (RUNNABLE)"),
    "DISPUTANDO" : (AMAR,      "Tentando adquirir o mutex (uma thread por vez) — BLOQUEADA na fila"),
    "EXECUTANDO" : (VERDE,     "Com acesso exclusivo — RODANDO no CPU"),
    "CALCULANDO" : (AZUL,      "Dentro da seção crítica — Data Section compartilhada"),
    "APLICANDO"  : (LARA,      "Escrevendo no estado global — seção crítica"),
    "LIBERANDO"  : (CIAN,      "Saindo da seção crítica — liberando mutex"),
    "TERMINADA"  : (TEXT2,     "Thread encerrada — recursos liberados"),
}

# CANDLE (formato vela do gráfico utilizado no HomeBroker)
#A cada 2 segundos, criação de uma nova vela, valores o,h,l,c iguais ao preço atual
class Candle:
    def __init__(self, o):
        self.o = self.h = self.l = self.c = o
#Novo preço p, preço fechamento = c, preço h é maior ou não
    def update(self, p):
        self.c = p; self.h = max(self.h, p); self.l = min(self.l, p)

# ESTADO GLOBAL (Data Section compartilhada — conceito do slide 4.1)
class EstadoMercado:
    """
    Esta classe representa a DATA SECTION compartilhada entre todas as threads.
    Slide 4.1: 'Uma Thread compartilha com outras Threads de um mesmo Processo:
    Seu Code Section, Data Section, Arquivos abertos'
    """
    def __init__(self):
        # MUTEX — evita race condition na seção crítica
        #cadeado, apenas thread atual
        self.lock          = threading.Lock() 
        # Data Section compartilhada (todas as threads leem/escrevem aqui)
        self.precos        = {t: d["preco"] for t, d in ACOES.items()} #preços atuais de cada ação
        self.candles       = {t: [] for t in ACOES} #histórico de gráfico de velas
        self.candle_cur    = {t: Candle(d["preco"]) for t, d in ACOES.items()}
        self.noticias      = deque(maxlen=8) #ultimas 8 notícias
        self.colisoes      = 0     # quantas vezes que determinada thread esperou na fila do mutex
        self.total         = 0
        self.rodando       = False
        self.num_threads   = 4
        self.volatilidade  = 1.0
        self.candle_secs   = 2.0
        self.ui_q          = queue.Queue()  #informações threads para a tela.
        self.threads_vivas : list = []
        self.threads_lock  = threading.Lock()
        self.travamentos   = 0     

#criação de mercado, onde threads terão que esperar para entrar
estado = EstadoMercado()
PID = os.getpid() 

# THREAD DE NOTÍCIA
# Cada instância = 1 Kernel Thread
# possui: Thread ID próprio, PC próprio, Stack própria, Register Set próprio
# compartilha: Code Section (este .py), Data Section (estado global acima)
#CRIAÇAO DE THREAD 
class ThreadNoticia(threading.Thread):
    _cnt = 0 #CONTADOR
    _cnt_lock = threading.Lock()   # lock para contador (seção crítica pequena)

    def __init__(self):
        #Se programa principal fechar, thread fecha também
        super().__init__(daemon=True)
        # ── Atributos da Stack (exclusivos desta thread) ──────────────────
        with ThreadNoticia._cnt_lock:
            ThreadNoticia._cnt += 1
            self.tid = ThreadNoticia._cnt          # Thread ID da simulação
        self.noticia    = random.choice(BANCO_NOTICIAS) # vai no banco de noticias e seleciona noticia aleatoria
        self.nome       = f"Thread-{self.tid}"     # nome no estilo Java/slides
        self.estado_thr = "NOVA"                   # estado atual da thread
        self.ts_inicio  = time.time()              # tempo de criação (Stack)
        self.so_ident   = None                     # ID real do Kernel (SO)
        self.impactos   = {}                       # resultado dos cálculos

    def _log(self, estado_thr, detalhe=""):
        """Envia entrada para o log da UI. Usa a Data Section compartilhada (ui_q)."""
        self.estado_thr = estado_thr #atualiza estado thread
        estado.ui_q.put({ #informaçoes thread
            "tid"    : self.tid,
            "nome"   : self.nome,
            "estado" : estado_thr,
            "detalhe": detalhe,
            "ts"     : time.time(),
            "noticia": self.noticia["titulo"][:48],
        })

    def run(self):
        """
        Método run() — executa na Stack PRÓPRIA desta thread.
        Variáveis locais (delay, var, novo, carga) ficam na Stack desta thread.
        """
        self.so_ident = self.ident

        with estado.threads_lock: #se mutex estiver com outra thread, fica bloqueada
            estado.threads_vivas.append(self)

        self._log("PRONTA", f"Notícia: {self.noticia['titulo'][:42]}")

        # Delay aleatório antes de disputar o lock.
        # Range amplo (0.05–1.0s) garante que threads de rajadas DIFERENTES
        # se encontrem no mutex — o que cria colisão real entre rajadas.
        delay = random.uniform(0.05, 1.0)
        self._log("PRONTA", f"Aguardando {delay:.2f}s antes do mutex...")
        time.sleep(delay)

        # DISPUTANDO — tentando entrar na seção crítica
        self._log("DISPUTANDO",
                  "Tentando adquirir o mutex — BLOQUEADA se ocupado!")

        #verifica se tem muita thread esperando, sendo assim, avisa o sistema de possível travamento
        n_so = threading.active_count()
        if n_so >= LIMITE_PERIGO:
            self._log("DISPUTANDO",
                      f"⚠ {n_so} Threads!risco de travamento!")
            with estado.threads_lock:
                estado.travamentos += 1 #mais uma thread esperando

        #execução, altera mutex, calcula e retorna os impactos com gráficos candle.
        with estado.lock:
            self._log("EXECUTANDO",
                      f"Mutex adquirido! [colisão #{estado.colisoes+1}]")
            estado.colisoes += 1
            estado.total    += 1

            self._log("CALCULANDO",
                      f"Ações: {list(self.noticia['impacto'].keys())}")
            self.impactos = {}

            for ticker, pct in self.noticia["impacto"].items():
                if ticker in estado.precos:
                    var  = (pct + random.gauss(0, 0.7)) * estado.volatilidade
                    novo = max(0.50, estado.precos[ticker] * (1 + var / 100))
                    estado.precos[ticker] = novo
                    estado.candle_cur[ticker].update(novo)
                    self.impactos[ticker] = var

            # ── TRABALHO EXTRA dentro do lock ────────────────────────────
            # Simula processamento de risco/análise da notícia.
            # Mantém o lock ocupado por mais tempo → fila de threads cresce
            # → overhead do SO aumenta → travamento proporcional ao slider.
            # Carga escala com o número de threads configurado.
            n_cfg = estado.num_threads
            carga = int(3000 + n_cfg * 800)   # de 3800 (n=1) até 20600 (n=22) iterações
            _ = sum(i * i for i in range(carga))   # CPU-bound: mantém o GIL ocupado

            self._log("APLICANDO",
                      "  ".join(f"{t}:{v:+.1f}%" for t, v in self.impactos.items()))

            estado.noticias.appendleft({
                "texto"      : self.noticia["titulo"],
                "cor"        : self.noticia["cor"],
                "intensidade": self.noticia["intensidade"],
                "ts"         : time.time(),
                "data"       : self.noticia["data"],
                "fonte"      : self.noticia["fonte"],
                "tickers"    : list(self.noticia["impacto"].keys()),
            })

        self._log("LIBERANDO", "Mutex liberado — próxima thread pode entrar")

        dur = time.time() - self.ts_inicio
        self._log("TERMINADA",
                  f"Duração: {dur:.3f}s | SO ident: {self.so_ident}")

        with estado.threads_lock:
            if self in estado.threads_vivas:
                estado.threads_vivas.remove(self)

# LOOPS DE BACKGROUND (threads daemon — morrem com o processo pai)
def loop_candles():
    while True:
        time.sleep(estado.candle_secs)
        if not estado.rodando: continue
        with estado.lock:
            for t in ACOES:
                estado.candles[t].append(estado.candle_cur[t])
                if len(estado.candles[t]) > 60: estado.candles[t] = estado.candles[t][-60:]
                estado.candle_cur[t] = Candle(estado.precos[t])

def loop_ruido():
    """Ruído de fundo — amplitude e frequência crescem com o slider."""
    while True:
        if not estado.rodando:
            time.sleep(0.3)
            continue
        n = estado.num_threads
        intervalo = max(0.10, 0.35 - n * 0.012)
        time.sleep(random.uniform(intervalo * 0.6, intervalo))
        with estado.lock:
            amp = (0.18 + n * 0.025) * estado.volatilidade
            for t in estado.precos:
                r    = random.gauss(0, amp)
                novo = max(0.50, estado.precos[t] * (1 + r / 100))
                estado.precos[t] = novo
                estado.candle_cur[t].update(novo)

def loop_noticias():
    """
    Motor do caos — princípio de acumulacao progressiva.
    Uma ThreadNoticia vive aproximadamente 0.3 a 1.0 segundo
    (delay + calculo + log). O travamento ocorre quando novas
    threads nascem mais rapido do que as antigas morrem.
    Faixas do slider:
      1- 4  threads: pausa 2.0-3.0s  → threads terminam antes da proxima rajada (estavel)
      5- 8  threads: pausa 1.0-1.8s  → leve acumulo, UI agitada
      9-13  threads: pausa 0.5-1.0s  → acumulo visivel, colisoes frequentes
     14-17  threads: pausa 0.2-0.5s  → acumulo rapido, UI lenta
     18-22  threads: pausa 0.03-0.15s→ avalanche de threads → TRAVAMENTO REAL
    Aleatoriedade dupla:
      1) Quantidade da rajada: N ate N*1.5 (varia a cada ciclo)
      2) Pausa: range aleatorio dentro da faixa
    Isso garante que cada ciclo seja diferente — caos real, nao repetitivo.
    """
    while True:
        if not estado.rodando:
            time.sleep(0.3)
            continue

        n = estado.num_threads

        # Quantidade aleatoria entre N e N + N//2 — imprevisivel a cada ciclo
        qtd = random.randint(n, n + random.randint(0, max(1, n // 2)))

        # Dispara TODAS sem join — acumulacao intencional
        for _ in range(qtd):
            ThreadNoticia().start()

        # Pausa inversamente proporcional — quanto mais threads, menor a pausa
        # Quando pausa < tempo_de_vida_da_thread → threads se acumulam → trava
        if   n <= 4:  pausa = random.uniform(2.0, 3.0)
        elif n <= 8:  pausa = random.uniform(1.0, 1.8)
        elif n <= 13: pausa = random.uniform(0.5, 1.0)
        elif n <= 17: pausa = random.uniform(0.2, 0.5)
        else:         pausa = random.uniform(0.03, 0.15)

        time.sleep(pausa)

def loop_espontaneo():
    """
    Breaking news — threads em momentos completamente aleatorios.
    Timing imprevisivel garante que o comportamento nunca se repete.
    Com slider alto, acelera o acumulo que leva ao travamento.
    """
    while True:
        if not estado.rodando:
            time.sleep(0.5)
            continue

        n = estado.num_threads

        # Espera aleatoria: mais curta com slider alto
        espera = random.uniform(0.3, max(0.4, 3.5 - n * 0.15))
        time.sleep(espera)

        # Quantidade: 1 no nivel baixo, ate n//2 no nivel alto
        qtd = random.randint(1, max(1, n // 2))
        for _ in range(qtd):
            ThreadNoticia().start()

def threads_so(): return threading.active_count()

# DESENHO DE CANDLES
def draw_candles(cv, ticker):
    cv.delete("all"); w = cv.winfo_width(); h = cv.winfo_height()
    if w < 20 or h < 10: return
    all_c = list(estado.candles[ticker]) + [estado.candle_cur[ticker]]
    if not all_c: return
    ml, mr, mt, mb = S(50), S(4), S(4), S(14)
    aw = w - ml - mr; ah = h - mt - mb
    for i in range(5):
        cv.create_line(ml, mt + i*ah//4, w-mr, mt + i*ah//4, fill=GRADE, dash=(2,4))
    prices = [p for c in all_c for p in (c.h, c.l)]
    mn = min(prices)*0.999; mx = max(prices)*1.001; rng = mx-mn if mx!=mn else 1.0
    def py(v): return mt + int((1-(v-mn)/rng)*ah)
    mv = max(1, aw//S(8)); vis = all_c[-mv:]; n = len(vis)
    step = aw/max(n,1); cw = max(2, min(int(step*0.6), S(12)))
    for i, c in enumerate(vis):
        xc = ml + int(i*step + step/2); cor = VERD2 if c.c>=c.o else VERM2
        cv.create_line(xc, py(c.h), xc, py(c.l), fill=cor, width=1)
        y0=min(py(c.o),py(c.c)); y1=max(py(c.o),py(c.c))
        cv.create_rectangle(xc-cw//2, y0, xc+cw//2, max(y1,y0+1), fill=cor, outline=cor)
    for i in range(5):
        cv.create_text(ml-2, mt+i*ah//4, text=f"{mx-(i/4)*rng:.2f}",
                       font=(FM, F(6)), fill=TEXT2, anchor="e")
    p = estado.precos[ticker]
    cv.create_line(ml, py(p), w-mr, py(p), fill=ACOES[ticker]["cor"], dash=(3,4), width=1)

# GUI PRINCIPAL, desenha a janela principal
class HomeBroker:
    def __init__(self, root):
        self.root     = root
        root.title(f"SIMULAÇÃO CAÓTICA DO MERCADO FINANCEIRO UTILIZANDO THREADS  [{SCR_W}×{SCR_H}]")
        root.configure(bg=BG)
        root.geometry(f"{WIN_W}x{WIN_H}")
        root.minsize(S(1000), S(680))
        self.acao_sel = tk.StringVar(value="VALE3")
        self.prev_p   = {t: d["preco"] for t, d in ACOES.items()}
        self.flash    = {}
        self._build()
        self._update()

    #BUILD 
    def _build(self):
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._header(); self._controles()
        tk.Frame(self.root, bg=GRADE, height=1).grid(row=1, column=0, sticky="sew")
        self._corpo(); self._footer()

    #cabeçalho
    def _header(self):
        h = tk.Frame(self.root, bg=BG, height=S(46))
        h.grid(row=0, column=0, sticky="ew"); h.grid_propagate(False)
        h.grid_columnconfigure(1, weight=1)
        tk.Label(h, text="SIMULAÇÃO CAÓTICA DO MERCADO FINANCEIRO UTILIZANDO THREADS",
                 font=(FM, F(12), "bold"), bg=BG, fg=AMAR
                 ).grid(row=0, column=0, padx=S(10), pady=S(7), sticky="w")
        info = tk.Frame(h, bg=BG); info.grid(row=0, column=2, padx=S(8), sticky="e")
        self.lbl_stats = tk.Label(info, text="", font=(FM, F(8)), bg=BG, fg=TEXT3)
        self.lbl_stats.pack(side="left", padx=S(6))
        tk.Frame(info, bg=GRADE, width=1, height=S(22)).pack(side="left", pady=S(8))
        self.lbl_pid = tk.Label(info, text=f"PID:{PID}", font=(FM, F(9), "bold"), bg=BG, fg=CIAN)
        self.lbl_pid.pack(side="left", padx=S(6))
        tk.Frame(info, bg=AMAR, width=2, height=S(22)).pack(side="left", pady=S(8))
        self.lbl_so = tk.Label(info, text="SO: — thr", font=(FM, F(9), "bold"), bg=BG, fg=VERDE)
        self.lbl_so.pack(side="left", padx=S(6))
        tk.Frame(info, bg=GRADE, width=1, height=S(22)).pack(side="left", pady=S(8))
        self.lbl_hora = tk.Label(info, text="", font=(FM, F(8)), bg=BG, fg=TEXT2)
        self.lbl_hora.pack(side="left", padx=S(6))

    #botoes, controles start, zoom, threads
    def _controles(self):
        c = tk.Frame(self.root, bg=BG2, height=S(50))
        c.grid(row=1, column=0, sticky="ew"); c.grid_propagate(False)
        col = 0
        def nxt(): nonlocal col; col += 1; return col - 1

        tk.Label(c, text="THREADS (UM-para-UM):", font=(FM, F(8), "bold"),
                 bg=BG2, fg=TEXT3).grid(row=0, column=nxt(), padx=(S(10),S(2)), pady=S(12))
        self.var_thr = tk.IntVar(value=4)
        self.lbl_thr = tk.Label(c, text=" 4", font=(FM, F(13), "bold"),
                                bg=BG2, fg=AMAR, width=3)
        self.lbl_thr.grid(row=0, column=nxt())
        ttk.Scale(c, from_=1, to=LIMITE_MAXIMO, orient="horizontal", length=S(170),
                  variable=self.var_thr, command=self._on_thr
                  ).grid(row=0, column=nxt(), padx=(S(2),S(10)))

        # Aviso de limite
        self.lbl_aviso = tk.Label(c, text="", font=(FM, F(8), "bold"),
                                  bg=BG2, fg=VERDE, width=35, anchor="w")
        self.lbl_aviso.grid(row=0, column=nxt(), padx=S(4))

        tk.Label(c, text="VOL:", font=(FM, F(8), "bold"), bg=BG2, fg=TEXT3
                 ).grid(row=0, column=nxt(), padx=(S(4),S(2)))
        self.var_vol = tk.DoubleVar(value=1.0)
        self.lbl_vol = tk.Label(c, text="1.0×", font=(FM, F(9), "bold"), bg=BG2, fg=LARA, width=5)
        self.lbl_vol.grid(row=0, column=nxt())
        ttk.Scale(c, from_=0.2, to=5.0, orient="horizontal", length=S(100),
                  variable=self.var_vol,
                  command=lambda v: [setattr(estado,"volatilidade",float(v)),
                                     self.lbl_vol.config(text=f"{float(v):.1f}×")]
                  ).grid(row=0, column=nxt(), padx=(S(2),S(10)))

        self.btn = tk.Button(c, text="▶ START", font=(FM, F(9), "bold"),
                             bg=VERDE, fg=BG, relief="flat", padx=S(8), command=self._toggle)
        self.btn.grid(row=0, column=nxt(), padx=S(3))
        tk.Button(c, text="↺ RESET", font=(FM, F(9)), bg=BG3, fg=TEXT3,
                  relief="flat", padx=S(8), command=self._reset).grid(row=0, column=nxt(), padx=S(3))
        tk.Button(c, text="⚡ NOTÍCIA", font=(FM, F(9), "bold"), bg=BG4, fg=AZUL,
                  relief="flat", padx=S(6),
                  command=lambda: ThreadNoticia().start()).grid(row=0, column=nxt(), padx=S(3))
        tk.Label(c, text="│ CANDLE:", font=(FM, F(8)), bg=BG2, fg=TEXT2
                 ).grid(row=0, column=nxt(), padx=(S(10),S(2)))
        for lbl2, val in [("1s",1),("2s",2),("5s",5)]:
            tk.Button(c, text=lbl2, font=(FM, F(8)), bg=BG3, fg=TEXT3, relief="flat", width=3,
                      command=lambda v=val: setattr(estado,"candle_secs",v)
                      ).grid(row=0, column=nxt(), padx=1)

    #divisão colunas
    def _corpo(self):
        body = tk.Frame(self.root, bg=BG)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=13, minsize=S(160))
        body.grid_columnconfigure(1, weight=55)
        body.grid_columnconfigure(2, weight=32, minsize=S(290))
        body.grid_rowconfigure(0, weight=1)
        self._col_acoes(body); self._col_centro(body); self._col_direita(body)

    # COLUNA AÇÕES
    def _col_acoes(self, body):
        esq = tk.Frame(body, bg=BG2); esq.grid(row=0, column=0, sticky="nsew")
        esq.grid_rowconfigure(1, weight=1); esq.grid_columnconfigure(0, weight=1)
        tk.Label(esq, text="TOP 10  IBOVESPA", font=(FM, F(7), "bold"),
                 bg=BG2, fg=TEXT2).grid(row=0, column=0, padx=S(8), pady=(S(6),S(2)), sticky="w")
        sa = tk.Frame(esq, bg=BG2); sa.grid(row=1, column=0, sticky="nsew")
        sa.grid_columnconfigure(0, weight=1)
        self.fa = {}
        for i, (ticker, d) in enumerate(ACOES.items()):
            f = tk.Frame(sa, bg=BG3, cursor="hand2")
            f.grid(row=i, column=0, sticky="ew", padx=S(4), pady=S(1))
            f.grid_columnconfigure(0, weight=1)
            l1 = tk.Frame(f, bg=BG3); l1.grid(row=0, column=0, sticky="ew", padx=S(6), pady=(S(4),S(1)))
            l1.grid_columnconfigure(1, weight=1)
            tk.Label(l1, text="●", font=(FM, F(7)), bg=BG3, fg=d["cor"]).grid(row=0, column=0)
            tk.Label(l1, text=ticker, font=(FM, F(9), "bold"), bg=BG3, fg=TEXTO
                     ).grid(row=0, column=1, padx=S(2), sticky="w")
            lp = tk.Label(l1, text=f"R${d['preco']:.2f}", font=(FM, F(9), "bold"), bg=BG3, fg=TEXTO)
            lp.grid(row=0, column=2, sticky="e")
            l2 = tk.Frame(f, bg=BG3); l2.grid(row=1, column=0, sticky="ew", padx=S(6), pady=(0,S(4)))
            l2.grid_columnconfigure(0, weight=1)
            tk.Label(l2, text=d["nome"][:16], font=(FM, F(7)), bg=BG3, fg=TEXT2
                     ).grid(row=0, column=0, sticky="w")
            lv = tk.Label(l2, text="0.00%", font=(FM, F(7), "bold"), bg=BG3, fg=TEXT2)
            lv.grid(row=0, column=1, sticky="e")
            for w in [f, l1, l2]: w.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            self.fa[ticker] = {"f":f,"l1":l1,"l2":l2,"lp":lp,"lv":lv,"ref":d["preco"]}

    #COLUNA CENTRAL
    def _col_centro(self, body):
        centro = tk.Frame(body, bg=BG); centro.grid(row=0, column=1, sticky="nsew")
        centro.grid_rowconfigure(2, weight=1); centro.grid_columnconfigure(0, weight=1)
        hg = tk.Frame(centro, bg=BG, height=S(38))
        hg.grid(row=0, column=0, sticky="ew", padx=S(6), pady=(S(4),0)); hg.grid_propagate(False)
        hg.grid_columnconfigure(1, weight=1)
        self.lbl_hdr = tk.Label(hg, text="VALE3 — Vale S.A.", font=(FM, F(10), "bold"), bg=BG, fg=TEXTO)
        self.lbl_hdr.grid(row=0, column=0, sticky="w")
        self.lbl_ohlc = tk.Label(hg, text="", font=(FM, F(7)), bg=BG, fg=TEXT2)
        self.lbl_ohlc.grid(row=0, column=1, padx=S(6), sticky="w")
        self.lbl_vgrande = tk.Label(hg, text="▲ 0.00%", font=(FM, F(9)), bg=BG, fg=VERDE)
        self.lbl_vgrande.grid(row=0, column=2, sticky="e", padx=(0,S(4)))
        self.lbl_pgrande = tk.Label(hg, text="R$ 68.50", font=(FM, F(15), "bold"), bg=BG, fg=VERDE)
        self.lbl_pgrande.grid(row=0, column=3, sticky="e", padx=(0,S(6)))
        cv_h = max(S(160), int(WIN_H * 0.26))
        self.cv_main = tk.Canvas(centro, bg=BG, highlightthickness=0, height=cv_h)
        self.cv_main.grid(row=1, column=0, sticky="ew", padx=S(6), pady=S(3))
        tk.Frame(centro, bg=GRADE, height=1).grid(row=1, column=0, sticky="sew", padx=S(6))
        tk.Label(centro, text="TODAS AS AÇÕES — DATA SECTION COMPARTILHADA (slide 4.1)",
                 font=(FM, F(7), "bold"), bg=BG, fg=TEXT2
                 ).grid(row=1, column=0, sticky="sw", padx=S(9), pady=(S(2),0))
        grd = tk.Frame(centro, bg=BG); grd.grid(row=2, column=0, sticky="nsew", padx=S(4), pady=S(3))
        for col in range(5): grd.grid_columnconfigure(col, weight=1)
        for row in range(2): grd.grid_rowconfigure(row, weight=1)
        self.mini = {}
        for i, ticker in enumerate(TICKERS):
            row, col = divmod(i, 5)
            cell = tk.Frame(grd, bg=BG3)
            cell.grid(row=row, column=col, padx=S(2), pady=S(2), sticky="nsew")
            cell.grid_columnconfigure(0, weight=1); cell.grid_rowconfigure(1, weight=1)
            hc = tk.Frame(cell, bg=BG3); hc.grid(row=0, column=0, sticky="ew", padx=S(3), pady=(S(3),0))
            hc.grid_columnconfigure(1, weight=1)
            tk.Label(hc, text=ticker, font=(FM, F(8), "bold"),
                     bg=BG3, fg=ACOES[ticker]["cor"]).grid(row=0, column=0, sticky="w")
            lmv = tk.Label(hc, text="0.00%", font=(FM, F(7), "bold"), bg=BG3, fg=TEXT2)
            lmv.grid(row=0, column=2, sticky="e")
            lmp = tk.Label(hc, text=f"R${ACOES[ticker]['preco']:.2f}", font=(FM, F(7)), bg=BG3, fg=TEXTO)
            lmp.grid(row=0, column=1, sticky="e", padx=S(2))
            cv = tk.Canvas(cell, bg=BG3, highlightthickness=0)
            cv.grid(row=1, column=0, sticky="nsew", padx=S(2), pady=(S(1),S(3)))
            for w in [cell, hc, cv]: w.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            self.mini[ticker] = {"cv": cv, "lp": lmp, "lv": lmv}

    #COLUNA DIREITA — 4 ABAS 
    def _col_direita(self, body):
        dc = tk.Frame(body, bg=BG2); dc.grid(row=0, column=2, sticky="nsew")
        dc.grid_rowconfigure(0, weight=1); dc.grid_columnconfigure(0, weight=1)
        style = ttk.Style(); style.theme_use("default")
        style.configure("D.TNotebook",     background=BG2, borderwidth=0)
        style.configure("D.TNotebook.Tab", background=BG3, foreground=TEXT3,
                        font=(FM, F(7), "bold"), padding=[S(5), S(3)])
        style.map("D.TNotebook.Tab", background=[("selected",BG4)], foreground=[("selected",AMAR)])
        nb = ttk.Notebook(dc, style="D.TNotebook")
        nb.grid(row=0, column=0, sticky="nsew", padx=S(3), pady=S(4))

        # ABA 1: NOTÍCIAS
        tab_n = tk.Frame(nb, bg=BG2)
        nb.add(tab_n, text="⚡ NOTÍCIAS")
        tab_n.grid_rowconfigure(1, weight=1); tab_n.grid_columnconfigure(0, weight=1)
        tk.Label(tab_n,
                 text="Cada notícia = 1 thread",
                 font=(FM, F(7)), bg=BG2, fg=TEXT3
                 ).grid(row=0, column=0, padx=S(6), pady=(S(5),S(3)), sticky="w")
        ff = tk.Frame(tab_n, bg=BG2); ff.grid(row=1, column=0, sticky="nsew", padx=S(4))
        ff.grid_columnconfigure(0, weight=1)
        self.feed = []
        for i in range(8):
            ff.grid_rowconfigure(i, weight=1)
            fn = tk.Frame(ff, bg=BG3); fn.grid(row=i, column=0, sticky="ew", pady=S(1))
            fn.grid_columnconfigure(1, weight=1)
            li = tk.Label(fn, text="", font=(FM, F(7), "bold"), bg=BG3, fg=AMAR, width=6, anchor="w")
            li.grid(row=0, column=0, padx=(S(5),0), pady=(S(3),S(1)))
            ld = tk.Label(fn, text="", font=(FM, F(6)), bg=BG3, fg=TEXT2)
            ld.grid(row=0, column=2, padx=S(3))
            lt = tk.Label(fn, text="—", font=(FM, F(8)), bg=BG3, fg=TEXT2,
                          wraplength=S(290), justify="left", anchor="w")
            lt.grid(row=1, column=0, columnspan=3, padx=S(5), pady=(0,S(3)), sticky="w")
            self.feed.append((li, ld, lt, fn))

        # ABA 2: LOG DE THREADS
        tab_t = tk.Frame(nb, bg=BG2)
        nb.add(tab_t, text="🔧 ESTADOS")
        tab_t.grid_rowconfigure(1, weight=1); tab_t.grid_columnconfigure(0, weight=1)
        # Legenda de estados (slide 4.1)
        leg = tk.Frame(tab_t, bg=BG2); leg.grid(row=0, column=0, sticky="ew", padx=S(5), pady=S(3))
        leg.grid_columnconfigure(0, weight=1)
        tk.Label(leg, text="Estados das Threads",
                 font=(FM, F(7), "bold"), bg=BG2, fg=TEXT3).grid(row=0, column=0, columnspan=4, sticky="w")
        for i, (nome, (cor, desc)) in enumerate(ESTADOS.items()):
            tk.Label(leg, text=f"■ {nome}", font=(FM, F(7), "bold"),
                     bg=BG2, fg=cor).grid(row=1+i//3, column=i%3, padx=S(3), sticky="w")
        lf = tk.Frame(tab_t, bg=BG2); lf.grid(row=1, column=0, sticky="nsew", padx=S(4), pady=(0,S(4)))
        lf.grid_rowconfigure(0, weight=1); lf.grid_columnconfigure(0, weight=1)
        self.log_txt = tk.Text(lf, bg="#05080F", fg=TEXT2, font=(FM, F(8)),
                               relief="flat", state="disabled", wrap="none")
        sb = tk.Scrollbar(lf, command=self.log_txt.yview, bg=BG3, width=S(8))
        self.log_txt.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns"); self.log_txt.grid(row=0, column=0, sticky="nsew")
        for nome, (cor, _) in ESTADOS.items():
            self.log_txt.tag_configure(nome, foreground=cor)
        self.log_txt.tag_configure("tid", foreground=ROXO)
        self.log_txt.tag_configure("ts",  foreground="#374151")
        self.log_txt.tag_configure("det", foreground=TEXT3)

        # ── ABA 3: GERENCIADOR DE PROCESSOS 
        tab_p = tk.Frame(nb, bg=BG2)
        nb.add(tab_p, text="🖥 PROCESSO")
        tab_p.grid_rowconfigure(3, weight=1); tab_p.grid_columnconfigure(0, weight=1)

        # Título académico
        tk.Label(tab_p,
                 text="Modelo UM-para-UM\n"
                      "Cada User Thread → 1 Thread (visível no SO)",
                 font=(FM, F(7)), bg=BG2, fg=AZUL, justify="left"
                 ).grid(row=0, column=0, padx=S(6), pady=(S(5),S(2)), sticky="w")

        # Processo
        ph = tk.Frame(tab_p, bg="#0D1A2A")
        ph.grid(row=1, column=0, sticky="ew", padx=S(4))
        for ct, w in [("NOME",10),("PID",7),("STATUS",10),("THR SO",7),("THR SIM",7),("TRAVAM.",7)]:
            tk.Label(ph, text=ct, font=(FM, F(7), "bold"), bg="#0D1A2A", fg=AZUL,
                     width=w, anchor="w").pack(side="left", padx=S(2), pady=S(3))
        pr = tk.Frame(tab_p, bg=BG3); pr.grid(row=2, column=0, sticky="ew", padx=S(4), pady=(S(1),S(4)))
        self.proc_cells = {}
        for key, w in [("nome",10),("pid",7),("status",10),("thr_so",7),("thr_sim",7),("trav",7)]:
            lb = tk.Label(pr, text="", font=(FM, F(8)), bg=BG3, fg=TEXTO, width=w, anchor="w")
            lb.pack(side="left", padx=S(2), pady=S(4)); self.proc_cells[key] = lb
        tk.Frame(tab_p, bg=GRADE, height=1).grid(row=2, column=0, sticky="sew", padx=S(4))

        # Tabela de threads (Stack individual de cada thread)
        tk.Label(tab_p,
                 text="Threads ativas — cada uma com Stack e PC próprios",
                 font=(FM, F(7), "bold"), bg=BG2, fg=TEXT2
                 ).grid(row=2, column=0, padx=S(6), pady=(S(36),S(2)), sticky="w")
        th = tk.Frame(tab_p, bg="#0D1A2A")
        th.grid(row=2, column=0, sticky="sew", padx=S(4), pady=(S(56),0))
        for ct, w in [("Thread ID",11),("SO ident",12),("Estado",12),("Stack(dur)",10)]:
            tk.Label(th, text=ct, font=(FM, F(7), "bold"), bg="#0D1A2A", fg=AZUL,
                     width=w, anchor="w").pack(side="left", padx=S(2), pady=S(2))
        tf = tk.Frame(tab_p, bg=BG2)
        tf.grid(row=3, column=0, sticky="nsew", padx=S(4), pady=(S(1),S(4)))
        tf.grid_columnconfigure(0, weight=1)
        self.thr_rows = []
        for i in range(20):
            tf.grid_rowconfigure(i, weight=1)
            row = tk.Frame(tf, bg=BG3 if i%2==0 else "#0F1820")
            row.grid(row=i, column=0, sticky="ew", pady=1)
            cells = {}
            for key, w in [("tid",11),("so_id",12),("estado",12),("dur",10)]:
                lb = tk.Label(row, text="", font=(FM, F(7)), bg=row["bg"], fg=TEXT2, width=w, anchor="w")
                lb.pack(side="left", padx=S(2), pady=S(1)); cells[key] = lb
            self.thr_rows.append((row, cells))

        #ABA 4: LEGENDA
        tab_l = tk.Frame(nb, bg=BG2)
        nb.add(tab_l, text="❓ LEGENDA")
        tab_l.grid_rowconfigure(0, weight=1); tab_l.grid_columnconfigure(0, weight=1)
        self._build_legenda(tab_l)

    def _build_legenda(self, frame):
        lf = tk.Frame(frame, bg=BG2)
        lf.grid(row=0, column=0, sticky="nsew")
        lf.grid_rowconfigure(0, weight=1); lf.grid_columnconfigure(0, weight=1)
        txt = tk.Text(lf, bg="#05080F", fg=TEXTO, font=(FM, F(8)),
                      relief="flat", wrap="word", state="normal", padx=S(8), pady=S(6))
        sb  = tk.Scrollbar(lf, command=txt.yview, bg=BG3, width=S(8))
        txt.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns"); txt.grid(row=0, column=0, sticky="nsew")
        txt.tag_configure("T", foreground=AMAR, font=(FM, F(8), "bold"))
        txt.tag_configure("K", foreground=AZUL,  font=(FM, F(8), "bold"))
        txt.tag_configure("D", foreground=TEXT2, font=(FM, F(8)))
        itens = [
            ("T","CABEÇALHO"),
            ("K","PID: XXXXX"),
            ("D","  Identificador único do processo no SO.\n Gerenciador de Tarefas → filtre por python.exe."),
            ("K","SO: N threads"),
            ("D","  Threads REAIS medidas via threading.active_count().\n  Sobe quando você aumenta o slider — visível no Gerenciador."),
            ("K","SIM: N  COL: N  VOL: N×  TRAV: N"),
            ("D","  Threads da simulação | Colisões no mutex | Volatilidade | Travamentos detectados"),
            ("T",""),("T","CONTROLES"),
            ("K","Slider THREADS (1–22) — Modelo UM-para-UM"),
            ("D","  Cada thread = 1 Thread real do SO.\n"
                 "  Verde ≤12: normal | Amarelo ≤18: alto overhead | Vermelho >18: risco de travar!"),
            ("K","Slider VOL (0.2–5.0×)"),
            ("D","  Multiplica o impacto de cada notícia nos preços."),
            ("K","▶ START / ⏸ PAUSE"),
            ("D","  Inicia ou pausa a simulação."),
            ("K","↺ RESET"),
            ("D","  Zera preços, candles, logs e contadores."),
            ("K","⚡ NOTÍCIA"),
            ("D","  Dispara 1 notícia manualmente (1 Thread)."),
            ("K","CANDLE 1s/2s/5s"),
            ("D","  Intervalo de fechamento das velas japonesas."),
            ("T",""),("T","GRÁFICO CANDLESTICK (OHLC)"),
            ("K","Vela verde"),
            ("D","  Fechamento (C) > Abertura (O) no período."),
            ("K","Vela vermelha"),
            ("D","  Fechamento (C) < Abertura (O) no período."),
            ("K","Corpo da vela"),
            ("D","  Diferença visual entre Abertura e Fechamento."),
            ("K","Pavio / Sombra (linha fina)"),
            ("D","  Máxima (H) e Mínima (L) atingidas no período."),
            ("K","Linha tracejada colorida"),
            ("D","  Preço atual em tempo real da ação."),
            ("K","O  H  L  C no cabeçalho"),
            ("D","  Open, High, Low, Close do candle em formação."),
            ("T",""),("T","MINI-GRID — TODAS AS AÇÕES"),
            ("K","Grid 2×5"),
            ("D","  Cada célula = 1 ação com candlestick próprio.\n"
                 "  Clique em qualquer célula para abrir no gráfico principal.\n"
                 "  Todas sofrem impacto simultâneo das notícias (Data Section compartilhada)."),
            ("T",""),("T","ABA ⚡ NOTÍCIAS"),
            ("K","[CRÍT] / [ALTA] / [MÉDI]"),
            ("D","  Intensidade da notícia — CRÍTICA, ALTA ou MÉDIA."),
            ("K","Data (ex: 2022-02-24)"),
            ("D","  Data histórica real do evento de mercado.\n  'GERADA' = notícia gerada."),
            ("T",""),("T","ABA 🔧 ESTADOS — LOG DE THREADS"),
            ("K","Thread-N"),
            ("D","  Nome da thread no estilo Java (Thread.currentThread().getName()).\n"
                 "  Cada thread possui Thread ID próprio (slide 4.1)."),
            ("K","NOVA"),
            ("D","  Thread instanciada, ainda não iniciada."),
            ("K","PRONTA"),
            ("D","  Na fila do escalonador — aguardando acesso à CPU (RUNNABLE)."),
            ("K","DISPUTANDO"),
            ("D","  Tentando adquirir o mutex. Se ocupado, BLOQUEIA aqui.\n"
                 "  Isso demonstra a colisão / contenção na seção crítica."),
            ("K","EXECUTANDO"),
            ("D","  Mutex adquirido — acesso exclusivo à Data Section.\n"
                 "  Equivale ao estado RUNNING no diagrama de estados de threads."),
            ("K","CALCULANDO"),
            ("D","  Lendo e calculando impacto nos preços (seção crítica)."),
            ("K","APLICANDO"),
            ("D","  Escrevendo novos preços na Data Section compartilhada."),
            ("K","LIBERANDO → TERMINADA"),
            ("D","  Mutex liberado. Stack e Heap da thread são desalocadas."),
            ("T",""),("T","ABA 🖥 PROCESSO — GERENCIADOR"),
            ("K","Thread ID / SO ident"),
            ("D","  Thread ID = sequencial da simulação.\n"
                 "  SO ident = thread.ident — identificador real atribuído pelo Kernel.\n"
                 "  Modelo UM-para-UM: cada Thread ID → 1 Thread"),
            ("K","THR SO"),
            ("D","  Threads reais do processo — mesma coluna 'Threads'\n"
                 "  que aparece no Gerenciador de Tarefas do Windows."),
            ("K","THR SIM"),
            ("D","  Threads configuradas no slider da simulação."),
            ("K","TRAVAM."),
            ("D","  Contador de vezes que uma thread detectou overhead excessivo.\n"
                 "  Demonstra a desvantagem do modelo UM-para-UM"),
            ("K","Estado (tabela de threads ativas)"),
            ("D","  Cada linha = 1 Thread em execução.\n"
                 "  Stack(dur) = tempo total que esta thread já está rodando\n"
                 "  (representa o uso da Stack própria de cada thread)."),
        ]
        for tag, texto in itens:
            txt.insert("end", f"{texto}\n", tag)
        txt.config(state="disabled")

    def _footer(self):
        f = tk.Frame(self.root, bg="#04070E", height=S(28))
        f.grid(row=3, column=0, sticky="ew"); f.grid_propagate(False)
        f.grid_columnconfigure(1, weight=1)
        self.lbl_fl = tk.Label(f, text="", font=(FM, F(7)), bg="#04070E", fg=TEXT2)
        self.lbl_fl.grid(row=0, column=0, padx=S(10), pady=S(4))
        tk.Label(f, text=f"Modelo UM-para-UM | {SCR_W}×{SCR_H} | Escala {SCALE:.2f}×",
                 font=(FM, F(7)), bg="#04070E", fg=TEXT2).grid(row=0, column=1)
        self.lbl_fr = tk.Label(f, text="", font=(FM, F(7), "bold"), bg="#04070E", fg=AMAR)
        self.lbl_fr.grid(row=0, column=2, padx=S(10))

    # CONTROLES
    def _on_thr(self, v):
        n = int(float(v)); estado.num_threads = n
        self.lbl_thr.config(text=f"{n:2d}")
        # 4 faixas progressivas — cada uma com comportamento diferente
        if n <= 4:
            self.lbl_aviso.config(text=f"● Mercado normal  ({n} Kernel Threads)", fg=VERDE)
        elif n <= LIMITE_AVISO:
            self.lbl_aviso.config(text=f"◆ Mercado agitado ({n} threads — caos crescente)", fg="#80FF80")
        elif n <= LIMITE_PERIGO:
            self.lbl_aviso.config(text=f"⚠ Mercado em pânico! ({n} threads — UI vai lentificar)", fg=AMAR)
        else:
            self.lbl_aviso.config(text=f"⛔ PERIGO! {n} threads → TRAVAMENTO REAL!", fg=VERM)

    def _toggle(self):
        estado.rodando = not estado.rodando
        self.btn.config(text="⏸ PAUSE" if estado.rodando else "▶ START",
                        bg=VERM if estado.rodando else VERDE)

    def _reset(self):
        estado.rodando = False; self.btn.config(text="▶ START", bg=VERDE)
        with estado.lock:
            for t, d in ACOES.items():
                estado.precos[t] = d["preco"]; estado.candles[t] = []
                estado.candle_cur[t] = Candle(d["preco"])
            estado.noticias.clear(); estado.colisoes = 0
            estado.total = 0; estado.travamentos = 0
        with estado.threads_lock: estado.threads_vivas.clear()
        self.prev_p = {t: d["preco"] for t, d in ACOES.items()}
        for t in self.fa: self.fa[t]["ref"] = ACOES[t]["preco"]
        self.log_txt.config(state="normal"); self.log_txt.delete("1.0","end")
        self.log_txt.config(state="disabled"); ThreadNoticia._cnt = 0

    def _sel(self, t): self.acao_sel.set(t); self.lbl_hdr.config(text=f"{t} — {ACOES[t]['nome']}")

    #LOG
    def _flush_log(self):
        """Lê até 12 mensagens da fila por frame. Limita para não travar a UI."""
        processados = 0
        try:
            while processados < 12:
                e = estado.ui_q.get_nowait()
                self.log_txt.config(state="normal")
                ts  = datetime.fromtimestamp(e["ts"]).strftime("%H:%M:%S.%f")[:-3]
                est = e["estado"]
                self.log_txt.insert("end", f"[{ts}] ", "ts")
                self.log_txt.insert("end", f"{e['nome']:<12}", "tid")
                self.log_txt.insert("end", f"► {est:<12}", est)
                if e["detalhe"]:
                    self.log_txt.insert("end", f"  {e['detalhe'][:52]}", "det")
                self.log_txt.insert("end", "\n")
                self.log_txt.config(state="disabled")
                processados += 1
        except queue.Empty:
            pass
        if processados > 0:
            self.log_txt.config(state="normal")
            self.log_txt.see("end")
            lines = int(self.log_txt.index("end-1c").split(".")[0])
            if lines > 400:
                self.log_txt.delete("1.0", "80.0")
            self.log_txt.config(state="disabled")

    def _update_proc(self):
        n_so  = threads_so(); n_sim = estado.num_threads
        cor_s = VERM if n_so >= LIMITE_PERIGO else (AMAR if n_so >= LIMITE_AVISO else VERDE)
        st    = "Em execução" if estado.rodando else "Pausado"
        self.proc_cells["nome"  ].config(text="python.exe", fg=CIAN)
        self.proc_cells["pid"   ].config(text=str(PID),     fg=AMAR)
        self.proc_cells["status"].config(text=st, fg=VERDE if estado.rodando else TEXT2)
        self.proc_cells["thr_so"].config(text=str(n_so),    fg=cor_s)
        self.proc_cells["thr_sim"].config(text=str(n_sim),  fg=AZUL)
        self.proc_cells["trav"  ].config(text=str(estado.travamentos), fg=VERM if estado.travamentos>0 else TEXT2)
        with estado.threads_lock: vivas = list(estado.threads_vivas)
        for i, (row, cells) in enumerate(self.thr_rows):
            if i < len(vivas):
                t = vivas[i]; dur = time.time() - t.ts_inicio
                cor_e, _ = ESTADOS.get(t.estado_thr, (TEXT2, ""))
                cells["tid"  ].config(text=t.nome,                  fg=ROXO)
                cells["so_id"].config(text=str(t.so_ident or "—")[:12], fg=TEXT3)
                cells["estado"].config(text=t.estado_thr,            fg=cor_e)
                cells["dur"  ].config(text=f"{dur:.2f}s",           fg=TEXT2)
                for cv in cells.values(): cv.config(bg=row["bg"])
            else:
                for cv in cells.values(): cv.config(text="")

    #UPDATE PRINCIPAL
    def _update(self):
        now = time.time(); sel = self.acao_sel.get()

        # Contador de frames — usado para rotacionar tarefas pesadas
        if not hasattr(self, "_frame"): self._frame = 0
        self._frame += 1

        self._flush_log()
        # Painel de processo só atualiza a cada 3 frames (300ms) — menos pesado
        if self._frame % 3 == 0:
            self._update_proc()

        self.lbl_hora.config(text=datetime.now().strftime("%d/%m  %H:%M:%S"))
        n_so = threads_so()
        cor_so = VERM if n_so>=LIMITE_PERIGO else (AMAR if n_so>=LIMITE_AVISO else VERDE)
        self.lbl_so.config(text=f"SO:{n_so}thr", fg=cor_so)
        self.lbl_stats.config(
            text=f"SIM:{estado.num_threads}t  COL:{estado.colisoes}  VOL:{estado.volatilidade:.1f}×  TRAV:{estado.travamentos}")
        for ticker, comp in self.fa.items():
            p = estado.precos.get(ticker,0); var=(p-comp["ref"])/comp["ref"]*100
            cor=VERDE if var>=0 else VERM; sig="▲" if var>=0 else "▼"
            comp["lp"].config(text=f"R${p:.2f}",fg=cor)
            comp["lv"].config(text=f"{sig}{abs(var):.1f}%",fg=cor)
            bg = "#0D2218" if (ticker in self.flash and now<self.flash[ticker] and var>=0) \
                 else "#220A0A" if (ticker in self.flash and now<self.flash[ticker]) \
                 else "#111C2E" if ticker==sel else BG3
            comp["f"].config(bg=bg); comp["l1"].config(bg=bg); comp["l2"].config(bg=bg)
        p=estado.precos.get(sel,0); ref=ACOES[sel]["preco"]
        var=(p-ref)/ref*100; cor=VERDE if var>=0 else VERM
        self.lbl_pgrande.config(text=f"R$ {p:.2f}",fg=cor)
        self.lbl_vgrande.config(text=f"{'▲' if var>=0 else '▼'} {abs(var):.2f}%",fg=cor)
        cd=estado.candle_cur.get(sel)
        if cd: self.lbl_ohlc.config(text=f"O:{cd.o:.2f}  H:{cd.h:.2f}  L:{cd.l:.2f}  C:{cd.c:.2f}")
        for ticker in estado.precos:
            if abs(estado.precos[ticker]-self.prev_p.get(ticker,0))>0.01:
                self.flash[ticker]=now+0.35
        self.prev_p=dict(estado.precos)

        # Gráfico principal — redesenha todo frame
        draw_candles(self.cv_main, sel)

        # Mini-grid — redesenha a cada 2 frames (200ms) para reduzir carga da UI
        # Os 10 canvases simultâneos são o maior custo de CPU da interface
        if self._frame % 2 == 0:
            for ticker, mc in self.mini.items():
                draw_candles(mc["cv"],ticker)
                p2=estado.precos.get(ticker,0); ref2=ACOES[ticker]["preco"]
                var2=(p2-ref2)/ref2*100; cor2=VERDE if var2>=0 else VERM
                mc["lp"].config(text=f"R${p2:.2f}",fg=cor2)
                mc["lv"].config(text=f"{'▲' if var2>=0 else '▼'}{abs(var2):.1f}%",fg=cor2)

        noticias=list(estado.noticias)
        for i,(li,ld,lt,fn) in enumerate(self.feed):
            if i<len(noticias):
                n=noticias[i]; idade=now-n["ts"]; cor_n=n["cor"] if idade<4 else TEXT2
                li.config(text=f"[{n['intensidade'][:4]}]",fg=cor_n)
                ld.config(text=n.get("data",""))
                lt.config(text=n["texto"],fg=cor_n)
                fn.config(bg=BG4 if idade<0.5 else BG3)
            else:
                li.config(text=""); ld.config(text=""); lt.config(text="—",fg=TEXT2); fn.config(bg=BG2)
        n=estado.num_threads; bar="█"*n+"░"*max(0,LIMITE_MAXIMO-n)
        self.lbl_fl.config(text=f"SIM [{bar}] {n}t")
        self.lbl_fr.config(text=f"↯ {estado.total} notícias  |  {estado.colisoes} colisões")
        # Intervalo de UI proporcional ao nível de caos:
        # Poucas threads → 80ms (suave) | Muitas threads → 120ms (já está travando mesmo)
        n_thr = estado.num_threads
        ms = 80 if n_thr <= 8 else (100 if n_thr <= 14 else 120)
        self.root.after(ms, self._update)

# MAIN
def main():
    # Inicia as 4 threads daemon de background:
    # loop_ruido: flutuações contínuas de preço
    # loop_noticias: rajadas de N threads simultâneas (SEM join)
    # loop_candles: fecha velas periodicamente
    # loop_espontaneo: threads individuais em momentos aleatórios (breaking news)
    for fn in [loop_ruido, loop_noticias, loop_candles, loop_espontaneo]:
        threading.Thread(target=fn, daemon=True).start()
    root = tk.Tk()
    HomeBroker(root)
 
    root.mainloop()

if __name__ == "__main__":
    main()
