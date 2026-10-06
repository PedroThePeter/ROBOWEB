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
    "[ESPECTRO TÉRMICO ESTRATIFICADO ATUALIZADO]"
)


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


def sortear_bilhete(pesos_lista: Sequence[float], rng=None) -> List[int]:
    rng = rng or secrets.SystemRandom()
    if sum(1 for p in pesos_lista if p > 0) < TAMANHO_BILHETE:
        return sorted(rng.sample(DEZENAS, TAMANHO_BILHETE))

    populacao = list(DEZENAS)
    restantes = list(pesos_lista)
    bilhete = []
    for _ in range(TAMANHO_BILHETE):
        i = rng.choices(range(len(populacao)), weights=restantes, k=1)[0]
        bilhete.append(populacao.pop(i))
        restantes.pop(i)
    return sorted(bilhete)


def sortear_bilhete_estratificado_quente(pesos_lista: Sequence[float], rng=None) -> List[int]:
    """
    Sorteio estratificado agora aplicado ao estado Quente (T = 100%):
    Força a distribuição estrutural exigida pelo analista:
    - 7 dezenas na faixa de 1 a 11
    - 4 dezenas na faixa de 12 a 18
    - 4 dezenas na faixa de 19 a 25
    """
    rng = rng or secrets.SystemRandom()
    
    faixa1 = list(range(1, 12))   # 1 a 11 -> sortear 7
    faixa2 = list(range(12, 19))  # 12 a 18 -> sortear 4
    faixa3 = list(range(19, 26))  # 19 a 25 -> sortear 4

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
        return gerar_jogos_genetico(
            quantidade=quantidade,
            concurso=concurso,
            caminho_pesos=self.caminho_pesos,
            pesos=pesos,
            temperatura=temperatura,
        )

    def executar(self, quantidade=1, concurso=None):
        return self.gerar_jogos(quantidade=quantidade, concurso=concurso)


def gerar_jogos_genetico(quantidade=1, concurso=None, caminho_pesos=None, pesos=None, rng=None, temperatura=0.0):
    if not isinstance(quantidade, int) or not (1 <= quantidade <= QUANTIDADE_MAXIMA):
        raise ValueError(f"quantidade deve ser um inteiro entre 1 e {QUANTIDADE_MAXIMA}.")
    
    rng = rng or secrets.SystemRandom()

    if pesos is not None:
        pesos_dict, valido = pesos, False
    else:
        pesos_dict, valido = carregar_pesos_para_engine(caminho_pesos)

    pesos_lista = _pesos_por_dezena(extrair_pesos_dict(pesos_dict))

    # Se a temperatura for 100.0 (Estado Quente), aplicamos a partição estrutural estricta 7-4-4
    if abs(temperatura - 100.0) < 1e-5:
        bilhete = sortear_bilhete_estratificado_quente(pesos_lista, rng)
        jogos = [bilhete]
    else:
        if temperatura > 0.0:
            t_norm = max(0.0, min(temperatura, 100.0)) / 100.0
            if pesos_lista:
                peso_medio = sum(pesos_lista) / len(pesos_lista)
                pesos_lista = [p * (1.0 - t_norm) + (peso_medio * t_norm) for p in pesos_lista]

        jogos = [sortear_bilhete(pesos_lista, rng) for _ in range(quantidade)]

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