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

    def juiz_de_atrasos_reais(self) -> Dict[str, Any]:
        """Calcula a ausência consecutiva (atraso) de cada dezena baseado nos últimos concursos."""
        atrasos = {i: 0 for i in range(1, 26)}
        
        for i in range(1, 26):
            count = 0
            # Percorre do último concurso de trás pra frente
            for idx in range(len(self.df)-1, -1, -1):
                row = self.df.iloc[idx][self.colunas_dezenas].values
                dezenas_sorteadas = []
                for val in row:
                    try: dezenas_sorteadas.append(int(val))
                    except: pass
                
                if i in dezenas_sorteadas:
                    break
                count += 1
            atrasos[i] = count
            
        # Dezenas que estão sem sair há 3 ou mais concursos (Pressão de Retorno)
        dezenas_criticas = [k for k, v in atrasos.items() if v >= 3]
        
        return {
            "atrasos": atrasos,
            "dezenas_criticas": dezenas_criticas
        }

    def juiz_de_co_ocorrencia(self) -> Dict[str, Any]:
        """Mapeia quais dezenas andam de mãos dadas (pares fortes) nos últimos 500 concursos."""
        pares = {}
        limite = min(500, len(self.df))
        df_recent = self.df.tail(limite)
        
        for _, row in df_recent.iterrows():
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
                    
        # Extrai os 10 pares que mais saem juntos historicamente
        top_pares = sorted(pares.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            "top_pares": [p[0] for p in top_pares]
        }

    def juiz_de_frequencia(self) -> Dict[str, Any]:
        contagem = {}
        for i in range(1, 26):
            soma = 0
            for col in self.colunas_dezenas:
                soma += (pd.to_numeric(self.df[col], errors='coerce') == i).sum()
            contagem[i] = int(soma)
        ordenados = sorted(contagem.items(), key=lambda x: x[1], reverse=True)
        return {
            "quentes": [item[0] for item in ordenados[:10]],
            "frias": [item[0] for item in ordenados[-5:]]
        }

    def juiz_de_paridade_e_primos(self) -> Dict[str, Any]:
        return {"pares_ideais": [7, 8], "primos_ideais": [5, 6]}

    def juiz_de_soma_e_amplitude(self) -> Dict[str, Any]:
        return {"soma_minima": 170, "soma_maxima": 220}

    def juiz_de_sequencias_e_moldura(self) -> Dict[str, Any]:
        return {"max_sequencia_consecutiva": 4, "moldura_ideal": [9, 10, 11]}


class CuradorDeValidacao:
    def __init__(self, stats_atrasos, stats_co_ocorrencia, stats_frequencia, 
                 stats_paridade, stats_soma, stats_seq_moldura, ultimo_concurso: List[int]):
        self.stats_atrasos = stats_atrasos
        self.stats_co_ocorrencia = stats_co_ocorrencia
        self.stats_frequencia = stats_frequencia
        self.stats_paridade = stats_paridade
        self.stats_soma = stats_soma
        self.stats_seq_moldura = stats_seq_moldura
        self.ultimo_concurso = set(ultimo_concurso)
        # Score fixado arquiteturalmente conforme decisão de projeto
        self.score_minimo = 150 

    def avaliar_bilhete(self, dezenas: List[int]) -> int:
        score = 0
        dezenas_set = set(dezenas)
        soma = sum(dezenas)

        # --- 1. SANEAMENTO BASE (Até 60 Pontos) ---
        if self.stats_soma["soma_minima"] <= soma <= self.stats_soma["soma_maxima"]:
            score += 15
            
        pares = len([n for n in dezenas if n % 2 == 0])
        if pares in self.stats_paridade["pares_ideais"]:
            score += 15
            
        primos = len([n for n in dezenas if n in {2, 3, 5, 7, 11, 13, 17, 19, 23}])
        if primos in self.stats_paridade["primos_ideais"]:
            score += 15
            
        max_seq, atual_seq = 1, 1
        dezenas_ord = sorted(dezenas)
        for i in range(len(dezenas_ord) - 1):
            if dezenas_ord[i+1] == dezenas_ord[i] + 1:
                atual_seq += 1
                max_seq = max(max_seq, atual_seq)
            else:
                atual_seq = 1
        if max_seq <= self.stats_seq_moldura["max_sequencia_consecutiva"]:
            score += 15

        # --- 2. EQUILÍBRIO (Até 30 Pontos) ---
        moldura = len(dezenas_set.intersection({1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}))
        if moldura in self.stats_seq_moldura["moldura_ideal"]:
            score += 15
            
        quentes = set(self.stats_frequencia.get("quentes", []))
        if 5 <= len(dezenas_set.intersection(quentes)) <= 8:
            score += 15

        # --- 3. DINÂMICA PREDITIVA DE ALTA PERFORMANCE (Até 90 Pontos) ---
        # A) Atrasos Reais: Bilhete deve resgatar pelo menos 1 dezena em atraso crítico (se houver)
        criticas = set(self.stats_atrasos.get("dezenas_criticas", []))
        if not criticas or len(dezenas_set.intersection(criticas)) >= 1:
            score += 30

        # B) Co-ocorrência: Bilhete deve conter pelo menos 2 duplas fortes
        top_pares = self.stats_co_ocorrencia.get("top_pares", [])
        pares_presentes = sum(1 for p1, p2 in top_pares if p1 in dezenas_set and p2 in dezenas_set)
        if pares_presentes >= 2:
            score += 30

        # C) Repulsão / Anti-Padrão: Historicamente, 8 a 10 dezenas se repetem. Cortamos os extremos.
        if self.ultimo_concurso:
            repetidas = len(dezenas_set.intersection(self.ultimo_concurso))
            if 8 <= repetidas <= 10:
                score += 30
        else:
            score += 30

        return score


class CuradorDeSelecaoFinal:
    def __init__(self, validador: CuradorDeValidacao):
        self.validador = validador

    def gerar_bilhetes_diamante(self, quantidade: int = 1, max_interseccao: int = 12) -> Dict[str, Any]:
        bilhetes_aprovados = []
        tentativas = 0
        max_tentativas = 30000 

        while len(bilhetes_aprovados) < quantidade and tentativas < max_tentativas:
            tentativas += 1
            candidato = sorted(random.sample(range(1, 26), 15))
            
            score = self.validador.avaliar_bilhete(candidato)
            # Exige RIGOR FIXO implementado no CuradorDeValidacao
            if score >= self.validador.score_minimo:
                valido = True
                for b in bilhetes_aprovados:
                    if len(set(candidato).intersection(set(b))) > max_interseccao:
                        valido = False
                        break
                if valido:
                    bilhetes_aprovados.append(candidato)

        taxa = (len(bilhetes_aprovados) / tentativas) * 100 if tentativas > 0 else 0

        return {
            "bilhetes": bilhetes_aprovados,
            "tentativas_gastas": tentativas,
            "eficiencia": f"{taxa:.3f}%",
            "score_aplicado": self.validador.score_minimo,
            "score_maximo_arquitetura": 180
        }