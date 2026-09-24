import pandas as pd
import random
from typing import List, Dict, Any

class LotofacilEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.colunas_dezenas = self._identificar_colunas()

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
                if 1 <= num <= 25:
                    dezenas.append(num)
            except (ValueError, TypeError):
                continue
        return dezenas

    def juiz_de_frequencia(self) -> Dict[str, Any]:
        total_sorteios = len(self.df)
        contagem = {}
        for i in range(1, 26):
            soma = 0
            for col in self.colunas_dezenas:
                soma += (pd.to_numeric(self.df[col], errors='coerce') == i).sum()
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
        return {
            "estado": "Ciclo Ativo",
            "dezenas_ausentes_no_ciclo": [2, 7, 13]
        }

    def juiz_de_paridade_e_primos(self) -> Dict[str, Any]:
        return {
            "pares_ideais": [7, 8],
            "impares_ideais": [7, 8],
            "primos_ideais": [5, 6]
        }

    def juiz_de_soma_e_amplitude(self) -> Dict[str, Any]:
        return {
            "soma_minima": 170,
            "soma_maxima": 220,
            "soma_ideal_media": 195
        }

    def juiz_de_sequencias_e_repeticoes(self) -> Dict[str, Any]:
        return {
            "max_sequencia_consecutiva": 4,
            "repetidas_ultimo_concurso_ideal": [8, 9, 10]
        }

    def juiz_de_moldura_e_miolo(self) -> Dict[str, Any]:
        return {
            "moldura_ideal": [9, 10, 11],
            "miolo_ideal": [4, 5, 6]
        }

    # --- NOVOS JUIZES ADICIONADOS ---
    def juiz_de_fibonacci(self) -> Dict[str, Any]:
        """Acompanha dezenas da Sequência de Fibonacci (1, 2, 3, 5, 8, 13, 21)."""
        return {
            "fibonacci_ideais": [3, 4, 5],
            "dezenas_fibonacci": [1, 2, 3, 5, 8, 13, 21]
        }

    def juiz_de_multiplos_de_tres(self) -> Dict[str, Any]:
        """Acompanha dezenas múltiplas de 3 (3, 6, 9, 12, 15, 18, 21, 24)."""
        return {
            "multiplos_ideais": [4, 5, 6],
            "dezenas_multiplos_3": [3, 6, 9, 12, 15, 18, 21, 24]
        }


class CuradorDeValidacao:
    def __init__(self, stats_frequencia, stats_ciclos, stats_paridade, stats_soma, 
                 stats_sequencias, stats_moldura, stats_fibonacci, stats_multiplos, 
                 ultimo_concurso: List[int], score_minimo: int = 160):
        self.stats_frequencia = stats_frequencia
        self.stats_ciclos = stats_ciclos
        self.stats_paridade = stats_paridade
        self.stats_soma = stats_soma
        self.stats_sequencias = stats_sequencias
        self.stats_moldura = stats_moldura
        self.stats_fibonacci = stats_fibonacci
        self.stats_multiplos = stats_multiplos
        self.ultimo_concurso = set(ultimo_concurso)
        self.score_minimo = score_minimo

    def avaliar_bilhete(self, dezenas: List[int]) -> int:
        score = 0
        dezenas_set = set(dezenas)
        soma = sum(dezenas)

        # --- 1. BASE ESSENCIAL (Até 100 Pontos) ---
        s_min = self.stats_soma.get("soma_minima", 170)
        s_max = self.stats_soma.get("soma_maxima", 220)
        if s_min <= soma <= s_max:
            score += 25

        pares = len([n for n in dezenas if n % 2 == 0])
        if pares in self.stats_paridade.get("pares_ideais", [7, 8]):
            score += 25

        primos_set = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        primos = len([n for n in dezenas if n in primos_set])
        if primos in self.stats_paridade.get("primos_ideais", [5, 6]):
            score += 25

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

        # --- 2. BÔNUS EXTRA DOS JUIZES ANTERIORES (Até +80 Pontos) ---
        quentes = set(self.stats_frequencia.get("quentes", []))
        if 6 <= len(dezenas_set.intersection(quentes)) <= 8:
            score += 20

        moldura_set = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        if len(dezenas_set.intersection(moldura_set)) in self.stats_moldura.get("moldura_ideal", [9, 10, 11]):
            score += 20

        ausentes = set(self.stats_ciclos.get("dezenas_ausentes_no_ciclo", [2, 7, 13]))
        if len(dezenas_set.intersection(ausentes)) >= 2:
            score += 20

        if self.ultimo_concurso:
            if 8 <= len(dezenas_set.intersection(self.ultimo_concurso)) <= 10:
                score += 20

        # --- 3. BÔNUS DOS NOVOS JUIZES (Até +40 Pontos -> TETO TOTAL: 220) ---
        fib_set = set(self.stats_fibonacci.get("dezenas_fibonacci", [1, 2, 3, 5, 8, 13, 21]))
        if len(dezenas_set.intersection(fib_set)) in self.stats_fibonacci.get("fibonacci_ideais", [3, 4, 5]):
            score += 20

        mult_set = set(self.stats_multiplos.get("dezenas_multiplos_3", [3, 6, 9, 12, 15, 18, 21, 24]))
        if len(dezenas_set.intersection(mult_set)) in self.stats_multiplos.get("multiplos_ideais", [4, 5, 6]):
            score += 20

        return score


class CuradorDeSelecaoFinal:
    def __init__(self, validador: CuradorDeValidacao):
        self.validador = validador

    def gerar_bilhetes_diamante(self, quantidade: int = 1, max_interseccao: int = 12) -> Dict[str, Any]:
        bilhetes_aprovados = []
        tentativas = 0
        max_tentativas = 20000 

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