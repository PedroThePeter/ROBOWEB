import os
import pandas as pd
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = FastAPI(title="Lotofácil Engine API", version="5.0 - Dynamic Logic")

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
        return LotofacilEngine(df), df
    else:
        raise RuntimeError(f"Arquivo '{NOME_ARQUIVO}' não foi encontrado.")

engine, df_lotofacil = carregar_engine()


class RequisicaoGerarJogos(BaseModel):
    quantidade: Optional[int] = 1
    max_interseccao: Optional[int] = 12


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "Lotofácil API v5 (Dinâmica Preditiva Ativa. Score fixado em 150).",
        "concursos_carregados": len(engine.df)
    }


@app.get("/api/estatisticas")
def obter_estatisticas():
    try:
        return {
            "total_concursos": len(engine.df),
            "atrasos_reais": engine.juiz_de_atrasos_reais(),
            "co_ocorrencia": engine.juiz_de_co_ocorrencia(),
            "frequencia": engine.juiz_de_frequencia()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@app.post("/api/gerar-jogos")
def gerar_jogos(req: RequisicaoGerarJogos):
    try:
        qtd = req.quantidade if req.quantidade is not None else 1
        interseccao = req.max_interseccao if req.max_interseccao is not None else 12

        # Executa a inteligência preditiva em tempo real
        validador = CuradorDeValidacao(
            stats_atrasos=engine.juiz_de_atrasos_reais(),
            stats_co_ocorrencia=engine.juiz_de_co_ocorrencia(),
            stats_frequencia=engine.juiz_de_frequencia(),
            stats_paridade=engine.juiz_de_paridade_e_primos(),
            stats_soma=engine.juiz_de_soma_e_amplitude(),
            stats_seq_moldura=engine.juiz_de_sequencias_e_moldura(),
            ultimo_concurso=engine.obter_ultimo_concurso()
        )
        
        gerador = CuradorDeSelecaoFinal(validador=validador)
        
        return gerador.gerar_bilhetes_diamante(quantidade=qtd, max_interseccao=interseccao)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha na geração: {str(e)}")


@app.post("/api/recarregar-base")
def recarregar_base_local():
    global engine, df_lotofacil
    try:
        if os.path.exists(NOME_ARQUIVO):
            df_lotofacil = pd.read_excel(NOME_ARQUIVO)
            engine = LotofacilEngine(df_lotofacil)
            return {"sucesso": True, "mensagem": f"Base recarregada: {len(df_lotofacil)} concursos."}
        else:
            return {"sucesso": False, "mensagem": "Arquivo não encontrado."}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}