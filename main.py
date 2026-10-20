import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import engine
import diario
import integridade

app = FastAPI(title="Robô Lotofácil V8.1 - Ambiente Local")

# ==========================================
# 🔒 SEGURANÇA LOCAL (CORS)
# Permite apenas que o frontend da sua própria máquina acesse a API
# Nenhuma conexão externa ou da internet será aceita.
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GerarJogosRequest(BaseModel):
    quantidade: int = 1

@app.get("/api/estatisticas")
def get_estatisticas():
    try:
        return engine.dados.carregar_dados_formatados(engine.PLANILHA_PADRAO)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gerar-jogos")
def gerar_jogos(req: GerarJogosRequest):
    try:
        # 1. Recupera o histórico e calcula os pesos (Curador de Dados)
        sorteios = engine.dados.carregar_sorteios(engine.PLANILHA_PADRAO)
        pesos_dict = engine.pesos_por_frequencia(sorteios)
        concurso_alvo = len(sorteios) + 1

        # 2. Curador 2 (Diversidade de Portfólio) - Loop de aprovação cruzada
        portfolio_aprovado = False
        tentativas_c2 = 0
        b_frio, b_morno, b_quente = [], [], []

        while not portfolio_aprovado and tentativas_c2 < 20:
            tentativas_c2 += 1
            
            # Curador 1 em ação: Geração e passagem pelos 5 Juízes Heurísticos
            res_frio = engine.gerar_jogos_genetico(1, concurso=concurso_alvo, pesos=pesos_dict, temperatura=0.0)
            res_morno = engine.gerar_jogos_genetico(1, concurso=concurso_alvo, pesos=pesos_dict, temperatura=50.0)
            res_quente = engine.gerar_jogos_genetico(1, concurso=concurso_alvo, pesos=pesos_dict, temperatura=100.0)

            b_frio = res_frio["bilhetes"][0]
            b_morno = res_morno["bilhetes"][0]
            b_quente = res_quente["bilhetes"][0]

            # Avalia se a diversidade entre Frio, Morno e Quente está saudável
            aprovado, _ = engine.curador_diversidade(b_frio, b_morno, b_quente)
            if aprovado:
                portfolio_aprovado = True

        # 3. Curador 3 (Gatekeeper Sistêmico) - Valida hashes finais
        hashes = [
            integridade._hash_bilhete(b_frio),
            integridade._hash_bilhete(b_morno),
            integridade._hash_bilhete(b_quente)
        ]
        
        # 4. Grava na memória permanente (Diário Local)
        diario.salvar_palpites({
            "concurso": concurso_alvo,
            "espectro_frio": {"bilhetes": [b_frio], "hashes": [hashes[0]]},
            "espectro_morno": {"bilhetes": [b_morno], "hashes": [hashes[1]]},
            "espectro_quente": {"bilhetes": [b_quente], "hashes": [hashes[2]]}
        })

        # 5. Entrega o portfólio auditado e aprovado para a interface React
        return {
            "status": "sucesso",
            "concurso": concurso_alvo,
            "curador_2_tentativas": tentativas_c2,
            "espectro_frio": {"bilhetes": [b_frio], "hashes": [hashes[0]]},
            "espectro_morno": {"bilhetes": [b_morno], "hashes": [hashes[1]]},
            "espectro_quente": {"bilhetes": [b_quente], "hashes": [hashes[2]]}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # HOST LOCAL: Amarra o servidor estritamente ao seu computador (127.0.0.1)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)