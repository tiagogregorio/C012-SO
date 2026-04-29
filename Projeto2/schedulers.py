"""
Algoritmos de escalonamento: FCFS, SJF e Round Robin.
Calculam Gantt, esperas e métricas
(unidades inteiras de tempo simulado).
"""
from models import ResultadoSimulacao

def simular_fcfs(processos_orig):
    """FCFS — First Come, First Served. Não preemptivo, ordem de chegada."""
    ps = sorted([
        {"nome": p.nome, "chegada": p.t_chegada_sim,
         "burst": p.burst_time, "cor": p.cor_gantt}
        for p in processos_orig
    ], key=lambda x: x["chegada"])

    t = 0; gantt = []; esperas = {}; turnarounds = {}

    for p in ps:
        if t < p["chegada"]:
            t = p["chegada"]   # CPU ociosa até o processo chegar
        esperas[p["nome"]] = t - p["chegada"]
        gantt.append((p["nome"], t, t + p["burst"], p["cor"]))
        t += p["burst"]
        turnarounds[p["nome"]] = t - p["chegada"]

    vals = list(esperas.values())
    media = sum(vals) / len(vals) if vals else 0
    formula = f"({' + '.join(str(v) for v in vals)}) / {len(vals)} = {media:.1f}"

    r = ResultadoSimulacao("FCFS", processos_orig, gantt, esperas, turnarounds, media)
    r.formula = formula
    return r

def simular_sjf(processos_orig):
    """SJF — Shortest Job First. Não preemptivo, menor burst_time primeiro."""
    ps = [{"nome": p.nome, "chegada": p.t_chegada_sim,
            "burst": p.burst_time, "restante": p.burst_time,
            "cor": p.cor_gantt}
           for p in processos_orig]

    t = min(p["chegada"] for p in ps)
    prontos = []; fila = list(ps)
    gantt = []; esperas = {}; turnarounds = {}
    primeiro_cpu = {}

    while fila or prontos:
        novos = [p for p in fila if p["chegada"] <= t]
        for p in novos: prontos.append(p); fila.remove(p)

        if not prontos:
            t = min(p["chegada"] for p in fila)
            continue

        prontos.sort(key=lambda p: p["burst"])
        c = prontos.pop(0)

        if c["nome"] not in primeiro_cpu:
            primeiro_cpu[c["nome"]] = t

        esperas[c["nome"]]     = t - c["chegada"]
        gantt.append((c["nome"], t, t + c["burst"], c["cor"]))
        t += c["burst"]
        turnarounds[c["nome"]] = t - c["chegada"]

    vals = list(esperas.values())
    media = sum(vals) / len(vals) if vals else 0
    formula = f"({' + '.join(str(v) for v in vals)}) / {len(vals)} = {media:.1f}"

    r = ResultadoSimulacao("SJF", processos_orig, gantt, esperas, turnarounds, media)
    r.formula = formula
    return r


def simular_rr(processos_orig, quantum):
    """
    Round Robin com quantum configurável. Preemptivo.

    Cada processo recebe no máximo `quantum` unidades de CPU por vez.
    Se não terminar, volta ao fim da fila e espera sua vez novamente.
    """

    # ─── PASSO 1: Prepara cópias dos processos como dicionários ───────────
    # Usamos cópias para não modificar os objetos originais.
    # "restante" começa igual ao burst e vai diminuindo a cada fatia executada.
    ps = [{"nome": p.nome, "chegada": p.t_chegada_sim,
            "burst": p.burst_time, "restante": p.burst_time,
            "cor": p.cor_gantt}
           for p in processos_orig]

    # ─── PASSO 2: Inicializa estruturas de controle ───────────────────────

    # Relógio simulado: começa no instante em que o primeiro processo chega
    t = min(p["chegada"] for p in ps)

    # Fila circular do Round Robin — processos prontos para executar
    fila_rr = []

    # Processos que ainda não chegaram ao sistema (chegada > t atual)
    restantes_orig = list(ps)

    # Resultado visual: lista de (nome, t_inicio, t_fim, cor) para desenhar o Gantt
    gantt = []

    # Registra o instante em que cada processo termina definitivamente
    conclusao = {}

    # Guarda os tempos de chegada para calcular as métricas no final
    chegadas = {p["nome"]: p["chegada"] for p in ps}

    # ─── PASSO 3: Loop principal ──────────────────────────────────────────
    # Continua enquanto houver processos esperando para chegar OU na fila
    while restantes_orig or fila_rr:

        # Admite na fila todos os processos cujo tempo de chegada já foi atingido
        novos = [p for p in restantes_orig if p["chegada"] <= t]
        for p in novos:
            fila_rr.append(p)
            restantes_orig.remove(p)

        # Se a fila ainda está vazia, a CPU fica ociosa:
        # avança o relógio até o próximo processo chegar
        if not fila_rr:
            t = min(p["chegada"] for p in restantes_orig)
            continue

        # Pega o primeiro processo da fila (política FIFO dentro do RR)
        c = fila_rr.pop(0)

        # Calcula a fatia: executa no máximo 1 quantum, mas nunca mais do que o necessário
        # Exemplo: restante=1 e quantum=3 → executa apenas 1u, não 3u
        fatia = min(quantum, c["restante"])

        # Registra esse bloco de execução no Gantt
        gantt.append((c["nome"], t, t + fatia, c["cor"]))

        # Avança o relógio e desconta o tempo executado
        t += fatia
        c["restante"] -= fatia

        # Admite processos que chegaram DURANTE a execução dessa fatia.
        # Eles entram na fila ANTES do processo atual voltar,
        # garantindo a ordem correta de escalonamento.
        novos2 = [p for p in restantes_orig if p["chegada"] <= t]
        for p in novos2:
            fila_rr.append(p)
            restantes_orig.remove(p)

        # Decide o destino do processo após a fatia:
        if c["restante"] > 0:
            # Ainda tem trabalho a fazer → preempção: volta ao FIM da fila
            # Essa é a essência do Round Robin — ninguém fica com a CPU para sempre
            fila_rr.append(c)
        else:
            # Terminou completamente → registra o instante de conclusão
            conclusao[c["nome"]] = t

    # ─── PASSO 4: Calcula as métricas ────────────────────────────────────

    # Turnaround = tempo total que o processo ficou no sistema (do início ao fim)
    turnarounds = {
        nome: max(0, conclusao[nome] - chegadas[nome])
        for nome in conclusao
    }

    #   espera = turnaround - burst
    #   tempo total no sistema menos o tempo que realmente usou a CPU.
    esperas_reais = {}
    for p in ps:
        if p["nome"] in conclusao:
            esperas_reais[p["nome"]] = max(0, turnarounds[p["nome"]] - p["burst"])

    # ─── PASSO 5: Monta e retorna o resultado ────────────────────────────

    vals = list(esperas_reais.values())
    media = sum(vals) / len(vals) if vals else 0

    # Fórmula legível para exibir na tela, ex: "(6 + 2 + 6) / 3 = 4,7"
    formula = f"({' + '.join(str(round(v,1)) for v in vals)}) / {len(vals)} = {media:.1f}"

    r = ResultadoSimulacao("RR", processos_orig, gantt, esperas_reais, turnarounds, media)
    r.formula = formula
    return r
