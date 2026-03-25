"""
LÓGICA DE EXECUÇÃO (engine.py)
Gerencia o ciclo de vida das threads e a simulação de mercado.
"""

import threading
import random
import time
import queue
from config import ACOES, BANCO_NOTICIAS, ESTADOS_THREAD, LIMITES_THREAD

class ThreadNoticia(threading.Thread):
    """
    Representa uma Kernel Thread (Modelo 1:1).
    Cada instância simula o processamento de uma notícia real.
    """
    _contador_id = 0
    _lock_id = threading.Lock()

    def __init__(self, mercado):
        super().__init__(daemon=True)
        self.mercado = mercado
        self.noticia = random.choice(BANCO_NOTICIAS)

        with self._lock_id:
            ThreadNoticia._contador_id += 1
            self.tid = ThreadNoticia._contador_id

        self.nome_thread = f"Thread-{self.tid}"
        self.ts_inicio = time.time()
        self.estado_atual = "NOVA"

    def _notificar_ui(self, estado, detalhe=""):
        """Envia o estado da thread para a fila de visualização da GUI."""
        self.estado_atual = estado
        self.mercado.ui_queue.put({
            "tid": self.tid,
            "nome": self.nome_thread,
            "estado": estado,
            "detalhe": detalhe,
            "ts": time.time(),
            "titulo_noticia": self.noticia["titulo"][:48]
        })

    def run(self):
        """Ciclo de vida: NOVA -> PRONTA -> DISPUTANDO -> EXECUTANDO -> TERMINADA"""
        self._notificar_ui("PRONTA", "Aguardando processamento...")
        time.sleep(random.uniform(0.05, 0.5))

        # 2. DISPUTANDO (Tentando adquirir o Mutex/Lock)
        self._notificar_ui("DISPUTANDO", "Tentando acessar Data Section...")
        
        # 3. SEÇÃO CRÍTICA (Lock adquirido)
        with self.mercado.lock:
            self._notificar_ui("EXECUTANDO", "Acesso exclusivo garantido!")
            self.mercado.registrar_colisao()

            # CALCULANDO impactos
            self._notificar_ui("CALCULANDO", "Processando algoritmos de risco...")
            for ticker, impacto_base in self.noticia["impacto"].items():
                if ticker in self.mercado.precos:
                    # Aplica volatilidade e ruído gaussiano
                    variacao = (impacto_base + random.gauss(0, 0.5)) * self.mercado.volatilidade
                    novo_valor = max(0.50, self.mercado.precos[ticker] * (1 + variacao / 100))
                    
                    # Atualiza a Data Section compartilhada
                    self.mercado.precos[ticker] = novo_valor
                    self.mercado.candle_atual[ticker].update(novo_valor)

            # Simulação de carga pesada (mantém o lock ocupado)
            # Quanto mais threads no slider, mais pesado fica o cálculo
            carga = 5000 + (self.mercado.num_threads_config * 1000)
            _ = sum(i * i for i in range(int(carga)))

            # APLICANDO e registrando no histórico de notícias
            self._notificar_ui("APLICANDO", "Gravando alterações no banco...")
            self.mercado.adicionar_noticia_historico(self.noticia)

        # 4. TERMINADA
        self._notificar_ui("LIBERANDO", "Liberando recursos da Stack...")
        self._notificar_ui("TERMINADA", f"Encerrada em {time.time()-self.ts_inicio:.3f}s")

# --- LOOPS DE BACKGROUND (Gerenciadores de Fluxo) ---

def loop_ruido_mercado(mercado):
    """Gera flutuações constantes (ruído) para manter o gráfico vivo."""
    while True:
        if mercado.rodando:
            with mercado.lock:
                amplitude = (0.2 + mercado.num_threads_config * 0.02) * mercado.volatilidade
                for t in mercado.precos:
                    r = random.gauss(0, amplitude)
                    mercado.precos[t] = max(0.5, mercado.precos[t] * (1 + r / 100))
                    mercado.candle_atual[t].update(mercado.precos[t])
        time.sleep(random.uniform(0.1, 0.3))

def loop_gerador_noticias(mercado):
    """Motor do Caos: Dispara rajadas de threads conforme o slider da UI."""
    while True:
        if mercado.rodando:
            n = mercado.num_threads_config
            # Cria rajada de threads proporcional ao slider
            qtd_rajada = random.randint(n, n + n // 2)
            
            for _ in range(qtd_rajada):
                ThreadNoticia(mercado).start()

            # Pausa inversamente proporcional: quanto mais threads, menor o descanso
            if n <= 4: pausa = random.uniform(2.0, 3.5)
            elif n <= 12: pausa = random.uniform(0.8, 1.5)
            else: pausa = random.uniform(0.05, 0.2) # Avalanche de threads
            
            time.sleep(pausa)
        else:
            time.sleep(0.5)

def iniciar_engine(mercado):
    """Inicia todos os serviços de suporte em threads separadas."""
    servicos = [
        (loop_ruido_mercado, "Servico-Ruido"),
        (loop_gerador_noticias, "Servico-Noticias")
    ]
    for func, nome in servicos:
        threading.Thread(target=func, args=(mercado,), name=nome, daemon=True).start()