"""
Widgets visuais: candlestick, Gantt e Timeline N×Tempo.
"""
import tkinter as tk
from tkinter import ttk

from config import (BG, BG3, BG4, VERD2, VERM2, AMAR, VERDE, TEXT2, TEXT3, GRADE,
                    FM, S, F, get_font, ACOES)
from models import ResultadoSimulacao
from state import G


def draw_candles(cv, ticker):
    """Desenha o gráfico de candlestick no Canvas cv para o ticker dado."""
    cv.delete("all"); w = cv.winfo_width(); h = cv.winfo_height()
    if w < 20 or h < 10: return
    with G.mutex_mkt:
        all_c = list(G.candles[ticker]) + [G.candle_cur[ticker]]
        cur_price = G.precos[ticker]
    if not all_c: return
    ml, mr, mt, mb = S(52), S(4), S(4), S(14)
    aw = w-ml-mr; ah = h-mt-mb
    for i in range(5): cv.create_line(ml, mt+i*ah//4, w-mr, mt+i*ah//4, fill=GRADE, dash=(2,4))
    prices = [v for c in all_c for v in (c.h, c.l)]
    mn = min(prices)*0.998; mx = max(prices)*1.002; rng = mx-mn if mx != mn else 1.0
    def py(v): return mt+int((1-(v-mn)/rng)*ah)
    vis = all_c[-max(1, aw//S(9)):]; step = aw/max(len(vis), 1); cw = max(2, min(int(step*0.6), S(11)))
    for i, c in enumerate(vis):
        xc = ml+int(i*step+step/2); cor = VERD2 if c.c >= c.o else VERM2
        cv.create_line(xc, py(c.h), xc, py(c.l), fill=cor, width=1)
        y0 = min(py(c.o), py(c.c)); y1 = max(py(c.o), py(c.c))
        cv.create_rectangle(xc-cw//2, y0, xc+cw//2, max(y1, y0+1), fill=cor, outline=cor)
    for i in range(5):
        cv.create_text(ml-2, mt+i*ah//4, text=f"{mx-(i/4)*rng:.2f}",
                       font=(FM, F(6)), fill=TEXT2, anchor="e")
    cv.create_line(ml, py(cur_price), w-mr, py(cur_price),
                   fill=ACOES[ticker]["cor"], dash=(3,4), width=1)


class WidgetGantt(tk.Frame):
    """
    Reproduz o diagrama de Gantt exatamente como nos slides do professor.
    Exibe os resultados de um algoritmo de escalonamento.
    """
    def __init__(self, parent, titulo, cor_titulo, bg_titulo):
        super().__init__(parent, bg=BG3, bd=1, relief="solid")
        self._resultado = None
        self._titulo    = titulo
        self._cor_t     = cor_titulo
        self._bg_t      = bg_titulo
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self._bg_t)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self._titulo, font=get_font(8, "bold"),
                 bg=self._bg_t, fg=self._cor_t, pady=S(3)
                 ).pack(side="left", padx=S(6))
        self.lbl_media = tk.Label(hdr, text="Espera Média: —",
                                  font=get_font(8, "bold"),
                                  bg=self._bg_t, fg=AMAR)
        self.lbl_media.pack(side="right", padx=S(8))

        cf = tk.Frame(self, bg=BG3)
        cf.pack(fill="x", padx=S(4), pady=(S(2), 0))
        self.cv = tk.Canvas(cf, bg="#1A2235", height=S(90), highlightthickness=0)
        sb = ttk.Scrollbar(cf, orient="horizontal", command=self.cv.xview)
        self.cv.configure(xscrollcommand=sb.set)
        self.cv.pack(side="top", fill="x")
        sb.pack(side="bottom", fill="x")

        self.tbl_frame = tk.Frame(self, bg=BG3)
        self.tbl_frame.pack(fill="x", padx=S(4), pady=S(2))

        self.frm_formula = tk.Frame(self, bg="#3D3200", bd=1, relief="solid")
        self.frm_formula.pack(fill="x", padx=S(4), pady=(0, S(4)))
        self.lbl_formula = tk.Label(self.frm_formula, text="",
                                    font=get_font(8, "bold"),
                                    bg="#3D3200", fg=AMAR, anchor="w")
        self.lbl_formula.pack(padx=S(8), pady=S(3))

    def atualizar(self, resultado: ResultadoSimulacao):
        self._resultado = resultado
        self._desenhar_gantt(resultado)
        self._desenhar_tabela(resultado)
        media_str = f"{resultado.media_espera:.1f} unidades"
        self.lbl_media.config(text=f"Espera Média: {media_str}")
        self.lbl_formula.config(text=f"Média de Espera: {resultado.formula}")

    def _desenhar_gantt(self, r: ResultadoSimulacao):
        self.cv.delete("all")
        w = self.cv.winfo_width()
        h = self.cv.winfo_height()
        if w < 10 or h < 10: return

        gantt = r.gantt
        if not gantt: return

        T_max = max(g[2] for g in gantt)
        T_max = max(T_max, 1)

        MARG_L = S(8); MARG_R = S(20)
        EIXO_Y = h - S(18)
        BARRA_H = S(45)
        BARRA_Y = EIXO_Y - BARRA_H - S(2)

        PX_POR_UNIDADE = S(35)
        LARGURA_TOTAL  = MARG_L + T_max * PX_POR_UNIDADE + MARG_R
        self.cv.configure(scrollregion=(0, 0, max(w, LARGURA_TOTAL), h))

        def tx(t): return MARG_L + t * PX_POR_UNIDADE

        self.cv.create_line(MARG_L, EIXO_Y, tx(T_max) + S(10), EIXO_Y, fill=TEXT3, width=1)

        passo = max(1, T_max // 10)
        for t in range(0, T_max + 1, passo):
            xp = tx(t)
            self.cv.create_line(xp, EIXO_Y, xp, EIXO_Y + S(4), fill=TEXT3)
            self.cv.create_text(xp, EIXO_Y + S(10), text=str(t),
                                font=(FM, F(6)), fill=TEXT3)

        # Aloca processos em linhas para evitar sobreposição (como no slide)
        linhas = {}
        linha_atual = 0

        for nome, t_ini, t_fim, cor in gantt:
            alocado = False
            for ln in range(linha_atual + 1):
                sobreposição = False
                for n2, i2, f2, c2 in gantt:
                    if linhas.get(n2) == ln and n2 != nome:
                        if not (t_fim <= i2 or t_ini >= f2):
                            sobreposição = True; break
                if not sobreposição:
                    if nome not in linhas:
                        linhas[nome] = ln
                    alocado = True; break
            if not alocado:
                linha_atual += 1
                linhas[nome] = linha_atual

        N_LINHAS = max(linhas.values()) + 1 if linhas else 1
        LINHA_H  = BARRA_H + S(2)
        self.cv.configure(height=max(S(90), S(26)*N_LINHAS + S(40)))

        for nome, t_ini, t_fim, cor in gantt:
            ln = linhas.get(nome, 0)
            y0 = BARRA_Y - ln * LINHA_H
            y1 = y0 + BARRA_H
            x0 = tx(t_ini); x1 = tx(t_fim)

            self.cv.create_rectangle(x0, y0, x1, y1, fill=cor, outline="white", width=1)

            if x1 - x0 > S(14):
                self.cv.create_text((x0+x1)//2, (y0+y1)//2, text=nome,
                                    font=(FM, F(7), "bold"), fill="white")

            for xt, val in [(x0, t_ini), (x1, t_fim)]:
                self.cv.create_line(xt, EIXO_Y, xt, y1, fill=TEXT2, dash=(2,3), width=1)
                self.cv.create_text(xt, y0 - S(8), text=str(val),
                                    font=(FM, F(6)), fill=TEXT2)

    def _desenhar_tabela(self, r: ResultadoSimulacao):
        for w in self.tbl_frame.winfo_children():
            w.destroy()

        if not r.esperas: return

        nomes   = list(r.esperas.keys())
        esperas = [r.esperas[n] for n in nomes]

        tk.Label(self.tbl_frame, text="Processo:",
                 font=get_font(7, "bold"), bg=BG4, fg=TEXT2,
                 width=10, relief="solid", bd=1).grid(row=0, column=0, sticky="nsew")

        for col, nome in enumerate(nomes):
            cor = next((g[3] for g in r.gantt if g[0]==nome), "#555555")
            tk.Label(self.tbl_frame, text=nome,
                     font=get_font(7, "bold"), bg=cor, fg="white",
                     width=6, relief="solid", bd=1
                     ).grid(row=0, column=col+1, sticky="nsew")

        tk.Label(self.tbl_frame, text="Espera:",
                 font=get_font(7), bg=BG3, fg=TEXT2,
                 width=10, relief="solid", bd=1).grid(row=1, column=0, sticky="nsew")

        for col, (nome, esp) in enumerate(zip(nomes, esperas)):
            cor_txt = VERM2 if esp > 15 else (AMAR if esp > 7 else VERD2)
            tk.Label(self.tbl_frame, text=str(round(esp, 1)),
                     font=get_font(8, "bold"), bg=BG3, fg=cor_txt,
                     width=6, relief="solid", bd=1
                     ).grid(row=1, column=col+1, sticky="nsew")

        tk.Label(self.tbl_frame, text="Chegada:",
                 font=get_font(7), bg=BG3, fg=TEXT2,
                 width=10, relief="solid", bd=1).grid(row=2, column=0, sticky="nsew")
        for col, nome in enumerate(nomes):
            proc = next((p for p in r.processos if p.nome == nome), None)
            chegada = proc.t_chegada_sim if proc else "—"
            tk.Label(self.tbl_frame, text=str(chegada),
                     font=get_font(7), bg=BG3, fg=TEXT3,
                     width=6, relief="solid", bd=1
                     ).grid(row=2, column=col+1, sticky="nsew")

        tk.Label(self.tbl_frame, text="Burst:",
                 font=get_font(7), bg=BG3, fg=TEXT2,
                 width=10, relief="solid", bd=1).grid(row=3, column=0, sticky="nsew")
        for col, nome in enumerate(nomes):
            proc = next((p for p in r.processos if p.nome == nome), None)
            burst = proc.burst_time if proc else "—"
            cor_b = next((p.cor_categoria() for p in r.processos if p.nome==nome), TEXT3)
            tk.Label(self.tbl_frame, text=str(burst),
                     font=get_font(7, "bold"), bg=BG3, fg=cor_b,
                     width=6, relief="solid", bd=1
                     ).grid(row=3, column=col+1, sticky="nsew")


# ═══════════════════════════════════════════════════════════════
#  WIDGET TIMELINE — Processos × Tempo Simulado
#  Eixo Y: cada processo é uma linha (N1, N2, ...)
#  Eixo X: tempo simulado em unidades inteiras
#  Célula sólida   = processo executando na CPU
#  Célula pontilhada = processo aguardando na fila
# ═══════════════════════════════════════════════════════════════
class WidgetTimeline(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=S(4), pady=(S(3), 0))
        tk.Label(hdr, text="TIMELINE — Processos × Tempo Simulado",
                 font=get_font(7, "bold"), bg=BG, fg=AMAR).pack(side="left")
        leg = tk.Frame(hdr, bg=BG); leg.pack(side="right")
        tk.Label(leg, text="■ exec",  font=get_font(6, "bold"), bg=BG, fg=VERDE).pack(side="left", padx=S(3))
        tk.Label(leg, text="□ wait",  font=get_font(6, "bold"), bg=BG, fg=TEXT3).pack(side="left", padx=S(3))

        cont = tk.Frame(self, bg=BG)
        cont.pack(fill="both", expand=True, padx=S(4), pady=(S(2), S(3)))
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)

        self.cv = tk.Canvas(cont, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(cont, orient="vertical",   command=self.cv.yview)
        hsb = ttk.Scrollbar(cont, orient="horizontal", command=self.cv.xview)
        self.cv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.cv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def atualizar(self, resultado, processos_ativos):
        """
        resultado        : ResultadoSimulacao do algoritmo atual (pode ser None)
        processos_ativos : lista de Processo em ready_queue + no_cpu
        """
        self._desenhar(resultado, processos_ativos)

    # ── internos ──────────────────────────────────────────────────────────

    def _segmentos(self, resultado, processos_ativos):
        """
        Retorna {nome: {pid, cor, chegada, segs: [{t_ini, t_fim, tipo}]}}
        'exec' = executando na CPU | 'wait' = aguardando na fila
        """
        out = {}
        t_agora = G.t_sim

        if resultado:
            chegadas = {p.nome: (p.t_chegada_sim, p.cor_gantt, p.pid)
                        for p in resultado.processos}
            por_proc = {}
            for nome, t_ini, t_fim, cor in resultado.gantt:
                por_proc.setdefault(nome, []).append((t_ini, t_fim))

            for nome, slices in por_proc.items():
                chegada, cor, pid = chegadas.get(nome, (0, "#888888", 0))
                segs = []; cur = chegada
                for t_ini, t_fim in sorted(slices):
                    if cur < t_ini:
                        segs.append({"t_ini": cur, "t_fim": t_ini, "tipo": "wait"})
                    segs.append({"t_ini": t_ini, "t_fim": t_fim, "tipo": "exec"})
                    cur = t_fim
                out[nome] = {"pid": pid, "cor": cor, "chegada": chegada, "segs": segs}

        # Processos ativos ainda não no resultado
        for proc in processos_ativos:
            if proc.nome in out:
                continue
            chegada = proc.t_chegada_sim
            segs = []
            if proc.t_inicio_cpu_sim is not None:
                if chegada < proc.t_inicio_cpu_sim:
                    segs.append({"t_ini": chegada, "t_fim": proc.t_inicio_cpu_sim, "tipo": "wait"})
                fim = max(proc.t_inicio_cpu_sim + 1, t_agora)
                segs.append({"t_ini": proc.t_inicio_cpu_sim, "t_fim": fim, "tipo": "exec"})
            else:
                segs.append({"t_ini": chegada, "t_fim": max(chegada + 1, t_agora), "tipo": "wait"})
            out[proc.nome] = {"pid": proc.pid, "cor": proc.cor_gantt,
                              "chegada": chegada, "segs": segs}
        return out

    def _desenhar(self, resultado, processos_ativos):
        self.cv.delete("all")
        data = self._segmentos(resultado, processos_ativos)
        if not data: return

        CELL  = S(20)   # px por unidade de tempo — igual à altura → quadrados naturais
        ROW_H = CELL
        ML    = S(46)   # margem esquerda para os labels
        MT    = S(20)   # margem topo para o eixo de tempo
        GAP   = S(3)    # espaço vertical entre linhas

        procs = sorted(data.items(), key=lambda x: x[1]["pid"])

        all_ends = [seg["t_fim"] for _, d in procs for seg in d["segs"]]
        T_max = max(max(all_ends, default=1), G.t_sim, 1)

        total_w = ML + T_max * CELL + CELL * 2
        total_h = MT + len(procs) * (ROW_H + GAP) + GAP
        self.cv.configure(scrollregion=(0, 0, total_w, total_h))

        # ── Eixo de tempo ───────────────────────────────────────────────
        passo = max(1, T_max // 15)
        for t in range(0, T_max + 1, passo):
            xp = ML + t * CELL
            self.cv.create_text(xp, MT - S(7), text=str(t),
                                font=(FM, F(6)), fill=TEXT3, anchor="center")
            self.cv.create_line(xp, MT - S(3), xp, MT, fill=TEXT3, width=1)
        self.cv.create_line(ML, MT, ML + T_max * CELL + CELL, MT, fill=TEXT3, width=1)

        # Grades verticais subtis
        for t in range(0, T_max + 1, passo):
            xp = ML + t * CELL
            self.cv.create_line(xp, MT, xp, total_h, fill=GRADE, dash=(1, 8))

        # ── Linhas de processo ──────────────────────────────────────────
        for row, (nome, d) in enumerate(procs):
            y0 = MT + row * (ROW_H + GAP) + GAP
            y1 = y0 + ROW_H
            yc = (y0 + y1) // 2
            cor = d["cor"]

            # Label
            self.cv.create_text(ML - S(5), yc, text=nome,
                                font=(FM, F(7), "bold"), fill=cor, anchor="e")

            # Uma célula por unidade de tempo
            for seg in d["segs"]:
                for t in range(seg["t_ini"], seg["t_fim"]):
                    cx0 = ML + t * CELL + 1
                    cx1 = ML + (t + 1) * CELL - 1
                    if seg["tipo"] == "exec":
                        self.cv.create_rectangle(cx0, y0 + 1, cx1, y1 - 1,
                                                 fill=cor, outline="white", width=1)
                    else:
                        self.cv.create_rectangle(cx0, y0 + 1, cx1, y1 - 1,
                                                 fill="", outline=cor,
                                                 width=1, dash=(3, 2))
