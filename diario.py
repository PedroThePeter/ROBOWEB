import os
import json
from typing import Dict, Any
from dados import carregar_sorteios

ARQUIVO_DIARIO = "palpites.json"

def obter_dados_diario() -> Dict[str, Any]:
    if not os.path.exists(ARQUIVO_DIARIO):
        return {"historico": [], "ultimos_palpites": []}
    try:
        with open(ARQUIVO_DIARIO, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if isinstance(dados, dict):
                return {
                    "historico": dados.get("historico", []),
                    "ultimos_palpites": dados.get("ultimos_palpites", [])
                }
    except Exception:
        pass
    return {"historico": [], "ultimos_palpites": []}


def salvar_palpites(dados_palpite: dict, origem: str = "api") -> bool:
    diario = obter_dados_diario()
    historico = diario["historico"]
    
    registro = {
        "concurso": dados_palpite.get("concurso"),
        "quantidade": dados_palpite.get("quantidade", 1),
        "jogos": dados_palpite.get("jogos", []),
        "hashes": dados_palpite.get("hashes", []),
        "origem": origem,  
        "acertos": []
    }
    
    historico.append(registro)
    ultimos = historico[-20:]
    
    try:
        with open(ARQUIVO_DIARIO, "w", encoding="utf-8") as f:
            json.dump({"historico": historico, "ultimos_palpites": ultimos}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def conferir_resultados(caminho_planilha: str) -> bool:
    if not os.path.exists(caminho_planilha):
        return False
    
    try:
        sorteios = carregar_sorteios(caminho_planilha)
        mapa_concursos = {}
        for idx, s in enumerate(sorteios):
            if isinstance(s, (list, tuple)):
                mapa_concursos[idx + 1] = set(s)
            elif isinstance(s, dict):
                c = s.get("concurso", idx + 1)
                dez = s.get("dezenas", s.get("sorteio", []))
                mapa_concursos[int(c)] = set(dez)
    except Exception:
        return False

    diario = obter_dados_diario()
    historico = diario["historico"]
    alterado = False

    for reg in historico:
        c = reg.get("concurso")
        if c is not None and int(c) in mapa_concursos:
            sorteio_oficial = mapa_concursos[int(c)]
            jogos = reg.get("jogos", [])
            acertos_lista = []
            for jogo in jogos:
                acertos = len(set(jogo).intersection(sorteio_oficial))
                acertos_lista.append(acertos)
            if reg.get("acertos") != acertos_lista:
                reg["acertos"] = acertos_lista
                alterado = True

    if alterado:
        try:
            with open(ARQUIVO_DIARIO, "w", encoding="utf-8") as f:
                json.dump({"historico": historico, "ultimos_palpites": diario["ultimos_palpites"]}, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            pass
    return False