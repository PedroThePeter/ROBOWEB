"""
Leitura da planilha de resultados da Lotofácil (formato da Caixa).

Antes, backtest.py e analise_memoria.py faziam `LotofacilGeneticEngine(df)._sorteios`
para ler a planilha, o que dependia de um motor que não existe mais. Agora a
leitura mora aqui, num lugar só.

A planilha precisa ter 15 colunas de dezenas chamadas "Bola1".."Bola15"
(ou "D1".."D15" / "Dezena1".."Dezena15"). Se houver uma coluna "Concurso",
ela é usada como número do concurso; senão vale a posição da linha (1, 2, 3...).
"""

import re
from typing import Dict, List

import pandas as pd


def _linha_valida(dezenas: List[int]) -> bool:
    return len(dezenas) == 15 and len(set(dezenas)) == 15 and all(1 <= d <= 25 for d in dezenas)


def _numero_no_nome(coluna) -> int:
    return int(re.search(r"\d+", str(coluna)).group())


def carregar_resultados(caminho: str) -> Dict[int, List[int]]:
    """Retorna {numero_do_concurso: dezenas_ordenadas}, na ordem cronológica."""
    if str(caminho).lower().endswith(".csv"):
        df = pd.read_csv(caminho, sep=None, engine="python")
    else:
        df = pd.read_excel(caminho)

    colunas = [c for c in df.columns if re.fullmatch(r"\s*bola\s*\d+\s*", str(c), re.I)]
    if len(colunas) != 15:
        colunas = [c for c in df.columns if re.fullmatch(r"\s*d(ezena)?\s*\d+\s*", str(c), re.I)]
    if len(colunas) != 15:
        raise ValueError(
            "Não encontrei as 15 colunas de dezenas (Bola1..Bola15). "
            f"Colunas da planilha: {list(df.columns)}"
        )
    colunas.sort(key=_numero_no_nome)

    col_concurso = next(
        (c for c in df.columns if str(c).strip().lower().startswith("concurso")), None
    )

    resultados: Dict[int, List[int]] = {}
    for posicao, (_, linha) in enumerate(df.iterrows(), 1):
        try:
            dezenas = sorted(int(linha[c]) for c in colunas)
            numero = int(linha[col_concurso]) if col_concurso is not None else posicao
        except (TypeError, ValueError):
            continue  # linha vazia, rodapé, texto, NaN...
        if _linha_valida(dezenas):
            resultados[numero] = dezenas
    return dict(sorted(resultados.items()))


def carregar_sorteios(caminho: str) -> List[List[int]]:
    """Só as dezenas de cada concurso, em ordem cronológica."""
    return list(carregar_resultados(caminho).values())