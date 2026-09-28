"""
Desdobramento (fechamento) para a Lotofácil.

IDEIA
Você escolhe um grupo de K dezenas (16 a 18). O módulo gera o MENOR conjunto de
bilhetes de 15 dezenas, todos formados só com essas K dezenas, que GARANTE um
mínimo de acertos (ex: 14) SE as 15 dezenas sorteadas estiverem todas dentro do
seu grupo.

MATEMÁTICA
Se o sorteio D está dentro do grupo, o que sobra do grupo (K-15 dezenas) é o
conjunto M "não sorteadas do grupo". Um bilhete B também deixa de fora K-15
dezenas do grupo (conjunto E). O número de acertos vira:

    acertos = (30 - K) + |M ∩ E|

Então "garantir G acertos" equivale a: para todo M possível, algum bilhete tem
|M ∩ E| >= G - (30 - K). É um problema de cobertura; resolvemos com o algoritmo
guloso clássico (bem próximo do mínimo) e depois VERIFICAMOS por força bruta.

LIMITE HONESTO
A garantia só vale se as 15 sorteadas caírem dentro das suas K dezenas.
Isso ocorre com probabilidade C(K,15)/C(25,15): cerca de 1 em 204 mil (K=16),
1 em 24 mil (K=17) e 1 em 4 mil (K=18). Desdobrar não aumenta o valor esperado
da aposta; só organiza como o dinheiro é distribuído.

USO EM LINHA DE COMANDO
    python desdobramento.py --dezenas 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17 --garantia 14
"""

import argparse
import math
from collections import Counter
from itertools import combinations
from typing import Any, Dict, List

import numpy as np

TAMANHO_MIN_POOL = 16
TAMANHO_MAX_POOL = 18
GARANTIA_MIN = 11
GARANTIA_MAX = 14


def probabilidade_pool_conter_sorteio(tamanho_pool: int) -> float:
    return math.comb(tamanho_pool, 15) / math.comb(25, 15)


def _validar(dezenas: List[int], garantia: int) -> None:
    if len(set(dezenas)) != len(dezenas):
        raise ValueError("Há dezenas repetidas na lista.")
    if any(d < 1 or d > 25 for d in dezenas):
        raise ValueError("Todas as dezenas devem estar entre 1 e 25.")
    if not (TAMANHO_MIN_POOL <= len(dezenas) <= TAMANHO_MAX_POOL):
        raise ValueError(
            f"Informe entre {TAMANHO_MIN_POOL} e {TAMANHO_MAX_POOL} dezenas "
            f"(recebi {len(dezenas)})."
        )
    if not (GARANTIA_MIN <= garantia <= GARANTIA_MAX):
        raise ValueError(f"A garantia deve estar entre {GARANTIA_MIN} e {GARANTIA_MAX}.")


def verificar_desdobramento(dezenas: List[int], bilhetes: List[List[int]]) -> Dict[int, int]:
    """
    Força bruta: para CADA sorteio possível dentro do grupo, calcula o melhor
    resultado entre os bilhetes. Retorna {melhor_acerto: quantos_sorteios}.
    """
    masks_bilhetes = [sum(1 << d for d in b) for b in bilhetes]
    distribuicao: Counter = Counter()
    for sorteio in combinations(dezenas, 15):
        mask_sorteio = sum(1 << d for d in sorteio)
        melhor = max(bin(mask_sorteio & mb).count("1") for mb in masks_bilhetes)
        distribuicao[melhor] += 1
    return dict(sorted(distribuicao.items()))


def gerar_desdobramento(dezenas: List[int], garantia: int = 14) -> Dict[str, Any]:
    dezenas = sorted(int(d) for d in dezenas)
    _validar(dezenas, garantia)

    k = len(dezenas)
    m = k - 15                 # quantas dezenas cada bilhete deixa de fora
    base = 30 - k              # acertos garantidos por QUALQUER bilhete do grupo
    t = garantia - base        # interseção mínima exigida entre M e E

    if t <= 0:
        # Qualquer bilhete já garante o pedido.
        excluidos_lista = [tuple(range(m))]
    else:
        todas_exclusoes = list(combinations(range(k), m))
        n = len(todas_exclusoes)

        incidencia = np.zeros((n, k), dtype=np.int16)
        for i, exclusao in enumerate(todas_exclusoes):
            incidencia[i, list(exclusao)] = 1

        intersecao = incidencia @ incidencia.T
        cobre = (intersecao >= t).astype(np.int32)

        nao_coberto = np.ones(n, dtype=np.int32)
        escolhidos: List[int] = []
        while nao_coberto.any():
            ganhos = cobre @ nao_coberto
            melhor = int(np.argmax(ganhos))
            escolhidos.append(melhor)
            nao_coberto = nao_coberto * (1 - cobre[melhor])

        excluidos_lista = [todas_exclusoes[i] for i in escolhidos]

    bilhetes: List[List[int]] = []
    for exclusao in excluidos_lista:
        fora = set(exclusao)
        bilhetes.append([dezenas[j] for j in range(k) if j not in fora])

    distribuicao = verificar_desdobramento(dezenas, bilhetes)
    garantia_ok = min(distribuicao) >= garantia
    prob = probabilidade_pool_conter_sorteio(k)

    return {
        "dezenas": dezenas,
        "tamanho_pool": k,
        "garantia_pedida": garantia,
        "garantia_verificada": garantia_ok,
        "bilhetes": bilhetes,
        "quantidade_bilhetes": len(bilhetes),
        "probabilidade_pool_conter_sorteio": prob,
        "um_em": round(1 / prob),
        "melhor_acerto_se_pool_conter_sorteio": distribuicao,
        "observacao": (
            "A garantia só vale se as 15 dezenas sorteadas estiverem todas dentro "
            "das dezenas escolhidas."
        ),
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description="Desdobramento com garantia para a Lotofácil")
    parser.add_argument("--dezenas", required=True, help="Dezenas separadas por vírgula (16 a 18)")
    parser.add_argument("--garantia", type=int, default=14, help="Acertos garantidos (11 a 14)")
    args = parser.parse_args()

    dezenas = [int(x) for x in args.dezenas.split(",")]
    r = gerar_desdobramento(dezenas, args.garantia)

    print(f"Grupo ({r['tamanho_pool']} dezenas): {r['dezenas']}")
    print(f"Garantia pedida: {r['garantia_pedida']} acertos | verificada: {r['garantia_verificada']}")
    print(f"Bilhetes necessários: {r['quantidade_bilhetes']}\n")
    for i, b in enumerate(r["bilhetes"], 1):
        print(f"Bilhete {i:2d}: {' - '.join(f'{d:02d}' for d in b)}")
    print(f"\nChance de as 15 sorteadas caírem no seu grupo: 1 em {r['um_em']:,}".replace(",", "."))
    print(f"Se cair, melhor resultado por sorteio possível: {r['melhor_acerto_se_pool_conter_sorteio']}")
    print(f"\n{r['observacao']}")


if __name__ == "__main__":
    _main()