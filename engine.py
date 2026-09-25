import pandas as pd
import random
from typing import List, Dict, Any

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

    def _identificar_colunas(self) -> List[str]:
        cols = []
        for c in self.df.columns:
            nome = str(c).lower().strip()
            if 'bola' in nome or 'dezena' in nome or (nome.startswith('d') and nome[1:].isdigit()):
                cols.append(c)
        if len(cols) < 15:
            cols = self.df.columns[2:17]
        return list(cols)

    def obter_ultimo_concurso(self) -> List[int]:
        if self.df.empty:
            return []
        ultimo_row = self.df.iloc[-1][self.colunas_dezenas].values
        dezenas = []
        for val in ultimo_row:
            try:
                num = int(val)
                if 1 <= num <= 25: dezenas.append(num)
            except: pass
        return dezenas

    def _analisar_horizonte(self, sub_df: pd.DataFrame) -> Dict[str, Any]:
        atrasos = {i: 0 for i in range(1, 26)}
        for i in range(1, 26):
            count = 0
            for idx in range(len(sub_df)-1, -1, -1):
                row = sub_df.iloc[idx][self.colunas_dezenas].values
                sorteadas = []
                for val in row:
                    try: sorteadas.append(int(val))
                    except: pass
                if i in sorteadas: break
                count += 1
            atrasos[i] = count
        
        criticas = [k for k, v in atrasos.items() if v >= 3]

        pares = {}
        for _, row in sub_df.iterrows():
            dezenas = []
            for val in row[self.colunas_dezenas].values:
                try:
                    n = int(val)
                    if 1 <= n <= 25: dezenas.append(n)
                except: pass
            dezenas = sorted(dezenas)
            for i in range(len(dezenas)):
                for j in range(i+1, len(dezenas)):
                    p = (dezenas[i], dezenas[j])
                    pares[p] = pares.get(p, 0) + 1
        top_pares = [p[0] for p in sorted(pares.items(), key=lambda x: x[1], reverse=True)[:10]]

        return {"criticas": criticas, "top_pares": top_pares}

    def comite_de_horizontes(self) -> Dict[str, Any]:
        """Ensemble combinando curto prazo (50 concursos) e longo prazo (total)."""
        df_curto = self.df.tail(min(50, len(self.df)))
        analise_curto = self._analisar_horizonte(df_curto)
        analise_longo = self._analisar_horizonte(self.df)

        criticas_consenso = list(set(analise_curto["criticas"] + analise_longo["criticas"]))
        pares_consenso = list(set(analise_curto["top_pares"][:5] + analise_longo["top_pares"][:5]))

        return {
            "dezenas_criticas": criticas_consenso,
            "top_pares": pares_consenso
        }

    def calcular_fitness(self, dezenas: List[int], stats: Dict[str, Any], ultimo_concurso: List[int]) -> int:
        score = 0
        dezenas_set = set(dezenas)
        soma = sum(dezenas)

        if 170 <= soma <= 220: score += self.pesos["soma"]
        
        pares = len([n for n in dezenas if n % 2 == 0])
        if pares in [7, 8]: score += self.pesos["paridade"]
            
        primos = len([n for n in dezenas if n in {2, 3, 5, 7, 11, 13, 17, 19, 23}])
        if primos in [5, 6]: score += self.pesos["primos"]

        max_seq, atual_seq = 1, 1
        dezenas_ord = sorted(dezenas)
        for i in range(len(dezenas_ord) - 1):
            if dezenas_ord[i+1] == dezenas_ord[i] + 1:
                atual_seq += 1
                max_seq = max(max_seq, atual_seq)
            else:
                atual_seq = 1
        if max_seq <= 4: score += self.pesos["sequencia"]

        moldura = len(dezenas_set.intersection({1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}))
        if moldura in [9, 10, 11]: score += self.pesos["moldura"]

        criticas = set(stats.get("dezenas_criticas", []))
        if not criticas or len(dezenas_set.intersection(criticas)) >= 1:
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

    def executar_geracao_genetica(self, quantidade_desejada: int = 1, score_minimo: int = 150) -> Dict[str, Any]:
        stats = self.comite_de_horizontes()
        ultimo = self.obter_ultimo_concurso()
        
        populacao_tamanho = 300
        populacao = [sorted(random.sample(range(1, 26), 15)) for _ in range(populacao_tamanho)]
        
        geracao_atual = 0
        max_geracoes = 50
        bilhetes_diamante = []
        geracoes_gastas = 0

        while len(bilhetes_diamante) < quantidade_desejada and geracao_atual < max_geracoes:
            geracao_atual += 1
            geracoes_gastas = geracao_atual

            avaliados = [(b, self.calcular_fitness(b, stats, ultimo)) for b in populacao]
            avaliados.sort(key=lambda x: x[1], reverse=True)

            aprovados_geracao = [b for b, score in avaliados if score >= score_minimo]
            
            for b in aprovados_geracao:
                if b not in bilhetes_diamante:
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
            "estrategia": "Comitê Genético com Mutação Estocástica (v6.0)"
        }