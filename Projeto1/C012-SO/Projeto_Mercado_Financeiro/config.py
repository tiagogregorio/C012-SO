"""
CONFIGURAÇÕES GERAIS DA SIMULAÇÃO (config.py)
Contém constantes de UI, definições de ativos e o banco de dados de notícias.
"""

import os

# --- INFORMAÇÕES DO SISTEMA ---
PID = os.getpid()

# --- LIMITES DE PERFORMANCE (THREADS) ---
# Define os gatilhos visuais e de comportamento da UI
LIMITES_THREAD = {
    "AVISO": 9,    # Amarelo: Início do overhead
    "PERIGO": 15,  # Vermelho: UI começa a engasgar
    "MAXIMO": 22   # Crítico: Risco real de travamento (Modelo 1:1)
}

# --- PALETA DE CORES (DESIGN DARK) ---
CORES = {
    "BG_PRINCIPAL": "#0A0E17",
    "BG_SECUNDARIO": "#0D1220",
    "BG_CARD": "#111827",
    "BG_HOVER": "#1C2333",
    "LINHA_GRADE": "#1E293B",
    
    "ALTA": "#00E676",      # Verde brilhante
    "ALTA_DARK": "#00C853", # Verde fechado (Candle)
    "BAIXA": "#FF1744",     # Vermelho brilhante
    "BAIXA_DARK": "#D50000",# Vermelho fechado (Candle)
    
    "ALERTA": "#FFD740",    # Amarelo
    "INFO": "#40C4FF",      # Azul
    "DESTAQUE": "#CE93D8",  # Roxo
    
    "TEXTO_PRIMARIO": "#E2E8F0",
    "TEXTO_SECUNDARIO": "#64748B",
    "TEXTO_MUTED": "#475569"
}

# --- DEFINIÇÕES DOS ATIVOS (IBOVESPA TOP 10) ---
ACOES = {
    "VALE3": {"nome": "Vale S.A.",        "preco": 68.50, "cor": "#4FC3F7"},
    "PETR4": {"nome": "Petrobras PN",     "preco": 38.20, "cor": "#FF8A65"},
    "ITUB4": {"nome": "Itaú Unibanco",    "preco": 34.80, "cor": "#A5D6A7"},
    "BBDC4": {"nome": "Bradesco PN",      "preco": 14.90, "cor": "#CE93D8"},
    "B3SA3": {"nome": "B3 S.A.",          "preco": 11.40, "cor": "#FFD54F"},
    "ABEV3": {"nome": "Ambev S.A.",       "preco": 12.80, "cor": "#80DEEA"},
    "MGLU3": {"nome": "Magazine Luiza",   "preco": 9.10,  "cor": "#F48FB1"},
    "WEGE3": {"nome": "WEG S.A.",         "preco": 51.30, "cor": "#BCAAA4"},
    "RENT3": {"nome": "Localiza",         "preco": 43.60, "cor": "#EF9A9A"},
    "SUZB3": {"nome": "Suzano S.A.",      "preco": 57.20, "cor": "#B39DDB"},
}

TICKERS = list(ACOES.keys())

# --- BANCO DE DADOS DE EVENTOS (NOTÍCIAS) ---
# Estrutura: { data, titulo, impacto: {ticker: %}, intensidade, cor, fonte }
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

# --- ESTADOS DAS THREADS (Para Log e Visualização) ---
ESTADOS_THREAD = {
    "NOVA":       (CORES["TEXTO_SECUNDARIO"], "Thread criada"),
    "PRONTA":     ("#90A4AE", "Aguardando CPU (Runnable)"),
    "DISPUTANDO": (CORES["ALERTA"], "Bloqueada tentando o Mutex"),
    "EXECUTANDO": (CORES["ALTA"], "No CPU (Acesso Exclusivo)"),
    "CALCULANDO": (CORES["INFO"], "Seção Crítica: Cálculos"),
    "APLICANDO":  ("#FF8A65", "Seção Crítica: Escrita"),
    "LIBERANDO":  ("#80DEEA", "Saindo da Seção Crítica"),
    "TERMINADA":  (CORES["TEXTO_MUTED"], "Recursos liberados")
}