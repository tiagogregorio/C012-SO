"""
Interface gráfica principal (HomeBroker)(abas).
"""
import tkinter as tk
from tkinter import ttk
import threading
import time
import queue
from datetime import datetime

from config import (BG, BG2, BG3, BG4, VERDE, VERD2, VERM, AMAR, AZUL,
                    LARA, CIAN, ROXO, TEXT2, TEXT3, FM, S, F,
                    get_font, _update_all_fonts, ACOES, PID, SCALE)
from state import G
from threads import ThreadExecutora
from widgets import draw_candles, WidgetGantt, WidgetTimeline
import config


class HomeBroker:
    def __init__(self, root):
        self.root        = root
        self._resize_job = None
        root.title("MERCADO FINANCEIRO — Escalonamento + Sincronização — INATEL")
        root.configure(bg=BG)
        root.geometry(f"{config.WIN_W}x{config.WIN_H}")
        root.minsize(S(700), S(450))
        root.resizable(True, True)
        self.acao_sel = tk.StringVar(value="VALE3")
        self.prev_p   = {t: d["preco"] for t, d in ACOES.items()}
        self.flash    = {}
        self._build()
        root.bind("<Configure>", self._on_resize)
        self._update()

    # ─── LAYOUT PRINCIPAL ─────────────────────────────────────────────────
    def _build(self):
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_columnconfigure(0, weight=1)
        self._header()
        self._controles()
        tk.Frame(self.root, bg="#1E293B", height=1).grid(row=1, column=0, sticky="ew")
        self._notebook_principal()
        self._footer()

    # ─── HEADER ───────────────────────────────────────────────────────────
    def _header(self):
        h = tk.Frame(self.root, bg=BG, height=S(44))
        h.grid(row=0, column=0, sticky="ew"); h.grid_propagate(False)
        h.grid_columnconfigure(1, weight=1)
        self._frame_header = h
        tk.Label(h, text="MERCADO FINANCEIRO — Scheduling de CPU + Sincronização",
                 font=get_font(11, "bold"), bg=BG, fg=AMAR
                 ).grid(row=0, column=0, padx=S(10), pady=S(6), sticky="w")
        inf = tk.Frame(h, bg=BG); inf.grid(row=0, column=2, padx=S(8), sticky="e")
        self.lbl_inf = tk.Label(inf, text="", font=get_font(11), bg=BG, fg=TEXT3)
        self.lbl_inf.pack(side="left", padx=S(5))
        tk.Label(inf, text=f"PID:{PID}", font=get_font(9,"bold"), bg=BG, fg=CIAN).pack(side="left", padx=S(5))
        self.lbl_so = tk.Label(inf, text="THR:—", font=get_font(9,"bold"), bg=BG, fg=VERDE)
        self.lbl_so.pack(side="left", padx=S(5))
        self.lbl_hora = tk.Label(inf, text="", font=get_font(11), bg=BG, fg=TEXT2)
        self.lbl_hora.pack(side="left", padx=S(5))

    # ─── CONTROLES ────────────────────────────────────────────────────────
    def _controles(self):
        c = tk.Frame(self.root, bg=BG2, height=S(54))
        c.grid(row=1, column=0, sticky="ew"); c.grid_propagate(False)
        self._frame_controls = c
        col = 0
        def nxt(): nonlocal col; col += 1; return col-1
        def _sl(lb, var, lo, hi, ln, cb, cor=AMAR, ini=""):
            tk.Label(c, text=lb, font=get_font(8,"bold"), bg=BG2, fg=TEXT3
                     ).grid(row=0, column=nxt(), padx=(S(8),S(2)), pady=S(12))
            l = tk.Label(c, text=ini, font=get_font(10,"bold"), bg=BG2, fg=cor, width=5)
            l.grid(row=0, column=nxt())
            ttk.Scale(c, from_=lo, to=hi, orient="horizontal", length=ln, variable=var, command=cb
                      ).grid(row=0, column=nxt(), padx=(S(2),S(6))); return l
        self.var_taxa = tk.DoubleVar(value=5.0)
        self.lbl_taxa = _sl("CHEGADA:", self.var_taxa, 1, 15, S(90),
            lambda v: [setattr(G,"taxa_chegada",float(v)), self.lbl_taxa.config(text=f"{float(v):.0f}s")], ini="5s")
        self.var_lim = tk.IntVar(value=8)
        self.lbl_lim = _sl("FILA MAX:", self.var_lim, 3, 15, S(80),
            lambda v: [setattr(G,"limite_fila",int(float(v))), self.lbl_lim.config(text=str(int(float(v))))], cor=LARA, ini="8")
        self.var_vol = tk.DoubleVar(value=1.0)
        self.lbl_vol = _sl("VOL:", self.var_vol, 0.2, 4.0, S(70),
            lambda v: [setattr(G,"volatilidade",float(v)), self.lbl_vol.config(text=f"{float(v):.1f}x")], cor=VERDE, ini="1.0x")
        self.var_rr = tk.IntVar(value=3)
        self.lbl_rr = _sl("RR-Q:", self.var_rr, 1, 10, S(70),
            lambda v: [setattr(G,"quantum_rr",int(float(v))), self.lbl_rr.config(text=f"{int(float(v))}u")], cor=ROXO, ini="3u")
        self.btn_play = tk.Button(c, text="INICIAR", font=get_font(9,"bold"), bg=VERD2, fg=BG,
                                  relief="flat", padx=S(8), command=self._toggle_play)
        self.btn_play.grid(row=0, column=nxt(), padx=S(6))
        self.btn_sync = tk.Button(c, text="COM SYNC", font=get_font(9,"bold"), bg="#1A3A2A", fg=VERDE,
                                  relief="flat", padx=S(6), command=self._toggle_sync)
        self.btn_sync.grid(row=0, column=nxt(), padx=S(4))
        tk.Button(c, text="RESET", font=get_font(11), bg=BG4, fg=TEXT3,
                  relief="flat", padx=S(5), command=self._reset
                  ).grid(row=0, column=nxt(), padx=S(4))

    def _toggle_play(self):
        G.rodando = not G.rodando
        self.btn_play.config(text="PAUSAR" if G.rodando else "INICIAR",
                             bg=AMAR if G.rodando else VERD2, fg=BG)

    def _toggle_sync(self):
        G.modo_sync = not G.modo_sync
        self.btn_sync.config(
            text="COM SYNC" if G.modo_sync else "SEM SYNC",
            bg="#1A3A2A" if G.modo_sync else "#3A1A1A",
            fg=VERDE if G.modo_sync else VERM)

    def _reset(self):
        G.rodando = False
        self.btn_play.config(text="INICIAR", bg=VERD2, fg=BG)
        G.reset()
        ThreadExecutora._cnt = 0
        for t in self.fa: self.fa[t]["ref"] = ACOES[t]["preco"]
        self.prev_p = {t: d["preco"] for t, d in ACOES.items()}
        self.log_txt.config(state="normal");   self.log_txt.delete("1.0","end")
        self.log_txt.config(state="disabled")
        self.sched_txt.config(state="normal"); self.sched_txt.delete("1.0","end")
        self.sched_txt.config(state="disabled")

    def _sel(self, t):
        self.acao_sel.set(t)
        self.lbl_hdr.config(text=f"{t} — {ACOES[t]['nome']}")

    def _toggle_view(self):
        if self._view == "candles":
            self._view = "timeline"
            self.timeline.tkraise()
            self.btn_toggle.config(text="Candles")
        else:
            self._view = "candles"
            self._gf.tkraise()
            self.btn_toggle.config(text="Timeline")

    # ─── NOTEBOOK PRINCIPAL ───────────────────────────────────────────────
    def _notebook_principal(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Main.TNotebook", background=BG, borderwidth=0)
        style.configure("Main.TNotebook.Tab",
                        background=BG4, foreground=TEXT2,
                        font=("Courier New", F(10), "bold"),
                        padding=[S(16), S(8)])
        style.map("Main.TNotebook.Tab",
                  background=[("selected", BG2)],
                  foreground=[("selected", AMAR)])

        nb = ttk.Notebook(self.root, style="Main.TNotebook")
        nb.grid(row=2, column=0, sticky="nsew", padx=S(4), pady=(S(3), 0))
        self._nb_main = nb

        self._tab_escalonador(nb)
        self._tab_mercado(nb)
        self._tab_sincronizacao(nb)

    # ─── ABA 1: ESCALONADOR ───────────────────────────────────────────────
    def _tab_escalonador(self, nb):
        tab = tk.Frame(nb, bg=BG)
        nb.add(tab, text=" Escalonamento de CPU  ")
        tab.grid_rowconfigure(0, weight=0)
        tab.grid_rowconfigure(1, weight=0)
        tab.grid_rowconfigure(2, weight=0)
        tab.grid_rowconfigure(3, weight=0)
        tab.grid_rowconfigure(4, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        self._build_fila_compacta(tab, row=0)

        self.gantt_fcfs = WidgetGantt(tab, "1) FCFS — First Come, First Served", "#BBDEFB", "#0D47A1")
        self.gantt_fcfs.grid(row=1, column=0, sticky="ew", padx=S(4), pady=S(2))

        self.gantt_sjf = WidgetGantt(tab, "2) SJF — Shortest Job First", "#C8E6C9", "#1B5E20")
        self.gantt_sjf.grid(row=2, column=0, sticky="ew", padx=S(4), pady=S(2))

        self.gantt_rr = WidgetGantt(tab, "3) RR — Round Robin (Quantum = ? u)", "#FFE0B2", "#E65100")
        self.gantt_rr.grid(row=3, column=0, sticky="ew", padx=S(4), pady=S(2))

        lf = tk.Frame(tab, bg=BG2)
        lf.grid(row=4, column=0, sticky="nsew", padx=S(4), pady=(S(2), S(3)))
        lf.grid_rowconfigure(1, weight=1); lf.grid_columnconfigure(0, weight=1)
        hdr_s = tk.Frame(lf, bg=BG2); hdr_s.grid(row=0, column=0, sticky="ew", padx=S(6), pady=S(4))
        tk.Label(hdr_s, text="LOG DO ESCALONADOR", font=get_font(9,"bold"), bg=BG2, fg=TEXT2).pack(side="left")
        self.lbl_total = tk.Label(hdr_s, text="Exec:0", font=get_font(9), bg=BG2, fg=AMAR)
        self.lbl_total.pack(side="right")
        self.sched_txt = tk.Text(lf, font=get_font(9), bg=BG, fg=TEXT3, state="disabled", wrap="none")
        sb_s = ttk.Scrollbar(lf, orient="vertical", command=self.sched_txt.yview)
        self.sched_txt.configure(yscrollcommand=sb_s.set)
        self.sched_txt.grid(row=1, column=0, sticky="nsew", padx=(S(4),0), pady=(0,S(3)))
        sb_s.grid(row=1, column=1, sticky="ns", pady=(0,S(3)))
        self.sched_txt.tag_config("chegou", foreground=AZUL)
        self.sched_txt.tag_config("cpu",    foreground=VERDE)
        self.sched_txt.tag_config("rr",     foreground=AMAR)
        self.sched_txt.tag_config("done",   foreground=TEXT2)
        self.sched_txt.tag_config("ts",     foreground=TEXT2)

    # ─── ABA 2: MERCADO ───────────────────────────────────────────────────
    def _tab_mercado(self, nb):
        tab = tk.Frame(nb, bg=BG)
        nb.add(tab, text="  Mercado Financeiro / Time line  ")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=0)
        tab.grid_columnconfigure(1, weight=1)

        self._painel_acoes(tab)

        f = tk.Frame(tab, bg=BG)
        f.grid(row=0, column=1, sticky="nsew")
        f.grid_rowconfigure(0, weight=1)
        f.grid_columnconfigure(0, weight=1)

        wrap = tk.Frame(f, bg=BG)
        wrap.grid(row=0, column=0, sticky="nsew", padx=S(3), pady=S(3))
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        gf = tk.Frame(wrap, bg=BG2)
        gf.grid(row=0, column=0, sticky="nsew")
        gf.grid_rowconfigure(1, weight=1); gf.grid_columnconfigure(0, weight=1)
        self._gf = gf

        hdr = tk.Frame(gf, bg=BG2); hdr.grid(row=0, column=0, sticky="ew", padx=S(6))
        self.lbl_hdr = tk.Label(hdr, text="VALE3 — Vale S.A.", font=get_font(12,"bold"), bg=BG2, fg=AZUL)
        self.lbl_hdr.pack(side="left")
        self.btn_toggle = tk.Button(hdr, text="Timeline", font=get_font(8,"bold"),
            bg=BG4, fg=AMAR, relief="flat", padx=S(6), command=self._toggle_view)
        self.btn_toggle.pack(side="left", padx=(S(12), 0))
        self.lbl_pg = tk.Label(hdr, text="R$ —", font=get_font(14,"bold"), bg=BG2, fg=VERDE)
        self.lbl_pg.pack(side="right", padx=S(8))
        self.lbl_vg = tk.Label(hdr, text="—", font=get_font(10), bg=BG2, fg=TEXT2)
        self.lbl_vg.pack(side="right")
        self.lbl_ohlc = tk.Label(hdr, text="", font=get_font(11), bg=BG2, fg=TEXT2)
        self.lbl_ohlc.pack(side="right", padx=S(8))
        self.cv_main = tk.Canvas(gf, bg=BG2, highlightthickness=0)
        self.cv_main.grid(row=1, column=0, sticky="nsew")

        self.timeline = WidgetTimeline(wrap)
        self.timeline.grid(row=0, column=0, sticky="nsew")
        self._view = "candles"
        gf.tkraise()

    # ─── ABA 3: SINCRONIZACAO ─────────────────────────────────────────────
    def _tab_sincronizacao(self, nb):
        tab = tk.Frame(nb, bg=BG2)
        nb.add(tab, text=" Sincronizacao / Race Condition  ")
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=0)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=0)

        hdr_t = tk.Frame(tab, bg=BG2); hdr_t.grid(row=0, column=0, columnspan=2, sticky="ew", padx=S(6), pady=S(4))
        tk.Label(hdr_t, text="SECAO CRITICA — PRECOS DAS ACOES",
                 font=get_font(10,"bold"), bg=BG2, fg=TEXT2).pack(side="left")
        self.lbl_race = tk.Label(hdr_t, text="RACE:0", font=get_font(10,"bold"), bg=BG2, fg=TEXT2)
        self.lbl_race.pack(side="right", padx=S(8))

        self.log_txt = tk.Text(tab, font=get_font(10), bg=BG, fg=TEXT3,
                               state="disabled", wrap="none")
        sb_t = ttk.Scrollbar(tab, orient="vertical", command=self.log_txt.yview)
        self.log_txt.configure(yscrollcommand=sb_t.set)
        self.log_txt.grid(row=1, column=0, sticky="nsew", padx=(S(6),0), pady=(0,S(4)))
        sb_t.grid(row=1, column=1, sticky="ns", pady=(0,S(4)))

        for e, c in [("DISPUTANDO",AMAR),("EXECUTANDO",VERDE),("CALCULANDO",AZUL),
                     ("LIBERANDO",CIAN),("RACE",VERM)]:
            self.log_txt.tag_config(e, foreground=c)
        self.log_txt.tag_config("ts",   foreground=TEXT2)
        self.log_txt.tag_config("thr",  foreground=ROXO)
        self.log_txt.tag_config("proc", foreground=AZUL)
        self.log_txt.tag_config("det",  foreground=TEXT3)

        pv = tk.Frame(tab, bg=BG3)
        pv.grid(row=2, column=0, columnspan=2, sticky="ew", padx=S(6), pady=(0,S(6)))
        tk.Label(pv, text="THREADS ATIVAS AGORA", font=get_font(9,"bold"), bg=BG3, fg=TEXT2
                 ).pack(anchor="w", padx=S(6), pady=(S(4),0))
        tf = tk.Frame(pv, bg=BG3); tf.pack(fill="x", padx=S(6), pady=(0,S(4)))
        cabecalhos = ["Thread", "Processo", "Estado",       "Tempo"]
        larguras   = [10,       10,          18,             8]
        for j, (h_txt, w) in enumerate(zip(cabecalhos, larguras)):
            tk.Label(tf, text=h_txt, font=get_font(9,"bold"), bg=BG3, fg=TEXT2,
                     width=w, anchor="w").grid(row=0, column=j, padx=S(3), sticky="w")
        self.thr_rows = []
        for i in range(5):
            bg_r = BG4 if i%2==0 else BG3; cells = {}
            for j, (k, w) in enumerate(zip(["thr","proc","est","dur"], larguras)):
                lb = tk.Label(tf, text="", font=get_font(9), bg=bg_r, fg=TEXT2,
                              anchor="w", width=w)
                lb.grid(row=i+1, column=j, padx=S(3), sticky="w"); cells[k] = lb
            self.thr_rows.append(({"bg":bg_r}, cells))

    # ─── CARTEIRA ─────────────────────────────────────────────────────────
    def _painel_acoes(self, parent):
        f = tk.Frame(parent, bg=BG3, width=S(180))
        f.grid(row=0, column=0, sticky="nsew"); f.grid_propagate(False)
        self._panel_left = f
        tk.Label(f, text="CARTEIRA", font=get_font(9,"bold"), bg=BG3, fg=TEXT2
                 ).pack(pady=(S(6),S(3)))
        self.fa = {}
        for ticker, d in ACOES.items():
            fr = tk.Frame(f, bg=BG3, cursor="hand2"); fr.pack(fill="x", padx=S(4), pady=S(2))
            fr.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            l1 = tk.Label(fr, text=ticker, font=get_font(10,"bold"), bg=BG3, fg=d["cor"], anchor="w")
            l1.pack(fill="x", padx=S(5)); l1.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            l2 = tk.Label(fr, text="R$--", font=get_font(9), bg=BG3, fg=TEXT2, anchor="w")
            l2.pack(fill="x", padx=S(5)); l2.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            lv = tk.Label(fr, text="--", font=get_font(11), bg=BG3, fg=TEXT2, anchor="w")
            lv.pack(fill="x", padx=S(5)); lv.bind("<Button-1>", lambda e, t=ticker: self._sel(t))
            self.fa[ticker] = {"f":fr,"l1":l1,"lp":l2,"lv":lv,"ref":d["preco"]}

    # ─── FILA COMPACTA ────────────────────────────────────────────────────
    def _build_fila_compacta(self, parent, row=0):
        sf = tk.Frame(parent, bg=BG4, height=S(120))
        sf.grid(row=row, column=0, sticky="ew", padx=S(4), pady=S(2))
        sf.grid_propagate(False); sf.grid_columnconfigure(0, weight=1)
        self._frame_queue = sf

        hdr = tk.Frame(sf, bg=BG4); hdr.grid(row=0, column=0, sticky="ew", padx=S(8), pady=(S(3),0))
        tk.Label(hdr, text="READY QUEUE — Processos aguardando CPU",
                 font=get_font(9,"bold"), bg=BG4, fg=AMAR).pack(side="left")

        for txt, cor in [("Curto",VERD2),("Medio",AMAR),("Longo","#D50000")]:
            tk.Label(hdr, text=txt, font=get_font(8,"bold"), bg=BG4, fg=cor).pack(side="left", padx=S(8))

        self.var_algo = tk.StringVar(value="FCFS")
        for algo, cor in [("FCFS",AZUL),("SJF",VERDE),("RR",LARA)]:
            tk.Radiobutton(hdr, text=algo, variable=self.var_algo, value=algo,
                           bg=BG4, fg=cor, selectcolor=BG2, activebackground=BG4,
                           font=get_font(9,"bold"),
                           command=lambda a=algo: setattr(G,"algoritmo",a)
                           ).pack(side="left", padx=S(5))

        self.lbl_fila_n = tk.Label(hdr, text="FILA: 0", font=get_font(10,"bold"), bg=BG4, fg=AMAR)
        self.lbl_fila_n.pack(side="right", padx=S(8))

        cf = tk.Frame(sf, bg=BG3); cf.grid(row=1, column=0, sticky="ew", padx=S(8), pady=(S(3),S(5)))
        self.cv_fila = tk.Canvas(cf, bg=BG3, height=S(85), highlightthickness=0)
        sb = ttk.Scrollbar(cf, orient="horizontal", command=self.cv_fila.xview)
        self.cv_fila.configure(xscrollcommand=sb.set)
        self.cv_fila.pack(side="top", fill="x"); sb.pack(side="bottom", fill="x")

    # ─── FOOTER ───────────────────────────────────────────────────────────
    def _footer(self):
        ff = tk.Frame(self.root, bg=BG4, height=S(22))
        ff.grid(row=3, column=0, sticky="ew"); ff.grid_propagate(False)
        self._frame_footer = ff
        self.lbl_fl = tk.Label(ff, text="", font=get_font(11), bg=BG4, fg=TEXT2)
        self.lbl_fl.pack(side="left", padx=S(8))
        self.lbl_fr = tk.Label(ff, text="", font=get_font(11), bg=BG4, fg=TEXT2)
        self.lbl_fr.pack(side="right", padx=S(8))

    # ─── ESCALA DINAMICA ──────────────────────────────────────────────────
    def _on_resize(self, event):
        if event.widget is not self.root: return
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(150, self._apply_scale, event.width, event.height)

    def _apply_scale(self, win_w, win_h):
        new_scale = max(0.5, min(win_h / 1920.0, win_w / 1080.0, 2.0))
        if abs(new_scale - config.SCALE) < 0.015:
            return
        config.SCALE = new_scale
        _update_all_fonts()
        self._frame_header.config(height=S(44))
        self._frame_controls.config(height=S(54))
        self._frame_footer.config(height=S(22))
        self._frame_queue.config(height=S(84))
        self._panel_left.config(width=S(180))
        self.cv_fila.config(height=S(44))

    # ─── DESENHO DA FILA ──────────────────────────────────────────────────
    def _desenhar_fila(self):
        self.cv_fila.delete("all")
        w = self.cv_fila.winfo_width(); h = self.cv_fila.winfo_height()
        if w < 10 or h < 10: return

        BW = S(90); BH = h-S(20); GAP = S(6); Y0 = S(10); YC = Y0+BH//2; algo = G.algoritmo

        with G.mutex_fila: fila = list(G.ready_queue)
        with G.mutex_cpu:  no_cpu = G.no_cpu
        with G.mutex_hist: hist = list(G.historico_vis)[-3:]

        if algo == "FCFS":   fila_vis = sorted(fila, key=lambda p: p.t_chegada_sim)
        elif algo == "SJF":  fila_vis = sorted(fila, key=lambda p: p.restante)
        else:                fila_vis = list(fila)

        n = (len(fila_vis) + 1 + len(hist) + 3)
        sw = max(w, n*(BW+GAP)+S(140))
        self.cv_fila.configure(scrollregion=(0, 0, sw, h))

        x = S(4)
        self.cv_fila.create_text(x+S(14), YC, text="FILA",
                                  font=(FM,F(7),"bold"), fill=TEXT3, anchor="center"); x += S(36)

        def bloco_fila(px, proc, cpu=False):
            bg = proc.cor_gantt; brd = VERDE if cpu else "white"; bw = 2 if cpu else 1
            self.cv_fila.create_rectangle(px, Y0, px+BW, Y0+BH, fill=bg, outline=brd, width=bw)
            self.cv_fila.create_text(px+BW//2, YC-S(12), text=proc.nome, font=(FM,F(11),"bold"), fill="white")
            if algo == "RR" and proc.restante < proc.burst_time-0.05:
                txt = f"r={proc.restante}u"; col = AMAR
            else:
                txt = f"b={proc.burst_time}u"; col = proc.cor_categoria()
            self.cv_fila.create_text(px+BW//2, YC+S(10), text=txt, font=(FM,F(7)), fill=col)

        if fila_vis:
            for proc in fila_vis: bloco_fila(x, proc); x += BW+GAP
        else:
            self.cv_fila.create_rectangle(x, Y0+S(4), x+BW, Y0+BH-S(4), fill=BG3, outline="#1E293B", dash=(3,3))
            self.cv_fila.create_text(x+BW//2, YC, text="vazia", font=(FM,F(8)), fill=TEXT2); x += BW+GAP

        x += S(5)
        self.cv_fila.create_text(x, YC, text=">", font=(FM,F(11),"bold"), fill=VERDE, anchor="w"); x += S(22)
        self.cv_fila.create_text(x, Y0, text="CPU", font=(FM,F(7),"bold"), fill=VERDE, anchor="w"); x += S(30)
        if no_cpu: bloco_fila(x, no_cpu, cpu=True)
        else:
            self.cv_fila.create_rectangle(x, Y0, x+BW, Y0+BH, fill=BG3, outline="#1E293B")
            self.cv_fila.create_text(x+BW//2, YC, text="IDLE", font=(FM,F(9)), fill=TEXT2)
        x += BW+GAP+S(10)
        self.cv_fila.create_text(x, YC, text=">", font=(FM,F(11),"bold"), fill=TEXT2, anchor="w"); x += S(22)
        self.cv_fila.create_text(x, Y0, text="DONE", font=(FM,F(7),"bold"), fill=TEXT2, anchor="w"); x += S(42)
        for proc in reversed(hist):
            self.cv_fila.create_rectangle(x, Y0+S(4), x+BW, Y0+BH-S(4), fill=BG3, outline="#1E293B")
            self.cv_fila.create_text(x+BW//2, YC-S(6), text=proc.nome, font=(FM,F(8)), fill=TEXT2)
            self.cv_fila.create_text(x+BW//2, YC+S(7), text=f"esp={proc.tempo_espera_sim}u",
                                     font=(FM,F(6)), fill=TEXT2)
            x += BW+GAP

    # ─── FLUSH DE EVENTOS ─────────────────────────────────────────────────
    def _flush_eventos(self):
        n = 0
        try:
            while n < 80:
                ev = G.ui_q.get_nowait(); tipo = ev["tipo"]
                if tipo == "thr":     self._ins_thr(ev)
                elif tipo == "sched": self._ins_sched(ev)
                n += 1
        except queue.Empty: pass
        if n:
            for txt in [self.sched_txt, self.log_txt]:
                txt.config(state="normal"); txt.see("end")
                if int(txt.index("end-1c").split(".")[0]) > 500: txt.delete("1.0","60.0")
                txt.config(state="disabled")

    def _ins_sched(self, ev):
        ts = datetime.fromtimestamp(ev["ts"]).strftime("%H:%M:%S"); acao = ev["acao"]
        self.sched_txt.config(state="normal")
        self.sched_txt.insert("end", f"[{ts}] ", "ts")
        if acao == "CHEGOU":
            cat = ev.get("cat","?"); cor = {"curto":"chegou","medio":"cpu","longo":"rr"}.get(cat,"done")
            self.sched_txt.insert("end",
                f"{ev['proc']} ← CHEGOU  t={ev['chegada']}  burst={ev['burst']}u  "
                f"({cat})\n", cor)
        elif acao == "CPU":
            self.sched_txt.insert("end",
                f"{ev['proc']} > CPU [{ev['algo']}]  rest={ev['restante']}u\n", "cpu")
        elif acao == "RR_VOLTA":
            self.sched_txt.insert("end",
                f"{ev['proc']} volta fila  restante={ev['restante']}u\n", "rr")
        elif acao == "CONCLUIU":
            self.sched_txt.insert("end",
                f"{ev['proc']} CONCLUIDO  espera={ev['espera']}u\n", "done")
        self.sched_txt.config(state="disabled")

    def _ins_thr(self, ev):
        ts = datetime.fromtimestamp(ev["ts"]).strftime("%H:%M:%S"); est = ev["estado"]
        self.log_txt.config(state="normal")
        self.log_txt.insert("end", f"[{ts}] ", "ts")
        self.log_txt.insert("end", f"{ev['nome']:<6}", "thr")
        self.log_txt.insert("end", f"[{ev['proc']}] ", "proc")
        tag = est if est in ("DISPUTANDO","EXECUTANDO","CALCULANDO","LIBERANDO","RACE") else "det"
        self.log_txt.insert("end", f"> {est:<12}", tag)
        if ev.get("det"): self.log_txt.insert("end", f" {ev['det'][:80]}", "det")
        self.log_txt.insert("end", "\n"); self.log_txt.config(state="disabled")

    # ─── ATUALIZACAO DE THREADS ───────────────────────────────────────────
    def _upd_threads(self):
        with G.mutex_thr: vivas = list(G.threads_ex)
        for i, (row, cells) in enumerate(self.thr_rows):
            if i < len(vivas):
                t = vivas[i]; dur = time.time()-t.ts
                cor = {"DISPUTANDO":AMAR,"EXECUTANDO":VERDE,"CALCULANDO":AZUL,
                       "LIBERANDO":CIAN,"RACE":VERM}.get(t.estado, TEXT2)
                cells["thr"].config(text=t.nome,       fg=ROXO)
                cells["proc"].config(text=t.proc.nome, fg=AZUL)
                cells["est"].config(text=t.estado,     fg=cor)
                cells["dur"].config(text=f"{dur:.1f}s", fg=TEXT2)
                for cv in cells.values(): cv.config(bg=row["bg"])
            else:
                for cv in cells.values(): cv.config(text="")

    # ─── LOOP PRINCIPAL DA UI ─────────────────────────────────────────────
    def _update(self):
        now = time.time(); sel = self.acao_sel.get()
        if not hasattr(self, "_fr"): self._fr = 0
        self._fr += 1

        self._flush_eventos()

        if self._fr % 2 == 0:
            self._desenhar_fila()
            self._upd_threads()

            with G.mutex_res:
                rf = G.res_fcfs; rs = G.res_sjf; rr = G.res_rr
            if rf: self.gantt_fcfs.atualizar(rf)
            if rs: self.gantt_sjf.atualizar(rs)
            if rr:
                q = G.quantum_rr
                self.gantt_rr._titulo = f"3) RR — Round Robin (Quantum = {q} u)"
                self.gantt_rr.atualizar(rr)

            res_map = {"FCFS": rf, "SJF": rs, "RR": rr}
            res_atual = res_map.get(G.algoritmo)
            with G.mutex_fila: fila_snap = list(G.ready_queue)
            with G.mutex_cpu:  cpu_snap  = G.no_cpu
            ativos = fila_snap + ([cpu_snap] if cpu_snap else [])
            self.timeline.atualizar(res_atual, ativos)

        with G.mutex_fila: n_fila = len(G.ready_queue)
        cor_f = VERM if n_fila >= G.limite_fila-1 else (AMAR if n_fila > 3 else VERDE)
        self.lbl_fila_n.config(text=f"FILA: {n_fila}", fg=cor_f)

        cor_r = VERM if G.races > 0 and self._fr%2 == 0 else TEXT2
        self.lbl_race.config(text=f"RACE: {G.races}", fg=cor_r,
                             font=get_font(10 if G.races > 0 else 9, "bold"))
        self.lbl_total.config(text=f"Exec: {G.total_exec}")

        self.lbl_hora.config(text=datetime.now().strftime("%H:%M:%S"))
        n_so = threading.active_count()
        self.lbl_so.config(text=f"THR:{n_so}",
                           fg=VERM if n_so > 12 else (AMAR if n_so > 6 else VERDE))
        modo = "SYNC" if G.modo_sync else "RACE"
        with G.mutex_hist: n_hist = len(G.historico)
        self.lbl_inf.config(
            text=f"Algo:{G.algoritmo}  RR-Q:{G.quantum_rr}u  COL:{G.colisoes}  VOL:{G.volatilidade:.1f}x  [{modo}]  Proc:{n_hist}",
            fg=VERDE if G.modo_sync else VERM)

        with G.mutex_mkt:
            snap_precos = dict(G.precos)
            snap_candle = G.candle_cur.get(sel)

        for ticker, comp in self.fa.items():
            p = snap_precos.get(ticker, 0); var = (p-comp["ref"])/comp["ref"]*100
            cor = VERDE if var >= 0 else VERM; sig = "+" if var >= 0 else "-"
            comp["lp"].config(text=f"R${p:.2f}", fg=cor)
            comp["lv"].config(text=f"{sig}{abs(var):.1f}%", fg=cor)
            ag = now < self.flash.get(ticker, 0)
            bg = "#0D2218" if ag and var >= 0 else "#220A0A" if ag else "#111C2E" if ticker == sel else BG3
            for w in [comp["f"],comp["l1"],comp["lp"],comp["lv"]]: w.config(bg=bg)

        p = snap_precos.get(sel, 0); ref = ACOES[sel]["preco"]; var = (p-ref)/ref*100
        cor = VERDE if var >= 0 else VERM
        self.lbl_pg.config(text=f"R$ {p:.2f}", fg=cor)
        self.lbl_vg.config(text=f"{'+ ' if var>=0 else '- '}{abs(var):.2f}%", fg=cor)
        if snap_candle:
            self.lbl_ohlc.config(text=f"O:{snap_candle.o:.2f}  H:{snap_candle.h:.2f}  L:{snap_candle.l:.2f}  C:{snap_candle.c:.2f}")
        for ticker in snap_precos:
            if abs(snap_precos[ticker]-self.prev_p.get(ticker,0)) > 0.01:
                self.flash[ticker] = now+0.3
        self.prev_p = snap_precos
        draw_candles(self.cv_main, sel)

        with G.mutex_fila: n_f = len(G.ready_queue)
        ram = int(n_f/max(G.limite_fila,1)*20)
        self.lbl_fl.config(text=f"RAM [{'#'*ram+'.'*(20-ram)}] {n_f}/{G.limite_fila}")
        self.lbl_fr.config(text=f"Exec:{G.total_exec}  Colisoes:{G.colisoes}  Races:{G.races}  Total proc:{n_hist}")

        self.root.after(120, self._update)
