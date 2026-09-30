import json
import os
from datetime import datetime

# Constantes de arquivos do diário
ARQUIVO_PALPITES = "palpites.json"

def salvar_palpites(dados_jogos, caminho_arquivo=None):
    """Salva os palpites gerados no histórico do diário."""
    alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_PALPITES
    historico = carregar_palpites(alvo)
    
    registro = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "concurso": dados_jogos.get("concurso"),
        "quantidade": dados_jogos.get("quantidade"),
        "jogos": dados_jogos.get("jogos", []),
        "hashes": dados_jogos.get("hashes", []),
        "trava_valida": dados_jogos.get("trava_valida", True)
    }
    
    historico.append(registro)
    
    try:
        with open(alvo, "w", encoding="utf-8") as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def carregar_palpites(caminho_arquivo=None):
    """Carrega o histórico de palpites salvos."""
    alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_PALPITES
    if os.path.exists(alvo):
        try:
            with open(alvo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []