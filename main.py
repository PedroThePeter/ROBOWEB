import os
import glob
import io
import joblib
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from supabase import create_client, Client

app = FastAPI(title="Robô Lotofácil Inteligente API")

# Habilita CORS para o frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# CONFIGURAÇÃO DO SUPABASE
# ---------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "SUA_URL_DO_SUPABASE")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "SUA_KEY_DO_SUPABASE")
BUCKET_NAME = "lotofacil-storage"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Nomes dos arquivos persistentes
FILE_NAME_OFFICIAL = "historico_oficial.xlsx"
MODEL_FILE_NAME = "modelo_rf_lotofacil.joblib"

# Estado Global na Memória
dataframe_global: Optional[pd.DataFrame] = None
ultimo_concurso_global: Optional[List[int]] = None
ultimo_numero_concurso: int = 0
session_id_global: str = "sessao_oficial"

# Constantes Estatísticas (Regras de Ouro)
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}


# ---------------------------------------------------------
# FUNÇÕES DE SINCRONIZAÇÃO COM NUVEM (SUPABASE)
# ---------------------------------------------------------

def baixar_do_supabase(filename: str) -> bool:
    """ Baixa um arquivo do Supabase Storage para o disco local do Render """
    try:
        res = supabase.storage.from_(BUCKET_NAME).download(filename)
        with open(filename, "wb") as f:
            f.write(res)
        print(f"✅ Arquivo '{filename}' restaurado da nuvem Supabase.")
        return True
    except Exception as e:
        print(f"ℹ️ Arquivo '{filename}' não encontrado no Supabase ou erro na busca: {e}")
        return False


def enviar_para_supabase(filepath: str, filename: str):
    """ Envia ou atualiza um arquivo no Supabase Storage """
    try:
        with open(filepath, "rb") as f:
            try:
                supabase.storage.from_(BUCKET_NAME).upload(
                    path=filename,
                    file=f,
                    file_options={"upsert": "true"}
                )
            except Exception:
                # Fallback caso o arquivo já exista (Update)
                f.seek(0)
                supabase.storage.from_(BUCKET_NAME).update(
                    path=filename,
                    file=f,
                    file_options={"upsert": "true"}
                )
        print(f"🚀 Arquivo '{filename}' salvo permanentemente no Supabase!")
    except Exception as e:
        print(f"❌ Erro ao enviar '{filename}' para o Supabase: {e}")


def carregar_base_e_modelo_inicial():
    """ Tenta restaurar os arquivos do Supabase antes de ligar o servidor """
    global dataframe_global, ultimo_concurso_global, ultimo_numero_concurso
    
    print("🔄 Inicializando sistema e buscando backups no Supabase...")
    
    # Baixa planilha e modelo da nuvem
    baixar_do_supabase(FILE_NAME_OFFICIAL)
    baixar_do_supabase(MODEL_FILE_NAME)

    # Verifica qual arquivo base usar
    arquivo_base = None
    if os.path.exists(FILE_NAME_OFFICIAL):
        arquivo_base = FILE_NAME_OFFICIAL
    else:
        arquivos = glob.glob("*.xlsx") + glob.glob("*.csv")
        if arquivos:
            arquivo_base = arquivos[0]

    if arquivo_base:
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

            print(f"📊 Base local carregada! Último concurso registrado: #{ultimo_numero_concurso}")

        except Exception as e:
            print(f"❌ Erro ao ler planilha inicial: {e}")
    else:
        print("⚠️ Nenhuma planilha base encontrada localmente ou na nuvem. Aguardando envio via upload.")

# Executa no boot
carregar_base_e_modelo_inicial()


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
    soma = sum(jogo)
    if not (180 <= soma <= 220):
        return False

    pares = len([n for n in jogo if n % 2 == 0])
    if pares not in [6, 7, 8, 9]:
        return False

    moldura = len([n for n in jogo if n in MOLDURA])
    if moldura not in [8, 9, 10, 11]:
        return False

    primos = len([n for n in jogo if n in PRIMOS])
    if primos not in [4, 5, 6, 7]:
        return False

    if ultimo_resultado and len(ultimo_resultado) == 15:
        repetidos = len(set(jogo).intersection(set(ultimo_resultado)))
        if repetidos not in [8, 9, 10]:
            return False

    return True


# ---------------------------------------------------------
# MACHINE LEARNING COM PERSISTÊNCIA JOBLIB
# ---------------------------------------------------------

def extrair_features_e_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """ Converte o histórico de concursos em matrizes de treino (X) e alvos (Y) (Versão Completa) """
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


def treinar_ou_carregar_rf(df: pd.DataFrame):
    """ Carrega o modelo treinado do disco (Supabase) ou treina um novo e o envia para a nuvem """
    if os.path.exists(MODEL_FILE_NAME):
        try:
            model = joblib.load(MODEL_FILE_NAME)
            print("🧠 Modelo Random Forest pré-treinado carregado com sucesso.")
            return model
        except Exception as e:
            print(f"⚠️ Erro ao carregar modelo local, re-treinando... {e}")

    print("⚙️ Treinando novo modelo Random Forest e salvando no Supabase...")
    X, Y = extrair_features_e_target(df)
    
    rf_base = RandomForestClassifier(n_estimators=60, max_depth=6, random_state=42, n_jobs=-1)
    model = MultiOutputClassifier(rf_base)
    if len(X) > 0:
        model.fit(X, Y)

    # Salva localmente e envia para o Supabase Storage
    joblib.dump(model, MODEL_FILE_NAME)
    enviar_para_supabase(MODEL_FILE_NAME, MODEL_FILE_NAME)

    return model


def prever_probabilidades_rf(df: pd.DataFrame, is_backtest: bool = False) -> np.ndarray:
    """ Calcula a probabilidade atual para cada dezena """
    if df is None or len(df) < 40:
        return np.full(25, 0.60)

    # Se for backtest, treina um modelo efêmero sem salvar no disco (para não sujar a base oficial)
    if is_backtest:
        X, Y = extrair_features_e_target(df)
        rf_base = RandomForestClassifier(n_estimators=60, max_depth=6, random_state=42, n_jobs=-1)
        model = MultiOutputClassifier(rf_base)
        if len(X) > 0:
            model.fit(X, Y)
    else:
        # Se for geração real, usa o modelo persistido do Supabase/Disco
        model = treinar_ou_carregar_rf(df)
    
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


def gerar_jogos_ml_com_ranking(df: pd.DataFrame, count: int = 5, is_backtest: bool = False):
    """ Gera palpites e retorna junto com o ranking de probabilidade """
    probs = prever_probabilidades_rf(df, is_backtest)
    
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
        carregar_base_e_modelo_inicial()
        
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
            df.to_csv(FILE_NAME_OFFICIAL, index=False)
        else:
            df = pd.read_excel(io.BytesIO(contents))
            df.to_excel(FILE_NAME_OFFICIAL, index=False)

        dataframe_global = df
        
        ultima_linha = df.iloc[-1].values
        ultimo_concurso_global = extrair_dezenas_linha(ultima_linha)
        
        if "Concurso" in df.columns:
            ultimo_numero_concurso = int(df["Concurso"].dropna().iloc[-1])
        else:
            ultimo_numero_concurso = len(df)

        # Envia a nova planilha para o Supabase
        enviar_para_supabase(FILE_NAME_OFFICIAL, FILE_NAME_OFFICIAL)
        
        # Como a base mudou, apaga o modelo velho localmente e no Supabase 
        # para forçar a IA a retreinar na próxima vez que gerar jogos
        if os.path.exists(MODEL_FILE_NAME):
            os.remove(MODEL_FILE_NAME)

        return {
            "session_id": session_id_global,
            "last_draw": ultimo_concurso_global,
            "stats": {
                "total_concursos": len(df),
                "ultimo_concurso": ultimo_numero_concurso
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")


@app.post("/api/generate")
def generate_tickets(req: GenerateRequest):
    jogos, ranking = gerar_jogos_ml_com_ranking(dataframe_global, count=req.count, is_backtest=False)
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

        # Passamos is_backtest=True para não gravar o modelo de simulação no Supabase
        bilhetes_gerados, _ = gerar_jogos_ml_com_ranking(df_historico_passado, count=bets_per_draw, is_backtest=True)
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