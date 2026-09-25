import os
import pandas as pd
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine import LotofacilGeneticEngine

app = FastAPI(title="Lotofácil Engine API", version="6.0 - Comitê Genético")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NOME_ARQUIVO = "Lotofacil.xlsx"

def carregar_engine():
    if os.path.exists(NOME_ARQUIVO):
        df = pd.read_excel(NOME_ARQUIVO)
        return LotofacilGeneticEngine(df), df
    else:
        raise RuntimeError(f"Arquivo '{NOME_ARQUIVO}' não foi encontrado.")

engine, df_lotofacil = carregar_engine()


class RequisicaoGerarJogos(BaseModel):
    quantidade: Optional[int] = 1


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "Lotofácil API v6.0 (Comitê Genético Ativo. Score fixado em 150).",
        "concursos_carregados": len(engine.df)
    }


@app.get("/api/estatisticas")
def obter_estatisticas():
    try:
        comite = engine.comite_de_horizontes()
        return {
            "total_concursos": len(engine.df),
            "comite_horizontes": comite
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@app.post("/api/gerar-jogos")
def gerar_jogos(req: RequisicaoGerarJogos):
    try:
        qtd = req.quantidade if req.quantidade is not None else 1
        return engine.executar_geracao_genetica(quantidade_desejada=qtd, score_minimo=150)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha na geração genética: {str(e)}")


@app.post("/api/recarregar-base")
def recarregar_base_local():
    global engine, df_lotofacil
    try:
        if os.path.exists(NOME_ARQUIVO):
            df_lotofacil = pd.read_excel(NOME_ARQUIVO)
            engine = LotofacilGeneticEngine(df_lotofacil)
            return {"sucesso": True, "mensagem": f"Base recarregada: {len(df_lotofacil)} concursos."}
        else:
            return {"sucesso": False, "mensagem": "Arquivo não encontrado."}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}