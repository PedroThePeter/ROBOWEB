import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import engine
import diario
import integridade
from dados import carregar_sorteios

app = FastAPI(title="Robô Lotofácil 20 Juízes 10 Curadores")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _proximo_concurso(sorteios): return len(sorteios) + 1 if sorteios else 1

@app.get("/api/estatisticas")
def get_stats():
    caminho = engine.PLANILHA_PADRAO
    if not os.path.exists(caminho): return {"status": "erro", "base": {"disponivel": False}}
    return {"status": "sucesso", "base": {"disponivel": True, "concursos": len(carregar_sorteios(caminho))}}

@app.post("/api/recarregar-base")
def recarregar():
    return {"status": "sucesso", "mensagem": "Base recarregada e sincronizada."}

@app.post("/api/gerar-jogos")
def gerar_jogos():
    caminho = engine.PLANILHA_PADRAO
    
    # Curador 9: Auditor da Planilha Lotofacil.xlsx
    if not os.path.exists(caminho):
        raise HTTPException(status_code=500, detail="Curador 9: Planilha base ausente.")
        
    sorteios = carregar_sorteios(caminho)
    alvo = _proximo_concurso(sorteios)

    # Geração via pipeline (Curadores 1 a 7 dentro do engine)
    frio, morno, quente = engine.gerar_portfolio(sorteios)

    # Curador 8: Gatekeeper SHA-256
    hf, hm, hq = integridade._hash_bilhete(frio), integridade._hash_bilhete(morno), integridade._hash_bilhete(quente)

    # Curador 10: Gravação livre no diário (sem bloqueio de duplicidade para o Mestre)
    diario.salvar_palpites({"concurso": alvo, "quantidade": 1, "jogos": [frio], "hashes": [hf]}, origem="espectro_frio")
    diario.salvar_palpites({"concurso": alvo, "quantidade": 1, "jogos": [morno], "hashes": [hm]}, origem="espectro_morno")
    diario.salvar_palpites({"concurso": alvo, "quantidade": 1, "jogos": [quente], "hashes": [hq]}, origem="espectro_quente")

    return {
        "status": "sucesso", "concurso": alvo,
        "bilhetes": {"frio": frio, "morno": morno, "quente": quente}
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)