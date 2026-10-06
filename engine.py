import math
import secrets
from collections import Counter
from typing import Dict, List, Optional, Sequence

from integridade import carregar_pesos_para_engine, _hash_bilhete, PESOS_PADRAO

DEZENAS = list(range(1, 26))
TAMANHO_BILHETE = 15
QUANTIDADE_MAXIMA = 100

AVISO = (
    "Os sorteios da Lotofácil são aleatórios: estes bilhetes não têm mais chance "
    "de acertar do que quaisquer outros de 15 dezenas. "
    "[PIPELINE DE CURADORIA ATIVADA]"
)

# ==========================================
# ⚖️ OS NOVOS JUÍZES (Filtros Heurísticos)
# ==========================================
def juiz_paridade(bilhete: List[int]) -> bool:
    pares = sum(1 for x in bilhete if x % 2 == 0)
    return 6 <= pares <= 9

def juiz_soma(bilhete: List[int]) -> bool:
    return 160 <= sum(bilhete) <= 210

def juiz_dispersao(bilhete: List[int]) -> bool:
    linhas = len(set((x - 1) // 5 for x in bilhete))
    colunas = len(set((x - 1) % 5 for x in bilhete))
    return linhas >= 4 and colunas >= 3

# ==========================================
# 🧠 OS CURADORES DE CÓDIGO
# ==========================================
def curador_microanalise(gerador_func, max_tentativas=500):
    """Curador 1: Submete os bilhetes aos 3 juízes individualmente."""
    for _ in range(max_tentativas):
        bilhete = gerador_func()
        if juiz_paridade(bilhete) and juiz_soma(bilhete) and juiz_dispersao(bilhete):
            return bilhete, True
    return gerador_func(), False

def curador_diversidade(frio: List[int], morno: List[int], quente: List[int]):
    """Curador 2: Analisa a diversidade do portfólio em conjunto."""
    i1 = len(set(frio) & set(morno))
    i2 = len(set(frio) & set(quente))
    i3 = len(set(morno) & set(quente))
    maior_sobreposicao = max(i1, i2, i3)
    
    if maior_sobreposicao > 11:
        return False, f"Curador 2 Reprovou: Sobreposição excessiva ({maior_sobreposicao} dezenas repetidas entre tickets)."
    return True, f"Curador 2 Aprovou: Diversidade máxima cruzada garantida (Max {maior_sobreposicao} interseções)."

def extrair_pesos_dict(pesos_input):
    if isinstance(pesos_input, tuple):
        return pesos_input[0]
    return pesos_input

def _pesos_por_dezena(pesos: Dict) -> List[float]:
    lista = []
    for d in DEZENAS:
        bruto = pesos.get(str(d), pesos.get(d, 1.0))
        try:
            v = float(bruto)
        except (TypeError, ValueError):
            v = 0.0
        lista.append(v if math.isfinite(v) and v > 0 else 0.0)
    return lista

def sortear_bilhete_estratificado_quente(pesos_lista: Sequence[float], rng=None) -> List[int]:
    """Mantém a geometria estrita 7-4-4 do Bilhete Quente (T=100%)"""
    rng = rng or secrets.SystemRandom()
    faixa1 = list(range(1, 12))
    faixa2 = list(range(12, 19))
    faixa3 = list(range(19, 26))

    def escolher_da_faixa(faixa, k):
        sub_pop = list(faixa)
        sub_pesos = [pesos_lista[d - 1] for d in sub_pop]
        escolhidos = []
        for _ in range(k):
            if sum(sub_pesos) <= 0:
                idx = rng.randrange(len(sub_pop))
            else:
                idx = rng.choices(range(len(sub_pop)), weights=sub_pesos, k=1)[0]
            escolhidos.append(sub_pop.pop(idx))
            sub_pesos.pop(idx)
        return escolhidos

    b1 = escolher_da_faixa(faixa1, 7)
    b2 = escolher_da_faixa(faixa2, 4)
    b3 = escolher_da_faixa(faixa3, 4)
    return sorted(b1 + b2 + b3)

def pesos_por_frequencia(sorteios: Sequence[Sequence[int]], janela: Optional[int] = None) -> Dict[str, float]:
    recentes = sorteios[-janela:] if janela else sorteios
    cont = Counter(d for s in recentes for d in s)
    return {str(d): float(cont.get(d, 0) + 1) for d in DEZENAS}

class LotofacilGeneticEngine:
    def __init__(self, caminho_pesos=None):
        self.caminho_pesos = caminho_pesos

    def gerar_jogos(self, quantidade=1, concurso=None, pesos=None, temperatura=0.0):
        return gerar_jogos_genetico(quantidade, concurso, self.caminho_pesos, pesos, temperatura)

def gerar_jogos_genetico(quantidade=1, concurso=None, caminho_pesos=None, pesos=None, rng=None, temperatura=0.0):
    if not isinstance(quantidade, int) or not (1 <= quantidade <= QUANTIDADE_MAXIMA):
        raise ValueError(f"quantidade deve ser um inteiro entre 1 e {QUANTIDADE_MAXIMA}.")
    
    rng = rng or secrets.SystemRandom()

    if pesos is not None:
        pesos_dict, valido = pesos, False
    else:
        pesos_dict, valido = carregar_pesos_para_engine(caminho_pesos)

    pesos_lista = _pesos_por_dezena(extrair_pesos_dict(pesos_dict))

    def gerador_temperatura():
        if abs(temperatura - 100.0) < 1e-5:
            return sortear_bilhete_estratificado_quente(pesos_lista, rng)
        else:
            p_lista = list(pesos_lista)
            if temperatura > 0.0:
                t_norm = max(0.0, min(temperatura, 100.0)) / 100.0
                if p_lista:
                    peso_medio = sum(p_lista) / len(p_lista)
                    p_lista = [p * (1.0 - t_norm) + (peso_medio * t_norm) for p in p_lista]

            if sum(1 for p in p_lista if p > 0) < TAMANHO_BILHETE:
                return sorted(rng.sample(DEZENAS, TAMANHO_BILHETE))

            populacao = list(DEZENAS)
            restantes = list(p_lista)
            bilhete = []
            for _ in range(TAMANHO_BILHETE):
                i = rng.choices(range(len(populacao)), weights=restantes, k=1)[0]
                bilhete.append(populacao.pop(i))
                restantes.pop(i)
            return sorted(bilhete)

    jogos = []
    for _ in range(quantidade):
        bilhete, _ = curador_microanalise(gerador_temperatura)
        jogos.append(bilhete)

    hashes = [_hash_bilhete(b) for b in jogos]

    return {
        "status": "sucesso",
        "concurso": concurso,
        "quantidade": len(jogos),
        "jogos": jogos,
        "bilhetes": jogos,
        "hashes": hashes,
        "trava_valida": valido,
        "aviso": AVISO,
        "temperatura_aplicada": temperatura
    }