import pandas as pd
import numpy as np
import random

class LotofacilEngine:
    def __init__(self, df: pd.DataFrame):
        """
        Recebe o DataFrame de concursos e realiza a limpeza inicial das colunas.
        """
        self.df = df.dropna(how='all').copy()
        self.dezenas_totais = np.arange(1, 26)
        
        # Identificação automática das 15 colunas de resultados
        self.colunas_dezenas = [col for col in self.df.columns if 'Bola' in str(col) or 'Dezena' in str(col)]
        
        if not self.colunas_dezenas or len(self.colunas_dezenas) != 15:
            self.colunas_dezenas = list(self.df.columns[-15:])

    def juiz_de_frequencia(self, janela=20):
        """
        1º JUIZ: Avalia dezenas quentes, frias e o atraso atual.
        """
        df_recente = self.df.tail(janela)[self.colunas_dezenas]
        todas_bolas_sorteadas = df_recente.values.ravel()
        
        frequencias_series = pd.Series(todas_bolas_sorteadas).value_counts()
        frequencias = frequencias_series.reindex(self.dezenas_totais, fill_value=0)

        grid_historico_invertido = self.df[self.colunas_dezenas][::-1].values
        
        atrasos = {}
        for dezena in self.dezenas_totais:
            linhas_encontradas = np.where(grid_historico_invertido == dezena)[0]
            atrasos[int(dezena)] = int(linhas_encontradas[0]) if len(linhas_encontradas) > 0 else len(self.df)

        return {
            "frequencias": {int(k): int(v) for k, v in frequencias.to_dict().items()},
            "atrasos": atrasos,
            "top_5_quentes": [int(x) for x in frequencias.nlargest(5).index],
            "top_5_frias": [int(x) for x in frequencias.nsmallest(5).index],
            "top_5_atrasadas": [int(x) for x in sorted(atrasos, key=atrasos.get, reverse=True)[:5]]
        }

    def juiz_de_padroes_e_ciclos(self):
        """
        2º JUIZ: Monitoriza o fechamento dos ciclos de 25 dezenas.
        """
        grid = self.df[self.colunas_dezenas].values
        
        ciclos_historico = []
        dezenas_ciclo_atual = set()
        concursos_no_ciclo_atual = 0
        
        for linha in grid:
            dezenas_ciclo_atual.update(linha)
            concursos_no_ciclo_atual += 1
            
            if len(dezenas_ciclo_atual) == 25:
                ciclos_historico.append(concursos_no_ciclo_atual)
                dezenas_ciclo_atual.clear()
                concursos_no_ciclo_atual = 0

        todas_dezenas = set(self.dezenas_totais)
        dezenas_faltantes = list(todas_dezenas - dezenas_ciclo_atual)
        
        estado_ciclo = "FECHADO" if concursos_no_ciclo_atual == 0 else "ABERTO"
        
        if estado_ciclo == "FECHADO":
            dezenas_faltantes = list(todas_dezenas)

        media_tamanho_ciclo = float(np.mean(ciclos_historico)) if ciclos_historico else 0.0

        return {
            "estado_ciclo_atual": estado_ciclo,
            "concursos_decorridos_ciclo": int(concursos_no_ciclo_atual),
            "dezenas_faltantes_para_fechar": [int(x) for x in sorted(dezenas_faltantes)],
            "media_duracao_ciclos_historico": round(media_tamanho_ciclo, 2),
            "total_ciclos_fechados": len(ciclos_historico)
        }

    def juiz_de_paridade_e_primos(self):
        """
        3º JUIZ: Avalia a proporção de números pares, ímpares e primos.
        """
        grid = self.df[self.colunas_dezenas].values
        
        pares_por_linha = np.sum(grid % 2 == 0, axis=1)
        primos_set = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        is_primo_grid = np.isin(grid, list(primos_set))
        primos_por_linha = np.sum(is_primo_grid, axis=1)

        dist_pares = pd.Series(pares_por_linha).value_counts()
        dist_primos = pd.Series(primos_por_linha).value_counts()

        top_pares = [int(p) for p in dist_pares.nlargest(4).index]
        top_primos = [int(p) for p in dist_primos.nlargest(4).index]

        return {
            "padroes_ideais": {
                "pares_impares": top_pares,
                "quantidades_primos": top_primos
            },
            "ultimo_concurso": {
                "pares": int(pares_por_linha[-1]),
                "impares": int(15 - pares_por_linha[-1]),
                "primos": int(primos_por_linha[-1])
            }
        }

    def juiz_de_soma_e_amplitude(self):
        """
        4º JUIZ: Analisa a soma total e a amplitude.
        """
        grid = self.df[self.colunas_dezenas].values
        
        somas = np.sum(grid, axis=1)
        amplitudes = np.ptp(grid, axis=1)

        q25, q75 = np.percentile(somas, [25, 75])
        q10, q90 = np.percentile(somas, [10, 90])

        dist_amplitudes = pd.Series(amplitudes).value_counts()
        top_3_amplitudes = [int(a) for a in dist_amplitudes.nlargest(3).index]

        return {
            "ultimo_concurso": {
                "soma": int(somas[-1]),
                "amplitude": int(amplitudes[-1])
            },
            "padroes_ideais": {
                "soma_zona_de_ouro": [int(q25), int(q75)],
                "soma_margem_seguranca": [int(q10), int(q90)],
                "top_3_amplitudes": top_3_amplitudes
            },
            "estatisticas_historicas": {
                "soma_media": round(float(np.mean(somas)), 1),
                "soma_minima_registada": int(np.min(somas)),
                "soma_maxima_registada": int(np.max(somas))
            }
        }

    def juiz_de_sequencias_e_repeticoes(self):
        """
        5º JUIZ: Controla repetições do concurso anterior e sequências consecutivas.
        """
        grid = self.df[self.colunas_dezenas].values
        
        matriz_binaria = np.zeros((len(grid), 25), dtype=bool)
        linhas_idx = np.repeat(np.arange(len(grid)), 15)
        colunas_idx = grid.ravel() - 1
        matriz_binaria[linhas_idx, colunas_idx] = True

        repeticoes_historico = np.sum(matriz_binaria[1:] & matriz_binaria[:-1], axis=1)
        dist_repeticoes = pd.Series(repeticoes_historico).value_counts()
        top_3_repeticoes = [int(r) for r in dist_repeticoes.nlargest(3).index]

        maiores_sequencias = [
            max([len(seq) for seq in np.split(linha, np.where(np.diff(linha) != 1)[0] + 1)]) 
            for linha in grid
        ]
        
        dist_sequencias = pd.Series(maiores_sequencias).value_counts()
        top_3_sequencias = [int(s) for s in dist_sequencias.nlargest(3).index]

        dezenas_ultimo_concurso = [int(x) for x in grid[-1]]
        ultima_repeticao = int(repeticoes_historico[-1]) if len(repeticoes_historico) > 0 else 0
        ultima_sequencia = int(maiores_sequencias[-1])

        return {
            "ultimo_concurso": {
                "dezenas": dezenas_ultimo_concurso,
                "repetidas_do_anterior": ultima_repeticao,
                "maior_sequencia_consecutiva": ultima_sequencia
            },
            "padroes_ideais": {
                "top_3_quantidades_repetidas": top_3_repeticoes,
                "top_3_tamanhos_sequencia": top_3_sequencias
            },
            "distribuicao_historica": {
                "repeticoes": {str(k): int(v) for k, v in dist_repeticoes.items()},
                "sequencias": {str(k): int(v) for k, v in dist_sequencias.items()}
            }
        }

    def juiz_de_moldura_e_miolo(self):
        """
        [AJUSTE 1] 6º JUIZ: Analisa o equilíbrio entre Moldura (bordas) e Miolo (centro).
        Moldura (16 dezenas): 1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25
        Miolo (9 dezenas): 7,8,9,12,13,14,17,18,19
        """
        grid = self.df[self.colunas_dezenas].values
        moldura_set = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
        
        is_moldura_grid = np.isin(grid, list(moldura_set))
        moldura_por_linha = np.sum(is_moldura_grid, axis=1)

        dist_moldura = pd.Series(moldura_por_linha).value_counts()
        top_moldura = [int(m) for m in dist_moldura.nlargest(4).index]

        return {
            "padroes_ideais": {
                "quantidades_moldura": top_moldura
            },
            "ultimo_concurso": {
                "moldura": int(moldura_por_linha[-1]),
                "miolo": int(15 - moldura_por_linha[-1])
            }
        }


class CuradorDeValidacao:
    def __init__(self, stats_ciclos, stats_paridade, stats_soma, stats_sequencias, stats_moldura=None, score_minimo=80):
        """
        Recebe os relatórios dos Juízes e aplica um sistema de pontuação (Score 0 a 100).
        """
        self.ciclos = stats_ciclos
        self.paridade = stats_paridade
        self.soma = stats_soma
        self.sequencias = stats_sequencias
        self.moldura = stats_moldura
        self.score_minimo = score_minimo
        
        self.primos_oficiais = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        self.moldura_oficial = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}

    def avaliar_bilhete(self, bilhete: list) -> tuple:
        """
        [AJUSTE 5] Avaliação baseada em Pontuação (Score de Qualidade Estatística 0-100).
        """
        if len(set(bilhete)) != 15:
            return False, "Rejeitado: O bilhete não contém 15 dezenas únicas."

        bilhete_set = set(bilhete)
        score = 0

        # 1. PARIDADE (Até 15 Pontos)
        qtd_pares = sum(1 for x in bilhete if x % 2 == 0)
        pares_aceites = self.paridade['padroes_ideais']['pares_impares']
        if qtd_pares in pares_aceites:
            score += 15
        elif abs(qtd_pares - pares_aceites[0]) == 1:
            score += 8

        # 2. PRIMOS (Até 15 Pontos)
        qtd_primos = len(bilhete_set.intersection(self.primos_oficiais))
        primos_aceites = self.paridade['padroes_ideais']['quantidades_primos']
        if qtd_primos in primos_aceites:
            score += 15
        elif abs(qtd_primos - primos_aceites[0]) == 1:
            score += 8

        # 3. SOMA TOTAL (Até 20 Pontos)
        soma_total = sum(bilhete)
        soma_ouro_min, soma_ouro_max = self.soma['padroes_ideais']['soma_zona_de_ouro']
        soma_seg_min, soma_seg_max = self.soma['padroes_ideais']['soma_margem_seguranca']
        if soma_ouro_min <= soma_total <= soma_ouro_max:
            score += 20
        elif soma_seg_min <= soma_total <= soma_seg_max:
            score += 12

        # 4. REPETIÇÕES DO CONCURSO ANTERIOR (Até 15 Pontos)
        ultimo_sorteio = set(self.sequencias['ultimo_concurso']['dezenas'])
        qtd_repetidas = len(bilhete_set.intersection(ultimo_sorteio))
        repeticoes_aceites = self.sequencias['padroes_ideais']['top_3_quantidades_repetidas']
        if qtd_repetidas in repeticoes_aceites:
            score += 15
        elif abs(qtd_repetidas - repeticoes_aceites[0]) == 1:
            score += 8

        # 5. SEQUÊNCIAS CONSECUTIVAS (Até 15 Pontos)
        bilhete_ordenado = sorted(list(bilhete))
        max_seq, seq_atual = 1, 1
        for i in range(1, 15):
            if bilhete_ordenado[i] == bilhete_ordenado[i-1] + 1:
                seq_atual += 1
                max_seq = max(max_seq, seq_atual)
            else:
                seq_atual = 1
        
        seqs_aceites = self.sequencias['padroes_ideais']['top_3_tamanhos_sequencia']
        if max_seq <= max(seqs_aceites):
            score += 15
        elif max_seq == max(seqs_aceites) + 1:
            score += 7

        # 6. MOLDURA vs. MIOLO (Até 10 Pontos - AJUSTE 1)
        qtd_moldura = len(bilhete_set.intersection(self.moldura_oficial))
        if self.moldura:
            moldura_aceita = self.moldura['padroes_ideais']['quantidades_moldura']
            if qtd_moldura in moldura_aceita:
                score += 10
            elif abs(qtd_moldura - moldura_aceita[0]) == 1:
                score += 5
        else:
            # Fallback histórico padrão (8, 9, 10 dezenas na moldura)
            if qtd_moldura in [8, 9, 10]:
                score += 10
            elif qtd_moldura in [7, 11]:
                score += 5

        # 7. CICLOS (Até 10 Pontos - AJUSTE 4: Flexibilizado)
        faltam = self.ciclos['dezenas_faltantes_para_fechar']
        if self.ciclos['estado_ciclo_atual'] == "ABERTO" and len(faltam) <= 3:
            interseccao_ciclo = len(set(faltam).intersection(bilhete_set))
            if interseccao_ciclo == len(faltam):
                score += 10  # Incluiu todas as faltantes
            elif interseccao_ciclo >= 1:
                score += 5   # Incluiu ao menos 1 dezena madura
        else:
            score += 10     # Ciclo fechado ou longe de fechar (neutro)

        # APROVAÇÃO FINAL PELO SCORE CORTE
        if score >= self.score_minimo:
            return True, f"Aprovado: Bilhete Diamante Estatístico (Score: {score}/100)."
        else:
            return False, f"Rejeitado: Score insuficiente ({score}/100 - Mínimo exigido: {self.score_minimo})."


class CuradorDeSelecaoFinal:
    def __init__(self, validador, stats_frequencia, stats_ciclos, stats_sequencias, stats_moldura=None):
        self.validador = validador
        self.frequencia = stats_frequencia
        self.ciclos = stats_ciclos
        self.sequencias = stats_sequencias
        self.moldura = stats_moldura
        self.dezenas_totais = set(range(1, 26))

    def gerar_bilhetes_diamante(self, quantidade=3, max_tentativas=10000, max_interseccao=12):
        """
        Gera bilhetes inteligentes com amostragem ponderada, flexibilidade de ciclo e controle de diversidade.
        """
        bilhetes_aprovados = []
        tentativas = 0

        # [AJUSTE 3] Amostragem Ponderada: Cria pesos com base na frequência das dezenas
        freq_dict = self.frequencia.get('frequencias', {})
        
        faltam_ciclo = self.ciclos['dezenas_faltantes_para_fechar']
        ultimo_concurso = set(self.sequencias['ultimo_concurso']['dezenas'])
        top_repeticoes = self.sequencias['padroes_ideais']['top_3_quantidades_repetidas']

        while len(bilhetes_aprovados) < quantidade and tentativas < max_tentativas:
            tentativas += 1
            bilhete_candidato = set()

            # [AJUSTE 4] Ciclo Probabilístico: 70% das vezes força todas as faltantes, 30% força apenas um subconjunto
            if self.ciclos['estado_ciclo_atual'] == "ABERTO" and len(faltam_ciclo) <= 3:
                if random.random() < 0.7:
                    bilhete_candidato.update(faltam_ciclo)
                else:
                    qtd_incluir = max(1, random.randint(1, len(faltam_ciclo)))
                    bilhete_candidato.update(random.sample(faltam_ciclo, qtd_incluir))

            # Variabilidade de Repetições do Concurso Anterior (Sorteia entre o Top 3)
            alvo_repeticoes = random.choice(top_repeticoes)
            disponiveis_ultimo = list(ultimo_concurso - bilhete_candidato)
            repetidas_ja_incluidas = len(bilhete_candidato.intersection(ultimo_concurso))
            faltam_repetir = alvo_repeticoes - repetidas_ja_incluidas

            if faltam_repetir > 0 and len(disponiveis_ultimo) >= faltam_repetir:
                escolhidas_ultimo = random.sample(disponiveis_ultimo, faltam_repetir)
                bilhete_candidato.update(escolhidas_ultimo)

            # [AJUSTE 3] Preenchimento Restante via Amostragem Ponderada por Frequência
            dezenas_restantes = list(self.dezenas_totais - bilhete_candidato)
            vagas_restantes = 15 - len(bilhete_candidato)

            if vagas_restantes > 0:
                pesos = np.array([freq_dict.get(n, 1) + 1.0 for n in dezenas_restantes], dtype=float)
                pesos /= pesos.sum()
                
                escolhidas_finais = np.random.choice(
                    dezenas_restantes, size=vagas_restantes, replace=False, p=pesos
                )
                bilhete_candidato.update([int(x) for x in escolhidas_finais])

            bilhete_lista = [int(x) for x in sorted(list(bilhete_candidato))]

            # Submete ao Validador com Score
            aprovado, motivo = self.validador.avaliar_bilhete(bilhete_lista)

            # [AJUSTE 2] Controle de Diversidade (Garante máxima intersecção permitida entre bilhetes)
            if aprovado:
                eh_diverso = True
                for b_existente in bilhetes_aprovados:
                    if len(set(bilhete_lista).intersection(set(b_existente))) > max_interseccao:
                        eh_diverso = False
                        break
                
                if eh_diverso and bilhete_lista not in bilhetes_aprovados:
                    bilhetes_aprovados.append(bilhete_lista)

        return {
            "bilhetes": bilhetes_aprovados,
            "tentativas_gastas": int(tentativas),
            "eficiencia": f"{(len(bilhetes_aprovados) / tentativas) * 100:.2f}%" if tentativas > 0 else "0%"
        }