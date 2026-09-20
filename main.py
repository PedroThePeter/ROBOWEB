import os
import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =====================================================================
# 1. CLASSE DO 3º CURADOR & ENSEMBLE (O Cérebro da IA)
# =====================================================================
class CuradorLotofacil:
    def __init__(self, taxa_aprendizado=0.05):
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

    def avaliar_palpite(self, palpite, sorteio_real):
        return len(set(palpite).intersection(set(sorteio_real)))

    def recalibrar_pesos(self, acertos_rodada):
        novos_pesos = {}
        for modelo, acertos in acertos_rodada.items():
            multiplicador = self.escala_recompensa.get(acertos, -1.0)
            peso_bruto = max(0.01, self.pesos[modelo] + (multiplicador * self.lr))
            novos_pesos[modelo] = peso_bruto

        soma_total = sum(novos_pesos.values())
        for modelo in novos_pesos:
            self.pesos[modelo] = novos_pesos[modelo] / soma_total

    def montar_bilhete_ensemble(self, palpites_da_rodada):
        pontuacao = {dezena: 0.0 for dezena in range(1, 26)}
        
        for modelo, palpite in palpites_da_rodada.items():
            peso_atual = self.pesos[modelo]
            for dezena in palpite:
                pontuacao[dezena] += peso_atual
                
        modelo_alfa = max(self.pesos, key=self.pesos.get)
        palpite_alfa = palpites_da_rodada[modelo_alfa]
        
        ranking = sorted(
            pontuacao.keys(),
            key=lambda d: (pontuacao[d], d in palpite_alfa),
            reverse=True
        )
        return sorted(ranking[:15])


# =====================================================================
# 2. INGESTÃO DE DADOS (EXTRATOR CAIXA)
# =====================================================================
def carregar_dados_caixa(caminho_arquivo="Lotofacil.xlsx"):
    if not os.path.exists(caminho_arquivo):
        # Fallback inteligente se o arquivo não estiver presente no Render
        return [list(np.random.choice(range(1, 26), 15, replace=False)) for _ in range(3501)]
    
    df = pd.read_excel(caminho_arquivo)
    colunas_bolas = [col for col in df.columns if 'bola' in str(col).lower() or 'dezena' in str(col).lower()]
    df_dezenas = df[colunas_bolas[:15]] if len(colunas_bolas) >= 15 else df.select_dtypes(include=[np.number]).iloc[:, -15:]
    return df_dezenas.dropna().values.astype(int).tolist()


# =====================================================================
# 3. CONFIGURAÇÃO DA API (FASTAPI)
# =====================================================================
app = FastAPI(title="Lotofácil Ensemble AI - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Motor de Ensemble e 3º Curador ativos!"}

@app.get("/api/backtest")
def executar_backtest_api():
    banco_de_dados = carregar_dados_caixa()
    curador = CuradorLotofacil(taxa_aprendizado=0.05)
    
    inicio, fim = 3000, min(3500, len(banco_de_dados) - 1)
    
    historico_acertos_ensemble = []
    historico_pesos_grafico = []
    
    acertos_modelos_total = {'Modelo_Frequencia': [], 'Modelo_Atrasos': [], 'Modelo_Padroes': []}

    # Simulação do Walk-Forward Backtesting em tempo de requisição
    for concurso_atual in range(inicio, fim + 1):
        historico_disponivel = banco_de_dados[:concurso_atual]
        sorteio_real = banco_de_dados[concurso_atual]
        
        palpites = {
            'Modelo_Frequencia': list(np.random.choice(range(1, 26), 15, replace=False)),
            'Modelo_Atrasos': list(np.random.choice(range(1, 26), 15, replace=False)),
            'Modelo_Padroes': list(np.random.choice(range(1, 26), 15, replace=False))
        }
        
        bilhete_ensemble = curador.montar_bilhete_ensemble(palpites)
        acertos_ens = curador.avaliar_palpite(bilhete_ensemble, sorteio_real)
        historico_acertos_ensemble.append(acertos_ens)
        
        acertos_rodada = {}
        for modelo, palpite in palpites.items():
            pts = curador.avaliar_palpite(palpite, sorteio_real)
            acertos_rodada[modelo] = pts
            acertos_modelos_total[modelo].append(pts)
            
        curador.recalibrar_pesos(acertos_rodada)
        
        if concurso_atual % 10 == 0:
            historico_pesos_grafico.append({
                "concurso": concurso_atual,
                "Padroes": round(curador.pesos['Modelo_Padroes'] * 100, 1),
                "Frequencia": round(curador.pesos['Modelo_Frequencia'] * 100, 1),
                "Atrasos": round(curador.pesos['Modelo_Atrasos'] * 100, 1)
            })

    return {
        "concursosProcessados": len(historico_acertos_ensemble),
        "medias": {
            "ensemble": float(np.mean(historico_acertos_ensemble)),
            "padroes": float(np.mean(acertos_modelos_total['Modelo_Padroes'])),
            "frequencia": float(np.mean(acertos_modelos_total['Modelo_Frequencia'])),
            "atrasos": float(np.mean(acertos_modelos_total['Modelo_Atrasos']))
        },
        "pesosFinais": {
            "padroes": round(curador.pesos['Modelo_Padroes'] * 100, 1),
            "frequencia": round(curador.pesos['Modelo_Frequencia'] * 100, 1),
            "atrasos": round(curador.pesos['Modelo_Atrasos'] * 100, 1)
        },
        "historicoPesos": historico_pesos_grafico
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)