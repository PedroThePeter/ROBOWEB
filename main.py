import os
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine import LotofacilGeneticEngine
from desdobramento import (
    gerar_desdobramento,
    TAMANHO_MIN_POOL,
    TAMANHO_MAX_POOL,
)

app = FastAPI(title="Lotofácil Engine API", version="8.0 - Portfólio + Desdobramento")

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
    diversidade_minima: Optional[int] = 4
    evitar_populares: Optional[bool] = True
    peso_equilibrio: Optional[float] = 2.0


class RequisicaoDesdobramento(BaseModel):
    dezenas: Optional[List[int]] = None   # se vazio, o robô sugere o grupo
    tamanho_pool: Optional[int] = 17      # usado só quando "dezenas" não é enviado
    garantia: Optional[int] = 14


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "Lotofácil API v8.0 (Portfólio Balanceado + Desdobramento).",
        "concursos_carregados": engine.total_concursos
    }


@app.get("/api/estatisticas")
def obter_estatisticas():
    try:
        comite = engine.comite_de_horizontes()
        return {
            "total_concursos": engine.total_concursos,
            "comite_horizontes": comite
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@app.post("/api/gerar-jogos")
def gerar_jogos(req: RequisicaoGerarJogos):
    try:
        qtd = req.quantidade if req.quantidade is not None else 1
        diversidade = req.diversidade_minima if req.diversidade_minima is not None else 4
        populares = req.evitar_populares if req.evitar_populares is not None else True
        equilibrio = req.peso_equilibrio if req.peso_equilibrio is not None else 2.0
        return engine.executar_geracao_genetica(
            quantidade_desejada=qtd,
            score_minimo=150,
            diversidade_minima=diversidade,
            evitar_populares=populares,
            peso_equilibrio=equilibrio,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha na geração genética: {str(e)}")


@app.post("/api/desdobramento")
def desdobramento(req: RequisicaoDesdobramento):
    try:
        garantia = req.garantia if req.garantia is not None else 14

        if req.dezenas:
            dezenas = req.dezenas
            origem = "informadas manualmente"
        else:
            tamanho = req.tamanho_pool if req.tamanho_pool is not None else 17
            if not (TAMANHO_MIN_POOL <= tamanho <= TAMANHO_MAX_POOL):
                raise ValueError(
                    f"tamanho_pool deve estar entre {TAMANHO_MIN_POOL} e {TAMANHO_MAX_POOL}."
                )
            dezenas = engine.sugerir_pool_dezenas(tamanho)
            origem = "sugeridas pelo robô"

        resultado = gerar_desdobramento(dezenas, garantia)
        resultado["origem_das_dezenas"] = origem
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha no desdobramento: {str(e)}")


@app.post("/api/recarregar-base")
def recarregar_base_local():
    global engine, df_lotofacil
    try:
        if os.path.exists(NOME_ARQUIVO):
            df_lotofacil = pd.read_excel(NOME_ARQUIVO)
            engine = LotofacilGeneticEngine(df_lotofacil)  # instância nova já nasce sem cache
            return {"sucesso": True, "mensagem": f"Base recarregada: {engine.total_concursos} concursos."}
        else:
            return {"sucesso": False, "mensagem": "Arquivo não encontrado."}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}