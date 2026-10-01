"""
Compara três estratégias de geração de bilhetes da Lotofácil, walk-forward:

  1. FREQUÊNCIA          -> engine.pesos_por_frequencia (o que o backtest/trava usam)
  2. FREQUÊNCIA + ATRASO -> analyzer.pesos_freq_atraso  (60% frequência + 40% atraso)
  3. ALEATÓRIO           -> sorteio uniforme (baseline)

Para cada concurso alvo N, as estratégias só enxergam os concursos anteriores a N
(mesma janela para as duas), geram bilhetes e são conferidas contra o MESMO sorteio N.
As diferenças são pareadas por rodada e resumidas com o mesmo IC de 95% (t de Student)
e o mesmo veredito do backtest.py (as funções são importadas de lá).

Comparações feitas: freq - aleatório, freq+atraso - aleatório, freq+atraso - freq.
Métricas: média de acertos e taxa de bilhetes com 11+.

CUIDADOS
  * São 3 comparações x 2 métricas = 6 testes: ~26% de chance de ao menos um
    "significativo" por puro acaso. Trate um achado isolado com desconfiança.
  * Com --passo menor que --janela, rodadas vizinhas compartilham dados e o IC
    fica otimista. Prefira --passo >= --janela para rodadas quase independentes.
  * Se tudo der "indistinguível do acaso", é o resultado esperado (ver analise_memoria.py).

USO
    python comparar_estrategias.py Lotofacil.xlsx
    python comparar_estrategias.py Lotofacil.xlsx --inicio 200 --passo 20 --janela 100 --bilhetes 10 --semente 42
"""

import argparse
import random
import statistics
import sys
import time
from typing import Callable, Dict, List

from services import analyzer
import backtest
import engine
from dados import carregar_sorteios

NOMES = {"freq": "Frequência", "fa": "Freq + Atraso", "aleatorio": "Aleatório"}


# ----------------------------------------------------------------------
# Geradores de bilhetes (só recebem o passado)
# ----------------------------------------------------------------------
def _bilhetes_com_pesos(pesos: Dict[str, float], n: int, rng: random.Random) -> List[List[int]]:
    lista = engine._pesos_por_dezena(pesos)
    return [engine.sortear_bilhete(lista, rng) for _ in range(n)]


def bilhetes_frequencia(passado, janela, n, rng):
    return _bilhetes_com_pesos(engine.pesos_por_frequencia(passado, janela or None), n, rng)


def bilhetes_freq_atraso(passado, janela, n, rng):
    recorte = passado[-janela:] if janela else passado
    stats = analyzer.calcular_stats_de_sorteios(recorte)
    return _bilhetes_com_pesos(analyzer.pesos_freq_atraso(stats), n, rng)


def bilhetes_aleatorios(passado, janela, n, rng):
    return [sorted(rng.sample(engine.DEZENAS, 15)) for _ in range(n)]


ESTRATEGIAS: Dict[str, Callable] = {
    "freq": bilhetes_frequencia,
    "fa": bilhetes_freq_atraso,
    "aleatorio": bilhetes_aleatorios,
}


# ----------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------
def rodar(sorteios, alvos, n_bilhetes, janela, rng) -> Dict[str, Dict[int, dict]]:
    resultados = {k: {} for k in ESTRATEGIAS}
    inicio = time.time()
    for k, idx in enumerate(alvos, 1):
        passado = sorteios[:idx]  # nunca inclui o alvo
        real = set(sorteios[idx])
        for nome, gerar in ESTRATEGIAS.items():
            # o baseline usa mais bilhetes por rodada para ficar pouco ruidoso
            qtd = backtest.BILHETES_BASELINE if nome == "aleatorio" else n_bilhetes
            resultados[nome][idx] = backtest.metricas_bilhetes(gerar(passado, janela, qtd, rng), real)
        if k % 50 == 0:
            print(f"   {k}/{len(alvos)} rodadas ({time.time() - inicio:.0f}s)")
    return resultados


def _taxa_global(res: Dict[int, dict]) -> float:
    todos = [a for r in res.values() for a in r["acertos"]]
    return sum(1 for a in todos if a >= backtest.LIMITE_PREMIO) / len(todos)


def _media_global(res: Dict[int, dict]) -> float:
    return statistics.mean(a for r in res.values() for a in r["acertos"])


def imprimir(res: Dict[str, Dict[int, dict]], n_bilhetes: int) -> None:
    n_rodadas = len(res["freq"])
    print("\n" + "=" * 72)
    print(f"RESULTADO — {n_rodadas} rodadas | {n_bilhetes} bilhetes/rodada por estratégia")
    print("=" * 72)
    print(f"{'':26s}{'Frequência':>13s}{'Freq+Atraso':>13s}{'Aleatório':>11s}{'Teórico':>9s}")
    print(f"{'Média de acertos':26s}"
          f"{_media_global(res['freq']):13.3f}{_media_global(res['fa']):13.3f}"
          f"{_media_global(res['aleatorio']):11.3f}{backtest.media_teorica():9.3f}")
    print(f"{'Bilhetes com 11+':26s}"
          f"{_taxa_global(res['freq']) * 100:12.2f}%{_taxa_global(res['fa']) * 100:12.2f}%"
          f"{_taxa_global(res['aleatorio']) * 100:10.2f}%{backtest.taxa_premio_teorica() * 100:8.2f}%")

    pares = [("freq", "aleatorio"), ("fa", "aleatorio"), ("fa", "freq")]
    print("\nDiferenças pareadas por rodada (IC 95%, t de Student):")
    for a, b in pares:
        titulo = f"{NOMES[a]} - {NOMES[b]}"
        m, lo, hi = backtest.ic95(backtest.diferencas_pareadas(res[a], res[b], "media"))
        mt, lot, hit = backtest.ic95(backtest.diferencas_pareadas(res[a], res[b], "taxa"))
        print(f"\n  {titulo}")
        print(f"    Média de acertos: {m:+.3f}  [{lo:+.3f} ; {hi:+.3f}]  => {backtest.veredito(lo, hi)}")
        print(f"    Taxa de 11+     : {mt * 100:+.2f} p.p. [{lot * 100:+.2f} ; {hit * 100:+.2f}]  => {backtest.veredito(lot, hit)}")

    print("\nLeitura: se todos os intervalos incluem zero, nenhuma estratégia se distingue do acaso,")
    print("e acrescentar 'atraso' não melhora a frequência. São 6 testes: um único 'ACIMA do acaso'")
    print("isolado ainda pode ser coincidência (~26% de chance de ao menos um por acaso).")


def main() -> None:
    p = argparse.ArgumentParser(description="Frequência x Freq+Atraso x Aleatório (walk-forward, IC 95%)")
    p.add_argument("planilha", help="Caminho para Lotofacil.xlsx ou .csv")
    p.add_argument("--inicio", type=int, default=100, help="Primeiro concurso (índice) a testar")
    p.add_argument("--passo", type=int, default=10, help="De quantos em quantos concursos testar")
    p.add_argument("--bilhetes", type=int, default=10, help="Bilhetes por rodada em cada estratégia (1 a 100)")
    p.add_argument("--janela", type=int, default=100, help="Concursos passados usados (0 = todos)")
    p.add_argument("--semente", type=int, default=None, help="Semente para resultado reproduzível")
    a = p.parse_args()

    if not (1 <= a.bilhetes <= engine.QUANTIDADE_MAXIMA):
        sys.exit(f"--bilhetes precisa estar entre 1 e {engine.QUANTIDADE_MAXIMA}.")
    if a.passo < 1 or a.janela < 0:
        sys.exit("--passo deve ser >= 1 e --janela >= 0.")

    sorteios = carregar_sorteios(a.planilha)
    if a.inicio >= len(sorteios):
        sys.exit(f"A base tem só {len(sorteios)} concursos válidos; --inicio ({a.inicio}) é maior.")

    rng = random.Random(a.semente)
    alvos = list(range(a.inicio, len(sorteios), a.passo))
    print(f"Base: {len(sorteios)} concursos | {len(alvos)} rodadas | janela {a.janela or 'toda a base'}")
    if a.passo < (a.janela or len(sorteios)):
        print("Aviso: passo menor que a janela -> rodadas correlacionadas, IC otimista.")

    imprimir(rodar(sorteios, alvos, a.bilhetes, a.janela, rng), a.bilhetes)


if __name__ == "__main__":
    main()