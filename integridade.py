import hashlib
import json
import os

# Constantes de arquivos de auditoria e trava do sistema
ARQUIVO_TRAVA = "trava.json"
ARQUIVO_COMPROVANTES = "comprovantes.csv"

# Pesos padrão do sistema
PESOS_PADRAO = {str(i): 1.0 for i in range(1, 26)}

def _hash_bilhete(bilhete):
    """Gera um hash SHA-256 completo (64 carateres) para o bilhete."""
    texto = str(sorted(bilhete)).encode("utf-8")
    return hashlib.sha256(texto).hexdigest()

def _hash_pesos(pesos):
    """Gera um hash SHA-256 para o dicionário/estrutura de pesos."""
    texto = json.dumps(pesos, sort_keys=True).encode("utf-8")
    return hashlib.sha256(texto).hexdigest()

def carregar_pesos_para_engine(caminho_arquivo=None):
    """Carrega os pesos e retorna uma tupla (pesos, valido) exigida pelos testes."""
    pesos = PESOS_PADRAO.copy()
    valido = False  # Por defeito é falso se não houver arquivo válido
    
    alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_TRAVA
    if os.path.exists(alvo):
        try:
            with open(alvo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                
                if isinstance(dados, dict):
                    if "pesos" in dados:
                        pesos_lidos = dados["pesos"]
                        # Suporta tanto "hash_pesos" quanto "hash"
                        hash_salvo = dados.get("hash_pesos") or dados.get("hash", "")
                        
                        # Validação rigorosa de integridade do hash SHA-256
                        if hash_salvo and hash_salvo == _hash_pesos(pesos_lidos):
                            pesos = pesos_lidos
                            valido = True
                        else:
                            # Violação de hash: força o fallback para o padrão e invalida
                            pesos = PESOS_PADRAO.copy()
                            valido = False
                    else:
                        pesos = dados
                        valido = True
        except Exception:
            pesos = PESOS_PADRAO.copy()
            valido = False
            
    return pesos, valido