import pandas as pd
import numpy as np
import random

class LotofacilEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.dezenas_totais = np.arange(1, 26)
        
        # Identifica colunas de dezenas
        self.colunas_dezenas = [col for col in self.df.columns if 'Bola' in str(col) or 'Dezena' in str(col)]
        if not self.colunas_dezenas or len(self.colunas_dezenas) != 15:
            self.colunas_dezenas = self.df.columns[-15:]

    def juiz_de_frequencia(self, janela=20):
        df_recente = self.df.tail(janela)[self.colunas_dezenas]
        todas_bolas_sorteadas = df_recente.values.ravel()
        frequencias_series = pd.Series(todas_bolas_sorteadas).value_counts()
        frequencias = frequencias_series.reindex(self.dezenas_totais, fill_value=0)

        grid_historico_invertido = self.df[self.colunas_dezenas][::-1].values
        atrasos = {}
        for dezena in self.dezenas_totais:
            linhas_encontradas = np.where(grid_historico_invertido == dezena)[0]
            atrasos[dezena] = int(linhas_encontradas[0]) if len(linhas_encontradas) > 0 else len(self.df)

        return {
            "frequencias": frequencias.to_dict(),
            "atrasos": atrasos,
            "top_5_quentes": frequencias.nlargest(5).index.tolist(),
            "top_5_frias": frequencias.nsmallest(5).index.tolist(),
            "top_5_atrasadas": sorted(atrasos, key=atrasos.get, reverse=True)[:5]
        }

    def juiz_de_padroes_e_ciclos(self):
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

        media_tamanho_ciclo = float(np.mean(ciclos_historico)) if ciclos_historico else 0

        return {
            "estado_ciclo_atual": estado_ciclo,
            "concursos_decorridos_ciclo": concursos_no_ciclo_atual,
            "dezenas_faltantes_para_fechar": sorted(dezenas_faltantes),
            "media_duracao_ciclos_historico": round(media_tamanho_ciclo, 2),
            "total_ciclos_fechados": len(ciclos_historico)
        }

    def juiz_de_paridade_e_primos(self):
        grid = self.df[self.colunas_dezenas].values
        primos_lotofacil = np.array([2, 3, 5, 7, 11, 13, 17, 19, 23])

        pares_por_concurso = np.sum(grid % 2 == 0, axis=1)
        impares_por_concurso = 15 - pares_por_concurso
        primos_por_concurso = np.sum(np.isin(grid, primos_lotofacil), axis=1)

        dist_pares = pd.Series(pares_por_concurso).value_counts()
        dist_primos = pd.Series(primos_por_concurso).value_counts()

        top_3_padroes_pares = dist_pares.nlargest(3).index.tolist()
        top_3_padroes_primos = dist_primos.nlargest(3).index.tolist()

        return {
            "ultimo_concurso": {
                "pares": int(pares_por_concurso[-1]),
                "impares": int(impares_por_concurso[-1]),
                "primos": int(primos_por_concurso[-1])
            },
            "padroes_ideais": {
                "pares_impares": [f"{p} Pares / {15-p} Ímpares" for p in top_3_padroes_pares],
                "quantidades_primos": [int(p) for p in top_3_padroes_primos]
            },
            "distribuicao_historica": {
                "pares": {str(k): int(v) for k, v in dist_pares.items()},
                "primos": {str(k): int(v) for k, v in dist_primos.items()}
            }
        }

    def juiz_de_soma_e_amplitude(self):
        grid = self.df[self.colunas_dezenas].values
        somas = np.sum(grid, axis=1)
        amplitudes = np.ptp(grid, axis=1)

        q25, q75 = np.percentile(somas, [25, 75])
        q10, q90 = np.percentile(somas, [10, 90])

        dist_amplitudes = pd.Series(amplitudes).value_counts()
        top_3_amplitudes = dist_amplitudes.nlargest(3).index.tolist()

        return {
            "ultimo_concurso": {
                "soma": int(somas[-1]),
                "amplitude": int(amplitudes[-1])
            },
            "padroes_ideais": {
                "soma_zona_de_ouro": [int(q25), int(q75)],
                "soma_margem_seguranca": [int(q10), int(q90)],
                "top_3_amplitudes": [int(a) for a in top_3_amplitudes]
            },
            "estatisticas_historicas": {
                "soma_media": round(float(np.mean(somas)), 1),
                "soma_minima_registada": int(np.min(somas)),
                "soma_maxima_registada": int(np.max(somas))
            }
        }

    def juiz_de_sequencias_e_repeticoes(self):
        grid = self.df[self.colunas_dezenas].values
        matriz_binaria = np.zeros((len(grid), 25), dtype=bool)
        
        linhas_idx = np.repeat(np.arange(len(grid)), 15)
        colunas_idx = grid.ravel() - 1 
        matriz_binaria[linhas_idx, colunas_idx] = True

        repeticoes_historico = np.sum(matriz_binaria[1:] & matriz_binaria[:-1], axis=1)
        dist_repeticoes = pd.Series(repeticoes_historico).value_counts()
        top_3_repeticoes = dist_repeticoes.nlargest(3).index.tolist()

        maiores_sequencias = [
            max([len(seq) for seq in np.split(linha, np.where(np.diff(linha) != 1)[0] + 1)]) 
            for linha in grid
        ]
        
        dist_sequencias = pd.Series(maiores_sequencias).value_counts()
        top_3_sequencias = dist_sequencias.nlargest(3).index.tolist()

        return {
            "ultimo_concurso": {
                "dezenas": [int(x) for x in grid[-1]],
                "repetidas_do_anterior": int(repeticoes_historico[-1]) if len(repeticoes_historico) > 0 else 0,
                "maior_sequencia_consecutiva": int(maiores_sequencias[-1])
            },
            "padroes_ideais": {
                "top_3_quantidades_repetidas": [int(r) for r in top_3_repeticoes],
                "top_3_tamanhos_sequencia": [int(s) for s in top_3_sequencias]
            },
            "distribuicao_historica": {
                "repeticoes": {str(k): int(v) for k, v in dist_repeticoes.items()},
                "sequencias": {str(k): int(v) for k, v in dist_sequencias.items()}
            }
        }

class CuradorDeValidacao:
    def __init__(self, stats_ciclos, stats_paridade, stats_soma, stats_sequencias):
        self.ciclos = stats_ciclos
        self.paridade = stats_paridade
        self.soma = stats_soma
        self.sequencias = stats_sequencias
        self.primos_oficiais = {2, 3, 5, 7, 11, 13, 17, 19, 23}

    def avaliar_bilhete(self, bilhete: list) -> tuple:
        if len(set(bilhete)) != 15:
            return False, "O bilhete não contém 15 dezenas únicas."

        bilhete_set = set(bilhete)
        
        qtd_pares = sum(1 for x in bilhete if x % 2 == 0)
        qtd_impares = 15 - qtd_pares
        qtd_primos = len(bilhete_set.intersection(self.primos_oficiais))
        soma_total = sum(bilhete)
        
        ultimo_sorteio = set(self.sequencias['ultimo_concurso']['dezenas'])
        qtd_repetidas = len(bilhete_set.intersection(ultimo_sorteio))
        
        bilhete_ordenado = sorted(list(bilhete))
        max_seq, seq_atual = 1, 1
        for i in range(1, 15):
            if bilhete_ordenado[i] == bilhete_ordenado[i-1] + 1:
                seq_atual += 1
                max_seq = max(max_seq, seq_atual)
            else:
                seq_atual = 1

        pares_aceites = [int(p.split()[0]) for p in self.paridade['padroes_ideais']['pares_impares']]
        if qtd_pares not in pares_aceites:
            return False, f"Proporção {qtd_pares} Pares / {qtd_impares} Ímpares improvável."

        primos_aceites = self.paridade['padroes_ideais']['quantidades_primos']
        if qtd_primos not in primos_aceites:
            return False, f"Quantidade de primos ({qtd_primos}) foge do padrão."

        soma_min, soma_max = self.soma['padroes_ideais']['soma_margem_seguranca']
        if not (soma_min <= soma_total <= soma_max):
            return False, f"Soma total ({soma_total}) fora da margem aceitável."

        repeticoes_aceites = self.sequencias['padroes_ideais']['top_3_quantidades_repetidas']
        if qtd_repetidas not in repeticoes_aceites:
            return False, f"Repetições do anterior ({qtd_repetidas}) fora do padrão."

        seqs_aceites = self.sequencias['padroes_ideais']['top_3_tamanhos_sequencia']
        if max_seq > max(seqs_aceites):
            return False, f"Sequência consecutiva muito longa ({max_seq})."

        faltam = self.ciclos['dezenas_faltantes_para_fechar']
        if self.ciclos['estado_ciclo_atual'] == "ABERTO" and len(faltam) <= 3:
            if not set(faltam).issubset(bilhete_set):
                return False, f"Ignorou dezenas maduras de fim de ciclo."

        return True, "Diamante Estatístico"

class CuradorDeSelecaoFinal:
    def __init__(self, validador, stats_frequencia, stats_ciclos, stats_sequencias):
        self.validador = validador
        self.frequencia = stats_frequencia
        self.ciclos = stats_ciclos
        self.sequencias = stats_sequencias
        self.dezenas_totais = set(range(1, 26))

    def gerar_bilhetes_diamante(self, quantidade=3, max_tentativas=10000):
        bilhetes_aprovados = []
        tentativas = 0
        dezenas_obrigatorias = set()
        
        faltam_ciclo = self.ciclos['dezenas_faltantes_para_fechar']
        if self.ciclos['estado_ciclo_atual'] == "ABERTO" and len(faltam_ciclo) <= 3:
            dezenas_obrigatorias.update(faltam_ciclo)

        ultimo_concurso = set(self.sequencias['ultimo_concurso']['dezenas'])
        alvo_repeticoes = self.sequencias['padroes_ideais']['top_3_quantidades_repetidas'][0]

        while len(bilhetes_aprovados) < quantidade and tentativas < max_tentativas:
            tentativas += 1
            bilhete_candidato = set(dezenas_obrigatorias)
            
            disponiveis_ultimo = list(ultimo_concurso - bilhete_candidato)
            repetidas_ja_incluidas = len(bilhete_candidato.intersection(ultimo_concurso))
            faltam_repetir = alvo_repeticoes - repetidas_ja_incluidas
            
            if faltam_repetir > 0 and len(disponiveis_ultimo) >= faltam_repetir:
                escolhidas_ultimo = random.sample(disponiveis_ultimo, faltam_repetir)
                bilhete_candidato.update(escolhidas_ultimo)

            dezenas_restantes = list(self.dezenas_totais - bilhete_candidato)
            vagas_restantes = 15 - len(bilhete_candidato)
            
            if vagas_restantes > 0:
                escolhidas_finais = random.sample(dezenas_restantes, vagas_restantes)
                bilhete_candidato.update(escolhidas_finais)

            bilhete_lista = sorted(list(bilhete_candidato))
            aprovado, _ = self.validador.avaliar_bilhete(bilhete_lista)
            
            if aprovado and bilhete_lista not in bilhetes_aprovados:
                bilhetes_aprovados.append(bilhete_lista)

        return {
            "bilhetes": bilhetes_aprovados,
            "tentativas_gastas": tentativas,
            "eficiencia": f"{(len(bilhetes_aprovados) / tentativas) * 100:.2f}%" if tentativas > 0 else "0%"
        }