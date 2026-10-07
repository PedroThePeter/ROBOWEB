import os
import time
from collections import Counter, defaultdict
import statistics

import engine
from dados import carregar_sorteios

PLANILHA_PADRAO = "Lotofacil.xlsx"
JANELA_INICIAL_WARMUP = 100  # Mínimo de concursos para estabilizar frequências estatísticas


def executar_walk_forward():
    if not os.path.exists(PLANILHA_PADRAO):
        print(f"❌ Erro: Planilha '{PLANILHA_PADRAO}' não foi encontrada na raiz do projeto.")
        return

    print("📊 Carregando histórico completo de sorteios...")
    sorteios = carregar_sorteios(PLANILHA_PADRAO)
    total_sorteios = len(sorteios)

    if total_sorteios <= JANELA_INICIAL_WARMUP:
        print(f"❌ Erro: A planilha possui apenas {total_sorteios} concursos. É necessário mais de {JANELA_INICIAL_WARMUP}.")
        return

    print(f"✅ {total_sorteios} concursos carregados com sucesso!")
    print(f"🔬 Iniciando Backtest Walk-Forward do Concurso {JANELA_INICIAL_WARMUP + 1} até {total_sorteios}...")
    print("--------------------------------------------------------------------------------")

    # Estruturas para métricas de acertos por temperatura
    estatisticas = {
        "espectro_frio": defaultdict(int),
        "espectro_morno": defaultdict(int),
        "espectro_quente": defaultdict(int)
    }
    
    lista_acertos = {
        "espectro_frio": [],
        "espectro_morno": [],
        "espectro_quente": []
    }

    inicio_tempo = time.time()
    total_simulado = 0

    # LOOP WALK-FORWARD (Inicia após a janela de aquecimento)
    for i in range(JANELA_INICIAL_WARMUP, total_sorteios):
        historico_passado = sorteios[:i]
        sorteio_real = set(sorteios[i])
        num_concurso_alvo = i + 1

        # 1. Extrai pesos usando apenas o passado (Out-of-Sample)
        pesos_dict = engine.pesos_por_frequencia(historico_passado)

        # 2. Gera os bilhetes do portfólio aplicando o Curador 2 (Diversidade)
        portfolio_aprovado = False
        tentativas_c2 = 0
        b_frio, b_morno, b_quente = [], [], []

        while not portfolio_aprovado and tentativas_c2 < 20:
            tentativas_c2 += 1
            
            # Geração com Curador 1 (3 Juízes Heurísticos) por temperatura
            res_frio = engine.gerar_jogos_genetico(1, concurso=num_concurso_alvo, pesos=pesos_dict, temperatura=0.0)
            res_morno = engine.gerar_jogos_genetico(1, concurso=num_concurso_alvo, pesos=pesos_dict, temperatura=50.0)
            res_quente = engine.gerar_jogos_genetico(1, concurso=num_concurso_alvo, pesos=pesos_dict, temperatura=100.0)

            b_frio = res_frio["bilhetes"][0]
            b_morno = res_morno["bilhetes"][0]
            b_quente = res_quente["bilhetes"][0]

            aprovado, _ = engine.curador_diversidade(b_frio, b_morno, b_quente)
            if aprovado:
                portfolio_aprovado = True

        # 3. Conferência de Acertos contra o resultado real do concurso i
        acertos_frio = len(set(b_frio) & sorteio_real)
        acertos_morno = len(set(b_morno) & sorteio_real)
        acertos_quente = len(set(b_quente) & sorteio_real)

        # 4. Gravação dos dados estatísticos
        estatisticas["espectro_frio"][acertos_frio] += 1
        estatisticas["espectro_morno"][acertos_morno] += 1
        estatisticas["espectro_quente"][acertos_quente] += 1

        lista_acertos["espectro_frio"].append(acertos_frio)
        lista_acertos["espectro_morno"].append(acertos_morno)
        lista_acertos["espectro_quente"].append(acertos_quente)

        total_simulado += 1

        # Feedback visual a cada 500 concursos processados
        if total_simulado % 500 == 0 or i == total_sorteios - 1:
            tempo_decorrido = time.time() - inicio_tempo
            print(f"⌛ Processados: {total_simulado}/{total_sorteios - JANELA_INICIAL_WARMUP} concursos... ({tempo_decorrido:.1f}s)")

    tempo_total = time.time() - inicio_tempo

    # ==========================================
    # 📈 RELATÓRIO FINAL DE PERFORMANCE
    # ==========================================
    print("\n" + "=" * 80)
    print(" 🏆 RELATÓRIO FINAL DO BACKTEST WALK-FORWARD (PIPELINE v8.1)")
    print("=" * 80)
    print(f"• Total de Concursos Analisados: {total_simulado}")
    print(f"• Tempo Total de Processamento: {tempo_total:.2f} segundos")
    print(f"• Média Teórica Aleatória de Acertos: 9.00 dezenas")
    print("-" * 80)

    for temp_nome, rotulo in [
        ("espectro_frio", "🧊 Frio (T=0% - Histórico Determinístico)"),
        ("espectro_morno", "🌤️ Morno (T=50% - Interpolação Estatística)"),
        ("espectro_quente", "🔥 Quente (T=100% - Geometria 7-4-4)")
    ]:
        acertos = lista_acertos[temp_nome]
        dist = estatisticas[temp_nome]
        media = statistics.mean(acertos) if acertos else 0
        desvio = statistics.stdev(acertos) if len(acertos) > 1 else 0
        taxa_premiacao = sum(1 for a in acertos if a >= 11) / len(acertos) * 100

        print(f"\n{rotulo}:")
        print(f"  └─ Média de Acertos: {media:.3f} dezenas (Desvio Padrão: {desvio:.2f})")
        print(f"  └─ Taxa de Bilhetes Premiados (11+ acertos): {taxa_premiacao:.2f}%")
        print("  └─ Distribuição Detalhada de Pontuações:")
        
        for pts in range(15, 8, -1):
            qtd = dist[pts]
            pct = (qtd / total_simulado) * 100
            destaque = " 🎯 [PREMIADO]" if pts >= 11 else ""
            print(f"      • {pts:02d} Pontos: {qtd:5d} bilhetes ({pct:6.2f}%){destaque}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    executar_walk_forward()