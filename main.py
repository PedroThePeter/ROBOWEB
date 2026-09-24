import os
import pandas as pd
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = FastAPI(title="Lotofácil Engine API", version="3.5")

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
        raise RuntimeError(f"Arquivo '{NOME_ARQUIVO}' não foi encontrado na pasta raiz do projeto.")

engine, df_lotofacil = carregar_engine()


class RequisicaoGerarJogos(BaseModel):
    quantidade: Optional[int] = 1
    score_minimo: Optional[int] = 140
    max_interseccao: Optional[int] = 12


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "Lotofácil Engine API operacional (Sistema de Score até 180).",
        "concursos_carregados": len(engine.df)
    }


@app.get("/api/estatisticas")
def obter_estatisticas():
    try:
        return {
            "total_concursos": len(engine.df),
            "frequencia": engine.juiz_de_frequencia(),
            "ciclos": engine.juiz_de_padroes_e_ciclos(),
            "paridade": engine.juiz_de_paridade_e_primos(),
            "soma": engine.juiz_de_soma_e_amplitude(),
            "sequencias": engine.juiz_de_sequencias_e_repeticoes(),
            "moldura": engine.juiz_de_moldura_e_miolo()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@app.post("/api/gerar-jogos")
def gerar_jogos(req: RequisicaoGerarJogos):
    try:
        qtd = req.quantidade if req.quantidade is not None else 1
        score = req.score_minimo if req.score_minimo is not None else 140
        interseccao = req.max_interseccao if req.max_interseccao is not None else 12

        stats_frequencia = engine.juiz_de_frequencia()
        stats_ciclos = engine.juiz_de_padroes_e_ciclos()
        stats_paridade = engine.juiz_de_paridade_e_primos()
        stats_soma = engine.juiz_de_soma_e_amplitude()
        stats_sequencias = engine.juiz_de_sequencias_e_repeticoes()
        stats_moldura = engine.juiz_de_moldura_e_miolo()
        ultimo_concurso = engine.obter_ultimo_concurso()

        validador = CuradorDeValidacao(
            stats_frequencia=stats_frequencia,
            stats_ciclos=stats_ciclos,
            stats_paridade=stats_paridade,
            stats_soma=stats_soma,
            stats_sequencias=stats_sequencias,
            stats_moldura=stats_moldura,
            ultimo_concurso=ultimo_concurso,
            score_minimo=score
        )
        
        gerador = CuradorDeSelecaoFinal(validador=validador)
        
        resultado = gerador.gerar_bilhetes_diamante(
            quantidade=qtd, 
            max_interseccao=interseccao
        )
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Falha na geração dos jogos: {str(e)}"
        )


@app.post("/api/recarregar-base")
def recarregar_base_local():
    global engine, df_lotofacil
    try:
        if os.path.exists(NOME_ARQUIVO):
            df_lotofacil = pd.read_excel(NOME_ARQUIVO)
            engine = LotofacilEngine(df_lotofacil)
            return {
                "sucesso": True,
                "mensagem": f"Base recarregada com sucesso! Total de concursos: {len(df_lotofacil)}",
                "total_concursos": len(df_lotofacil)
            }
        else:
            return {
                "sucesso": False,
                "mensagem": f"Arquivo '{NOME_ARQUIVO}' não encontrado."
            }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao recarregar a planilha: {str(e)}"
        }