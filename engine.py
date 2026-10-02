import math
import secrets  # <--- ALTERAÇÃO 1: Importamos entropia do SO (criptográfica)
from collections import Counter
from typing import Dict, List, Optional, Sequence

from integridade import carregar_pesos_para_engine, _hash_bilhete, PESOS_PADRAO

DEZENAS = list(range(1, 26))
TAMANHO_BILHETE = 15
QUANTIDADE_MAXIMA = 100

AVISO = (
    "Os sorteios da Lotofácil são aleatórios: estes bilhetes não têm mais chance "
    "de acertar do que quaisquer outros de 15 dezenas. "
    "[GERAÇÃO DE ENTROPIA CRIPTOGRÁFICA ATIVADA]" # <--- ALTERAÇÃO 2: Aviso atualizado
)


def extrair_pesos_dict(pesos_input):
    """Garante o dicionário de pesos, mesmo que venha como tupla (pesos, valido)."""
    if isinstance(pesos_input, tuple):
        return pesos_input[0]
    return pesos_input


def _pesos_por_dezena(pesos: Dict) -> List[float]:
    """Lista de 25 pesos (dezenas 1..25). Valor inválido, negativo ou infinito vira 0."""
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
    """Sorteia 15 dezenas distintas, com probabilidade proporcional aos pesos."""
    # <--- ALTERAÇÃO 3: Inicialização quântica/criptográfica caso não venha de laboratório (testes)
    rng = rng or secrets.SystemRandom()

    # Com menos de 15 pesos positivos não dá para montar um bilhete ponderado
    # (random.choices levantaria erro no meio do sorteio): cai no sorteio simples.
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


def pesos_por_frequencia(sorteios: Sequence[Sequence[int]], janela: Optional[int] = None) -> Dict[str, float]:
    """
    Peso de cada dezena = vezes que saiu nos últimos `janela` concursos (+1 de suavização).
    Sem histórico, todos os pesos valem 1.0. Use no backtest ou para montar uma trava
    (integridade.gravar_trava). Atenção: o backtest mostra se isso supera o acaso.
    """
    recentes = sorteios[-janela:] if janela else sorteios
    cont = Counter(d for s in recentes for d in s)
    return {str(d): float(cont.get(d, 0) + 1) for d in DEZENAS}


class LotofacilGeneticEngine:
    """Wrapper de compatibilidade para módulos que instanciam o motor."""

    def __init__(self, caminho_pesos=None):
        self.caminho_pesos = caminho_pesos

    def gerar_jogos(self, quantidade=10, concurso=None, pesos=None):
        return gerar_jogos_genetico(
            quantidade=quantidade,
            concurso=concurso,
            caminho_pesos=self.caminho_pesos,
            pesos=pesos,
        )

    def executar(self, quantidade=10, concurso=None):
        return self.gerar_jogos(quantidade=quantidade, concurso=concurso)


def gerar_jogos_genetico(quantidade=10, concurso=None, caminho_pesos=None, pesos=None, rng=None):
    """
    Gera bilhetes por seleção ponderada pelos pesos ativos (da trava, ou os passados em `pesos`).
    Observação: apesar do nome, não há algoritmo genético aqui; é sorteio ponderado.
    Retorna dict com os jogos, os hashes SHA-256 e se a trava de pesos estava válida.
    """
    if not isinstance(quantidade, int) or not (1 <= quantidade <= QUANTIDADE_MAXIMA):
        raise ValueError(f"quantidade deve ser um inteiro entre 1 e {QUANTIDADE_MAXIMA}.")
    
    # <--- ALTERAÇÃO 4: Aplicação da segurança criptográfica em nível superior
    rng = rng or secrets.SystemRandom()

    if pesos is not None:
        pesos_dict, valido = pesos, False  # pesos avulsos não passam pela trava
    else:
        pesos_dict, valido = carregar_pesos_para_engine(caminho_pesos)

    pesos_lista = _pesos_por_dezena(extrair_pesos_dict(pesos_dict))

    jogos = [sortear_bilhete(pesos_lista, rng) for _ in range(quantidade)]
    hashes = [_hash_bilhete(b) for b in jogos]

    return {
        "status": "sucesso",
        "concurso": concurso,
        "quantidade": quantidade,
        "jogos": jogos,
        "bilhetes": jogos,  # interfaces que leem 'bilhetes'
        "hashes": hashes,
        "trava_valida": valido,
        "aviso": AVISO,
    }