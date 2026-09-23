import os
import requests
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = FastAPI(title="Lotofácil Engine API", version="2.1")

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
        # Se não houver planilha, cria uma estrutura básica ou levanta erro legível
        raise RuntimeError(f"Arquivo '{NOME_ARQUIVO}' não foi encontrado na pasta raiz.")

engine, df_lotofacil = carregar_engine()


class RequisicaoGerarJogos(BaseModel):
    quantidade: int = 1
    score_minimo: int = 80
    max_interseccao: int = 12


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "Lotofácil Engine API está em execução.",
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
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")


@app.post("/api/gerar-jogos")
def gerar_jogos(req: RequisicaoGerarJogos):
    """
    Gera jogos protegendo a rota contra exceções não tratadas que causam erro 500 sem CORS
    """
    try:
        validador = CuradorDeValidacao(engine=engine, score_minimo=req.score_minimo)
        gerador = CuradorDeSelecaoFinal(engine=engine, validador=validador)
        
        resultado = gerador.gerar_bilhetes_diamante(
            quantidade=req.quantidade, 
            max_interseccao=req.max_interseccao
        )
        return resultado
    except Exception as e:
        # Evita a queda com Erro 500 genérico e envia mensagem clara
        raise HTTPException(
            status_code=400, 
            detail=f"Não foi possível gerar os bilhetes com os parâmetros atuais: {str(e)}"
        )


@app.post("/api/atualizar-base")
def atualizar_base_caixa():
    global engine, df_lotofacil
    
    try:
        url_caixa = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
        
        # Headers mais robustos para evitar o bloqueio 403 da Caixa em servidores na nuvem
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
                "mensagem": "A Caixa bloqueou temporariamente a requisição direta (Erro 403). Tente novamente em alguns instantes."
            }
        elif response.status_code != 200:
            return {
                "sucesso": False,
                "mensagem": f"O servidor da Caixa retornou o código HTTP {response.status_code}."
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
                "mensagem": f"A base já está 100% atualizada com o concurso {ultimo_concurso_local}!",
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
            "mensagem": f"Sucesso! Concurso {ultimo_concurso_caixa} adicionado à base.",
            "total_concursos": len(df_lotofacil),
            "novo_sorteio_adicionado": True
        }

    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Não foi possível sincronizar com a Caixa no momento: {str(e)}"
        }