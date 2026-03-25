"""
DATA SECTION (models.py)
Estruturas compartilhadas entre Engine e Interface.
"""

import threading
import queue
import time
from collections import deque
from config import ACOES


class Candle:
    """Representa uma vela OHLC (Open, High, Low, Close)."""

    def __init__(self, preco_inicial: float):
        self.o = self.h = self.l = self.c = float(preco_inicial)

    def update(self, preco: float) -> None:
        p = float(preco)
        self.c = p
        self.h = max(self.h, p)
        self.l = min(self.l, p)


class EstadoMercado:
    """
    Data Section compartilhada por todas as threads da simulacao.
    """

    def __init__(self):
        # Locks de sincronizacao
        self.lock = threading.Lock()
        self.threads_lock = threading.Lock()

        # Estado de mercado
        self.precos = {ticker: dados["preco"] for ticker, dados in ACOES.items()}
        self.historico_candles = {ticker: [] for ticker in ACOES}
        self.candle_atual = {
            ticker: Candle(dados["preco"]) for ticker, dados in ACOES.items()
        }

        # Historico de noticias exibidas na UI
        self.noticias = deque(maxlen=8)

        # Flags de simulacao
        self.rodando = False
        self.volatilidade = 1.0
        self.num_threads_config = 4
        self.candle_intervalo = 2.0

        # Comunicacao thread -> UI
        self.ui_queue = queue.Queue()

        # Metricas e monitoramento
        self.colisoes = 0
        self.total_noticias = 0
        self.travamentos_detectados = 0
        self.threads_vivas = []

    def registrar_colisao(self) -> None:
        """
        Incrementa metricas de colisao.
        Deve ser chamado dentro de um bloco protegido por self.lock.
        """
        self.colisoes += 1
        self.total_noticias += 1

    def registrar_travamento(self) -> None:
        """Incrementa contador de possivel travamento/sobrecarga."""
        self.travamentos_detectados += 1

    def adicionar_noticia_historico(self, noticia_data: dict) -> None:
        """
        Salva noticia processada para o feed da interface.
        Estrutura padronizada para evitar ifs na UI.
        """
        self.noticias.appendleft(
            {
                "texto": noticia_data.get("titulo", ""),
                "cor": noticia_data.get("cor", "#64748B"),
                "intensidade": noticia_data.get("intensidade", "MEDIA"),
                "ts": time.time(),
                "data": noticia_data.get("data", ""),
                "fonte": noticia_data.get("fonte", ""),
                "tickers": list(noticia_data.get("impacto", {}).keys()),
            }
        )