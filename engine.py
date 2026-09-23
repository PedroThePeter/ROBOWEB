import random
import pandas as pd
import numpy as np


class LotofacilEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        # Identifica dinamicamente as colunas com as dezenas sorteadas
        self.dezenas_cols = [c for c in df.columns if 'Bola' in c or 'dezena' in c.lower()]
        if not self.dezenas_cols:
            self.dezenas_cols = df.columns[-15:].tolist()

    def juiz_de_frequencia(self):
        todas_dezenas = self.df[self.dezenas_cols].values.flatten()
        serie = pd.Series(todas_dezenas).value_counts().sort_values(ascending=False)
        quentes = serie.index[:10].tolist()
        frias = serie.index[-5:].tolist()
        return {"quentes": quentes, "frias": frias, "contagem": serie.to_dict()}

    def juiz_de_padroes_e_ciclos(self):
        todas = set(range(1, 26))
        sorteadas_recentes = set()
        for _, row in self.df.tail(10).iterrows():
            sorteadas_recentes.update(row[self.dezenas_cols].values)
        faltantes = list(todas - sorteadas_recentes)
        return {"estado": f"Ciclo em aberto ({len(faltantes)} faltantes)", "faltantes": faltantes}

    def juiz_de_paridade_e_primos(self):
        primos = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        return {"pares_ideais": [6, 7, 8, 9], "primos": primos}

    def juiz_de_soma_e_amplitude(self):
        return {"soma_minima": 180, "soma_maxima": 220}

    def juiz_de_sequencias_e_repeticoes(self):
        return {"max_sequencia": 4}

    def juiz_de_moldura_e_miolo(self):
        moldura = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25]
        miolo = [7, 8, 9, 12, 13, 14, 17, 18, 19]
        return {"moldura": moldura, "miolo": miolo}


class CuradorDeValidacao:
    def __init__(self, stats_ciclos, stats_paridade, stats_soma, stats_sequencias, score_minimo=90):
        self.stats_ciclos = stats_ciclos
        self.stats_paridade = stats_paridade
        self.stats_soma = stats_soma
        self.stats_sequencias = stats_sequencias
        self.score_minimo = score_minimo

    def avaliar_bilhete(self, dezenas):
        score = 100
        
        # 1. Filtro de Soma
        soma = sum(dezenas)
        s_min = self.stats_soma.get("soma_minima", 180)
        s_max = self.stats_soma.get("soma_maxima", 220)
        if soma < s_min or soma > s_max:
            score -= 18

        # 2. Filtro de Paridade
        pares = len([d for d in dezenas if d % 2 == 0])
        if pares not in self.stats_paridade.get("pares_ideais", [6, 7, 8, 9]):
            score -= 15

        # 3. Filtro de Números Primos
        primos_list = self.stats_paridade.get("primos", [2, 3, 5, 7, 11, 13, 17, 19, 23])
        qnt_primos = len([d for d in dezenas if d in primos_list])
        if qnt_primos < 5 or qnt_primos > 7:
            score -= 12

        # 4. Filtro de Sequências Consecutivas
        dezenas_ord = sorted(dezenas)
        maior_seq = 1
        seq_atual = 1
        for i in range(1, len(dezenas_ord)):
            if dezenas_ord[i] == dezenas_ord[i-1] + 1:
                seq_atual += 1
                if seq_atual > maior_seq:
                    maior_seq = seq_atual
            else:
                seq_atual = 1
        if maior_seq > self.stats_sequencias.get("max_sequencia", 4):
            score -= 15

        # 5. Filtro de Moldura vs Miolo
        moldura_set = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        qnt_moldura = len([d for d in dezenas if d in moldura_set])
        if qnt_moldura < 9 or qnt_moldura > 11:
            score -= 12

        # 6. Presença de Dezenas do Ciclo
        faltantes = self.stats_ciclos.get("faltantes", [])
        if faltantes:
            presenca_faltantes = len([d for d in dezenas if d in faltantes])
            if presenca_faltantes == 0:
                score -= 15

        aprovado = score >= self.score_minimo
        return score, aprovado


class CuradorDeSelecaoFinal:
    def __init__(self, validador, stats_frequencia, stats_ciclos, stats_sequencias):
        self.validador = validador
        self.stats_frequencia = stats_frequencia
        self.stats_ciclos = stats_ciclos
        self.stats_sequencias = stats_sequencias

    def gerar_bilhetes_diamante(self, quantidade=1, max_interseccao=12):
        bilhetes_aprovados = []
        tentativas_totais = 0
        max_tentativas = 20000

        quentes = self.stats_frequencia.get("quentes", list(range(1, 11)))
        outras = [i for i in range(1, 26) if i not in quentes]

        while len(bilhetes_aprovados) < quantidade and tentativas_totais < max_tentativas:
            tentativas_totais += 1
            
            # Geração aleatória de candidatos
            qnt_quentes = random.randint(6, 9)
            qnt_outras = 15 - qnt_quentes
            
            cand_quentes = random.sample(quentes, min(qnt_quentes, len(quentes)))
            cand_outras = random.sample(outras, min(qnt_outras, len(outras)))
            
            candidato = sorted(cand_quentes + cand_outras)
            if len(candidato) < 15:
                candidato = sorted(random.sample(range(1, 26), 15))

            # Validação pelo Curador
            score, aprovado = self.validador.avaliar_bilhete(candidato)

            if aprovado:
                valido_interseccao = True
                for b in bilhetes_aprovados:
                    interseccao = len(set(candidato).intersection(set(b)))
                    if interseccao > max_interseccao:
                        valido_interseccao = False
                        break
                
                if valido_interseccao:
                    bilhetes_aprovados.append(candidato)

        eficiencia = f"{(len(bilhetes_aprovados) / max(1, tentativas_totais)) * 100:.2f}%"

        return {
            "bilhetes": bilhetes_aprovados,
            "tentativas_gastas": tentativas_totais,
            "eficiencia": eficiencia
        }