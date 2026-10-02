"""
Análise estatística e geração de bilhetes por frequência + atraso.

Leitura da planilha via dados.py (mesma validação do restante do sistema).
Os pesos gerados são compatíveis com engine.gerar_jogos_genetico(pesos=...),
com integridade.gravar_trava(...) e com o diário/comprovantes.

ATENÇÃO: a mistura frequência + atraso é uma HIPÓTESE. O analise_memoria.py
não encontrou evidência de "dívida de atraso". Valide com backtest walk-forward
antes de tratar esses pesos como algo além de uma forma de variar os bilhetes.
"""

import itertools
import math
import secrets  # <--- ALTERAÇÃO 1: Substitui import random
import statistics
from collections import Counter
from typing import Dict, List, Optional

import integridade
from dados import carregar_sorteios

# Armazenamento em memória das sessões (listas de sorteios já validados)
sessions: Dict[str, dict] = {}

PESO_FREQUENCIA = 0.6
PESO_ATRASO = 0.4
PESO_MINIMO = 0.01
MAX_TENTATIVAS = 10000


def process_upload(file_path: str, session_id: str) -> dict:
    """Lê a planilha (xlsx/csv) pelo dados.py e guarda os sorteios válidos na sessão."""
    try:
        sorteios = carregar_sorteios(file_path)
        if not sorteios:
            raise ValueError("A planilha não tem nenhum concurso válido.")
        sessions[session_id] = {"sorteios": sorteios}
        return {"total_concursos": len(sorteios), "colunas_identificadas": 15}
    except Exception as e:
        raise ValueError(f"Erro ao processar arquivo: {e}")


def calcular_stats_de_sorteios(sorteios: List[List[int]]) -> dict:
    """Estatísticas a partir de uma lista de sorteios (ordem cronológica)."""
    if not sorteios:
        raise ValueError("Sem sorteios para analisar.")

    freq = Counter(d for s in sorteios for d in s)
    frequencias = {d: freq.get(d, 0) for d in range(1, 26)}
    frequencias = dict(sorted(frequencias.items(), key=lambda x: x[1], reverse=True))

    # Atraso: concursos desde a última aparição (0 = saiu no último concurso)
    total = len(sorteios)
    atrasos: Dict[int, int] = {}
    for d in range(1, 26):
        atrasos[d] = total
        for passos, s in enumerate(reversed(sorteios)):
            if d in s:
                atrasos[d] = passos
                break

    pares = [sum(1 for d in s if d % 2 == 0) for s in sorteios]
    somas = [sum(s) for s in sorteios]

    pares_counter: Counter = Counter()
    for s in sorteios:
        pares_counter.update(itertools.combinations(sorted(s), 2))

    return {
        "frequencias": frequencias,
        "atrasos": atrasos,
        "par_impar": {
            "media_pares": float(statistics.mean(pares)),
            "media_impares": float(15 - statistics.mean(pares)),
        },
        "soma": {
            "media": float(statistics.mean(somas)),
            "desvio_padrao": float(statistics.stdev(somas)) if len(somas) > 1 else 0.0,
        },
        "top_pares": [{"par": f"{p[0]}-{p[1]}", "freq": c} for p, c in pares_counter.most_common(10)],
    }


def calculate_stats(session_id: str) -> dict:
    data = sessions.get(session_id)
    if not data:
        raise ValueError("Sessão não encontrada.")
    return calcular_stats_de_sorteios(data["sorteios"])


def pesos_freq_atraso(stats: dict, number_range: int = 25,
                      peso_freq: float = PESO_FREQUENCIA,
                      peso_atraso: float = PESO_ATRASO) -> Dict[str, float]:
    """
    Peso de cada dezena = frequência normalizada * peso_freq + atraso normalizado * peso_atraso.
    Devolve {"1": peso, ..., "25": peso} (chaves em texto, como o engine e a trava esperam).
    """
    freq = stats.get("frequencias", {})
    atraso = stats.get("atrasos", {})
    max_freq = max(freq.values(), default=0) or 1
    max_atraso = max(atraso.values(), default=0) or 1

    pesos: Dict[str, float] = {}
    for n in range(1, number_range + 1):
        f = freq.get(n, freq.get(str(n), 0))
        a = atraso.get(n, atraso.get(str(n), 0))
        score = (f / max_freq) * peso_freq + (a / max_atraso) * peso_atraso
        pesos[str(n)] = max(score, PESO_MINIMO)
    return pesos


def _sortear_ponderado(pesos: Dict[int, float], quantidade: int, rng) -> List[int]:
    """Sorteio sem reposição proporcional aos pesos (método das chaves exponenciais)."""
    chaves = {d: rng.random() ** (1.0 / w) for d, w in pesos.items()}
    return sorted(sorted(chaves, key=chaves.get, reverse=True)[:quantidade])


def generate_tickets(config: dict, stats: dict, rng=None) -> List[dict]:
    """
    config: ticket_count (obrigatório); total_numbers (padrão 15); number_range (padrão 25);
            fixed_numbers; excluded_numbers; filtrar_soma (padrão True).
    Pode devolver menos bilhetes que o pedido se o filtro de soma for muito restritivo:
    confira len(resultado).
    """
    # <--- ALTERAÇÃO 2: Sistema protegido com secrets
    rng = rng or secrets.SystemRandom()
    
    total = int(config.get("total_numbers", 15))
    faixa = int(config.get("number_range", 25))
    fixos = sorted(set(int(n) for n in config.get("fixed_numbers", [])))
    excluidos = set(int(n) for n in config.get("excluded_numbers", []))
    quantidade = int(config["ticket_count"])

    if quantidade < 1:
        raise ValueError("ticket_count deve ser pelo menos 1.")
    if any(n < 1 or n > faixa for n in fixos):
        raise ValueError(f"Dezenas fixas devem estar entre 1 e {faixa}.")
    if set(fixos) & excluidos:
        raise ValueError("Uma dezena não pode ser fixa e excluída ao mesmo tempo.")
    if len(fixos) > total:
        raise ValueError("Há mais dezenas fixas do que o tamanho do bilhete.")

    pesos_todos = pesos_freq_atraso(stats, faixa)
    pool = {int(n): w for n, w in pesos_todos.items()
            if int(n) not in excluidos and int(n) not in fixos}
    faltam = total - len(fixos)
    if faltam > len(pool):
        raise ValueError("Dezenas insuficientes depois de aplicar fixas e excluídas.")

    soma_min = soma_max = None
    soma = stats.get("soma") or {}
    if config.get("filtrar_soma", True) and soma.get("desvio_padrao", 0) > 0:
        soma_min = soma["media"] - soma["desvio_padrao"]
        soma_max = soma["media"] + soma["desvio_padrao"]

    bilhetes: List[dict] = []
    vistos = set()
    tentativas = 0
    while len(bilhetes) < quantidade and tentativas < MAX_TENTATIVAS:
        tentativas += 1
        candidato = sorted(fixos + _sortear_ponderado(pool, faltam, rng)) if faltam > 0 else list(fixos)
        chave = tuple(candidato)
        if chave in vistos:
            continue
        s = sum(candidato)
        if soma_min is not None and not (soma_min <= s <= soma_max):
            continue
        vistos.add(chave)
        pares = sum(1 for x in candidato if x % 2 == 0)
        bilhetes.append({
            "numeros": candidato,
            "soma": s,
            "pares": pares,
            "impares": total - pares,
            "score_confianca": round(sum(pesos_todos[str(n)] for n in candidato) / total * 100, 1),
            "hash": integridade._hash_bilhete(candidato),
        })
    return bilhetes


def gerar_para_diario(session_id: str, quantidade: int = 10, concurso: Optional[int] = None,
                      rng=None) -> dict:
    """
    Gera bilhetes de Lotofácil (15 de 25) no mesmo formato do engine, pronto para
    diario.salvar_palpites(...) e integridade.registrar_comprovantes(concurso, resultado["bilhetes"]).
    """
    stats = calculate_stats(session_id)
    tickets = generate_tickets(
        {"ticket_count": quantidade, "total_numbers": 15, "number_range": 25}, stats, rng
    )
    jogos = [t["numeros"] for t in tickets]
    return {
        "status": "sucesso",
        "concurso": concurso,
        "quantidade": len(jogos),
        "jogos": jogos,
        "bilhetes": jogos,
        "hashes": [t["hash"] for t in tickets],
        "trava_valida": False,  # pesos calculados na hora, não vêm da trava
    }