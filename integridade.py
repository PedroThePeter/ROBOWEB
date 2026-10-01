import csv
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

# Constantes de arquivos de auditoria e trava do sistema
ARQUIVO_TRAVA = "trava.json"
ARQUIVO_COMPROVANTES = "comprovantes.csv"
CAMPOS_COMPROVANTE = ["concurso", "hash", "registrado_em"]

# Pesos padrão do sistema (todos iguais = sorteio uniforme)
PESOS_PADRAO = {str(i): 1.0 for i in range(1, 26)}


def _gravar_atomico(caminho: str, texto: str) -> None:
    """Escreve num arquivo temporário e troca, para nunca deixar arquivo pela metade."""
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(texto)
    os.replace(tmp, caminho)


def _hash_bilhete(bilhete) -> str:
    """SHA-256 completo (64 caracteres) do bilhete, independente da ordem das dezenas."""
    texto = json.dumps(sorted(int(d) for d in bilhete)).encode("utf-8")
    return hashlib.sha256(texto).hexdigest()


def _hash_pesos(pesos) -> str:
    """SHA-256 do dicionário de pesos."""
    texto = json.dumps(pesos, sort_keys=True).encode("utf-8")
    return hashlib.sha256(texto).hexdigest()


# ----------------------------------------------------------------------
# Trava de pesos
# ----------------------------------------------------------------------
def carregar_pesos_para_engine(caminho_arquivo=None) -> Tuple[Dict, bool]:
    """
    Retorna (pesos, valido).
    valido=True só se existir um arquivo de trava com 'pesos' e um hash que confira.
    Qualquer outra situação (sem arquivo, JSON quebrado, sem 'pesos', hash errado)
    cai nos pesos padrão com valido=False.
    """
    alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_TRAVA
    if not os.path.exists(alvo):
        return PESOS_PADRAO.copy(), False

    try:
        with open(alvo, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return PESOS_PADRAO.copy(), False

    # Antes, um JSON sem a chave "pesos" era aceito como válido (furava a trava).
    if not isinstance(dados, dict) or not isinstance(dados.get("pesos"), dict):
        return PESOS_PADRAO.copy(), False

    pesos = dados["pesos"]
    hash_salvo = dados.get("hash_pesos") or dados.get("hash") or ""
    if hash_salvo and hash_salvo == _hash_pesos(pesos):
        return dict(pesos), True
    return PESOS_PADRAO.copy(), False


def gravar_trava(pesos: Dict, caminho_arquivo=None) -> str:
    """Grava a trava (pesos + hash + data). Retorna o hash gravado."""
    alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_TRAVA
    h = _hash_pesos(pesos)
    conteudo = {
        "pesos": pesos,
        "hash_pesos": h,
        "data_trava": datetime.now().isoformat(timespec="seconds"),
    }
    _gravar_atomico(alvo, json.dumps(conteudo, ensure_ascii=False, indent=2))
    return h


# ----------------------------------------------------------------------
# Comprovantes (hash dos bilhetes registrado ANTES do sorteio)
# ----------------------------------------------------------------------
def _ler_comprovantes(caminho_arquivo=None) -> List[Dict[str, str]]:
    alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_COMPROVANTES
    if not os.path.exists(alvo):
        return []
    with open(alvo, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _gravar_comprovantes(linhas: List[Dict[str, str]], caminho_arquivo=None) -> None:
    alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_COMPROVANTES
    tmp = alvo + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_COMPROVANTE, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)
    os.replace(tmp, alvo)


def registrar_comprovantes(concurso, bilhetes, caminho_arquivo=None) -> Tuple[int, int]:
    """Grava um comprovante por bilhete. Retorna (novos, ja_existiam)."""
    linhas = _ler_comprovantes(caminho_arquivo)
    existentes = {(l["concurso"], l["hash"]) for l in linhas}
    novos = repetidos = 0
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for b in bilhetes:
        h = _hash_bilhete(b)
        if (str(concurso), h) in existentes:
            repetidos += 1
            continue
        linhas.append({"concurso": str(concurso), "hash": h, "registrado_em": agora})
        existentes.add((str(concurso), h))
        novos += 1
    if novos:
        _gravar_comprovantes(linhas, caminho_arquivo)
    return novos, repetidos