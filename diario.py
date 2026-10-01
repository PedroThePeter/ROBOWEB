"""
Diário de palpites: guarda cada geração de bilhetes em palpites.json e permite
conferir com o resultado oficial depois.

    python diario.py conferir Lotofacil.xlsx
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

ARQUIVO_PALPITES = "palpites.json"


def _alvo(caminho_arquivo) -> str:
    return caminho_arquivo if caminho_arquivo else ARQUIVO_PALPITES


def _gravar_atomico(caminho: str, historico: List[dict]) -> None:
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)


def carregar_palpites(caminho_arquivo=None) -> List[dict]:
    """
    Carrega o histórico (sempre uma lista de registros).
    Se o arquivo estiver corrompido, ele é preservado como '.corrompido' em vez de
    ser sobrescrito na próxima gravação (antes o histórico inteiro era perdido).
    """
    alvo = _alvo(caminho_arquivo)
    if not os.path.exists(alvo):
        return []
    try:
        with open(alvo, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        try:
            os.replace(alvo, alvo + ".corrompido")
        except OSError:
            pass
        return []
    except OSError:
        return []

    if isinstance(dados, dict):  # formato antigo
        dados = dados.get("historico", [])
    if not isinstance(dados, list):
        return []
    return [r for r in dados if isinstance(r, dict)]


def salvar_palpites(dados_jogos: dict, caminho_arquivo=None, origem: str = "api") -> bool:
    """Acrescenta os bilhetes gerados ao diário. Ignora repetição exata (mesmo concurso e mesmos bilhetes)."""
    alvo = _alvo(caminho_arquivo)
    historico = carregar_palpites(alvo)

    concurso = dados_jogos.get("concurso")
    hashes = list(dados_jogos.get("hashes", []))
    if concurso is not None and hashes and any(
        r.get("concurso") == concurso and r.get("hashes") == hashes for r in historico
    ):
        return True  # já registrado (ex.: rotina rodada duas vezes)

    jogos = dados_jogos.get("jogos") or dados_jogos.get("bilhetes") or []
    historico.append({
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "concurso": concurso,
        "quantidade": dados_jogos.get("quantidade", len(jogos)),
        "jogos": jogos,
        "hashes": hashes,
        "trava_valida": dados_jogos.get("trava_valida", True),
        "origem": origem,
    })

    try:
        _gravar_atomico(alvo, historico)
        return True
    except OSError:
        return False


def obter_dados_diario(caminho_arquivo=None) -> Dict[str, list]:
    """Dicionário padronizado com 'historico' e 'ultimos_palpites'."""
    historico = carregar_palpites(caminho_arquivo)
    ultimos = historico[-1].get("jogos", []) if historico else []
    return {"historico": historico, "ultimos_palpites": ultimos}


def conferir(planilha: Optional[str] = None, caminho_arquivo=None,
             resultados: Optional[Dict[int, List[int]]] = None) -> List[dict]:
    """
    Compara os palpites ainda não conferidos com o resultado oficial do mesmo concurso
    e grava 'acertos' no diário. `resultados` é {concurso: dezenas}; se omitido, lê a planilha.
    """
    if resultados is None:
        from dados import carregar_resultados
        resultados = carregar_resultados(planilha)

    alvo = _alvo(caminho_arquivo)
    historico = carregar_palpites(alvo)
    resumo = []
    mudou = False
    for r in historico:
        c = r.get("concurso")
        if c is None or "acertos" in r or c not in resultados:
            continue
        sorteio = set(resultados[c])
        r["acertos"] = [len(sorteio & set(j)) for j in r.get("jogos", [])]
        r["conferido_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resumo.append({"concurso": c, "acertos": r["acertos"]})
        mudou = True
    if mudou:
        _gravar_atomico(alvo, historico)
    return resumo


def _main() -> None:
    parser = argparse.ArgumentParser(description="Diário de palpites da Lotofácil")
    sub = parser.add_subparsers(dest="comando", required=True)
    p = sub.add_parser("conferir", help="Confere os palpites com a planilha de resultados")
    p.add_argument("planilha", help="Caminho para Lotofacil.xlsx")
    args = parser.parse_args()

    resumo = conferir(args.planilha)
    if not resumo:
        print("Nada novo para conferir (ou a planilha ainda não tem esses concursos).")
        return
    for item in resumo:
        a = item["acertos"]
        print(f"Concurso {item['concurso']}: acertos {a} | melhor {max(a) if a else '-'}")


if __name__ == "__main__":
    _main()