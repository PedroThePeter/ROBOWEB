"""
Backtest walk-forward do motor da Lotofácil.

Para cada concurso alvo N, o motor só enxerga os concursos anteriores a N: calcula
pesos por frequência (janela dos últimos --janela concursos), gera bilhetes e é
comparado com bilhetes aleatórios NO MESMO concurso.

Mede:
  1. Média de acertos.
  2. Taxa de bilhetes premiados (11+ acertos), que é o que realmente paga.
  3. Diferença PAREADA por rodada com intervalo de confiança de 95% (t de Student).
     Se o intervalo inclui zero, a diferença não se distingue do acaso.
  4. Valores teóricos de um bilhete aleatório, para conferir o baseline.

Uso:
    python backtest.py Lotofacil.xlsx --inicio 100 --passo 10 --bilhetes 3
    python backtest.py Lotofacil.xlsx --janela 50 --semente 42
"""

import argparse
import math
import random
import statistics
import sys
import time
from typing import Dict, List

import engine
from dados import carregar_sorteios

LIMITE_PREMIO = 11          # a Lotofácil paga de 11 a 15 acertos
BILHETES_BASELINE = 200     # bilhetes aleatórios por rodada (baseline pouco ruidoso)

# Valor crítico t (bicaudal, 95%) por graus de liberdade (sem depender do scipy).
_T975 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
    9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074,
    23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045,
    30: 2.042,
}


def _t_critico(graus: int) -> float:
    if graus in _T975:
        return _T975[graus]
    if graus <= 60:
        return 2.000
    if graus <= 120:
        return 1.980
    return 1.960


# ----------------------------------------------------------------------
# Valores teóricos de um bilhete aleatório de 15 dezenas
# ----------------------------------------------------------------------
def media_teorica() -> float:
    return 15 * 15 / 25


def taxa_premio_teorica() -> float:
    total = math.comb(25, 15)
    favoraveis = sum(math.comb(15, k) * math.comb(10, 15 - k) for k in range(LIMITE_PREMIO, 16))
    return favoraveis / total


# ----------------------------------------------------------------------
# Estatística
# ----------------------------------------------------------------------
def calcular_ic95_t_student(amostra):
    """Retorna (média, limite_inferior, limite_superior, margem) com IC de 95% por t de Student."""
    if not amostra:
        return 0.0, 0.0, 0.0, 0.0
    media = statistics.mean(amostra)
    n = len(amostra)
    if n < 2:
        return media, media, media, 0.0
    margem = _t_critico(n - 1) * statistics.stdev(amostra) / math.sqrt(n)
    return media, media - margem, media + margem, margem


def ic95(valores: List[float]):
    media, inferior, superior, _ = calcular_ic95_t_student(valores)
    return media, inferior, superior


def metricas_bilhetes(bilhetes: List[List[int]], real: set) -> Dict[str, float]:
    acertos = [len(real.intersection(b)) for b in bilhetes]
    return {
        "media": statistics.mean(acertos),
        "taxa": sum(1 for a in acertos if a >= LIMITE_PREMIO) / len(acertos),
        "acertos": acertos,
    }


def diferencas_pareadas(a: Dict[int, dict], b: Dict[int, dict], chave: str) -> List[float]:
    comuns = sorted(set(a) & set(b))
    return [a[i][chave] - b[i][chave] for i in comuns]


def veredito(inferior: float, superior: float) -> str:
    if inferior > 0:
        return "ACIMA do acaso"
    if superior < 0:
        return "ABAIXO do acaso"
    return "indistinguível do acaso"


# ----------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------
def rodar_baseline(sorteios: List[List[int]], alvos: List[int], rng: random.Random) -> Dict[int, dict]:
    saida = {}
    for idx in alvos:
        # <--- ALTERAÇÃO 1: Baseline respeita a reprodutibilidade do RNG
        bilhetes = [sorted(rng.sample(range(1, 26), 15)) for _ in range(BILHETES_BASELINE)]
        saida[idx] = metricas_bilhetes(bilhetes, set(sorteios[idx]))
    return saida


def rodar_engine(sorteios: List[List[int]], alvos: List[int], n_bilhetes: int, janela: int, rng: random.Random) -> Dict[int, dict]:
    saida = {}
    inicio = time.time()
    for k, idx in enumerate(alvos, 1):
        pesos = engine.pesos_por_frequencia(sorteios[:idx], janela or None)  # só o passado
        # <--- ALTERAÇÃO 2: Passamos o RNG com seed para forçar a engine a agir como laboratório
        resultado = engine.gerar_jogos_genetico(quantidade=n_bilhetes, pesos=pesos, rng=rng)
        saida[idx] = metricas_bilhetes(resultado["bilhetes"], set(sorteios[idx]))
        if k % 50 == 0:
            print(f"   [engine] {k}/{len(alvos)} rodadas ({time.time() - inicio:.0f}s)")
    return saida


def imprimir_resultado_principal(eng: Dict[int, dict], base: Dict[int, dict]):
    comuns = sorted(set(eng) & set(base))
    todos_eng = [a for i in comuns for a in eng[i]["acertos"]]
    todos_base = [a for i in comuns for a in base[i]["acertos"]]

    m_media, lo_media, hi_media = ic95(diferencas_pareadas(eng, base, "media"))
    m_taxa, lo_taxa, hi_taxa = ic95(diferencas_pareadas(eng, base, "taxa"))

    print("\n" + "=" * 68)
    print(f"RESULTADO — {len(comuns)} rodadas, {len(todos_eng)} bilhetes da engine")
    print("=" * 68)
    print(f"{'':28s}{'Engine':>10s}{'Aleatório':>12s}{'Teórico':>10s}")
    print(f"{'Média de acertos':28s}{statistics.mean(todos_eng):10.3f}{statistics.mean(todos_base):12.3f}{media_teorica():10.3f}")
    taxa_eng = sum(1 for a in todos_eng if a >= LIMITE_PREMIO) / len(todos_eng)
    taxa_base = sum(1 for a in todos_base if a >= LIMITE_PREMIO) / len(todos_base)
    print(f"{'Bilhetes com 11+ (premiados)':28s}{taxa_eng * 100:9.2f}%{taxa_base * 100:11.2f}%{taxa_premio_teorica() * 100:9.2f}%")

    print("\nDiferença engine - aleatório (pareada por rodada, IC 95% t de Student):")
    print(f"  Média de acertos : {m_media:+.3f}  [{lo_media:+.3f} ; {hi_media:+.3f}]  => {veredito(lo_media, hi_media)}")
    print(f"  Taxa de 11+      : {m_taxa * 100:+.2f} p.p. [{lo_taxa * 100:+.2f} ; {hi_taxa * 100:+.2f}]  => {veredito(lo_taxa, hi_taxa)}")
    print("  (Mesmo com dados puramente aleatórios, ~5% dos testes saem 'significativos' por acaso.)")

    print("\nDistribuição de acertos da engine:")
    for n in range(LIMITE_PREMIO, 16):
        qtd = sum(1 for a in todos_eng if a == n)
        if qtd:
            print(f"  {n} acertos: {qtd}x")


def rodar_backtest(caminho: str, inicio: int, passo: int, n_bilhetes: int, janela: int, semente: int = None) -> None:
    sorteios = carregar_sorteios(caminho)
    total = len(sorteios)

    if inicio >= total:
        print(f"A base tem só {total} concursos válidos; --inicio ({inicio}) é maior que isso.")
        sys.exit(1)

    # <--- ALTERAÇÃO 3: Criamos um RNG dedicado para o escopo do backtest
    rng = random.Random(semente)

    alvos = list(range(inicio, total, passo))
    print(f"Base: {total} concursos válidos | {len(alvos)} rodadas | {n_bilhetes} bilhetes por rodada | janela {janela or 'toda a base'}")
    print(f"Sorteio teórico: média {media_teorica():.3f} acertos, {taxa_premio_teorica() * 100:.2f}% dos bilhetes com 11+")

    base = rodar_baseline(sorteios, alvos, rng)
    eng = rodar_engine(sorteios, alvos, n_bilhetes, janela, rng)
    imprimir_resultado_principal(eng, base)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest walk-forward do motor da Lotofácil")
    parser.add_argument("planilha", help="Caminho para Lotofacil.xlsx")
    parser.add_argument("--inicio", type=int, default=100, help="Primeiro concurso (índice) a testar")
    parser.add_argument("--passo", type=int, default=10, help="De quantos em quantos concursos testar")
    parser.add_argument("--bilhetes", type=int, default=3, help="Bilhetes gerados por rodada (1 a 100)")
    parser.add_argument("--janela", type=int, default=100, help="Concursos passados usados nos pesos (0 = todos)")
    parser.add_argument("--semente", type=int, default=None, help="Semente aleatória para resultado reproduzível")
    args = parser.parse_args()

    # Passamos a semente explicitamente para a função
    rodar_backtest(args.planilha, args.inicio, args.passo, args.bilhetes, args.janela, args.semente)