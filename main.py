import os
import glob
import io
import pandas as pd
import numpy as np
import requests
import urllib3
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Desativa avisos de SSL ao consultar a API da Caixa na nuvem
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="Robô Lotofácil Inteligente API")

# Habilita CORS para o frontend (React) conseguir acessar a API na web sem bloqueios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado Global na Memória
FILE_NAME_OFFICIAL = "historico_oficial.xlsx"
dataframe_global: Optional[pd.DataFrame] = None
ultimo_concurso_global: Optional[List[int]] = None
ultimo_numero_concurso: int = 0
session_id_global: str = "sessao_oficial"


def extrair_dezenas_linha(row) -> List[int]:
    """ Extrai as 15 dezenas de uma linha do DataFrame """
    numeros = []
    for val in row:
        try:
            num = int(val)
            if 1 <= num <= 25:
                numeros.append(num)
        except (ValueError, TypeError):
            continue
    return sorted(numeros[-15:]) if len(numeros) >= 15 else sorted(numeros)


def carregar_e_sincronizar_base():
    """ Carrega a planilha oficial do disco e busca novos concursos na Caixa """
    global dataframe_global, ultimo_concurso_global, ultimo_numero_concurso
    
    print("Iniciando robô e verificando atualizações...")
    
    if not os.path.exists(FILE_NAME_OFFICIAL):
        arquivos = glob.glob("*.xlsx") + glob.glob("*.csv")
        if arquivos:
            arquivo_base = arquivos[0]
        else:
            print("⚠️ Nenhuma planilha base encontrada. Aguardando envio via upload.")
            return
    else:
        arquivo_base = FILE_NAME_OFFICIAL

    try:
        if arquivo_base.endswith(".csv"):
            df = pd.read_csv(arquivo_base)
        else:
            df = pd.read_excel(arquivo_base)

        dataframe_global = df
        
        ultima_linha = df.iloc[-1].values
        ultimo_concurso_global = extrair_dezenas_linha(ultima_linha)
        
        if "Concurso" in df.columns:
            ultimo_numero_concurso = int(df["Concurso"].dropna().iloc[-1])
        else:
            ultimo_numero_concurso = len(df)

        print(f"📊 Base carregada! Último concurso registrado: #{ultimo_numero_concurso}")

        sincronizar_com_caixa()

    except Exception as e:
        print(f"❌ Erro ao ler planilha inicial: {e}")


def sincronizar_com_caixa():
    """ Consulta a API pública da Caixa fingindo ser um navegador para evitar bloqueios """
    global dataframe_global, ultimo_concurso_global, ultimo_numero_concurso
    
    if ultimo_numero_concurso <= 0:
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://loterias.caixa.gov.br/",
        "Connection": "keep-alive"
    }

    proximo_concurso = ultimo_numero_concurso + 1
    novos_sorteios = []

    print(f"🔎 Buscando o concurso {proximo_concurso} na internet...")

    while True:
        url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/{proximo_concurso}"
        try:
            res = requests.get(url, headers=headers, verify=False, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                lista = data.get("listaDezenas", []) or data.get("dezenasSorteadasOrdemSorteio", [])
                
                dezenas = [int(n) for n in lista]
                if len(dezenas) == 15:
                    dezenas.sort()
                    novos_sorteios.append({
                        "Concurso": proximo_concurso,
                        "Dezenas": dezenas
                    })
                    ultimo_concurso_global = dezenas
                    ultimo_numero_concurso = proximo_concurso
                    print(f"✅ Sucesso! Concurso {proximo_concurso} baixado: {dezenas}")
                    proximo_concurso += 1
                    continue
                    
            elif res.status_code == 404:
                print(f"👍 Tudo atualizado! O concurso {proximo_concurso} ainda não foi sorteado (404).")
                break
            elif res.status_code == 403:
                print(f"🛑 BLOQUEIO CAIXA (403): O IP do Render foi bloqueado ao tentar buscar o concurso {proximo_concurso}.")
                break
            else:
                print(f"⚠️ Falha inesperada. Código da Caixa: {res.status_code}")
                break
                
        except requests.exceptions.Timeout:
            print(f"⏳ Tempo esgotado ao conectar com a Caixa no concurso {proximo_concurso}.")
            break
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            break

    if novos_sorteios and dataframe_global is not None:
        try:
            novas_linhas = []
            for item in novos_sorteios:
                row_dict = {"Concurso": item["Concurso"]}
                for i, d in enumerate(item["Dezenas"], 1):
                    row_dict[f"Bola{i}"] = d
                novas_linhas.append(row_dict)
            
            df_novos = pd.DataFrame(novas_linhas)
            dataframe_global = pd.concat([dataframe_global, df_novos], ignore_index=True)
            
            if FILE_NAME_OFFICIAL.endswith(".csv"):
                dataframe_global.to_csv(FILE_NAME_OFFICIAL, index=False)
            else:
                dataframe_global.to_excel(FILE_NAME_OFFICIAL, index=False)
                
            print(f"🚀 Banco de dados atualizado! +{len(novos_sorteios)} sorteio(s) adicionado(s) à planilha.")
        except Exception as e:
            print(f"⚠️ Erro ao salvar atualização no arquivo: {e}")

    print("✅ Processo de sincronização finalizado!")


# Carrega e sincroniza a base assim que o servidor liga
carregar_e_sincronizar_base()


class GenerateRequest(BaseModel):
    session_id: Optional[str] = "sessao_oficial"
    count: int = 5
    total_numbers: int = 15
    range: int = 25


def gerar_jogos_com_base(df_sub: pd.DataFrame, count: int = 12) -> List[List[int]]:
    """ Gera palpites com base em uma fatia histórica específica do DataFrame """
    if df_sub is None or len(df_sub) == 0:
        return [sorted(np.random.choice(range(1, 26), 15, replace=False).tolist()) for _ in range(count)]

    todas_dezenas = []
    for idx in range(len(df_sub)):
        todas_dezenas.extend(extrair_dezenas_linha(df_sub.iloc[idx].values))
    
    counts = pd.Series(todas_dezenas).value_counts()
    
    pesos = np.ones(25)
    for num in range(1, 26):
        pesos[num - 1] = counts.get(num, 1)
    
    pesos = pesos / pesos.sum()

    jogos = []
    for _ in range(count):
        escolhidos = np.random.choice(range(1, 26), size=15, replace=False, p=pesos)
        jogos.append(sorted([int(x) for x in escolhidos]))

    return jogos


def gerar_jogos_inteligentes(count: int = 5) -> List[List[int]]:
    """ Algoritmo de geração de palpites baseado em toda a base atual """
    return gerar_jogos_com_base(dataframe_global, count=count)


@app.get("/api/status")
def get_status():
    global dataframe_global, ultimo_concurso_global, session_id_global
    
    if dataframe_global is None:
        carregar_e_sincronizar_base()
        
    return {
        "session_id": session_id_global,
        "last_draw": ultimo_concurso_global if ultimo_concurso_global else [],
        "stats": {
            "total_concursos": len(dataframe_global) if dataframe_global is not None else 0,
            "ultimo_concurso": ultimo_numero_concurso
        }
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    global dataframe_global, ultimo_concurso_global, ultimo_numero_concurso
    
    try:
        contents = await file.read()
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        dataframe_global = df
        
        if file.filename.endswith(".csv"):
            df.to_csv(FILE_NAME_OFFICIAL, index=False)
        else:
            df.to_excel(FILE_NAME_OFFICIAL, index=False)
        
        ultima_linha = df.iloc[-1].values
        ultimo_concurso_global = extrair_dezenas_linha(ultima_linha)
        ultimo_numero_concurso = len(df)

        return {
            "session_id": session_id_global,
            "last_draw": ultimo_concurso_global,
            "stats": {"total_concursos": len(df)}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")


@app.post("/api/generate")
def generate_tickets(req: GenerateRequest):
    jogos = gerar_jogos_inteligentes(count=req.count)
    return {"tickets": jogos}


# 🚀 ROTA DE BACKTEST REAL (CRUZAMENTO JOGO A JOGO CONTRA O HISTÓRICO)
@app.post("/api/backtest")
async def run_backtest(
    file: Optional[UploadFile] = File(None),
    test_draws: int = Form(10),
    bets_per_draw: int = Form(12),
    session_id: Optional[str] = Form(None)
):
    global dataframe_global
    
    df = dataframe_global
    if file is not None:
        try:
            contents = await file.read()
            if file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar planilha de backtest: {str(e)}")

    if df is None or len(df) < 2:
        raise HTTPException(status_code=400, detail="Base de dados insuficiente para executar o Backtest.")

    total_concursos = len(df)
    qtd_testes = min(test_draws, total_concursos - 1)
    
    placar = {"11": 0, "12": 0, "13": 0, "14": 0, "15": 0}
    total_apostas = 0

    # Determina o índice de início para testar os últimos N concursos
    inicio_idx = total_concursos - qtd_testes

    for i in range(inicio_idx, total_concursos):
        # Pega somente o histórico PASSADO (até o concurso i-1) para evitar que o robô 'veja o futuro'
        df_historico_passado = df.iloc[:i]
        
        # Concurso real sorteado que servirá de gabarito para a conferência
        resultado_real = set(extrair_dezenas_linha(df.iloc[i].values))

        if len(resultado_real) < 15:
            continue

        # Geramos os palpites usando puramente os dados passados
        bilhetes_gerados = gerar_jogos_com_base(df_historico_passado, count=bets_per_draw)
        total_apostas += len(bilhetes_gerados)

        # Cruzamento real: confere acerto por acerto contra o sorteio oficial
        for bilhete in bilhetes_gerados:
            acertos = len(set(bilhete).intersection(resultado_real))
            if acertos >= 11:
                chave = str(acertos)
                if chave in placar:
                    placar[chave] += 1

    resumo = {
        "total_apostas": total_apostas,
        "11": placar["11"],
        "12": placar["12"],
        "13": placar["13"],
        "14": placar["14"],
        "15": placar["15"]
    }

    return {"resumo": resumo}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)