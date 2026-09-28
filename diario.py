"""
Diário de palpites: registra o que o robô sugeriu, confere com o resultado real
e mede se o desempenho está acima do acaso.

FLUXO
  1) Antes do sorteio, registre os bilhetes que você vai jogar:
       python diario.py registrar --concurso 3789 --bilhete 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
       python diario.py registrar --concurso 3789 --arquivo meus_bilhetes.txt
  2) Depois do sorteio, atualize a planilha Lotofacil.xlsx e rode:
       python diario.py conferir Lotofacil.xlsx
  3) Quando quiser ver o balanço acumulado:
       python diario.py relatorio

Os dados ficam no arquivo palpites.csv, na mesma pasta. Guarde esse arquivo (ou
versione no git): se o servidor do Render reiniciar, o disco dele é apagado, por isso
o diário é uma ferramenta local.

POR QUE COMPARAR COM 9,0
Um bilhete qualquer de 15 dezenas acerta em média 9,0 (15 x 15 / 25) e 10,59% dos
bilhetes chegam a 11+. Só faz sentido dizer que o robô "acerta mais" se ele ficar
consistentemente acima disso, com margem maior que o ruído.
"""

import argparse
import csv
import math
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set

import pandas as pd

from engine import LotofacilGeneticEngine
from backtest import ic95, media_teorica, taxa_premio_teorica, LIMITE_PREMIO

ARQUIVO = "palpites.csv"
CAMPOS = ["concurso", "bilhete", "origem", "registrado_em", "acertos", "sorteadas"]


# ----------------------------------------------------------------------
# Armazenamento
# ----------------------------------------------------------------------
def _ler() -> List[Dict[str, str]]:
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _gravar(linhas: List[Dict[str, str]]) -> None:
    with open(ARQUIVO, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(linhas)


def _parse_bilhete(texto: str) -> List[int]:
    partes = [p for p in re.split(r"[,\s;-]+", texto.strip()) if p]
    dezenas = sorted(int(p) for p in partes)
    if len(dezenas) != 15 or len(set(dezenas)) != 15:
        raise ValueError(f"Bilhete inválido (precisa de 15 dezenas diferentes): {texto!r}")
    if dezenas[0] < 1 or dezenas[-1] > 25:
        raise ValueError(f"Dezenas devem estar entre 1 e 25: {texto!r}")
    return dezenas


def _fmt(dezenas) -> str:
    return "-".join(f"{d:02d}" for d in sorted(dezenas))


def _dezenas_da_linha(texto: str) -> List[int]:
    return [int(x) for x in texto.split("-")] if texto else []


# ----------------------------------------------------------------------
# Comandos
# ----------------------------------------------------------------------
def registrar(concurso: int, bilhetes_txt: List[str], origem: str) -> None:
    linhas = _ler()
    existentes = {(int(l["concurso"]), l["bilhete"]) for l in linhas}
    novos = 0
    for txt in bilhetes_txt:
        bilhete = _fmt(_parse_bilhete(txt))
        if (concurso, bilhete) in existentes:
            print(f"  (já registrado) {bilhete}")
            continue
        linhas.append({
            "concurso": str(concurso), "bilhete": bilhete, "origem": origem,
            "registrado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "acertos": "", "sorteadas": "",
        })
        novos += 1
    _gravar(linhas)
    print(f"{novos} bilhete(s) registrado(s) para o concurso {concurso}. Total no diário: {len(linhas)}.")


def _carregar_resultados(planilha: str) -> Dict[int, Set[int]]:
    df = pd.read_excel(planilha)
    engine = LotofacilGeneticEngine(df)
    col_concurso = next((c for c in df.columns if "concurso" in str(c).lower()), df.columns[0])
    resultados: Dict[int, Set[int]] = {}
    for _, row in df.iterrows():
        dezenas = engine._extrair_dezenas_linha(row)
        if len(dezenas) != 15:
            continue
        try:
            resultados[int(row[col_concurso])] = set(dezenas)
        except (ValueError, TypeError):
            continue
    return resultados


def conferir(planilha: str) -> None:
    linhas = _ler()
    if not linhas:
        print("O diário está vazio. Registre bilhetes primeiro (python diario.py registrar ...).")
        return

    resultados = _carregar_resultados(planilha)
    por_concurso: Dict[int, List[Dict[str, str]]] = defaultdict(list)
    conferidos_agora = 0

    for linha in linhas:
        if linha["acertos"] != "":
            continue
        concurso = int(linha["concurso"])
        if concurso not in resultados:
            continue
        sorteadas = resultados[concurso]
        bilhete = set(_dezenas_da_linha(linha["bilhete"]))
        linha["acertos"] = str(len(bilhete & sorteadas))
        linha["sorteadas"] = _fmt(sorteadas)
        por_concurso[concurso].append(linha)
        conferidos_agora += 1

    _gravar(linhas)

    if conferidos_agora == 0:
        pendentes = sorted({int(l["concurso"]) for l in linhas if l["acertos"] == ""})
        print("Nenhum bilhete novo para conferir.")
        if pendentes:
            print(f"Concursos aguardando resultado na planilha: {pendentes}")
        return

    for concurso in sorted(por_concurso):
        sorteadas = resultados[concurso]
        print("=" * 70)
        print(f"CONCURSO {concurso} — sorteadas: {_fmt(sorteadas)}")
        print("=" * 70)
        uso: Dict[int, int] = defaultdict(int)
        for linha in por_concurso[concurso]:
            bilhete = _dezenas_da_linha(linha["bilhete"])
            faltaram = [d for d in bilhete if d not in sorteadas]
            for d in bilhete:
                uso[d] += 1
            premio = "  <-- PREMIADO" if int(linha["acertos"]) >= LIMITE_PREMIO else ""
            print(f"  {linha['bilhete']}  => {linha['acertos']:>2s} acertos{premio}")
            print(f"      apostadas que não saíram: {_fmt(faltaram)}")
        media = statistics.mean(int(l["acertos"]) for l in por_concurso[concurso])
        print(f"\n  Média do concurso: {media:.2f} acertos (esperado de um bilhete qualquer: {media_teorica():.1f})")
        falhas = sorted(((d, q) for d, q in uso.items() if d not in sorteadas), key=lambda x: -x[1])[:5]
        if falhas:
            print("  Dezenas mais apostadas que não saíram: " +
                  ", ".join(f"{d:02d} (em {q} bilhete{'s' if q > 1 else ''})" for d, q in falhas))
        print("  Lembrete: cada dezena tem 60% de chance de sair; faltar é normal (40%).\n")


def relatorio() -> None:
    linhas = [l for l in _ler() if l["acertos"] != ""]
    if not linhas:
        print("Ainda não há bilhetes conferidos. Use 'registrar' e depois 'conferir'.")
        return

    por_concurso: Dict[int, List[int]] = defaultdict(list)
    for l in linhas:
        por_concurso[int(l["concurso"])].append(int(l["acertos"]))

    todos = [a for lista in por_concurso.values() for a in lista]
    medias = [statistics.mean(lista) for lista in por_concurso.values()]
    n_conc = len(medias)
    premiados = sum(1 for a in todos if a >= LIMITE_PREMIO) / len(todos)

    print("=" * 70)
    print(f"BALANÇO — {n_conc} concurso(s), {len(todos)} bilhete(s) conferido(s)")
    print("=" * 70)
    print(f"Média de acertos por bilhete : {statistics.mean(todos):.3f}   (acaso: {media_teorica():.3f})")
    print(f"Bilhetes com 11+ (premiados) : {premiados:.2%}   (acaso: {taxa_premio_teorica():.2%})")
    print(f"Melhor bilhete: {max(todos)} acertos | pior: {min(todos)}")

    dist = defaultdict(int)
    for a in todos:
        dist[a] += 1
    print("Distribuição: " + " | ".join(f"{k}: {dist[k]}x" for k in sorted(dist)))

    if n_conc >= 3:
        diffs = [m - media_teorica() for m in medias]
        media_d, lo, hi = ic95(diffs)
        erro = statistics.stdev(diffs) / math.sqrt(n_conc)
        print(f"\nDiferença para o acaso (por concurso): {media_d:+.3f}  IC 95% [{lo:+.3f} ; {hi:+.3f}]")
        if lo > 0:
            print("=> Acima do acaso com esse volume de dados (confirme com mais concursos).")
        elif hi < 0:
            print("=> Abaixo do acaso.")
        else:
            print("=> Indistinguível do acaso.")
        print(f"Com {n_conc} concursos, só dá para detectar uma vantagem de pelo menos ~{2.8 * erro:.2f} acertos por bilhete.")
        print("Vantagens menores que isso ficam invisíveis; é preciso acumular mais concursos.")
    else:
        print("\nPoucos concursos (menos de 3) para calcular margem de confiança. Continue registrando.")

    # Calibração por dezena
    usado: Dict[int, int] = defaultdict(int)
    saiu: Dict[int, int] = defaultdict(int)
    for l in linhas:
        sorteadas = set(_dezenas_da_linha(l["sorteadas"]))
        for d in _dezenas_da_linha(l["bilhete"]):
            usado[d] += 1
            if d in sorteadas:
                saiu[d] += 1
    print("\nDezenas mais usadas nos seus bilhetes e quanto saíram (esperado 60%):")
    for d, q in sorted(usado.items(), key=lambda x: -x[1])[:8]:
        print(f"   {d:02d}: usada em {q} bilhete{'s' if q > 1 else ''}, saiu em {saiu[d] / q:.0%}")
    print("(Bilhetes do mesmo concurso compartilham o mesmo sorteio; a amostra efetiva é menor que a contagem.)")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diário de palpites da Lotofácil")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_reg = sub.add_parser("registrar", help="Registra bilhetes para um concurso futuro")
    p_reg.add_argument("--concurso", type=int, required=True, help="Número do concurso alvo")
    p_reg.add_argument("--bilhete", action="append", default=[], help="15 dezenas separadas por vírgula (repita a opção para vários)")
    p_reg.add_argument("--arquivo", help="Arquivo de texto com um bilhete por linha")
    p_reg.add_argument("--origem", default="robo", help="Rótulo de origem (ex: robo, manual)")

    p_conf = sub.add_parser("conferir", help="Confere os bilhetes pendentes com a planilha")
    p_conf.add_argument("planilha", help="Caminho para Lotofacil.xlsx atualizada")

    sub.add_parser("relatorio", help="Balanço acumulado contra o acaso")

    args = parser.parse_args()

    try:
        if args.comando == "registrar":
            bilhetes = list(args.bilhete)
            if args.arquivo:
                with open(args.arquivo, encoding="utf-8") as f:
                    bilhetes += [ln for ln in f.read().splitlines() if ln.strip()]
            if not bilhetes:
                raise SystemExit("Informe --bilhete ou --arquivo.")
            registrar(args.concurso, bilhetes, args.origem)
        elif args.comando == "conferir":
            conferir(args.planilha)
        else:
            relatorio()
    except ValueError as erro:
        raise SystemExit(f"Erro: {erro}")