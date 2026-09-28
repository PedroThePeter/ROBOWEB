import random
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

PESOS_PADRAO: Dict[str, int] = {
    "atraso": 30,
    "co_ocorrencia": 30,
    "paridade": 15,
    "primos": 15,
    "soma": 15,
    "moldura": 15,
    "repetidas_anterior": 30,
    "sequencia": 15,
}

PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}

# O volante da Lotofácil é uma grade 5x5:
#  1  2  3  4  5
#  6  7  8  9 10
# 11 12 13 14 15
# 16 17 18 19 20
# 21 22 23 24 25
LINHAS_VOLANTE = [set(range(i, i + 5)) for i in (1, 6, 11, 16, 21)]
COLUNAS_VOLANTE = [set(range(c, 26, 5)) for c in (1, 2, 3, 4, 5)]


class LotofacilGeneticEngine:
    def __init__(
        self,
        df: pd.DataFrame,
        pesos: Optional[Dict[str, int]] = None,
        sorteios: Optional[List[List[int]]] = None,
    ):
        """
        df: planilha com o histórico (do concurso mais antigo para o mais recente).
        pesos: sobrescreve parte (ou todos) os pesos padrão. Usado no teste de ablação.
        sorteios: histórico já extraído (lista de listas de 15 dezenas). Usado pelo
                  backtest para não reprocessar a planilha inteira a cada rodada.
        """
        self.df = df
        self.colunas_dezenas = self._identificar_colunas()
        self.pesos = dict(PESOS_PADRAO)
        if pesos:
            self.pesos.update(pesos)

        self._sorteios: List[List[int]] = (
            sorteios if sorteios is not None else self._extrair_todos_sorteios()
        )
        # Cache do comitê de horizontes; só muda quando a base muda.
        self._cache_comite: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Base de dados
    # ------------------------------------------------------------------
    @property
    def total_concursos(self) -> int:
        return len(self._sorteios)

    @property
    def pontuacao_maxima(self) -> int:
        return sum(self.pesos.values())

    def _identificar_colunas(self) -> List[str]:
        cols = []
        for c in self.df.columns:
            nome = str(c).lower().strip()
            if 'bola' in nome or 'dezena' in nome or (nome.startswith('d') and nome[1:].isdigit()):
                cols.append(c)
        if len(cols) < 15:
            cols = self.df.columns[2:17]
        return list(cols)

    def invalidar_cache(self):
        """Chame isso sempre que o histórico mudar."""
        self._cache_comite = None

    def _extrair_dezenas_linha(self, row) -> List[int]:
        dezenas = []
        for val in row[self.colunas_dezenas].values:
            try:
                n = int(val)
                if 1 <= n <= 25:
                    dezenas.append(n)
            except (ValueError, TypeError):
                pass
        return dezenas

    def _extrair_todos_sorteios(self) -> List[List[int]]:
        sorteios: List[List[int]] = []
        for _, row in self.df.iterrows():
            dezenas = self._extrair_dezenas_linha(row)
            if len(dezenas) == 15:  # ignora linhas incompletas/malformadas
                sorteios.append(sorted(dezenas))
        return sorteios

    def obter_ultimo_concurso(self) -> List[int]:
        return list(self._sorteios[-1]) if self._sorteios else []

    # ------------------------------------------------------------------
    # Análise estatística (comitê de horizontes)
    # ------------------------------------------------------------------
    def _analisar_horizonte(self, sorteios: List[List[int]]) -> Dict[str, Any]:
        """Uma única passada calcula o atraso de todas as dezenas e os pares."""
        n = len(sorteios)
        ultimo_indice_visto: Dict[int, Optional[int]] = {i: None for i in range(1, 26)}
        pares: Dict[Tuple[int, int], int] = {}

        for pos, dezenas in enumerate(sorteios):
            for d in dezenas:
                ultimo_indice_visto[d] = pos
            for i in range(len(dezenas)):
                for j in range(i + 1, len(dezenas)):
                    p = (dezenas[i], dezenas[j])
                    pares[p] = pares.get(p, 0) + 1

        atrasos = {}
        for i in range(1, 26):
            if ultimo_indice_visto[i] is None:
                atrasos[i] = n
            else:
                atrasos[i] = (n - 1) - ultimo_indice_visto[i]

        criticas = [k for k, v in atrasos.items() if v >= 3]
        top_pares = [p[0] for p in sorted(pares.items(), key=lambda x: x[1], reverse=True)[:10]]

        return {"criticas": criticas, "top_pares": top_pares, "atrasos": atrasos}

    def comite_de_horizontes(self, forcar_recalculo: bool = False) -> Dict[str, Any]:
        """Ensemble entre curto prazo (50 concursos) e longo prazo (todos). Cacheado."""
        if self._cache_comite is not None and not forcar_recalculo:
            return self._cache_comite

        analise_curto = self._analisar_horizonte(self._sorteios[-50:])
        analise_longo = self._analisar_horizonte(self._sorteios)

        criticas_consenso = list(set(analise_curto["criticas"] + analise_longo["criticas"]))
        pares_consenso = list(set(analise_curto["top_pares"][:5] + analise_longo["top_pares"][:5]))

        resultado = {
            "dezenas_criticas": criticas_consenso,
            "top_pares": pares_consenso
        }
        self._cache_comite = resultado
        return resultado

    # ------------------------------------------------------------------
    # Pontuação de um bilhete
    # ------------------------------------------------------------------
    def calcular_fitness(self, dezenas: List[int], stats: Dict[str, Any], ultimo_concurso: List[int]) -> int:
        score = 0
        dezenas_set = set(dezenas)
        soma = sum(dezenas)

        if 170 <= soma <= 220:
            score += self.pesos["soma"]

        pares = len([n for n in dezenas if n % 2 == 0])
        if pares in [7, 8]:
            score += self.pesos["paridade"]

        primos = len([n for n in dezenas if n in PRIMOS])
        if primos in [5, 6]:
            score += self.pesos["primos"]

        max_seq, atual_seq = 1, 1
        dezenas_ord = sorted(dezenas)
        for i in range(len(dezenas_ord) - 1):
            if dezenas_ord[i + 1] == dezenas_ord[i] + 1:
                atual_seq += 1
                max_seq = max(max_seq, atual_seq)
            else:
                atual_seq = 1
        if max_seq <= 4:
            score += self.pesos["sequencia"]

        moldura = len(dezenas_set.intersection(MOLDURA))
        if moldura in [9, 10, 11]:
            score += self.pesos["moldura"]

        criticas = set(stats.get("dezenas_criticas", []))
        if criticas and len(dezenas_set.intersection(criticas)) >= 1:
            score += self.pesos["atraso"]

        top_pares = stats.get("top_pares", [])
        pares_presentes = sum(1 for p1, p2 in top_pares if p1 in dezenas_set and p2 in dezenas_set)
        if pares_presentes >= 2:
            score += self.pesos["co_ocorrencia"]

        if ultimo_concurso:
            repetidas = len(dezenas_set.intersection(set(ultimo_concurso)))
            if 8 <= repetidas <= 10:
                score += self.pesos["repetidas_anterior"]
        else:
            score += self.pesos["repetidas_anterior"]

        return score

    @staticmethod
    def _padrao_popular(bilhete: List[int]) -> bool:
        """
        Heurística leve: marca bilhetes com 2+ linhas ou 2+ colunas COMPLETAS do
        volante. São desenhos "visuais" que tendem a ser apostados por muita gente.
        Não há dado público de popularidade por combinação; isso é só uma suposição
        razoável e pode ser desligada (evitar_populares=False).
        """
        s = set(bilhete)
        linhas_completas = sum(1 for linha in LINHAS_VOLANTE if linha <= s)
        colunas_completas = sum(1 for coluna in COLUNAS_VOLANTE if coluna <= s)
        return linhas_completas >= 2 or colunas_completas >= 2

    # ------------------------------------------------------------------
    # Operadores genéticos
    # ------------------------------------------------------------------
    def _cruzar_bilhetes(self, pai1: List[int], pai2: List[int]) -> List[int]:
        filho = list(set(random.sample(pai1, 8) + random.sample(pai2, 7)))
        while len(filho) < 15:
            candidato = random.randint(1, 25)
            if candidato not in filho:
                filho.append(candidato)
        return sorted(filho[:15])

    def _mutar_bilhete(self, bilhete: List[int], taxa_mutacao: float = 0.18) -> List[int]:
        mutado = list(bilhete)
        if random.random() < taxa_mutacao:
            idx_remover = random.randint(0, 14)
            novo_num = random.randint(1, 25)
            while novo_num in mutado:
                novo_num = random.randint(1, 25)
            mutado[idx_remover] = novo_num
        return sorted(mutado)

    @staticmethod
    def _distancia_minima(candidato: List[int], selecionados: List[List[int]]) -> int:
        """Menor número de dezenas diferentes entre o candidato e os já escolhidos."""
        if not selecionados:
            return 15
        cand_set = set(candidato)
        return min(len(cand_set.symmetric_difference(set(s))) for s in selecionados)

    # ------------------------------------------------------------------
    # Geração de candidatos + seleção em portfólio
    # ------------------------------------------------------------------
    def gerar_candidatos(
        self,
        alvo: int,
        score_minimo: int,
        evitar_populares: bool = True,
        max_geracoes: int = 50,
    ) -> Tuple[List[Tuple[List[int], int]], int]:
        """
        Evolui a população e junta bilhetes aprovados (sem repetição) até chegar
        em `alvo` candidatos. Retorna (lista de (bilhete, score), gerações usadas).
        """
        stats = self.comite_de_horizontes()
        ultimo = self.obter_ultimo_concurso()

        populacao_tamanho = 300
        populacao = [sorted(random.sample(range(1, 26), 15)) for _ in range(populacao_tamanho)]

        candidatos: List[Tuple[List[int], int]] = []
        vistos: Set[Tuple[int, ...]] = set()
        geracoes = 0

        while len(candidatos) < alvo and geracoes < max_geracoes:
            geracoes += 1

            avaliados = [(b, self.calcular_fitness(b, stats, ultimo)) for b in populacao]
            avaliados.sort(key=lambda x: x[1], reverse=True)

            for b, score in avaliados:
                if score < score_minimo:
                    break  # lista ordenada: o resto é pior
                chave = tuple(b)
                if chave in vistos:
                    continue
                if evitar_populares and self._padrao_popular(b):
                    continue
                vistos.add(chave)
                candidatos.append((b, score))

            if len(candidatos) >= alvo:
                break

            melhores_pais = [b for b, _ in avaliados[:int(populacao_tamanho * 0.3)]]
            nova_populacao = list(melhores_pais)
            while len(nova_populacao) < populacao_tamanho:
                p1, p2 = random.choices(melhores_pais, k=2)
                filho = self._cruzar_bilhetes(p1, p2)
                filho = self._mutar_bilhete(filho, taxa_mutacao=0.18)
                nova_populacao.append(filho)
            populacao = nova_populacao

        return candidatos, geracoes

    def selecionar_portfolio(
        self,
        candidatos: List[Tuple[List[int], int]],
        quantidade: int,
        diversidade_minima: int = 4,
        peso_equilibrio: float = 2.0,
    ) -> List[List[int]]:
        """
        Escolhe `quantidade` bilhetes como um CONJUNTO, não um a um.

        A cada passo, escolhe o candidato de menor custo:
            custo = peso_equilibrio * carga - score / 30
        onde `carga` é a média de vezes que as dezenas do candidato já foram usadas
        nos bilhetes escolhidos. Isso empurra o conjunto para usar todas as dezenas
        de forma parelha (nenhuma dezena fica "todo mundo depende dela"), sem
        abrir mão do score. Se a diversidade mínima esgotar os candidatos, ela é
        relaxada em 1 dezena por vez.
        """
        selecionados: List[List[int]] = []
        contagem = {d: 0 for d in range(1, 26)}
        restantes = list(candidatos)
        diversidade_atual = diversidade_minima

        while restantes and len(selecionados) < quantidade:
            n_sel = len(selecionados)
            melhor_idx = None
            melhor_custo = None

            for idx, (b, score) in enumerate(restantes):
                if diversidade_atual > 0 and self._distancia_minima(b, selecionados) < diversidade_atual:
                    continue
                carga = sum(contagem[d] for d in b) / max(1, n_sel)
                custo = peso_equilibrio * carga - score / 30 + random.random() * 0.01
                if melhor_custo is None or custo < melhor_custo:
                    melhor_custo = custo
                    melhor_idx = idx

            if melhor_idx is None:
                if diversidade_atual > 0:
                    diversidade_atual -= 1
                    continue
                break

            b, _ = restantes.pop(melhor_idx)
            selecionados.append(b)
            for d in b:
                contagem[d] += 1

        return selecionados

    def executar_geracao_genetica(
        self,
        quantidade_desejada: int = 1,
        score_minimo: int = 150,
        diversidade_minima: int = 4,
        evitar_populares: bool = True,
        peso_equilibrio: float = 2.0,
    ) -> Dict[str, Any]:
        alvo = max(quantidade_desejada * 5, 30)
        candidatos, geracoes = self.gerar_candidatos(alvo, score_minimo, evitar_populares)
        bilhetes = self.selecionar_portfolio(
            candidatos, quantidade_desejada, diversidade_minima, peso_equilibrio
        )

        frequencia = Counter(d for b in bilhetes for d in b)
        distancia_real = None
        if len(bilhetes) >= 2:
            distancia_real = min(
                len(set(bilhetes[i]).symmetric_difference(set(bilhetes[j])))
                for i in range(len(bilhetes)) for j in range(i + 1, len(bilhetes))
            )

        resposta: Dict[str, Any] = {
            "bilhetes": bilhetes,
            "geracoes_gastas": geracoes,
            "score_aplicado": score_minimo,
            "pontuacao_maxima": self.pontuacao_maxima,
            "diversidade_minima_aplicada": diversidade_minima,
            "distancia_minima_real": distancia_real,
            "frequencia_dezenas": {d: frequencia.get(d, 0) for d in range(1, 26)},
            "candidatos_avaliados": len(candidatos),
            "estrategia": "Comitê Genético + Portfólio Balanceado (v8.0)",
        }
        if len(bilhetes) < quantidade_desejada:
            resposta["aviso"] = (
                f"Só foi possível montar {len(bilhetes)} de {quantidade_desejada} bilhetes "
                f"com score >= {score_minimo}."
            )
        return resposta

    # ------------------------------------------------------------------
    # Sugestão de dezenas para desdobramento
    # ------------------------------------------------------------------
    def sugerir_pool_dezenas(self, tamanho: int = 17, score_minimo: int = 150) -> List[int]:
        """
        Sugere `tamanho` dezenas contando quais aparecem mais nos bilhetes de maior
        score. Sem vantagem preditiva comprovada: é um ponto de partida. O caminho
        principal do desdobramento é você informar as dezenas que quiser.
        """
        candidatos, _ = self.gerar_candidatos(200, score_minimo, evitar_populares=False)
        freq = Counter(d for b, _ in candidatos for d in b)
        ranking = sorted(range(1, 26), key=lambda d: (-freq[d], random.random()))
        return sorted(ranking[:tamanho])