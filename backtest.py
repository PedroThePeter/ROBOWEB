"""
Backtesting walk-forward para o LotofacilGeneticEngine.

IDEIA:
Para cada concurso real N no histórico (a partir de um ponto de corte
mínimo, ex: concurso 100), rodamos a engine usando SOMENTE os concursos
1..N-1 (nunca informação do futuro), geramos alguns bilhetes candidatos,
e comparamos com o resultado real do concurso N para ver quantos pontos
eles teriam feito.

Isso responde à pergunta real: "os critérios de pontuação e o score
mínimo escolhidos realmente geram bilhetes melhores que o acaso, quando
testados de forma honesta contra o histórico?"

Como usar:
    python backtest.py Lotofacil.xlsx --inicio 100 --passo 10 --bilhetes 3

Isso testa a cada 10 concursos (pra rodar mais rápido), gerando 3
bilhetes por rodada, e no final mostra:
  - distribuição de acertos dos bilhetes da engine
  - distribuição de acertos de bilhetes 100% aleatórios (baseline)
  - se a engine bate o baseline aleatório de forma consistente
"""

import argparse
import random
import statistics
import sys
from typing import List

import pandas as pd

from engine import LotofacilGeneticEngine


def gerar_bilhete_aleatorio() -> List[int]:
    return sorted(random.sample(range(1, 26), 15))


def contar_acertos(bilhete: List[int], resultado_real: List[int]) -> int:
    return len(set(bilhete).intersection(set(resultado_real)))


def rodar_backtest(caminho_planilha: str, inicio: int, passo: int, n_bilhetes: int, score_minimo: int):
    df_completo = pd.read_excel(caminho_planilha)
    total = len(df_completo)

    if inicio >= total:
        print(f"Base tem só {total} concursos; --inicio ({inicio}) é maior que isso.")
        sys.exit(1)

    acertos_engine: List[int] = []
    acertos_aleatorio: List[int] = []
    rodadas = 0

    for idx_alvo in range(inicio, total, passo):
        df_treino = df_completo.iloc[:idx_alvo]  # só passado, nunca o alvo
        linha_real = df_completo.iloc[idx_alvo]

        engine = LotofacilGeneticEngine(df_treino)
        resultado_real = engine._extrair_dezenas_linha(linha_real)
        if len(resultado_real) != 15:
            continue  # linha malformada, pula

        resultado = engine.executar_geracao_genetica(
            quantidade_desejada=n_bilhetes,
            score_minimo=score_minimo,
        )

        bilhetes_gerados = resultado["bilhetes"]
        if not bilhetes_gerados:
            continue

        rodadas += 1
        for b in bilhetes_gerados:
            acertos_engine.append(contar_acertos(b, resultado_real))

        for _ in range(n_bilhetes):
            acertos_aleatorio.append(contar_acertos(gerar_bilhete_aleatorio(), resultado_real))

        if rodadas % 5 == 0:
            print(f"... {rodadas} rodadas processadas (concurso {idx_alvo}/{total})")

    if not acertos_engine:
        print("Nenhuma rodada produziu bilhetes (score_minimo pode estar alto demais para bases pequenas).")
        return

    print("\n" + "=" * 60)
    print(f"RESULTADO DO BACKTEST — {rodadas} rodadas, {len(acertos_engine)} bilhetes da engine avaliados")
    print("=" * 60)

    def resumo(nome, dados):
        media = statistics.mean(dados)
        mediana = statistics.median(dados)
        desvio = statistics.stdev(dados) if len(dados) > 1 else 0.0
        maximo = max(dados)
        print(f"{nome:20s} | média={media:5.2f}  mediana={mediana:5.1f}  desvio={desvio:4.2f}  máx={maximo}")

    resumo("Engine (genético)", acertos_engine)
    resumo("Baseline aleatório", acertos_aleatorio)

    diff = statistics.mean(acertos_engine) - statistics.mean(acertos_aleatorio)
    print(f"\nDiferença de média (engine - aleatório): {diff:+.3f} pontos")
    if diff > 0.15:
        print("=> Sinal de que os critérios ajudam, mas rode com mais rodadas/dados antes de confiar.")
    elif diff < -0.15:
        print("=> Engine está PIOR que aleatório neste histórico. Vale revisar os pesos.")
    else:
        print("=> Sem diferença estatisticamente relevante frente ao acaso neste teste.")

    print("\nDistribuição de acertos da engine:")
    for n in range(11, 16):
        qtd = sum(1 for a in acertos_engine if a == n)
        if qtd:
            print(f"  {n} acertos: {qtd}x")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest walk-forward da LotofacilGeneticEngine")
    parser.add_argument("planilha", help="Caminho para Lotofacil.xlsx")
    parser.add_argument("--inicio", type=int, default=100, help="Primeiro concurso (índice) a testar")
    parser.add_argument("--passo", type=int, default=10, help="De quantos em quantos concursos testar")
    parser.add_argument("--bilhetes", type=int, default=3, help="Bilhetes gerados por rodada")
    parser.add_argument("--score-minimo", type=int, default=150, help="Score mínimo usado na engine")
    args = parser.parse_args()

    rodar_backtest(args.planilha, args.inicio, args.passo, args.bilhetes, args.score_minimo)