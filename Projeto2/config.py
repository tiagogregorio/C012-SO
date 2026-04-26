"""
Constantes globais: escala de tela, paleta de cores, fontes,
dados das ações e banco de notícias.
"""
import tkinter as tk
from tkinter import font as tkfont
import os


# ═══════════════════════════════════════════════════════════════
#  RESOLUÇÃO E ESCALA
# ═══════════════════════════════════════════════════════════════
def _detectar():
    tmp = tk.Tk(); tmp.withdraw()
    sw = tmp.winfo_screenwidth(); sh = tmp.winfo_screenheight()
    tmp.destroy()
    f = max(1.2, min(sh / 1080.0, sw / 1920.0, 2.0))
    return f, sw, sh, min(int(1580*f), sw-20), min(int(940*f), sh-40)

SCALE, SCR_W, SCR_H, WIN_W, WIN_H = _detectar()
def S(x): return max(1, int(x * SCALE))
def F(x): return max(11, int(x * SCALE))

# ═══════════════════════════════════════════════════════════════
#  FONTES (escala dinâmica)
# ═══════════════════════════════════════════════════════════════
FM = "Courier New"
_FONTS: dict = {}

def get_font(size: int, weight: str = "normal", family: str = None) -> "tkfont.Font":
    fam = family or FM
    key = (size, weight, fam)
    if key not in _FONTS:
        # Aumentamos o tamanho base de todas as fontes em +2 pontos
        _FONTS[key] = tkfont.Font(family=fam, size=F(size + 2), weight=weight)
    return _FONTS[key]

def _update_all_fonts():
    for (size, weight, fam), font in _FONTS.items():
        font.configure(size=F(size + 2))

# ═══════════════════════════════════════════════════════════════
#  PALETA
# ═══════════════════════════════════════════════════════════════
BG, BG2, BG3, BG4   = "#0A0E17", "#0D1220", "#111827", "#1C2333"
VERDE, VERD2         = "#00E676", "#00C853"
VERM, VERM2          = "#FF1744", "#D50000"
AMAR, AZUL           = "#FFD740", "#40C4FF"
LARA, CIAN, ROXO     = "#FF8A65", "#80DEEA", "#CE93D8"
TEXTO, TEXT2, TEXT3  = "#E2E8F0", "#64748B", "#94A3B8"
GRADE                = "#1E293B"

# Cada processo recebe uma cor única e consistente no Gantt
PALETA_PROCESSOS = [
    "#E65100",  # laranja escuro  (como no slide do professor)
    "#1565C0",  # azul escuro
    "#2E7D32",  # verde escuro
    "#6A1B9A",  # roxo escuro
    "#AD1457",  # rosa escuro
    "#00838F",  # ciano escuro
    "#F9A825",  # amarelo escuro
    "#4527A0",  # índigo
    "#558B2F",  # verde oliva
    "#D84315",  # laranja queimado
    "#00695C",  # verde teal
    "#283593",  # azul índigo
]

# ═══════════════════════════════════════════════════════════════
#  AÇÕES DO MERCADO (seção crítica dos preços)
# ═══════════════════════════════════════════════════════════════
ACOES = {
    "VALE3": {"nome": "Vale S.A.",      "preco": 68.50, "cor": "#4FC3F7"},
    "PETR4": {"nome": "Petrobras PN",   "preco": 38.20, "cor": "#FF8A65"},
    "ITUB4": {"nome": "Itaú Unibanco",  "preco": 34.80, "cor": "#A5D6A7"},
    "BBDC4": {"nome": "Bradesco PN",    "preco": 14.90, "cor": "#CE93D8"},
    "B3SA3": {"nome": "B3 S.A.",        "preco": 11.40, "cor": "#FFD54F"},
    "ABEV3": {"nome": "Ambev S.A.",     "preco": 12.80, "cor": "#80DEEA"},
    "MGLU3": {"nome": "Magazine Luiza", "preco":  9.10, "cor": "#F48FB1"},
    "WEGE3": {"nome": "WEG S.A.",       "preco": 51.30, "cor": "#BCAAA4"},
    "RENT3": {"nome": "Localiza",       "preco": 43.60, "cor": "#EF9A9A"},
    "SUZB3": {"nome": "Suzano S.A.",    "preco": 57.20, "cor": "#B39DDB"},
}

# ═══════════════════════════════════════════════════════════════
#  BANCO DE NOTÍCIAS
#  Burst INTENCIONALMENTE variado em 3 faixas para o SJF ser visível
# ═══════════════════════════════════════════════════════════════
BANCO_NOTICIAS = [
    # BURST CURTO: 1 ação → burst ≈ 2-4 unidades
    {"titulo":"Brumadinho: Vale suspende operações",
     "impacto":{"VALE3":-24.5},"data":"2019-01-25"},
    {"titulo":"Suzano oferta pela Int. Paper",
     "impacto":{"SUZB3":+12.3},"data":"2023-05-30"},
    {"titulo":"WEG bate recorde de exportação",
     "impacto":{"WEGE3":+7.2},"data":"GERADA"},
    {"titulo":"Magazine Luiza fecha lojas",
     "impacto":{"MGLU3":-9.1},"data":"GERADA"},
    {"titulo":"Localiza conclui fusão com Unidas",
     "impacto":{"RENT3":+8.1},"data":"2024-02-28"},

    # BURST MÉDIO: 3-5 ações → burst ≈ 6-12 unidades
    {"titulo":"China anuncia pacote de US$ 1,4 tri",
     "impacto":{"VALE3":+8.3,"SUZB3":+2.1,"PETR4":+1.8},"data":"2021-03-10"},
    {"titulo":"Fed corta juros em 0,5 p.p.",
     "impacto":{"ITUB4":+3.2,"B3SA3":+3.8,"MGLU3":+5.1},"data":"2024-09-18"},
    {"titulo":"BC sobe Selic em 0,75 p.p.",
     "impacto":{"ITUB4":+3.9,"BBDC4":+3.2,"MGLU3":-5.2,"B3SA3":-2.1},"data":"GERADA"},
    {"titulo":"Lula vence eleição — mercado reage",
     "impacto":{"B3SA3":-6.2,"PETR4":+3.1,"ITUB4":-3.5},"data":"2022-10-30"},
    {"titulo":"Reforma fiscal aprovada no Congresso",
     "impacto":{"B3SA3":+4.1,"ITUB4":+2.8,"BBDC4":+2.4,"ABEV3":+1.2},"data":"GERADA"},

    # BURST LONGO: 8-10 ações → burst ≈ 16-25 unidades
    {"titulo":"COVID-19: circuit breaker — queda geral",
     "impacto":{"PETR4":-12.3,"VALE3":-9.8,"ITUB4":-11.2,"BBDC4":-10.5,
                "MGLU3":-13.1,"ABEV3":-8.4,"WEGE3":-9.6,"RENT3":-12.8,
                "B3SA3":-11.0,"SUZB3":-7.2},"data":"2020-03-18"},
    {"titulo":"Rússia invade Ucrânia — mercados caem",
     "impacto":{"PETR4":+9.2,"VALE3":+2.3,"SUZB3":+1.8,"ABEV3":-1.2,
                "ITUB4":-2.1,"BBDC4":-1.8,"MGLU3":-3.2,"WEGE3":-1.1},"data":"2022-02-24"},
]
PID = os.getpid()
