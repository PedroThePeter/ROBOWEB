"""
Backtest v2 (walk-forward) para o LotofacilGeneticEngine.

Para cada concurso alvo N, a engine só enxerga os concursos anteriores a N,
gera bilhetes e é comparada com bilhetes aleatórios NO MESMO concurso.

O que a v2 acrescenta:
  1. Taxa de bilhetes premiados (11+ acertos), que é o que realmente paga.
  2. Comparação PAREADA por rodada com intervalo de confiança de 95% (t de Student).
     Se o intervalo inclui zero, a diferença não se distingue do acaso. O baseline
     usa 200 bilhetes aleatórios por rodada para não injetar ruído na comparação.
     (Mesmo assim, ~5% dos testes sobre dados puramente aleatórios saem "significativos"
     por acaso: é assim que um intervalo de 95% funciona.)
  3. Valores teóricos de um bilhete aleatório, para conferir o baseline.
  4. Teste de ablação (--ablacao): remove um critério por vez e mede o efeito.

Uso:
    python backtest.py Lotofacil.xlsx --inicio 100 --passo 10 --bilhetes 3
    python backtest.py Lotofacil.xlsx --inicio 100 --passo 30 --bilhetes 3 --ablacao
    python backtest.py Lotofacil.xlsx --semente 42      # resultado reproduzível
"""

import argparse
import math
import random
import statistics
import sys
import time
from typing import Dict, List, Optional

import pandas as pd

from engine import LotofacilGeneticEngine, PESOS_PADRAO

LIMITE_PREMIO = 11  # a Lotofácil paga de 11 a 15 acertos
BILHETES_BASELINE = 200  # bilhetes aleatórios por rodada (baseline pouco ruidoso)

# Valor crítico t (bicaudal, 95%) por graus de liberdade. Com poucas rodadas, usar
# 1,96 (normal) deixaria o intervalo estreito demais e geraria falsos positivos.
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
    favoraveis = sum(
        math.comb(15, k) * math.comb(10, 15 - k) for k in range(LIMITE_PREMIO, 16)
    )
    return favoraveis / total


# ----------------------------------------------------------------------
# Métricas
# ----------------------------------------------------------------------
def metricas_bilhetes(bilhetes: List[List[int]], real: set) -> Dict[str, float]:
    acertos = [len(real.intersection(b)) for b in bilhetes]
    return {
        "media": statistics.mean(acertos),
        "taxa": sum(1 for a in acertos if a >= LIMITE_PREMIO) / len(acertos),
        "acertos": acertos,
    }


def ic95(valores: List[float]):
    n = len(valores)
    media = statistics.mean(valores)
    if n < 2:
        return media, media, media
    erro = statistics.stdev(valores) / math.sqrt(n)
    t = _t_critico(n - 1)
    return media, media - t * erro, media + t * erro


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
def carregar_base(caminho: str):
    df = pd.read_excel(caminho)
    sorteios = LotofacilGeneticEngine(df)._sorteios
    return df, sorteios


def rodar_baseline(sorteios: List[List[int]], alvos: List[int]) -> Dict[int, dict]:
    saida = {}
    for idx in alvos:
        bilhetes = [sorted(random.sample(range(1, 26), 15)) for _ in range(BILHETES_BASELINE)]
        saida[idx] = metricas_bilhetes(bilhetes, set(sorteios[idx]))
    return saida


def rodar_engine(
    df: pd.DataFrame,
    sorteios: List[List[int]],
    alvos: List[int],
    n_bilhetes: int,
    pesos: Optional[Dict[str, int]],
    score_minimo: int,
    rotulo: str,
) -> Dict[int, dict]:
    saida = {}
    inicio = time.time()
    for k, idx in enumerate(alvos, 1):
        engine = LotofacilGeneticEngine(df.iloc[:idx], pesos=pesos, sorteios=sorteios[:idx])
        resultado = engine.executar_geracao_genetica(
            quantidade_desejada=n_bilhetes, score_minimo=score_minimo
        )
        if not resultado["bilhetes"]:
            continue
        saida[idx] = metricas_bilhetes(resultado["bilhetes"], set(sorteios[idx]))
        if k % 50 == 0:
            print(f"   [{rotulo}] {k}/{len(alvos)} rodadas ({time.time() - inicio:.0f}s)")
    return saida


def imprimir_resultado_principal(eng: Dict[int, dict], base: Dict[int, dict], n_bilhetes: int):
    comuns = sorted(set(eng) & set(base))
    todos_eng = [a for i in comuns for a in eng[i]["acertos"]]
    todos_base = [a for i in comuns for a in base[i]["acertos"]]

    d_media = diferencas_pareadas(eng, base, "media")
    d_taxa = diferencas_pareadas(eng, base, "taxa")
    m_media, lo_media, hi_media = ic95(d_media)
    m_taxa, lo_taxa, hi_taxa = ic95(d_taxa)

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

    print("\nDistribuição de acertos da engine:")
    for n in range(LIMITE_PREMIO, 16):
        qtd = sum(1 for a in todos_eng if a == n)
        if qtd:
            print(f"  {n} acertos: {qtd}x")


def rodar_ablacao(df, sorteios, alvos, n_bilhetes, score_minimo, base, eng_completa):
    razao = score_minimo / sum(PESOS_PADRAO.values())
    print("\n" + "=" * 68)
    print("ABLAÇÃO — removendo um critério por vez (score mínimo proporcional)")
    print("=" * 68)
    linhas = []
    for criterio in PESOS_PADRAO:
        pesos = dict(PESOS_PADRAO)
        pesos[criterio] = 0
        sm = round(razao * sum(pesos.values()))
        res = rodar_engine(df, sorteios, alvos, n_bilhetes, pesos, sm, f"sem {criterio}")

        d_base = diferencas_pareadas(res, base, "media")
        d_full = diferencas_pareadas(res, eng_completa, "media")
        if len(d_base) < 2 or len(d_full) < 2:
            continue
        m_b, lo_b, hi_b = ic95(d_base)
        m_f, lo_f, hi_f = ic95(d_full)
        linhas.append((criterio, sm, m_b, lo_b, hi_b, m_f, lo_f, hi_f))

    print(f"{'Sem o critério':22s}{'Score mín':>10s}{'Δ vs aleatório [IC95%]':>32s}{'Δ vs engine completa [IC95%]':>34s}")
    for criterio, sm, m_b, lo_b, hi_b, m_f, lo_f, hi_f in linhas:
        print(
            f"{criterio:22s}{sm:10d}"
            f"{m_b:+10.3f} [{lo_b:+.3f};{hi_b:+.3f}]"
            f"{m_f:+12.3f} [{lo_f:+.3f};{hi_f:+.3f}]"
        )
    print(
        "\nComo ler: se remover um critério NÃO piora o resultado (Δ vs completa perto de 0,\n"
        "intervalo incluindo 0), ele não está contribuindo. Atenção: ao testar 8 critérios,\n"
        "um deles pode parecer relevante só por acaso; desconfie de um resultado isolado."
    )


def rodar_backtest(caminho, inicio, passo, n_bilhetes, score_minimo, ablacao):
    df, sorteios = carregar_base(caminho)
    total = len(sorteios)

    if inicio >= total:
        print(f"A base tem só {total} concursos válidos; --inicio ({inicio}) é maior que isso.")
        sys.exit(1)

    alvos = list(range(inicio, total, passo))
    print(f"Base: {total} concursos válidos | {len(alvos)} rodadas | {n_bilhetes} bilhetes por rodada")
    print(f"Sorteio teórico: média {media_teorica():.3f} acertos, {taxa_premio_teorica() * 100:.2f}% dos bilhetes com 11+")

    base = rodar_baseline(sorteios, alvos)
    eng = rodar_engine(df, sorteios, alvos, n_bilhetes, None, score_minimo, "engine")

    if not eng:
        print("Nenhuma rodada produziu bilhetes (score mínimo alto demais?).")
        return

    imprimir_resultado_principal(eng, base, n_bilhetes)

    if ablacao:
        rodar_ablacao(df, sorteios, alvos, n_bilhetes, score_minimo, base, eng)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest walk-forward v2 da LotofacilGeneticEngine")
    parser.add_argument("planilha", help="Caminho para Lotofacil.xlsx")
    parser.add_argument("--inicio", type=int, default=100, help="Primeiro concurso (índice) a testar")
    parser.add_argument("--passo", type=int, default=10, help="De quantos em quantos concursos testar")
    parser.add_argument("--bilhetes", type=int, default=3, help="Bilhetes gerados por rodada")
    parser.add_argument("--score-minimo", type=int, default=150, help="Score mínimo usado na engine")
    parser.add_argument("--ablacao", action="store_true", help="Roda também o teste de ablação (demora mais)")
    parser.add_argument("--semente", type=int, default=None, help="Semente aleatória para resultado reproduzível")
    args = parser.parse_args()

    if args.semente is not None:
        random.seed(args.semente)

    rodar_backtest(args.planilha, args.inicio, args.passo, args.bilhetes, args.score_minimo, args.ablacao)