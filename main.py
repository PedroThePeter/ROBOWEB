import os
import requests
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importa as classes do seu motor de inteligência estatística
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = FastAPI(title="Lotofácil Engine API", version="2.0")

# Configuração de CORS para permitir requisições do app.jsx (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NOME_ARQUIVO = "Lotofacil.xlsx"

# Helper para carregar/instanciar o engine a partir do Excel local
def carregar_engine():
    if os.path.exists(NOME_ARQUIVO):
        df = pd.read_excel(NOME_ARQUIVO)
        return LotofacilEngine(df), df
    else:
        raise FileNotFoundError(f"Arquivo '{NOME_ARQUIVO}' não foi encontrado na pasta raiz.")

# Instancia o engine e o dataframe globalmente no arranque da API
engine, df_lotofacil = carregar_engine()


# --- MODELOS DE DADOS (Pydantic) ---
class RequisicaoGerarJogos(BaseModel):
    quantidade: int = 1
    score_minimo: int = 80
    max_interseccao: int = 12


# --- ROTAS DA API ---

@app.get("/api/estatisticas")
def obter_estatisticas():
    """Retorna o relatório resumido dos 6 Juízes para a interface React"""
    return {
        "total_concursos": len(engine.df),
        "frequencia": engine.juiz_de_frequencia(),
        "ciclos": engine.juiz_de_padroes_e_ciclos(),
        "paridade": engine.juiz_de_paridade_e_primos(),
        "soma": engine.juiz_de_soma_e_amplitude(),
        "sequencias": engine.juiz_de_sequencias_e_repeticoes(),
        "moldura": engine.juiz_de_moldura_e_miolo()
    }


@app.post("/api/gerar-jogos")
def gerar_jogos(req: RequisicaoGerarJogos):
    """Gera os Bilhetes Diamante submetendo-os aos Juízes e aos Curadores em cadeia"""
    validador = CuradorDeValidacao(engine=engine, score_minimo=req.score_minimo)
    gerador = CuradorDeSelecaoFinal(engine=engine, validador=validador)
    
    resultado = gerador.gerar_bilhetes_diamante(
        quantidade=req.quantidade, 
        max_interseccao=req.max_interseccao
    )
    return resultado


# =========================================================================
# SOLUÇÃO 1: ATUALIZAÇÃO AUTOMÁTICA VIA API DA CAIXA
# =========================================================================
@app.post("/api/atualizar-base")
def atualizar_base_caixa():
    """
    Busca o resultado do concurso mais recente na API oficial da Caixa.
    Se houver novo concurso, grava no Lotofacil.xlsx e recarrega o Engine.
    """
    global engine, df_lotofacil
    
    try:
        # 1. Consulta a API pública da Caixa Econômica Federal
        url_caixa = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
        
        # O parâmetro verify=False evita travamentos por certificado SSL do servidor governamental
        response = requests.get(url_caixa, timeout=10, verify=False)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, 
                detail="Não foi possível conectar ao servidor da Caixa."
            )
            
        dados_caixa = response.json()
        ultimo_concurso_caixa = dados_caixa["numero"]
        dezenas_sorteadas = [int(d) for d in dados_caixa["listaDezenas"]]
        
        # 2. Verifica o concurso mais atual gravado na planilha local
        if "Concurso" in df_lotofacil.columns:
            ultimo_concurso_local = int(df_lotofacil["Concurso"].max())
        else:
            ultimo_concurso_local = len(df_lotofacil)

        # Se já estiver atualizado, interrompe e avisa a interface
        if ultimo_concurso_caixa <= ultimo_concurso_local:
            return {
                "sucesso": True,
                "mensagem": f"A base já está 100% atualizada com o concurso {ultimo_concurso_local}!",
                "total_concursos": len(df_lotofacil),
                "novo_sorteio_adicionado": False
            }

        # 3. Monta a nova linha de dados mantendo a estrutura da planilha
        nova_linha = {"Concurso": ultimo_concurso_caixa}
        
        # Estrutura padrão de colunas Bola1 a Bola15 com as dezenas sorteadas
        for idx, dezena in enumerate(sorted(dezenas_sorteadas), start=1):
            nova_linha[f"Bola{idx}"] = dezena

        # 4. Concatena e salva de volta no arquivo Excel
        df_novo = pd.concat([df_lotofacil, pd.DataFrame([nova_linha])], ignore_index=True)
        df_novo.to_excel(NOME_ARQUIVO, index=False)

        # 5. Atualiza a memória global e recarrega o engine estatístico
        df_lotofacil = df_novo
        engine = LotofacilEngine(df_lotofacil)

        return {
            "sucesso": True,
            "mensagem": f"Sucesso! Concurso {ultimo_concurso_caixa} adicionado à base.",
            "total_concursos": len(df_lotofacil),
            "novo_sorteio_adicionado": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao sincronizar com a Caixa: {str(e)}"
        )