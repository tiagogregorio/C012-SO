"""
ThreadExecutora — demonstra seção crítica com e sem mutex.
"""
import threading
import random
import time

from state import G

class ThreadExecutora(threading.Thread):
    _cnt = 0; _lck = threading.Lock()

    def __init__(self, proc):
        super().__init__(daemon=True)
        with ThreadExecutora._lck:
            ThreadExecutora._cnt += 1; self.tid = ThreadExecutora._cnt
        self.proc   = proc
        self.nome   = f"T{self.tid}"
        self.estado = "AGUARDANDO"
        self.ts     = time.time()

    def _log(self, e, d=""):
        self.estado = e
        G.ui_q.put({"tipo":"thr","nome":self.nome,"proc":self.proc.nome,
                    "estado":e,"det":d,"ts":time.time()})

    def _com_mutex(self):
        """wait(mutex) → Seção Crítica → signal(mutex)"""
        self._log("DISPUTANDO", f"wait(mutex) — {self.proc.nome}")
        with G.mutex_mkt:                          # ← wait(mutex)
            self._log("EXECUTANDO", f"mutex OK — {self.proc.nome}")
            G.colisoes += 1
            self._log("CALCULANDO", f"Preços: {list(self.proc.noticia['impacto'].keys())}")
            for ticker, pct in self.proc.noticia["impacto"].items():
                if ticker in G.precos:
                    var  = (pct + random.gauss(0, 0.4)) * G.volatilidade
                    novo = max(0.50, G.precos[ticker] * (1 + var/100))
                    G.precos[ticker] = novo
                    G.candle_cur[ticker].update(novo)
            time.sleep(0.03)
            G.feed_exec.appendleft({"proc":self.proc.nome,
                "texto":self.proc.noticia["titulo"],
                "data":self.proc.noticia["data"],"ts":time.time()})
            G.total_exec += 1
        self._log("LIBERANDO", "signal(mutex)")   # ← signal(mutex)

    def _sem_mutex(self):
        """SEM proteção → Race Condition demonstrada passo a passo"""
        self._log("RACE", f"⚠ INICIANDO SEM MUTEX — {self.proc.nome}")
        
        for ticker, pct in self.proc.noticia["impacto"].items():
            if ticker in G.precos:
                # 1. LEITURA: A thread pega o valor da RAM
                lido = G.precos[ticker]
                self._log("RACE", f" LENDO {ticker}: R${lido:.2f} (Calculando...)")
                
                # 2. JANELA DE VULNERABILIDADE: Congelamos a thread por quase 1s
                # Isso dá tempo de sobra para o SO trocar de contexto e outra thread ler o mesmo valor!
                time.sleep(0.8) 
                
                # 3. CÁLCULO E ESCRITA: A thread devolve o valor para a RAM
                var  = (pct + random.gauss(0, 0.4)) * G.volatilidade
                novo_preco = max(0.50, lido * (1 + var/100))
                
                self._log("RACE", f" GRAVANDO {ticker}: R${novo_preco:.2f} (Sobrescreveu!)")

                G.precos[ticker] = novo_preco
                G.candle_cur[ticker].update(G.precos[ticker])
                
        with G.mutex_thr: G.races += 1
        G.feed_exec.appendleft({"proc":self.proc.nome,
            "texto":"⚠ RACE: "+self.proc.noticia["titulo"],
            "data":self.proc.noticia["data"],"ts":time.time()})
        G.total_exec += 1
                
        with G.mutex_thr: G.races += 1
        G.feed_exec.appendleft({"proc":self.proc.nome,
            "texto":"⚠ RACE: "+self.proc.noticia["titulo"],
            "data":self.proc.noticia["data"],"ts":time.time()})
        G.total_exec += 1

    def run(self):
        try:
            with G.mutex_thr: G.threads_ex.append(self)
            if G.modo_sync: self._com_mutex()
            else:           self._sem_mutex()
        finally:
            with G.mutex_thr:
                if self in G.threads_ex: G.threads_ex.remove(self)
