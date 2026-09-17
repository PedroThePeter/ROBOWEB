import os
import glob
import io
import pandas as pd
import numpy as np
import requests
import urllib3
from typing import List, Tuple, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier

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

# Constantes Estatísticas (Regras de Ouro)
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}


# ---------------------------------------------------------
# FUNÇÕES AUXILIARES DE TRATAMENTO DE DADOS
# ---------------------------------------------------------

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


def e_jogo_valido(jogo: List[int], ultimo_resultado: Optional[List[int]] = None) -> bool:
    """ Valida se o palpite cumpre as 'Regras de Ouro' estatísticas da Lotofácil """
    # 1. Soma Total (Faixa ideal: 180 a 220)
    soma = sum(jogo)
    if not (180 <= soma <= 220):
        return False

    # 2. Equilibrio Par / Ímpar (6 a 9 pares)
    pares = len([n for n in jogo if n % 2 == 0])
    if pares not in [6, 7, 8, 9]:
        return False

    # 3. Quantidade na Moldura/Borda (8 a 11 números)
    moldura = len([n for n in jogo if n in MOLDURA])
    if moldura not in [8, 9, 10, 11]:
        return False

    # 4. Quantidade de Primos (4 a 7 primos)
    primos = len([n for n in jogo if n in PRIMOS])
    if primos not in [4, 5, 6, 7]:
        return False

    # 5. Repetição do Último Concurso (8 a 10 repetidos)
    if ultimo_resultado and len(ultimo_resultado) == 15:
        repetidos = len(set(jogo).intersection(set(ultimo_resultado)))
        if repetidos not in [8, 9, 10]:
            return False

    return True


# ---------------------------------------------------------
# SINCRONIZAÇÃO E LEITURA DA PLANILHA / CAIXA
# ---------------------------------------------------------

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


# Inicializa o carregamento no boot
carregar_e_sincronizar_base()


# ---------------------------------------------------------
# MACHINE LEARNING (RANDOM FOREST)
# ---------------------------------------------------------

def extrair_features_e_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """ Converte o histórico de concursos em matrizes de treino (X) e alvos (Y) """
    dezenas_por_concurso = [extrair_dezenas_linha(df.iloc[i].values) for i in range(len(df))]
    
    X, Y = [], []
    janela_minima = 30
    
    for i in range(janela_minima, len(dezenas_por_concurso)):
        historico_passado = dezenas_por_concurso[:i]
        sorteio_atual = set(dezenas_por_concurso[i])
        
        ultimos_10 = historico_passado[-10:]
        ultimos_25 = historico_passado[-25:]
        ultimo_sorteio = set(historico_passado[-1])
        
        features_i = []
        for num in range(1, 26):
            freq_10 = sum(1 for jogo in ultimos_10 if num in jogo) / 10.0
            freq_25 = sum(1 for jogo in ultimos_25 if num in jogo) / 25.0
            saiu_ultimo = 1 if num in ultimo_sorteio else 0
            
            atraso = 0
            for idx, jogo in enumerate(reversed(historico_passado)):
                if num in jogo:
                    atraso = idx
                    break
            
            features_i.extend([freq_10, freq_25, saiu_ultimo, atraso])
            
        target_i = [1 if num in sorteio_atual else 0 for num in range(1, 26)]
        
        X.append(features_i)
        Y.append(target_i)
        
    return np.array(X), np.array(Y)


def treinar_e_prever_probabilidades_rf(df: pd.DataFrame) -> np.ndarray:
    """ Treina o Random Forest e calcula a probabilidade atual para cada uma das 25 dezenas """
    if df is None or len(df) < 40:
        return np.full(25, 0.60)

    X, Y = extrair_features_e_target(df)
    
    if len(X) == 0:
        return np.full(25, 0.60)

    rf_base = RandomForestClassifier(
        n_estimators=60,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )
    
    model = MultiOutputClassifier(rf_base)
    model.fit(X, Y)
    
    dezenas_totais = [extrair_dezenas_linha(df.iloc[i].values) for i in range(len(df))]
    ultimos_10 = dezenas_totais[-10:]
    ultimos_25 = dezenas_totais[-25:]
    ultimo_sorteio = set(dezenas_totais[-1])
    
    features_proximo = []
    for num in range(1, 26):
        freq_10 = sum(1 for jogo in ultimos_10 if num in jogo) / 10.0
        freq_25 = sum(1 for jogo in ultimos_25 if num in jogo) / 25.0
        saiu_ultimo = 1 if num in ultimo_sorteio else 0
        
        atraso = 0
        for idx, jogo in enumerate(reversed(dezenas_totais)):
            if num in jogo:
                atraso = idx
                break
                
        features_proximo.extend([freq_10, freq_25, saiu_ultimo, atraso])
        
    X_proximo = np.array([features_proximo])
    probabilidades_raw = model.predict_proba(X_proximo)
    
    probs_dezenas = []
    for i in range(25):
        prob_1 = probabilidades_raw[i][0][1] if len(probabilidades_raw[i][0]) > 1 else 0.5
        probs_dezenas.append(prob_1)
        
    return np.array(probs_dezenas)


def gerar_jogos_ml_com_ranking(df: pd.DataFrame, count: int = 5):
    """ Gera palpites e retorna junto com o ranking de probabilidade do Random Forest """
    probs = treinar_e_prever_probabilidades_rf(df)
    
    ranking = []
    for num in range(1, 26):
        prob = float(probs[num - 1])
        ranking.append({
            "dezena": num,
            "probabilidade": round(prob * 100, 2)
        })
    
    ranking_ordenado = sorted(ranking, key=lambda x: x["probabilidade"], reverse=True)
    
    pesos = probs / probs.sum()
    ultimo_sorteio = extrair_dezenas_linha(df.iloc[-1].values) if df is not None and len(df) > 0 else None

    jogos_validos = []
    tentativas = 0
    max_tentativas = count * 400

    while len(jogos_validos) < count and tentativas < max_tentativas:
        tentativas += 1
        escolhidos = sorted([int(x) for x in np.random.choice(range(1, 26), size=15, replace=False, p=pesos)])
        
        if e_jogo_valido(escolhidos, ultimo_sorteio):
            if escolhidos not in jogos_validos:
                jogos_validos.append(escolhidos)

    while len(jogos_validos) < count:
        escolhidos = sorted([int(x) for x in np.random.choice(range(1, 26), size=15, replace=False, p=pesos)])
        if escolhidos not in jogos_validos:
            jogos_validos.append(escolhidos)

    return jogos_validos, ranking_ordenado


# ---------------------------------------------------------
# ENDPOINTS DA API (FASTAPI)
# ---------------------------------------------------------

class GenerateRequest(BaseModel):
    session_id: Optional[str] = "sessao_oficial"
    count: int = 5


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
    jogos, ranking = gerar_jogos_ml_com_ranking(dataframe_global, count=req.count)
    return {
        "tickets": jogos,
        "ranking": ranking
    }


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

    inicio_idx = total_concursos - qtd_testes

    for i in range(inicio_idx, total_concursos):
        df_historico_passado = df.iloc[:i]
        resultado_real = set(extrair_dezenas_linha(df.iloc[i].values))

        if len(resultado_real) < 15:
            continue

        bilhetes_gerados, _ = gerar_jogos_ml_com_ranking(df_historico_passado, count=bets_per_draw)
        total_apostas += len(bilhetes_gerados)

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