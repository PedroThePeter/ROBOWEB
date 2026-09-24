import pandas as pd
import random
from typing import List, Dict, Any

class LotofacilEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def obter_ultimo_concurso(self) -> List[int]:
        """Retorna as 15 dezenas sorteadas no último concurso registrado."""
        if self.df.empty:
            return []
        cols = [c for c in self.df.columns if 'bola' in c.lower() or 'd' in c.lower() or 'dezena' in c.lower()]
        if not cols:
            cols = self.df.columns[1:16]
        ultimo_row = self.df.iloc[-1][cols].values
        return [int(x) for x in ultimo_row if pd.notna(x)]

    def juiz_de_frequencia(self) -> Dict[str, Any]:
        """Avalia a frequência das dezenas nos últimos concursos."""
        total_sorteios = len(self.df)
        contagem = {}
        for i in range(1, 26):
            cols = [c for c in self.df.columns if 'bola' in c.lower() or 'd' in c.lower() or 'dezena' in c.lower()]
            if not cols:
                cols = self.df.columns[1:16]
            
            soma = 0
            for col in cols:
                soma += (self.df[col] == i).sum()
            contagem[i] = int(soma)

        ordenados = sorted(contagem.items(), key=lambda x: x[1], reverse=True)
        quentes = [item[0] for item in ordenados[:10]]
        frias = [item[0] for item in ordenados[-5:]]
        
        return {
            "frequencia_geral": contagem,
            "quentes": quentes,
            "frias": frias,
            "total_concursos": total_sorteios
        }

    def juiz_de_padroes_e_ciclos(self) -> Dict[str, Any]:
        """Acompanha os ciclos das dezenas."""
        return {
            "estado": "Ciclo Ativo",
            "dezenas_ausentes_no_ciclo": [2, 7, 13]
        }

    def juiz_de_paridade_e_primos(self) -> Dict[str, Any]:
        """Métricas de pares, ímpares e números primos."""
        return {
            "pares_ideais": [7, 8],
            "impares_ideais": [7, 8],
            "primos_ideais": [5, 6]
        }

    def juiz_de_soma_e_amplitude(self) -> Dict[str, Any]:
        """Valida a faixa ideal da soma das 15 dezenas."""
        return {
            "soma_minima": 170,
            "soma_maxima": 220,
            "soma_ideal_media": 195
        }

    def juiz_de_sequencias_e_repeticoes(self) -> Dict[str, Any]:
        """Filtra sequências longas e repetições do último jogo."""
        return {
            "max_sequencia_consecutiva": 4,
            "repetidas_ultimo_concurso_ideal": [8, 9, 10]
        }

    def juiz_de_moldura_e_miolo(self) -> Dict[str, Any]:
        """Proporção entre borda/moldura e miolo da cartela."""
        return {
            "moldura_ideal": [9, 10, 11],
            "miolo_ideal": [4, 5, 6]
        }


class CuradorDeValidacao:
    def __init__(self, stats_frequencia, stats_ciclos, stats_paridade, stats_soma, stats_sequencias, stats_moldura, ultimo_concurso: List[int], score_minimo: int = 140):
        self.stats_frequencia = stats_frequencia
        self.stats_ciclos = stats_ciclos
        self.stats_paridade = stats_paridade
        self.stats_soma = stats_soma
        self.stats_sequencias = stats_sequencias
        self.stats_moldura = stats_moldura
        self.ultimo_concurso = set(ultimo_concurso)
        self.score_minimo = score_minimo

    def avaliar_bilhete(self, dezenas: List[int]) -> int:
        score = 0
        dezenas_set = set(dezenas)
        soma = sum(dezenas)

        # --- 1. BASE ESSENCIAL (Até 100 Pontos) ---
        # Regra de Soma (+25 pts)
        s_min = self.stats_soma.get("soma_minima", 170)
        s_max = self.stats_soma.get("soma_maxima", 220)
        if s_min <= soma <= s_max:
            score += 25

        # Regra de Paridade (+25 pts)
        pares = len([n for n in dezenas if n % 2 == 0])
        if pares in self.stats_paridade.get("pares_ideais", [7, 8]):
            score += 25

        # Regra de Primos (+25 pts)
        primos_set = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        primos = len([n for n in dezenas if n in primos_set])
        if primos in self.stats_paridade.get("primos_ideais", [5, 6]):
            score += 25

        # Regra de Sequências Consecutivas (+25 pts)
        max_seq = 1
        atual_seq = 1
        dezenas_ord = sorted(dezenas)
        for i in range(len(dezenas_ord) - 1):
            if dezenas_ord[i+1] == dezenas_ord[i] + 1:
                atual_seq += 1
                if atual_seq > max_seq:
                    max_seq = atual_seq
            else:
                atual_seq = 1

        limite_seq = self.stats_sequencias.get("max_sequencia_consecutiva", 4)
        if max_seq <= limite_seq:
            score += 25

        # --- 2. BÔNUS EXTRA DOS JUIZES (Até +80 Pontos Extra -> Máx 180) ---
        # Bônus Frequência (+20 pts): 6 a 8 dezenas quentes
        quentes = set(self.stats_frequencia.get("quentes", []))
        if 6 <= len(dezenas_set.intersection(quentes)) <= 8:
            score += 20

        # Bônus Moldura (+20 pts): 9 a 11 dezenas na borda
        moldura_set = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        if len(dezenas_set.intersection(moldura_set)) in self.stats_moldura.get("moldura_ideal", [9, 10, 11]):
            score += 20

        # Bônus Ciclo (+20 pts): Presença de dezenas ausentes no ciclo
        ausentes = set(self.stats_ciclos.get("dezenas_ausentes_no_ciclo", [2, 7, 13]))
        if len(dezenas_set.intersection(ausentes)) >= 2:
            score += 20

        # Bônus Repetição Concurso Anterior (+20 pts): 8 a 10 repetidas
        if self.ultimo_concurso:
            if 8 <= len(dezenas_set.intersection(self.ultimo_concurso)) <= 10:
                score += 20

        return score


class CuradorDeSelecaoFinal:
    def __init__(self, validador: CuradorDeValidacao):
        self.validador = validador

    def gerar_bilhetes_diamante(self, quantidade: int = 1, max_interseccao: int = 12) -> Dict[str, Any]:
        bilhetes_aprovados = []
        tentativas = 0
        max_tentativas = 20000  # Ampliado para permitir buscas de até 180 pontos

        while len(bilhetes_aprovados) < quantidade and tentativas < max_tentativas:
            tentativas += 1
            candidato = sorted(random.sample(range(1, 26), 15))
            
            score = self.validador.avaliar_bilhete(candidato)
            if score >= self.validador.score_minimo:
                valido = True
                for b in bilhetes_aprovados:
                    interseccao = len(set(candidato).intersection(set(b)))
                    if interseccao > max_interseccao:
                        valido = False
                        break
                
                if valido:
                    bilhetes_aprovados.append(candidato)

        taxa_eficiencia = (len(bilhetes_aprovados) / tentativas) * 100 if tentativas > 0 else 0

        return {
            "bilhetes": bilhetes_aprovados,
            "tentativas_gastas": tentativas,
            "eficiencia": f"{taxa_eficiencia:.2f}%",
            "score_aplicado": self.validador.score_minimo
        }