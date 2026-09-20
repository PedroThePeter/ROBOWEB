import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# 1. CLASSE DO 3º CURADOR & ENSEMBLE
# =====================================================================
class CuradorLotofacil:
    def __init__(self, taxa_aprendizado=0.05):
        # Freio de mão conservador (2% a 5%)
        self.lr = taxa_aprendizado
        
        # Escala Assimétrica de Recompensa/Punição (O Placar)
        self.escala_recompensa = {
            **{i: -1.0 for i in range(11)},  # 0 a 10 acertos: Punição (-1.0)
            11: 0.0,                         # 11 acertos: Neutro (0.0)
            12: 1.0,                         # 12 acertos: Recompensa leve (+1.0)
            13: 3.0,                         # 13 acertos: Recompensa forte (+3.0)
            14: 10.0,                        # 14 acertos: Recompensa máxima (+10.0)
            15: 10.0                         # 15 acertos: Jackpot (+10.0)
        }
        
        # Pesos Iniciais dos Sub-modelos (Equilibrados)
        self.pesos = {
            'Modelo_Frequencia': 0.333,
            'Modelo_Atrasos': 0.333,
            'Modelo_Padroes': 0.334
        }
        
        # Histórico de Desempenho para Auditoria
        self.historico_pesos = {modelo: [] for modelo in self.pesos.keys()}
        self.historico_acertos_modelos = {modelo: [] for modelo in self.pesos.keys()}
        self.historico_acertos_ensemble = []

    def avaliar_palpite(self, palpite, sorteio_real):
        """Calcula a quantidade de acertos entre o palpite e o sorteio real."""
        return len(set(palpite).intersection(set(sorteio_real)))

    def recalibrar_pesos(self, acertos_rodada):
        """O Coração do 3º Curador: Aplica punição/recompensa e normaliza os pesos."""
        novos_pesos = {}
        
        for modelo, acertos in acertos_rodada.items():
            multiplicador = self.escala_recompensa.get(acertos, -1.0)
            
            # Atualiza o peso garantindo piso mínimo de 1% (evita zerar modelo)
            peso_bruto = max(0.01, self.pesos[modelo] + (multiplicador * self.lr))
            novos_pesos[modelo] = peso_bruto

        # Normalização (Soma total dos pesos sempre = 100%)
        soma_total = sum(novos_pesos.values())
        for modelo in novos_pesos:
            self.pesos[modelo] = novos_pesos[modelo] / soma_total

    def montar_bilhete_ensemble(self, palpites_da_rodada):
        """Aplica Votação Ponderada + Voto de Minerva do Modelo Alfa para o Bilhete Final."""
        pontuacao = {dezena: 0.0 for dezena in range(1, 26)}
        
        # 1. Votação Ponderada pelos Pesos
        for modelo, palpite in palpites_da_rodada.items():
            peso_atual = self.pesos[modelo]
            for dezena in palpite:
                pontuacao[dezena] += peso_atual
                
        # 2. Identifica o Modelo Alfa do momento para critério de desempate
        modelo_alfa = max(self.pesos, key=self.pesos.get)
        palpite_alfa = palpites_da_rodada[modelo_alfa]
        
        # 3. Ordenação por Pontuação + Desempate pelo Modelo Alfa
        ranking = sorted(
            pontuacao.keys(),
            key=lambda d: (pontuacao[d], d in palpite_alfa),
            reverse=True
        )
        
        # 4. Retorna as 15 dezenas definitivas do bilhete
        return sorted(ranking[:15])

    def registrar_historico(self, acertos_rodada, acertos_ensemble):
        """Grava a evolução para gerar o dashboard final."""
        for modelo in self.pesos.keys():
            self.historico_pesos[modelo].append(self.pesos[modelo])
            self.historico_acertos_modelos[modelo].append(acertos_rodada[modelo])
        self.historico_acertos_ensemble.append(acertos_ensemble)


# =====================================================================
# 2. INGESTÃO DE DADOS (EXTRATOR CAIXA)
# =====================================================================
def extrair_dezenas_linha_caixa(caminho_arquivo="Lotofacil.xlsx"):
    """
    Carrega a planilha da Caixa e isola exatamente as 15 dezenas sorteadas de cada concurso.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"⚠️ Arquivo '{caminho_arquivo}' não encontrado. Gerando base simulada para teste...")
        # Fallback para teste caso o arquivo não esteja no diretório local
        return [list(np.random.choice(range(1, 26), 15, replace=False)) for _ in range(3501)]

    print(f"📥 Lendo arquivo oficial: {caminho_arquivo}...")
    df = pd.read_excel(caminho_arquivo)
    
    # Procura colunas que contêm as dezenas (ex: 'Bola1' até 'Bola15' ou colunas numéricas de sorteio)
    colunas_bolas = [col for col in df.columns if 'bola' in str(col).lower() or 'dezena' in str(col).lower()]
    
    if len(colunas_bolas) >= 15:
        df_dezenas = df[colunas_bolas[:15]]
    else:
        # Se não encontrar pelos nomes, pega as 15 últimas colunas com dados numéricos
        df_dezenas = df.select_dtypes(include=[np.number]).iloc[:, -15:]

    historico_sorteios = df_dezenas.dropna().values.astype(int).tolist()
    print(f"✅ Total de {len(historico_sorteios)} concursos oficiais carregados com sucesso.")
    return historico_sorteios


# =====================================================================
# 3. INTERFACE DOS SUB-MODELOS DE IA
# =====================================================================
def gerar_palpite_frequencia(historico):
    """Modelo 1: Seleciona as dezenas mais frequentes do histórico."""
    # Substitua pela sua função real do Modelo de Frequência
    return list(np.random.choice(range(1, 26), 15, replace=False))

def gerar_palpite_atrasos(historico):
    """Modelo 2: Analisa dezenas com maior ciclo de atraso."""
    # Substitua pela sua função real do Modelo de Atrasos
    return list(np.random.choice(range(1, 26), 15, replace=False))

def gerar_palpite_padroes(historico):
    """Modelo 3: Analisa equilíbrio de pares/Ímpares, primos e moldura."""
    # Substitua pela sua função real do Modelo de Padrões
    return list(np.random.choice(range(1, 26), 15, replace=False))


# =====================================================================
# 4. EXECUÇÃO DO WALK-FORWARD BACKTESTING
# =====================================================================
def executar_backtest(caminho_excel="Lotofacil.xlsx", inicio=3000, fim=3500):
    banco_de_dados = extrair_dezenas_linha_caixa(caminho_excel)
    curador = CuradorLotofacil(taxa_aprendizado=0.05)
    
    # Ajusta o limite se a planilha tiver menos concursos
    fim = min(fim, len(banco_de_dados) - 1)
    
    print(f"\n🚀 Iniciando Walk-Forward Backtesting (Concursos {inicio} a {fim})...")
    
    for concurso_atual in range(inicio, fim + 1):
        # 1. Evita Data Leakage (Treina apenas com os dados até o concurso anterior)
        historico_disponivel = banco_de_dados[:concurso_atual]
        sorteio_real = banco_de_dados[concurso_atual]
        
        # 2. As IAs geram seus palpites
        palpites_da_rodada = {
            'Modelo_Frequencia': gerar_palpite_frequencia(historico_disponivel),
            'Modelo_Atrasos': gerar_palpite_atrasos(historico_disponivel),
            'Modelo_Padroes': gerar_palpite_padroes(historico_disponivel)
        }
        
        # 3. O Curador gera o Bilhete Final (Ensemble) antes do sorteio
        bilhete_ensemble = curador.montar_bilhete_ensemble(palpites_da_rodada)
        
        # 4. Sorteio acontece: Auditoria de acertos
        acertos_ensemble = curador.avaliar_palpite(bilhete_ensemble, sorteio_real)
        
        acertos_modelos = {}
        for modelo, palpite in palpites_da_rodada.items():
            acertos_modelos[modelo] = curador.avaliar_palpite(palpite, sorteio_real)
            
        # 5. O 3º Curador recalibra os pesos para o próximo concurso
        curador.recalibrar_pesos(acertos_modelos)
        curador.registrar_historico(acertos_modelos, acertos_ensemble)

        if (concurso_atual - inicio + 1) % 100 == 0 or concurso_atual == fim:
            print(f"⏳ Processado concurso {concurso_atual}/{fim} | Média Ensemble: {np.mean(curador.historico_acertos_ensemble):.2f} pts")

    # =====================================================================
    # 5. DASHBOARD E RELATÓRIO FINAL
    # =====================================================================
    print("\n" + "="*50)
    print("🏁 RESULTADO FINAL DO TREINAMENTO (CONCURSO " + str(fim) + ")")
    print("="*50)
    print("Pesos finais calibrados para o próximo jogo real:")
    for modelo, peso in curador.pesos.items():
        print(f" • {modelo}: {peso*100:.2f}% de relevância")
        
    print("\nDesempenho Médio no Backtest (500 jogos):")
    print(f" 🎯 BILHETE ENSEMBLE (OFICIAL): {np.mean(curador.historico_acertos_ensemble):.2f} acertos/jogo")
    for modelo, acertos in curador.historico_acertos_modelos.items():
        print(f"   - {modelo}: {np.mean(acertos):.2f} acertos/jogo")

    # Plota o gráfico de evolução dos pesos
    plt.figure(figsize=(12, 5))
    for modelo, evolucao in curador.historico_pesos.items():
        plt.plot(range(inicio, fim + 1), [p * 100 for p in evolucao], label=modelo, linewidth=2)
    
    plt.title("Evolução dos Pesos de Confiança (3º Curador) - Walk-Forward", fontsize=12)
    plt.xlabel("Concursos da Lotofácil")
    plt.ylabel("Peso de Confiança (%)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    executar_backtest(caminho_excel="Lotofacil.xlsx", inicio=3000, fim=3500)