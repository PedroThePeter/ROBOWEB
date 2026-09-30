"""
Análise de "memória" do histórico da Lotofácil.

PERGUNTA QUE RESPONDE
Os sorteios passados carregam alguma informação sobre os próximos? Se carregam,
o robô tem o que aprender. Se não carregam, ajustar pesos depois de cada erro
seria perseguir ruído.

COMO FUNCIONA
Se os sorteios fossem totalmente aleatórios e sem memória, cada dezena teria 60%
de chance (15 em 25) em qualquer sorteio, e duas dezenas específicas teriam 35% de
chance de saírem juntas. Cada teste abaixo compara o que ocorreu na sua planilha
com esses valores, medindo o desvio em "z" (quantos desvios-padrão de distância).

CUIDADO COM MUITOS TESTES
Testar 300 pares de dezenas significa que ~15 deles parecem "especiais" só por
acaso. Por isso cada teste mostra também o limite de Bonferroni: um z só conta como
achado real se passar dele.

USO
    python analise_memoria.py Lotofacil.xlsx
    python analise_memoria.py Lotofacil.xlsx --dezena 5     # autópsia da dezena 5
"""

import argparse
import math
from collections import Counter, defaultdict
from itertools import combinations
from typing import Dict, List, Optional, Tuple

import pandas as pd

from engine import LotofacilGeneticEngine

P_DEZENA = 15 / 25                                   # 60%
P_PAR = (15 * 14) / (25 * 24)                        # 35%
MEDIA_REPETIDAS = 15 * 15 / 25                       # 9,0
DESVIO_REPETIDAS = math.sqrt(15 * 0.6 * 0.4 * (10 / 24))
ATRASO_MAX = 6                                       # agrupa atrasos >= 6


# ----------------------------------------------------------------------
# Estatística básica (sem depender de scipy)
# ----------------------------------------------------------------------
def p_bilateral(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


def z_bonferroni(n_testes: int, alfa: float = 0.05) -> float:
    """z mínimo para um achado valer depois de corrigir por n_testes comparações."""
    alvo = alfa / n_testes
    baixo, alto = 0.0, 10.0
    for _ in range(60):
        meio = (baixo + alto) / 2
        if math.erfc(meio / math.sqrt(2)) > alvo:
            baixo = meio
        else:
            alto = meio
    return (baixo + alto) / 2


def qui2_pvalor(x: float, graus: int) -> float:
    """p-valor do qui-quadrado (aproximação de Wilson-Hilferty; boa para graus >= 3)."""
    if x <= 0:
        return 1.0
    z = ((x / graus) ** (1 / 3) - (1 - 2 / (9 * graus))) / math.sqrt(2 / (9 * graus))
    return 0.5 * math.erfc(z / math.sqrt(2))


# ----------------------------------------------------------------------
# Testes
# ----------------------------------------------------------------------
def teste_frequencia(sorteios: List[List[int]]) -> Dict[int, Tuple[int, float]]:
    """Alguma dezena sai mais ou menos que os 60% esperados? -> {dezena: (vezes, z)}"""
    n = len(sorteios)
    cont = Counter(d for s in sorteios for d in s)
    desvio = math.sqrt(n * P_DEZENA * (1 - P_DEZENA))
    return {d: (cont[d], (cont[d] - n * P_DEZENA) / desvio) for d in range(1, 26)}


def teste_repeticao(sorteios: List[List[int]]) -> Dict:
    """Quantas dezenas do sorteio anterior se repetem? Esperado: média 9,0."""
    reps = [len(set(a) & set(b)) for a, b in zip(sorteios, sorteios[1:])]
    m = len(reps)
    media = sum(reps) / m
    z = (media - MEDIA_REPETIDAS) / (DESVIO_REPETIDAS / math.sqrt(m))

    total = math.comb(25, 15)
    prob = {k: math.comb(15, k) * math.comb(10, 15 - k) / total for k in range(5, 16)}
    faixas = [
        ("<=6", range(0, 7)), ("7", [7]), ("8", [8]), ("9", [9]),
        ("10", [10]), ("11", [11]), (">=12", range(12, 16)),
    ]
    linhas = []
    qui2 = 0.0
    for nome, ks in faixas:
        obs = sum(1 for r in reps if r in ks)
        esp = m * sum(prob.get(k, 0.0) for k in ks)
        linhas.append((nome, obs, esp))
        qui2 += (obs - esp) ** 2 / esp
    return {
        "media": media, "z": z, "linhas": linhas,
        "qui2": qui2, "p_qui2": qui2_pvalor(qui2, len(faixas) - 1),
    }


def teste_atraso(sorteios: List[List[int]], dezena: Optional[int] = None) -> List[Tuple[str, int, float, float]]:
    """
    Depois de K sorteios seguidos SEM sair, qual a chance de a dezena sair?
    Se houvesse "dívida" (atraso que se corrige), a taxa subiria com K.
    Sem memória, deveria ficar em ~60% para qualquer K.
    Retorna [(rotulo_K, amostra, taxa_observada, z)].
    """
    sequencia = {d: 0 for d in range(1, 26)}
    est: Dict[int, List[int]] = defaultdict(lambda: [0, 0])  # K -> [amostra, saidas]
    alvo = range(1, 26) if dezena is None else [dezena]

    for s in sorteios:
        conjunto = set(s)
        for d in alvo:
            k = min(sequencia[d], ATRASO_MAX)
            est[k][0] += 1
            if d in conjunto:
                est[k][1] += 1
        for d in range(1, 26):
            sequencia[d] = 0 if d in conjunto else sequencia[d] + 1

    linhas = []
    for k in range(0, ATRASO_MAX + 1):
        n, saidas = est[k]
        if n == 0:
            continue
        taxa = saidas / n
        z = (taxa - P_DEZENA) / math.sqrt(P_DEZENA * (1 - P_DEZENA) / n)
        rotulo = f">={k}" if k == ATRASO_MAX else str(k)
        linhas.append((rotulo, n, taxa, z))
    return linhas


def teste_pares(sorteios: List[List[int]]) -> List[Tuple[Tuple[int, int], int, float]]:
    """Algum par sai junto mais do que os 35% esperados? Ordenado por |z|."""
    n = len(sorteios)
    cont: Counter = Counter()
    for s in sorteios:
        for par in combinations(s, 2):
            cont[par] += 1
    desvio = math.sqrt(n * P_PAR * (1 - P_PAR))
    lista = [
        (par, cont.get(par, 0), (cont.get(par, 0) - n * P_PAR) / desvio)
        for par in combinations(range(1, 26), 2)
    ]
    lista.sort(key=lambda x: abs(x[2]), reverse=True)
    return lista


# ----------------------------------------------------------------------
# Relatórios
# ----------------------------------------------------------------------
def relatorio_geral(sorteios: List[List[int]]) -> None:
    n = len(sorteios)
    achados = 0
    print("=" * 70)
    print(f"ANÁLISE DE MEMÓRIA — {n} concursos")
    print("=" * 70)
    print("Se os sorteios não têm memória: cada dezena sai em 60% dos concursos, e a")
    print("média de repetidas do concurso anterior é 9,0.\n")

    # 1) Frequência
    freq = teste_frequencia(sorteios)
    limite = z_bonferroni(25)
    maior = max(freq.items(), key=lambda x: abs(x[1][1]))
    print("[1] FREQUÊNCIA DAS DEZENAS")
    print(f"    Maior desvio: dezena {maior[0]:02d} saiu {maior[1][0]}x ({maior[1][0] / n:.1%}), z = {maior[1][1]:+.2f}")
    print(f"    Limite de Bonferroni (25 dezenas): |z| > {limite:.2f}")
    if abs(maior[1][1]) > limite:
        achados += 1
        print("    => ATENÇÃO: há dezena com frequência fora do esperado.")
    else:
        print("    => Nenhuma dezena foge do esperado.")

    # 2) Repetição
    rep = teste_repeticao(sorteios)
    print("\n[2] REPETIÇÃO DO CONCURSO ANTERIOR")
    print(f"    Média observada: {rep['media']:.3f} (esperado {MEDIA_REPETIDAS:.1f}), z = {rep['z']:+.2f}")
    print(f"    Distribuição: {'faixa':>6s} {'obs':>6s} {'esperado':>9s}")
    for nome, obs, esp in rep["linhas"]:
        print(f"                  {nome:>6s} {obs:6d} {esp:9.1f}")
    print(f"    Qui-quadrado = {rep['qui2']:.1f}, p ≈ {rep['p_qui2']:.3f}")
    if abs(rep["z"]) > 1.96 or rep["p_qui2"] < 0.05:
        achados += 1
        print("    => ATENÇÃO: a repetição difere do acaso puro.")
    else:
        print("    => Compatível com acaso puro. A faixa 8-10 usada no robô é só a mais comum,")
        print("       não uma condição que aumenta a chance de acerto.")

    # 3) Atraso
    atraso = teste_atraso(sorteios)
    limite_a = z_bonferroni(len(atraso))
    print("\n[3] ATRASO: chance de sair depois de K sorteios seguidos fora")
    print(f"    {'K':>4s} {'amostra':>9s} {'taxa':>8s} {'z':>7s}   (esperado 60,0%)")
    sinal_atraso = False
    for rotulo, amostra, taxa, z in atraso:
        marca = "  <== fora do esperado" if abs(z) > limite_a else ""
        sinal_atraso = sinal_atraso or bool(marca)
        print(f"    {rotulo:>4s} {amostra:9d} {taxa:8.1%} {z:+7.2f}{marca}")
    if sinal_atraso:
        achados += 1
        print("    => ATENÇÃO: a chance de sair muda conforme o atraso.")
    else:
        print("    => A taxa fica em ~60% qualquer que seja o atraso: nenhuma evidência de")
        print("       'dívida' que o sorteio precise pagar. O critério de dezenas críticas não")
        print("       encontra apoio nestes dados.")

    # 4) Pares
    pares = teste_pares(sorteios)
    limite_p = z_bonferroni(len(pares))
    acima_196 = sum(1 for _, _, z in pares if abs(z) > 1.96)
    acima_bonf = sum(1 for _, _, z in pares if abs(z) > limite_p)
    print("\n[4] PARES DE DEZENAS (esperado: saírem juntas em 35% dos concursos)")
    for (a, b), cont, z in pares[:5]:
        print(f"    {a:02d}&{b:02d}: {cont}x ({cont / n:.1%}), z = {z:+.2f}")
    print(f"    Pares com |z| > 1,96: {acima_196} de {len(pares)}  (por puro acaso, esperados ~{len(pares) * 0.05:.0f})")
    print(f"    Pares acima do limite de Bonferroni (|z| > {limite_p:.2f}): {acima_bonf}")
    if acima_bonf > 0:
        achados += 1
        print("    => ATENÇÃO: há pares que saem juntos além do acaso.")
    else:
        print("    => Os pares 'campeões' são o que o acaso produz entre 300 possibilidades.")

    # Conclusão
    print("\n" + "=" * 70)
    if achados == 0:
        print("CONCLUSÃO: nenhum dos 4 testes encontrou padrão além do acaso.")
        print("Nada indica que haja o que 'aprender' do histórico: ajustar o robô após cada erro seria")
        print("perseguir ruído. O que vale é usar o robô para organizar aposta (portfólio")
        print("e desdobramento) e medir o desempenho real com o diário de palpites.")
    else:
        print(f"CONCLUSÃO: {achados} teste(s) apontaram desvio do acaso puro.")
        print("Isso merece investigação, mas NÃO prova que dá para prever. Próximo passo:")
        print("validar fora da amostra (backtest walk-forward) usando exatamente esse padrão.")


def autopsia(sorteios: List[List[int]], dezena: int) -> None:
    n = len(sorteios)
    presencas = [dezena in s for s in sorteios]
    saiu = sum(presencas)
    fora = n - saiu

    print("=" * 70)
    print(f"AUTÓPSIA DA DEZENA {dezena:02d}")
    print("=" * 70)
    print(f"Em {n} concursos, a dezena {dezena:02d} saiu {saiu}x ({saiu / n:.1%}). Esperado: 60,0%.")
    print(f"Ficou de fora {fora}x ({fora / n:.1%}). Ou seja, quatro em cada dez concursos ela")
    print("não sai: quem apostou nela e viu ela faltar passou por uma situação comum.\n")

    recentes = presencas[-30:]
    print("Últimos 30 concursos (■ saiu, □ não saiu; o mais recente é o da direita):")
    print("   " + "".join("■" if p else "□" for p in recentes))

    atual = 0
    for p in reversed(presencas):
        if p == presencas[-1]:
            atual += 1
        else:
            break
    print(f"\nSituação atual: {'SAIU' if presencas[-1] else 'FICOU FORA'} nos últimos {atual} concurso(s) seguidos.")

    print(f"\nDepois de K concursos seguidos fora, com que frequência a {dezena:02d} saiu?")
    print(f"    {'K':>4s} {'amostra':>9s} {'taxa':>8s}   (K=0 significa: tinha saído no concurso anterior)")
    for rotulo, amostra, taxa, z in teste_atraso(sorteios, dezena):
        print(f"    {rotulo:>4s} {amostra:9d} {taxa:8.1%}")
    print("    Se as taxas ficam perto de 60% para todo K, o passado recente não ajuda a")
    print("    prever essa dezena. (Amostras pequenas oscilam bastante.)")

    companheiras = []
    com = [s for s in sorteios if dezena in s]
    if com:
        esperado = 14 / 24
        desvio = math.sqrt(esperado * (1 - esperado) / len(com))
        for outra in range(1, 26):
            if outra == dezena:
                continue
            taxa = sum(1 for s in com if outra in s) / len(com)
            companheiras.append((outra, taxa, (taxa - esperado) / desvio))
        companheiras.sort(key=lambda x: abs(x[2]), reverse=True)
        print(f"\nDezenas que mais se afastam do esperado quando a {dezena:02d} sai (esperado 58,3%):")
        for outra, taxa, z in companheiras[:3]:
            print(f"    {outra:02d}: {taxa:.1%} (z = {z:+.2f})")
        print(f"    Limite de Bonferroni (24 comparações): |z| > {z_bonferroni(24):.2f}")


def carregar_sorteios(caminho: str) -> List[List[int]]:
    df = pd.read_excel(caminho)
    return LotofacilGeneticEngine(df)._sorteios


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Testa se o histórico da Lotofácil tem padrões além do acaso")
    parser.add_argument("planilha", help="Caminho para Lotofacil.xlsx")
    parser.add_argument("--dezena", type=int, default=None, help="Faz a autópsia de uma dezena (1 a 25)")
    args = parser.parse_args()

    sorteios = carregar_sorteios(args.planilha)
    if len(sorteios) < 100:
        print(f"Base com só {len(sorteios)} concursos válidos: pequena demais para testes confiáveis.")

    if args.dezena is not None:
        if not 1 <= args.dezena <= 25:
            raise SystemExit("A dezena deve estar entre 1 e 25.")
        autopsia(sorteios, args.dezena)
    else:
        relatorio_geral(sorteios)
import math
from scipy.stats import norm

def calcular_z_bonferroni(num_testes=1, alpha=0.05):
    """Calcula o limiar z ajustado pela correção de Bonferroni."""
    alpha_ajustado = alpha / num_testes
    return abs(norm.ppf(alpha_ajustado / 2))

def validar_frequencia_repetidas_esperada():
    """Retorna a média teórica de dezenas repetidas do concurso anterior."""
    return 9.0