import pandas as pd
import random
from typing import List, Dict, Any, Optional


class LotofacilGeneticEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.colunas_dezenas = self._identificar_colunas()
        self.pesos = {
            "atraso": 30,
            "co_ocorrencia": 30,
            "paridade": 15,
            "primos": 15,
            "soma": 15,
            "moldura": 15,
            "repetidas_anterior": 30,
            "sequencia": 15
        }
        # Cache das análises de horizonte. Só é recalculado quando a base
        # é recarregada (ver invalidar_cache) ou na primeira chamada.
        self._cache_comite: Optional[Dict[str, Any]] = None

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
        """Chame isso sempre que self.df mudar (ex: recarregar planilha)."""
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

    def obter_ultimo_concurso(self) -> List[int]:
        if self.df.empty:
            return []
        return self._extrair_dezenas_linha(self.df.iloc[-1])

    def _analisar_horizonte(self, sub_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Versão O(n): uma única passada pelo sub_df calcula o atraso de
        todas as 25 dezenas simultaneamente (antes era O(25*n)), e os
        pares de co-ocorrência na mesma passada.
        """
        n = len(sub_df)
        ultimo_indice_visto = {i: None for i in range(1, 26)}
        pares: Dict[tuple, int] = {}

        # Percorre do concurso mais antigo para o mais recente
        for pos in range(n):
            row = sub_df.iloc[pos]
            dezenas = sorted(self._extrair_dezenas_linha(row))
            for d in dezenas:
                ultimo_indice_visto[d] = pos
            for i in range(len(dezenas)):
                for j in range(i + 1, len(dezenas)):
                    p = (dezenas[i], dezenas[j])
                    pares[p] = pares.get(p, 0) + 1

        atrasos = {}
        for i in range(1, 26):
            if ultimo_indice_visto[i] is None:
                # Nunca apareceu na janela: atraso = tamanho da janela
                atrasos[i] = n
            else:
                # Quantos concursos se passaram desde a última aparição
                atrasos[i] = (n - 1) - ultimo_indice_visto[i]

        criticas = [k for k, v in atrasos.items() if v >= 3]
        top_pares = [p[0] for p in sorted(pares.items(), key=lambda x: x[1], reverse=True)[:10]]

        return {"criticas": criticas, "top_pares": top_pares, "atrasos": atrasos}

    def comite_de_horizontes(self, forcar_recalculo: bool = False) -> Dict[str, Any]:
        """Ensemble combinando curto prazo (50 concursos) e longo prazo (total).
        Resultado é cacheado em memória: recalcular esse ensemble em toda
        chamada de /api/estatisticas ou a cada bilhete gerado é desperdício,
        já que só muda quando a planilha é recarregada.
        """
        if self._cache_comite is not None and not forcar_recalculo:
            return self._cache_comite

        df_curto = self.df.tail(min(50, len(self.df)))
        analise_curto = self._analisar_horizonte(df_curto)
        analise_longo = self._analisar_horizonte(self.df)

        criticas_consenso = list(set(analise_curto["criticas"] + analise_longo["criticas"]))
        pares_consenso = list(set(analise_curto["top_pares"][:5] + analise_longo["top_pares"][:5]))

        resultado = {
            "dezenas_criticas": criticas_consenso,
            "top_pares": pares_consenso
        }
        self._cache_comite = resultado
        return resultado

    def calcular_fitness(self, dezenas: List[int], stats: Dict[str, Any], ultimo_concurso: List[int]) -> int:
        score = 0
        dezenas_set = set(dezenas)
        soma = sum(dezenas)

        if 170 <= soma <= 220:
            score += self.pesos["soma"]

        pares = len([n for n in dezenas if n % 2 == 0])
        if pares in [7, 8]:
            score += self.pesos["paridade"]

        primos = len([n for n in dezenas if n in {2, 3, 5, 7, 11, 13, 17, 19, 23}])
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

        moldura = len(dezenas_set.intersection({1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}))
        if moldura in [9, 10, 11]:
            score += self.pesos["moldura"]

        # CORREÇÃO: antes, quando não havia dezenas críticas, o score
        # de "atraso" era dado de graça sempre (bug). Agora só pontua
        # quando existe de fato uma dezena crítica presente no bilhete.
        criticas = set(stats.get("dezenas_criticas", []))
        if criticas and len(dezenas_set.intersection(criticas)) >= 1:
            score += self.pesos["atraso"]

        top_pares = stats.get("top_pares", [])
        pares_presentes = sum(1 for p1, p2 in top_pares if p1 in dezenas_set and p2 in dezenas_set)
        if pares_presentes >= 2:
            score += self.pesos["co_ocorrencia"]

        # CORREÇÃO: mesma lógica — só pontua "grátis" se de fato não
        # houver concurso anterior para comparar (base vazia).
        if ultimo_concurso:
            repetidas = len(dezenas_set.intersection(set(ultimo_concurso)))
            if 8 <= repetidas <= 10:
                score += self.pesos["repetidas_anterior"]
        else:
            score += self.pesos["repetidas_anterior"]

        return score

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
        """Menor número de dezenas diferentes entre `candidato` e qualquer
        bilhete já selecionado. Usado para forçar diversidade."""
        if not selecionados:
            return 15
        cand_set = set(candidato)
        return min(len(cand_set.symmetric_difference(set(s))) for s in selecionados)

    def executar_geracao_genetica(
        self,
        quantidade_desejada: int = 1,
        score_minimo: int = 150,
        diversidade_minima: int = 4,
    ) -> Dict[str, Any]:
        """
        diversidade_minima: número mínimo de dezenas que cada novo bilhete
        aprovado precisa ter de diferença em relação a TODOS os bilhetes já
        escolhidos (medido em diferença simétrica). Evita que, com
        score_minimo alto, os bilhetes aprovados saiam praticamente clones
        uns dos outros. Use 0 para desligar esse filtro.
        """
        stats = self.comite_de_horizontes()
        ultimo = self.obter_ultimo_concurso()

        populacao_tamanho = 300
        populacao = [sorted(random.sample(range(1, 26), 15)) for _ in range(populacao_tamanho)]

        geracao_atual = 0
        max_geracoes = 50
        bilhetes_diamante: List[List[int]] = []
        geracoes_gastas = 0

        while len(bilhetes_diamante) < quantidade_desejada and geracao_atual < max_geracoes:
            geracao_atual += 1
            geracoes_gastas = geracao_atual

            avaliados = [(b, self.calcular_fitness(b, stats, ultimo)) for b in populacao]
            avaliados.sort(key=lambda x: x[1], reverse=True)

            aprovados_geracao = [b for b, score in avaliados if score >= score_minimo]

            for b in aprovados_geracao:
                if b in bilhetes_diamante:
                    continue
                if diversidade_minima > 0 and self._distancia_minima(b, bilhetes_diamante) < diversidade_minima:
                    continue
                bilhetes_diamante.append(b)
                if len(bilhetes_diamante) >= quantidade_desejada:
                    break

            if len(bilhetes_diamante) >= quantidade_desejada:
                break

            melhores_pais = [b for b, score in avaliados[:int(populacao_tamanho * 0.3)]]

            nova_populacao = list(melhores_pais)
            while len(nova_populacao) < populacao_tamanho:
                p1, p2 = random.choices(melhores_pais, k=2)
                filho = self._cruzar_bilhetes(p1, p2)
                filho = self._mutar_bilhete(filho, taxa_mutacao=0.18)
                nova_populacao.append(filho)

            populacao = nova_populacao

        return {
            "bilhetes": bilhetes_diamante[:quantidade_desejada],
            "geracoes_gastas": geracoes_gastas,
            "score_aplicado": score_minimo,
            "diversidade_minima_aplicada": diversidade_minima,
            "estrategia": "Comitê Genético com Mutação Estocástica + Diversidade (v7.0)"
        }