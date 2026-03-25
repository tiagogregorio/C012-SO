"""INTERFACE PRINCIPAL (extraida do simulador monolitico)."""

import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime

from config import CORES, ACOES, TICKERS, ESTADOS_THREAD, LIMITES_THREAD, PID
from models import Candle
from engine import ThreadNoticia


def _detectar():
    tmp = tk.Tk(); tmp.withdraw()
    sw, sh = tmp.winfo_screenwidth(), tmp.winfo_screenheight()
    tmp.destroy()
    f = max(0.60, min(sh / 1080.0, 2.0))
    return f, sw, sh, min(int(1560 * f), sw - 30), min(int(940 * f), sh - 50)


SCALE, SCR_W, SCR_H, WIN_W, WIN_H = _detectar()


def S(x):
    return max(1, int(x * SCALE))


def F(x):
    return max(7, int(x * SCALE))


BG = CORES["BG_PRINCIPAL"]
BG2 = CORES["BG_SECUNDARIO"]
BG3 = CORES["BG_CARD"]
BG4 = CORES["BG_HOVER"]
VERDE = CORES["ALTA"]
VERD2 = CORES["ALTA_DARK"]
VERM = CORES["BAIXA"]
VERM2 = CORES["BAIXA_DARK"]
AMAR = CORES["ALERTA"]
AZUL = CORES["INFO"]
ROXO = CORES["DESTAQUE"]
TEXTO = CORES["TEXTO_PRIMARIO"]
TEXT2 = CORES["TEXTO_SECUNDARIO"]
TEXT3 = CORES["TEXTO_MUTED"]
GRADE = CORES["LINHA_GRADE"]
FM = "Courier New"


def threads_so():
    return threading.active_count()


def draw_candles(cv, ticker, estado):
    cv.delete("all")
    w = cv.winfo_width()
    h = cv.winfo_height()
    if w < 20 or h < 10:
        return
    all_c = list(estado.historico_candles[ticker]) + [estado.candle_atual[ticker]]
    if not all_c:
        return
    ml, mr, mt, mb = S(50), S(4), S(4), S(14)
    aw = w - ml - mr
    ah = h - mt - mb
    for i in range(5):
        cv.create_line(ml, mt + i * ah // 4, w - mr, mt + i * ah // 4, fill=GRADE, dash=(2, 4))
    prices = [p for c in all_c for p in (c.h, c.l)]
    mn = min(prices) * 0.999
    mx = max(prices) * 1.001
    rng = mx - mn if mx != mn else 1.0

    def py(v):
        return mt + int((1 - (v - mn) / rng) * ah)

    mv = max(1, aw // S(8))
    vis = all_c[-mv:]
    n = len(vis)
    step = aw / max(n, 1)
    cw = max(2, min(int(step * 0.6), S(12)))
    for i, c in enumerate(vis):
        xc = ml + int(i * step + step / 2)
        cor = VERD2 if c.c >= c.o else VERM2
        cv.create_line(xc, py(c.h), xc, py(c.l), fill=cor, width=1)
        y0 = min(py(c.o), py(c.c))
        y1 = max(py(c.o), py(c.c))
        cv.create_rectangle(xc - cw // 2, y0, xc + cw // 2, max(y1, y0 + 1), fill=cor, outline=cor)
    for i in range(5):
        cv.create_text(ml - 2, mt + i * ah // 4, text=f"{mx - (i / 4) * rng:.2f}", font=(FM, F(6)), fill=TEXT2, anchor="e")
    p = estado.precos[ticker]
    cv.create_line(ml, py(p), w - mr, py(p), fill=ACOES[ticker]["cor"], dash=(3, 4), width=1)


class HomeBroker:
    def __init__(self, root, mercado):
        self.root = root
        self.mercado = mercado
        root.title(f"SIMULAÇÃO CAÓTICA DO MERCADO FINANCEIRO UTILIZANDO THREADS  [{SCR_W}×{SCR_H}]")
        root.configure(bg=BG)
        root.geometry(f"{WIN_W}x{WIN_H}")
        root.minsize(S(1000), S(680))
        self.acao_sel = tk.StringVar(value="VALE3")
        self.prev_p = {t: d["preco"] for t, d in ACOES.items()}
        self.flash = {}
        self._build()
        self._update()

    def _build(self):
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._header()
        self._controles()
        tk.Frame(self.root, bg=GRADE, height=1).grid(row=1, column=0, sticky="sew")
        self._corpo()
        self._footer()

    def _header(self):
        h = tk.Frame(self.root, bg=BG, height=S(46))
        h.grid(row=0, column=0, sticky="ew")
        h.grid_propagate(False)
        h.grid_columnconfigure(1, weight=1)
        tk.Label(h, text="SIMULAÇÃO CAÓTICA DO MERCADO FINANCEIRO UTILIZANDO THREADS", font=(FM, F(12), "bold"), bg=BG, fg=AMAR).grid(row=0, column=0, padx=S(10), pady=S(7), sticky="w")
        info = tk.Frame(h, bg=BG)
        info.grid(row=0, column=2, padx=S(8), sticky="e")
        self.lbl_stats = tk.Label(info, text="", font=(FM, F(8)), bg=BG, fg=TEXT3)
        self.lbl_stats.pack(side="left", padx=S(6))
        tk.Frame(info, bg=GRADE, width=1, height=S(22)).pack(side="left", pady=S(8))
        self.lbl_pid = tk.Label(info, text=f"PID:{PID}", font=(FM, F(9), "bold"), bg=BG, fg=AZUL)
        self.lbl_pid.pack(side="left", padx=S(6))
        tk.Frame(info, bg=AMAR, width=2, height=S(22)).pack(side="left", pady=S(8))
        self.lbl_so = tk.Label(info, text="SO: — thr", font=(FM, F(9), "bold"), bg=BG, fg=VERDE)
        self.lbl_so.pack(side="left", padx=S(6))
        tk.Frame(info, bg=GRADE, width=1, height=S(22)).pack(side="left", pady=S(8))
        self.lbl_hora = tk.Label(info, text="", font=(FM, F(8)), bg=BG, fg=TEXT2)
        self.lbl_hora.pack(side="left", padx=S(6))

    def _controles(self):
        c = tk.Frame(self.root, bg=BG2, height=S(50))
        c.grid(row=1, column=0, sticky="ew")
        c.grid_propagate(False)
        col = 0

        def nxt():
            nonlocal col
            col += 1
            return col - 1

        tk.Label(c, text="THREADS (UM-para-UM):", font=(FM, F(8), "bold"), bg=BG2, fg=TEXT3).grid(row=0, column=nxt(), padx=(S(10), S(2)), pady=S(12))
        self.var_thr = tk.IntVar(value=4)
        self.lbl_thr = tk.Label(c, text=" 4", font=(FM, F(13), "bold"), bg=BG2, fg=AMAR, width=3)
        self.lbl_thr.grid(row=0, column=nxt())
        ttk.Scale(c, from_=1, to=LIMITES_THREAD["MAXIMO"], orient="horizontal", length=S(170), variable=self.var_thr, command=self._on_thr).grid(row=0, column=nxt(), padx=(S(2), S(10)))

        self.lbl_aviso = tk.Label(c, text="", font=(FM, F(8), "bold"), bg=BG2, fg=VERDE, width=35, anchor="w")
        self.lbl_aviso.grid(row=0, column=nxt(), padx=S(4))

        tk.Label(c, text="VOL:", font=(FM, F(8), "bold"), bg=BG2, fg=TEXT3).grid(row=0, column=nxt(), padx=(S(4), S(2)))
        self.var_vol = tk.DoubleVar(value=1.0)
        self.lbl_vol = tk.Label(c, text="1.0×", font=(FM, F(9), "bold"), bg=BG2, fg=AMAR, width=5)
        self.lbl_vol.grid(row=0, column=nxt())
        ttk.Scale(c, from_=0.2, to=5.0, orient="horizontal", length=S(100), variable=self.var_vol, command=lambda v: [setattr(self.mercado, "volatilidade", float(v)), self.lbl_vol.config(text=f"{float(v):.1f}×")]).grid(row=0, column=nxt(), padx=(S(2), S(10)))

        self.btn = tk.Button(c, text="▶ START", font=(FM, F(9), "bold"), bg=VERDE, fg=BG, relief="flat", padx=S(8), command=self._toggle)
        self.btn.grid(row=0, column=nxt(), padx=S(3))
        tk.Button(c, text="↺ RESET", font=(FM, F(9)), bg=BG3, fg=TEXT3, relief="flat", padx=S(8), command=self._reset).grid(row=0, column=nxt(), padx=S(3))
        tk.Button(c, text="⚡ NOTÍCIA", font=(FM, F(9), "bold"), bg=BG4, fg=AZUL, relief="flat", padx=S(6), command=lambda: ThreadNoticia(self.mercado).start()).grid(row=0, column=nxt(), padx=S(3))
        tk.Label(c, text="│ CANDLE:", font=(FM, F(8)), bg=BG2, fg=TEXT2).grid(row=0, column=nxt(), padx=(S(10), S(2)))
        for lbl2, val in [("1s", 1), ("2s", 2), ("5s", 5)]:
            tk.Button(c, text=lbl2, font=(FM, F(8)), bg=BG3, fg=TEXT3, relief="flat", width=3, command=lambda v=val: setattr(self.mercado, "candle_intervalo", v)).grid(row=0, column=nxt(), padx=1)

    def _corpo(self,):
        body = tk.Frame(self.root, bg=BG)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=13, minsize=S(160))
        body.grid_columnconfigure(1, weight=55)
        body.grid_columnconfigure(2, weight=32, minsize=S(290))
        body.grid_rowconfigure(0, weight=1)
        self._col_acoes(body)
        self._col_centro(body)
        self._col_direita(body)

    def _col_acoes(self, body):
        esq = tk.Frame(body, bg=BG2)
        esq.grid(row=0, column=0, sticky="nsew")
        esq.grid_rowconfigure(1, weight=1)
        esq.grid_columnconfigure(0, weight=1)
        tk.Label(esq, text="TOP 10  IBOVESPA", font=(FM, F(7), "bold"), bg=BG2, fg=TEXT2).grid(row=0, column=0, padx=S(8), pady=(S(6), S(2)), sticky="w")
        sa = tk.Frame(esq, bg=BG2)
        sa.grid(row=1, column=0, sticky="nsew")
        sa.grid_columnconfigure(0, weight=1)
        self.fa = {}
        for i, (ticker, d) in enumerate(ACOES.items()):
            f = tk.Frame(sa, bg=BG3, cursor="hand2")
            f.grid(row=i, column=0, sticky="ew", padx=S(4), pady=S(1))
            f.grid_columnconfigure(0, weight=1)
            l1 = tk.Frame(f, bg=BG3)
            l1.grid(row=0, column=0, sticky="ew", padx=S(6), pady=(S(4), S(1)))
            l1.grid_columnconfigure(1, weight=1)
            tk.Label(l1, text="●", font=(FM, F(7)), bg=BG3, fg=d["cor"]).grid(row=0, column=0)
            tk.Label(l1, text=ticker, font=(FM, F(9), "bold"), bg=BG3, fg=TEXTO).grid(row=0, column=1, padx=S(2), sticky="w")
            lp = tk.Label(l1, text=f"R${d['preco']:.2f}", font=(FM, F(9), "bold"), bg=BG3, fg=TEXTO)
            lp.grid(row=0, column=2, sticky="e")
            l2 = tk.Frame(f, bg=BG3)
            l2.grid(row=1, column=0, sticky="ew", padx=S(6), pady=(0, S(4)))
            l2.grid_columnconfigure(0, weight=1)
            tk.Label(l2, text=d["nome"][:16], font=(FM, F(7)), bg=BG3, fg=TEXT2).grid(row=0, column=0, sticky="w")
            lv = tk.Label(l2, text="0.00%", font=(FM, F(7), "bold"), bg=BG3, fg=TEXT2)
            lv.grid(row=0, column=1, sticky="e")
            for w in [f, l1, l2]:
                w.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            self.fa[ticker] = {"f": f, "l1": l1, "l2": l2, "lp": lp, "lv": lv, "ref": d["preco"]}

    def _col_centro(self, body):
        centro = tk.Frame(body, bg=BG)
        centro.grid(row=0, column=1, sticky="nsew")
        centro.grid_rowconfigure(2, weight=1)
        centro.grid_columnconfigure(0, weight=1)
        hg = tk.Frame(centro, bg=BG, height=S(38))
        hg.grid(row=0, column=0, sticky="ew", padx=S(6), pady=(S(4), 0))
        hg.grid_propagate(False)
        hg.grid_columnconfigure(1, weight=1)
        self.lbl_hdr = tk.Label(hg, text="VALE3 — Vale S.A.", font=(FM, F(10), "bold"), bg=BG, fg=TEXTO)
        self.lbl_hdr.grid(row=0, column=0, sticky="w")
        self.lbl_ohlc = tk.Label(hg, text="", font=(FM, F(7)), bg=BG, fg=TEXT2)
        self.lbl_ohlc.grid(row=0, column=1, padx=S(6), sticky="w")
        self.lbl_vgrande = tk.Label(hg, text="▲ 0.00%", font=(FM, F(9)), bg=BG, fg=VERDE)
        self.lbl_vgrande.grid(row=0, column=2, sticky="e", padx=(0, S(4)))
        self.lbl_pgrande = tk.Label(hg, text="R$ 68.50", font=(FM, F(15), "bold"), bg=BG, fg=VERDE)
        self.lbl_pgrande.grid(row=0, column=3, sticky="e", padx=(0, S(6)))
        cv_h = max(S(160), int(WIN_H * 0.26))
        self.cv_main = tk.Canvas(centro, bg=BG, highlightthickness=0, height=cv_h)
        self.cv_main.grid(row=1, column=0, sticky="ew", padx=S(6), pady=S(3))
        tk.Frame(centro, bg=GRADE, height=1).grid(row=1, column=0, sticky="sew", padx=S(6))
        tk.Label(centro, text="TODAS AS AÇÕES — DATA SECTION COMPARTILHADA (slide 4.1)", font=(FM, F(7), "bold"), bg=BG, fg=TEXT2).grid(row=1, column=0, sticky="sw", padx=S(9), pady=(S(2), 0))
        grd = tk.Frame(centro, bg=BG)
        grd.grid(row=2, column=0, sticky="nsew", padx=S(4), pady=S(3))
        for col in range(5):
            grd.grid_columnconfigure(col, weight=1)
        for row in range(2):
            grd.grid_rowconfigure(row, weight=1)
        self.mini = {}
        for i, ticker in enumerate(TICKERS):
            row, col = divmod(i, 5)
            cell = tk.Frame(grd, bg=BG3)
            cell.grid(row=row, column=col, padx=S(2), pady=S(2), sticky="nsew")
            cell.grid_columnconfigure(0, weight=1)
            cell.grid_rowconfigure(1, weight=1)
            hc = tk.Frame(cell, bg=BG3)
            hc.grid(row=0, column=0, sticky="ew", padx=S(3), pady=(S(3), 0))
            hc.grid_columnconfigure(1, weight=1)
            tk.Label(hc, text=ticker, font=(FM, F(8), "bold"), bg=BG3, fg=ACOES[ticker]["cor"]).grid(row=0, column=0, sticky="w")
            lmv = tk.Label(hc, text="0.00%", font=(FM, F(7), "bold"), bg=BG3, fg=TEXT2)
            lmv.grid(row=0, column=2, sticky="e")
            lmp = tk.Label(hc, text=f"R${ACOES[ticker]['preco']:.2f}", font=(FM, F(7)), bg=BG3, fg=TEXTO)
            lmp.grid(row=0, column=1, sticky="e", padx=S(2))
            cv = tk.Canvas(cell, bg=BG3, highlightthickness=0)
            cv.grid(row=1, column=0, sticky="nsew", padx=S(2), pady=(S(1), S(3)))
            for w in [cell, hc, cv]:
                w.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            self.mini[ticker] = {"cv": cv, "lp": lmp, "lv": lmv}

    def _col_direita(self, body):
        dc = tk.Frame(body, bg=BG2)
        dc.grid(row=0, column=2, sticky="nsew")
        dc.grid_rowconfigure(0, weight=1)
        dc.grid_columnconfigure(0, weight=1)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("D.TNotebook", background=BG2, borderwidth=0)
        style.configure("D.TNotebook.Tab", background=BG3, foreground=TEXT3, font=(FM, F(7), "bold"), padding=[S(5), S(3)])
        style.map("D.TNotebook.Tab", background=[("selected", BG4)], foreground=[("selected", AMAR)])
        nb = ttk.Notebook(dc, style="D.TNotebook")
        nb.grid(row=0, column=0, sticky="nsew", padx=S(3), pady=S(4))

        tab_n = tk.Frame(nb, bg=BG2)
        nb.add(tab_n, text="⚡ NOTÍCIAS")
        tab_n.grid_rowconfigure(1, weight=1)
        tab_n.grid_columnconfigure(0, weight=1)
        tk.Label(tab_n, text="Cada notícia = 1 thread", font=(FM, F(7)), bg=BG2, fg=TEXT3).grid(row=0, column=0, padx=S(6), pady=(S(5), S(3)), sticky="w")
        ff = tk.Frame(tab_n, bg=BG2)
        ff.grid(row=1, column=0, sticky="nsew", padx=S(4))
        ff.grid_columnconfigure(0, weight=1)
        self.feed = []
        for i in range(8):
            ff.grid_rowconfigure(i, weight=1)
            fn = tk.Frame(ff, bg=BG3)
            fn.grid(row=i, column=0, sticky="ew", pady=S(1))
            fn.grid_columnconfigure(1, weight=1)
            li = tk.Label(fn, text="", font=(FM, F(7), "bold"), bg=BG3, fg=AMAR, width=6, anchor="w")
            li.grid(row=0, column=0, padx=(S(5), 0), pady=(S(3), S(1)))
            ld = tk.Label(fn, text="", font=(FM, F(6)), bg=BG3, fg=TEXT2)
            ld.grid(row=0, column=2, padx=S(3))
            lt = tk.Label(fn, text="—", font=(FM, F(8)), bg=BG3, fg=TEXT2, wraplength=S(290), justify="left", anchor="w")
            lt.grid(row=1, column=0, columnspan=3, padx=S(5), pady=(0, S(3)), sticky="w")
            self.feed.append((li, ld, lt, fn))

        tab_t = tk.Frame(nb, bg=BG2)
        nb.add(tab_t, text="🔧 ESTADOS")
        tab_t.grid_rowconfigure(1, weight=1)
        tab_t.grid_columnconfigure(0, weight=1)
        leg = tk.Frame(tab_t, bg=BG2)
        leg.grid(row=0, column=0, sticky="ew", padx=S(5), pady=S(3))
        leg.grid_columnconfigure(0, weight=1)
        tk.Label(leg, text="Estados das Threads", font=(FM, F(7), "bold"), bg=BG2, fg=TEXT3).grid(row=0, column=0, columnspan=4, sticky="w")
        for i, (nome, (cor, desc)) in enumerate(ESTADOS_THREAD.items()):
            tk.Label(leg, text=f"■ {nome}", font=(FM, F(7), "bold"), bg=BG2, fg=cor).grid(row=1 + i // 3, column=i % 3, padx=S(3), sticky="w")
        lf = tk.Frame(tab_t, bg=BG2)
        lf.grid(row=1, column=0, sticky="nsew", padx=S(4), pady=(0, S(4)))
        lf.grid_rowconfigure(0, weight=1)
        lf.grid_columnconfigure(0, weight=1)
        self.log_txt = tk.Text(lf, bg="#05080F", fg=TEXT2, font=(FM, F(8)), relief="flat", state="disabled", wrap="none")
        sb = tk.Scrollbar(lf, command=self.log_txt.yview, bg=BG3, width=S(8))
        self.log_txt.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        self.log_txt.grid(row=0, column=0, sticky="nsew")
        for nome, (cor, _) in ESTADOS_THREAD.items():
            self.log_txt.tag_configure(nome, foreground=cor)
        self.log_txt.tag_configure("tid", foreground=ROXO)
        self.log_txt.tag_configure("ts", foreground="#374151")
        self.log_txt.tag_configure("det", foreground=TEXT3)

        tab_p = tk.Frame(nb, bg=BG2)
        nb.add(tab_p, text="🖥 PROCESSO")
        tab_p.grid_rowconfigure(3, weight=1)
        tab_p.grid_columnconfigure(0, weight=1)
        tk.Label(tab_p, text="Modelo UM-para-UM\nCada User Thread → 1 Thread (visível no SO)", font=(FM, F(7)), bg=BG2, fg=AZUL, justify="left").grid(row=0, column=0, padx=S(6), pady=(S(5), S(2)), sticky="w")
        ph = tk.Frame(tab_p, bg="#0D1A2A")
        ph.grid(row=1, column=0, sticky="ew", padx=S(4))
        for ct, w in [("NOME", 10), ("PID", 7), ("STATUS", 10), ("THR SO", 7), ("THR SIM", 7), ("TRAVAM.", 7)]:
            tk.Label(ph, text=ct, font=(FM, F(7), "bold"), bg="#0D1A2A", fg=AZUL, width=w, anchor="w").pack(side="left", padx=S(2), pady=S(3))
        pr = tk.Frame(tab_p, bg=BG3)
        pr.grid(row=2, column=0, sticky="ew", padx=S(4), pady=(S(1), S(4)))
        self.proc_cells = {}
        for key, w in [("nome", 10), ("pid", 7), ("status", 10), ("thr_so", 7), ("thr_sim", 7), ("trav", 7)]:
            lb = tk.Label(pr, text="", font=(FM, F(8)), bg=BG3, fg=TEXTO, width=w, anchor="w")
            lb.pack(side="left", padx=S(2), pady=S(4))
            self.proc_cells[key] = lb
        tk.Frame(tab_p, bg=GRADE, height=1).grid(row=2, column=0, sticky="sew", padx=S(4))
        tk.Label(tab_p, text="Threads ativas — cada uma com Stack e PC próprios", font=(FM, F(7), "bold"), bg=BG2, fg=TEXT2).grid(row=2, column=0, padx=S(6), pady=(S(36), S(2)), sticky="w")
        th = tk.Frame(tab_p, bg="#0D1A2A")
        th.grid(row=2, column=0, sticky="sew", padx=S(4), pady=(S(56), 0))
        for ct, w in [("Thread ID", 11), ("SO ident", 12), ("Estado", 12), ("Stack(dur)", 10)]:
            tk.Label(th, text=ct, font=(FM, F(7), "bold"), bg="#0D1A2A", fg=AZUL, width=w, anchor="w").pack(side="left", padx=S(2), pady=S(2))
        tf = tk.Frame(tab_p, bg=BG2)
        tf.grid(row=3, column=0, sticky="nsew", padx=S(4), pady=(S(1), S(4)))
        tf.grid_columnconfigure(0, weight=1)
        self.thr_rows = []
        for i in range(20):
            tf.grid_rowconfigure(i, weight=1)
            row = tk.Frame(tf, bg=BG3 if i % 2 == 0 else "#0F1820")
            row.grid(row=i, column=0, sticky="ew", pady=1)
            cells = {}
            for key, w in [("tid", 11), ("so_id", 12), ("estado", 12), ("dur", 10)]:
                lb = tk.Label(row, text="", font=(FM, F(7)), bg=row["bg"], fg=TEXT2, width=w, anchor="w")
                lb.pack(side="left", padx=S(2), pady=S(1))
                cells[key] = lb
            self.thr_rows.append((row, cells))

        tab_l = tk.Frame(nb, bg=BG2)
        nb.add(tab_l, text="❓ LEGENDA")
        tab_l.grid_rowconfigure(0, weight=1)
        tab_l.grid_columnconfigure(0, weight=1)
        self._build_legenda(tab_l)

    def _build_legenda(self, frame):
        lf = tk.Frame(frame, bg=BG2)
        lf.grid(row=0, column=0, sticky="nsew")
        lf.grid_rowconfigure(0, weight=1)
        lf.grid_columnconfigure(0, weight=1)
        txt = tk.Text(lf, bg="#05080F", fg=TEXTO, font=(FM, F(8)), relief="flat", wrap="word", state="normal", padx=S(8), pady=S(6))
        sb = tk.Scrollbar(lf, command=txt.yview, bg=BG3, width=S(8))
        txt.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        txt.grid(row=0, column=0, sticky="nsew")
        txt.tag_configure("T", foreground=AMAR, font=(FM, F(8), "bold"))
        txt.tag_configure("K", foreground=AZUL, font=(FM, F(8), "bold"))
        txt.tag_configure("D", foreground=TEXT2, font=(FM, F(8)))
        itens = [
            ("T", "CABEÇALHO"),
            ("K", "PID: XXXXX"),
            ("D", "  Identificador único do processo no SO.\n Gerenciador de Tarefas → filtre por python.exe."),
            ("K", "SO: N threads"),
            ("D", "  Threads REAIS medidas via threading.active_count().\n  Sobe quando você aumenta o slider — visível no Gerenciador."),
        ]
        for tag, texto in itens:
            txt.insert("end", f"{texto}\n", tag)
        txt.config(state="disabled")

    def _footer(self):
        f = tk.Frame(self.root, bg="#04070E", height=S(28))
        f.grid(row=3, column=0, sticky="ew")
        f.grid_propagate(False)
        f.grid_columnconfigure(1, weight=1)
        self.lbl_fl = tk.Label(f, text="", font=(FM, F(7)), bg="#04070E", fg=TEXT2)
        self.lbl_fl.grid(row=0, column=0, padx=S(10), pady=S(4))
        tk.Label(f, text=f"Modelo UM-para-UM | {SCR_W}×{SCR_H} | Escala {SCALE:.2f}×", font=(FM, F(7)), bg="#04070E", fg=TEXT2).grid(row=0, column=1)
        self.lbl_fr = tk.Label(f, text="", font=(FM, F(7), "bold"), bg="#04070E", fg=AMAR)
        self.lbl_fr.grid(row=0, column=2, padx=S(10))

    def _on_thr(self, v):
        n = int(float(v))
        self.mercado.num_threads_config = n
        self.lbl_thr.config(text=f"{n:2d}")
        if n <= 4:
            self.lbl_aviso.config(text=f"● Mercado normal  ({n} Kernel Threads)", fg=VERDE)
        elif n <= LIMITES_THREAD["AVISO"]:
            self.lbl_aviso.config(text=f"◆ Mercado agitado ({n} threads — caos crescente)", fg="#80FF80")
        elif n <= LIMITES_THREAD["PERIGO"]:
            self.lbl_aviso.config(text=f"⚠ Mercado em pânico! ({n} threads — UI vai lentificar)", fg=AMAR)
        else:
            self.lbl_aviso.config(text=f"⛔ PERIGO! {n} threads → TRAVAMENTO REAL!", fg=VERM)

    def _toggle(self):
        self.mercado.rodando = not self.mercado.rodando
        self.btn.config(text="⏸ PAUSE" if self.mercado.rodando else "▶ START", bg=VERM if self.mercado.rodando else VERDE)

    def _reset(self):
        self.mercado.rodando = False
        self.btn.config(text="▶ START", bg=VERDE)
        with self.mercado.lock:
            for t, d in ACOES.items():
                self.mercado.precos[t] = d["preco"]
                self.mercado.historico_candles[t] = []
                self.mercado.candle_atual[t] = Candle(d["preco"])
            self.mercado.noticias.clear()
            self.mercado.colisoes = 0
            self.mercado.total_noticias = 0
            self.mercado.travamentos_detectados = 0
        with self.mercado.threads_lock:
            self.mercado.threads_vivas.clear()
        self.prev_p = {t: d["preco"] for t, d in ACOES.items()}
        for t in self.fa:
            self.fa[t]["ref"] = ACOES[t]["preco"]
        self.log_txt.config(state="normal")
        self.log_txt.delete("1.0", "end")
        self.log_txt.config(state="disabled")
        ThreadNoticia._contador_id = 0

    def _sel(self, t):
        self.acao_sel.set(t)
        self.lbl_hdr.config(text=f"{t} — {ACOES[t]['nome']}")

    def _flush_log(self):
        processados = 0
        try:
            while processados < 12:
                e = self.mercado.ui_queue.get_nowait()
                self.log_txt.config(state="normal")
                ts = datetime.fromtimestamp(e["ts"]).strftime("%H:%M:%S.%f")[:-3]
                est = e["estado"]
                self.log_txt.insert("end", f"[{ts}] ", "ts")
                self.log_txt.insert("end", f"{e['nome']:<12}", "tid")
                self.log_txt.insert("end", f"► {est:<12}", est)
                if e["detalhe"]:
                    self.log_txt.insert("end", f"  {e['detalhe'][:52]}", "det")
                self.log_txt.insert("end", "\n")
                self.log_txt.config(state="disabled")
                processados += 1
        except Exception:
            pass
        if processados > 0:
            self.log_txt.config(state="normal")
            self.log_txt.see("end")
            lines = int(self.log_txt.index("end-1c").split(".")[0])
            if lines > 400:
                self.log_txt.delete("1.0", "80.0")
            self.log_txt.config(state="disabled")

    def _update_proc(self):
        n_so = threads_so()
        n_sim = self.mercado.num_threads_config
        cor_s = VERM if n_so >= LIMITES_THREAD["PERIGO"] else (AMAR if n_so >= LIMITES_THREAD["AVISO"] else VERDE)
        st = "Em execução" if self.mercado.rodando else "Pausado"
        self.proc_cells["nome"].config(text="python.exe", fg=AZUL)
        self.proc_cells["pid"].config(text=str(PID), fg=AMAR)
        self.proc_cells["status"].config(text=st, fg=VERDE if self.mercado.rodando else TEXT2)
        self.proc_cells["thr_so"].config(text=str(n_so), fg=cor_s)
        self.proc_cells["thr_sim"].config(text=str(n_sim), fg=AZUL)
        self.proc_cells["trav"].config(text=str(self.mercado.travamentos_detectados), fg=VERM if self.mercado.travamentos_detectados > 0 else TEXT2)
        with self.mercado.threads_lock:
            vivas = list(self.mercado.threads_vivas)
        for i, (row, cells) in enumerate(self.thr_rows):
            if i < len(vivas):
                t = vivas[i]
                dur = time.time() - t.ts_inicio
                cor_e, _ = ESTADOS_THREAD.get(t.estado_atual, (TEXT2, ""))
                cells["tid"].config(text=t.nome_thread, fg=ROXO)
                cells["so_id"].config(text=str(t.ident or "—")[:12], fg=TEXT3)
                cells["estado"].config(text=t.estado_atual, fg=cor_e)
                cells["dur"].config(text=f"{dur:.2f}s", fg=TEXT2)
                for cv in cells.values():
                    cv.config(bg=row["bg"])
            else:
                for cv in cells.values():
                    cv.config(text="")

    def _update(self):
        now = time.time()
        sel = self.acao_sel.get()
        if not hasattr(self, "_frame"):
            self._frame = 0
        self._frame += 1

        self._flush_log()
        if self._frame % 3 == 0:
            self._update_proc()

        self.lbl_hora.config(text=datetime.now().strftime("%d/%m  %H:%M:%S"))
        n_so = threads_so()
        cor_so = VERM if n_so >= LIMITES_THREAD["PERIGO"] else (AMAR if n_so >= LIMITES_THREAD["AVISO"] else VERDE)
        self.lbl_so.config(text=f"SO:{n_so}thr", fg=cor_so)
        self.lbl_stats.config(text=f"SIM:{self.mercado.num_threads_config}t  COL:{self.mercado.colisoes}  VOL:{self.mercado.volatilidade:.1f}×  TRAV:{self.mercado.travamentos_detectados}")
        for ticker, comp in self.fa.items():
            p = self.mercado.precos.get(ticker, 0)
            var = (p - comp["ref"]) / comp["ref"] * 100
            cor = VERDE if var >= 0 else VERM
            sig = "▲" if var >= 0 else "▼"
            comp["lp"].config(text=f"R${p:.2f}", fg=cor)
            comp["lv"].config(text=f"{sig}{abs(var):.1f}%", fg=cor)
            bg = "#0D2218" if (ticker in self.flash and now < self.flash[ticker] and var >= 0) else "#220A0A" if (ticker in self.flash and now < self.flash[ticker]) else "#111C2E" if ticker == sel else BG3
            comp["f"].config(bg=bg)
            comp["l1"].config(bg=bg)
            comp["l2"].config(bg=bg)
        p = self.mercado.precos.get(sel, 0)
        ref = ACOES[sel]["preco"]
        var = (p - ref) / ref * 100
        cor = VERDE if var >= 0 else VERM
        self.lbl_pgrande.config(text=f"R$ {p:.2f}", fg=cor)
        self.lbl_vgrande.config(text=f"{'▲' if var >= 0 else '▼'} {abs(var):.2f}%", fg=cor)
        cd = self.mercado.candle_atual.get(sel)
        if cd:
            self.lbl_ohlc.config(text=f"O:{cd.o:.2f}  H:{cd.h:.2f}  L:{cd.l:.2f}  C:{cd.c:.2f}")
        for ticker in self.mercado.precos:
            if abs(self.mercado.precos[ticker] - self.prev_p.get(ticker, 0)) > 0.01:
                self.flash[ticker] = now + 0.35
        self.prev_p = dict(self.mercado.precos)

        draw_candles(self.cv_main, sel, self.mercado)
        if self._frame % 2 == 0:
            for ticker, mc in self.mini.items():
                draw_candles(mc["cv"], ticker, self.mercado)
                p2 = self.mercado.precos.get(ticker, 0)
                ref2 = ACOES[ticker]["preco"]
                var2 = (p2 - ref2) / ref2 * 100
                cor2 = VERDE if var2 >= 0 else VERM
                mc["lp"].config(text=f"R${p2:.2f}", fg=cor2)
                mc["lv"].config(text=f"{'▲' if var2 >= 0 else '▼'}{abs(var2):.1f}%", fg=cor2)

        noticias = list(self.mercado.noticias)
        for i, (li, ld, lt, fn) in enumerate(self.feed):
            if i < len(noticias):
                n = noticias[i]
                idade = now - n["ts"]
                cor_n = n["cor"] if idade < 4 else TEXT2
                li.config(text=f"[{n['intensidade'][:4]}]", fg=cor_n)
                ld.config(text=n.get("data", ""))
                lt.config(text=n["texto"], fg=cor_n)
                fn.config(bg=BG4 if idade < 0.5 else BG3)
            else:
                li.config(text="")
                ld.config(text="")
                lt.config(text="—", fg=TEXT2)
                fn.config(bg=BG2)
        n = self.mercado.num_threads_config
        bar = "█" * n + "░" * max(0, LIMITES_THREAD["MAXIMO"] - n)
        self.lbl_fl.config(text=f"SIM [{bar}] {n}t")
        self.lbl_fr.config(text=f"↯ {self.mercado.total_noticias} notícias  |  {self.mercado.colisoes} colisões")
        ms = 80 if n <= 8 else (100 if n <= 14 else 120)
        self.root.after(ms, self._update)