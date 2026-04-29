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
    """
    SJF — Shortest Job First.
    Algoritmo não preemptivo que escolhe o processo com o menor burst_time primeiro.
    """
    # 1. PREPARAÇÃO: Transforma os objetos Processo em dicionários simples para a simulação
    ps = [{"nome": p.nome, "chegada": p.t_chegada_sim,
           "burst": p.burst_time, "restante": p.burst_time,
           "cor": p.cor_gantt}
          for p in processos_orig]

    # Inicializa o tempo no momento da chegada do primeiro processo
    t = min(p["chegada"] for p in ps)

    # Listas de controle: 'prontos' (aguardando CPU) e 'fila' (ainda não chegaram)
    prontos = []
    fila = list(ps)

    # Estruturas para armazenar os resultados que serão desenhados na UI
    gantt = []
    esperas = {}
    turnarounds = {}
    primeiro_cpu = {}

    # 2. LOOP PRINCIPAL: Executa enquanto houver processos para processar
    while fila or prontos:
        # Move processos que já "chegaram" no tempo 't' para a lista de prontos
        novos = [p for p in fila if p["chegada"] <= t]
        for p in novos:
            prontos.append(p)
            fila.remove(p)

        # Se ninguém chegou ainda, o tempo avança até a próxima chegada
        if not prontos:
            t = min(p["chegada"] for p in fila)
            continue

        # 3. O CORAÇÃO DO SJF: Ordena a lista de prontos pelo menor tempo de execução (burst)
        prontos.sort(key=lambda p: p["burst"])

        # Seleciona o processo mais curto (o primeiro da lista ordenada)
        c = prontos.pop(0)

        if c["nome"] not in primeiro_cpu:
            primeiro_cpu[c["nome"]] = t

        # 4. CÁLCULO DE MÉTRICAS: Registra a espera e monta o bloco do gráfico
        # Espera = Tempo atual - Tempo de chegada
        esperas[c["nome"]] = t - c["chegada"]

        # Adiciona ao Gantt: (nome, início, fim, cor)
        gantt.append((c["nome"], t, t + c["burst"], c["cor"]))

        # Avança o relógio 't' somando o burst do processo que acabou de rodar
        t += c["burst"]

        # Turnaround = Tempo total desde a chegada até o fim da execução
        turnarounds[c["nome"]] = t - c["chegada"]

    # 5. FINALIZAÇÃO: Calcula a média e formata a string da fórmula para a UI
    vals = list(esperas.values())
    media = sum(vals) / len(vals) if vals else 0
    formula = f"({' + '.join(str(v) for v in vals)}) / {len(vals)} = {media:.1f}"

    # Retorna o objeto ResultadoSimulacao com tudo mastigado para a interface
    r = ResultadoSimulacao("SJF", processos_orig, gantt, esperas, turnarounds, media)
    r.formula = formula
    return r

def simular_rr(processos_orig, quantum):
    """Round Robin com quantum configurável. Preemptivo."""
    ps = [{"nome": p.nome, "chegada": p.t_chegada_sim,
            "burst": p.burst_time, "restante": p.burst_time,
            "cor": p.cor_gantt}
           for p in processos_orig]

    t = min(p["chegada"] for p in ps)
    fila_rr = []
    restantes_orig = list(ps)
    gantt = []; conclusao = {}
    chegadas = {p["nome"]: p["chegada"] for p in ps}

    while restantes_orig or fila_rr:
        novos = [p for p in restantes_orig if p["chegada"] <= t]
        for p in novos:
            fila_rr.append(p); restantes_orig.remove(p)

        if not fila_rr:
            t = min(p["chegada"] for p in restantes_orig)
            continue

        c = fila_rr.pop(0)

        fatia = min(quantum, c["restante"])
        gantt.append((c["nome"], t, t + fatia, c["cor"]))
        t += fatia
        c["restante"] -= fatia

        novos2 = [p for p in restantes_orig if p["chegada"] <= t]
        for p in novos2:
            fila_rr.append(p); restantes_orig.remove(p)

        if c["restante"] > 0:
            fila_rr.append(c)          # volta ao fim da fila
        else:
            conclusao[c["nome"]] = t   # concluído

    # Espera real no RR = turnaround - burst
    turnarounds = {nome: max(0, conclusao[nome] - chegadas[nome]) for nome in conclusao}
    esperas_reais = {}
    for p in ps:
        if p["nome"] in conclusao:
            esperas_reais[p["nome"]] = max(0, turnarounds[p["nome"]] - p["burst"])

    vals = list(esperas_reais.values())
    media = sum(vals) / len(vals) if vals else 0
    formula = f"({' + '.join(str(round(v,1)) for v in vals)}) / {len(vals)} = {media:.1f}"

    r = ResultadoSimulacao("RR", processos_orig, gantt, esperas_reais, turnarounds, media)
    r.formula = formula
    return r
