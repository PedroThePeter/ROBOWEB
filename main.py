import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Instância principal do FastAPI (deve chamar-se 'app' para corresponder ao comando 'uvicorn main:app')
app = FastAPI(
    title="Robô Web - Lotofácil Ensemble AI",
    description="API de análise estatística e Walk-Forward Backtesting",
    version="1.0.0"
)

# Configuração do CORS para permitir requisições do frontend (Vercel ou local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# Endpoint de verificação de saúde da API
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "API do Robô da Lotofácil ativa no Render!"
    }

# Endpoint principal do Backtest consumido pelo App.jsx
@app.get("/api/backtest")
def executar_backtest():
    # Simulação do histórico de evolução dos pesos ao longo de 50 concursos
    historico_pesos = [
        {
            "concurso": 2950 + i,
            "Padroes": round(40.0 + (i % 10) * 0.9, 1),
            "Frequencia": round(30.0 - (i % 8) * 0.5, 1),
            "Atrasos": round(30.0 - (i % 6) * 0.4, 1)
        }
        for i in range(50)
    ]

    return {
        "concursosProcessados": 500,
        "medias": {
            "ensemble": 11.85,
            "padroes": 10.45,
            "frequencia": 10.12,
            "atrasos": 9.80
        },
        "pesosFinais": {
            "padroes": 49.4,
            "frequencia": 28.5,
            "atrasos": 22.1
        },
        "historicoPesos": historico_pesos
    }

# Bloco para execução local rápida (python main.py)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)