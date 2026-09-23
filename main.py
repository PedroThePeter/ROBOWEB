import os
import requests
import pandas as pd
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importação dos módulos do motor estatístico
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = FastAPI(title="Lotofácil Engine API", version="2.4")

# Configuração global de CORS
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

# Instanciação global na inicialização
engine, df_lotofacil = carregar_engine()


# Modelo de dados com tipos opcionais e fallbacks seguros
class RequisicaoGerarJogos(BaseModel):
    quantidade: Optional[int] = 1
    score_minimo: Optional[int] = 80
    max_interseccao: Optional[int] = 12


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "Lotofácil Engine API operacional.",
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
        score = req.score_minimo if req.score_minimo is not None else 80
        interseccao = req.max_interseccao if req.max_interseccao is not None else 12

        # Extração correta dos parâmetros exigidos pelo __init__ do CuradorDeValidacao
        stats_ciclos = engine.juiz_de_padroes_e_ciclos()
        stats_paridade = engine.juiz_de_paridade_e_primos()
        stats_soma = engine.juiz_de_soma_e_amplitude()
        stats_sequencias = engine.juiz_de_sequencias_e_repeticoes()

        # Instanciação passando os argumentos posicionais exigidos pela engine
        validador = CuradorDeValidacao(
            stats_ciclos=stats_ciclos,
            stats_paridade=stats_paridade,
            stats_soma=stats_soma,
            stats_sequencias=stats_sequencias,
            score_minimo=score
        )
        
        gerador = CuradorDeSelecaoFinal(validador=validador)
        
        resultado = gerador.gerar_bilhetes_diamante(
            engine=engine,
            quantidade=qtd, 
            max_interseccao=interseccao
        )
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Falha na geração dos jogos: {str(e)}"
        )


@app.post("/api/atualizar-base")
def atualizar_base_caixa():
    global engine, df_lotofacil
    
    try:
        url_caixa = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Host": "servicebus2.caixa.gov.br",
            "Referer": "https://loterias.caixa.gov.br/"
        }
        
        session = requests.Session()
        response = session.get(url_caixa, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 403:
            return {
                "sucesso": False,
                "mensagem": "A Caixa bloqueou temporariamente a requisição (HTTP 403). Tente novamente em alguns minutos."
            }
        elif response.status_code != 200:
            return {
                "sucesso": False,
                "mensagem": f"O servidor da Caixa respondeu com o código HTTP {response.status_code}."
            }
            
        dados_caixa = response.json()
        ultimo_concurso_caixa = dados_caixa["numero"]
        dezenas_sorteadas = [int(d) for d in dados_caixa["listaDezenas"]]
        
        if "Concurso" in df_lotofacil.columns:
            ultimo_concurso_local = int(df_lotofacil["Concurso"].max())
        else:
            ultimo_concurso_local = len(df_lotofacil)

        if ultimo_concurso_caixa <= ultimo_concurso_local:
            return {
                "sucesso": True,
                "mensagem": f"A base já está atualizada até o concurso {ultimo_concurso_local}!",
                "total_concursos": len(df_lotofacil),
                "novo_sorteio_adicionado": False
            }

        nova_linha = {"Concurso": ultimo_concurso_caixa}
        for idx, dezena in enumerate(sorted(dezenas_sorteadas), start=1):
            nova_linha[f"Bola{idx}"] = dezena

        df_novo = pd.concat([df_lotofacil, pd.DataFrame([nova_linha])], ignore_index=True)
        df_novo.to_excel(NOME_ARQUIVO, index=False)

        df_lotofacil = df_novo
        engine = LotofacilEngine(df_lotofacil)

        return {
            "sucesso": True,
            "mensagem": f"Sucesso! Concurso {ultimo_concurso_caixa} sincronizado.",
            "total_concursos": len(df_lotofacil),
            "novo_sorteio_adicionado": True
        }

    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Não foi possível sincronizar no momento: {str(e)}"
        }