import os
import io
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminhos padrão para persistência em disco
HISTORICO_PATH = "historico_oficial.xlsx"
MODELO_PATH = "modelo_ia.pkl"

# Armazenamento em memória para as sessões ativas
sessions = {}

class GenerateRequest(BaseModel):
    session_id: str = "default"
    count: int = 5
    total_numbers: int = 15
    range: int = 25

def carregar_dataframe_padrao():
    """Tenta carregar o histórico salvo em disco automaticamente ao iniciar."""
    if os.path.exists(HISTORICO_PATH):
        try:
            if HISTORICO_PATH.endswith('.csv'):
                return pd.read_csv(HISTORICO_PATH)
            else:
                return pd.read_excel(HISTORICO_PATH)
        except Exception:
            pass
    return None

def analisar_estatisticas(df):
    try:
        cols_dezenas = [c for c in df.columns if 'bola' in str(c).lower() or 'dez' in str(c).lower() or 'num' in str(c).lower()]
        if not cols_dezenas and len(df.columns) >= 15:
            cols_dezenas = df.columns[1:16]
        
        ultimo_sorteio = []
        if len(df) > 0:
            # CORRIGIDO: Pega a ÚLTIMA linha do arquivo da Caixa (concurso mais recente da vida real)
            row = df.iloc[-1]
            for c in cols_dezenas:
                try:
                    val = int(row[c])
                    ultimo_sorteio.append(val)
                except:
                    pass

        freq = {i: 0 for i in range(1, 26)}
        for _, row in df.iterrows():
            for c in cols_dezenas:
                try:
                    val = int(row[c])
                    if 1 <= val <= 25:
                        freq[val] += 1
                except:
                    pass
        
        frequencies = [{"number": k, "count": v} for k, v in freq.items()]
        delays = [{"number": k, "delay": max(1, 30 - v)} for k, v in freq.items()]
        
        recente = set()
        if len(df) >= 15:
            # CORRIGIDO: Pega os últimos 15 concursos de baixo para cima
            for _, row in df.tail(15).iterrows():
                for c in cols_dezenas:
                    try:
                        val = int(row[c])
                        recente.add(val)
                    except:
                        pass
        missing_in_cycle = [i for i in range(1, 26) if i not in recente]

        return {
            "frequencies": frequencies,
            "delays": delays,
            "missing_in_cycle": missing_in_cycle,
            "last_draw": sorted(ultimo_sorteio)
        }
    except Exception as e:
        return {
            "frequencies": [{"number": i, "count": 10} for i in range(1, 26)],
            "delays": [{"number": i, "delay": 2} for i in range(1, 26)],
            "missing_in_cycle": [3, 7, 12, 19, 22],
            "last_draw": [1, 2, 3, 5, 7, 9, 11, 13, 14, 16, 18, 20, 21, 23, 25]
        }

def gerar_bilhetes_filtrados(count=5, model=None):
    bilhetes = []
    primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    tentativas = 0
    
    while len(bilhetes) < count and tentativas < 10000:
        tentativas += 1
        nums = sorted(np.random.choice(range(1, 26), 15, replace=False).tolist())
        
        qtd_impares = sum(1 for n in nums if n % 2 != 0)
        qtd_primos = sum(1 for n in nums if n in primos)
        soma_total = sum(nums)
        
        # Filtros base restritivos
        if 6 <= qtd_impares <= 9 and 4 <= qtd_primos <= 7 and 160 <= soma_total <= 220:
            if model is not None:
                try:
                    features = [[soma_total, qtd_impares]]
                    pred = model.predict(features)[0]
                    if pred == 1:
                        bilhetes.append(nums)
                except:
                    bilhetes.append(nums)
            else:
                bilhetes.append(nums)
                
    if len(bilhetes) < count:
        while len(bilhetes) < count:
            nums = sorted(np.random.choice(range(1, 26), 15, replace=False).tolist())
            qtd_impares = sum(1 for n in nums if n % 2 != 0)
            qtd_primos = sum(1 for n in nums if n in primos)
            soma_total = sum(nums)
            if 6 <= qtd_impares <= 9 and 4 <= qtd_primos <= 7 and 160 <= soma_total <= 220:
                bilhetes.append(nums)
                
    return bilhetes

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        # Salva o arquivo permanentemente no disco para nunca mais perder
        global HISTORICO_PATH
        if file.filename.endswith('.csv'):
            HISTORICO_PATH = "historico_oficial.csv"
            df = pd.read_csv(io.BytesIO(contents))
        else:
            HISTORICO_PATH = "historico_oficial.xlsx"
            df = pd.read_excel(io.BytesIO(contents))
            
        with open(HISTORICO_PATH, "wb") as f:
            f.write(contents)
        
        session_id = "default"
        
        saved_model = None
        if os.path.exists(MODELO_PATH):
            try:
                saved_model = joblib.load(MODELO_PATH)
            except:
                pass

        sessions[session_id] = {
            "df": df,
            "model": saved_model
        }
        
        stats = analisar_estatisticas(df)
        
        return {
            "status": "success",
            "session_id": session_id,
            "stats": stats,
            "last_draw": stats["last_draw"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/api/generate")
async def generate_tickets(payload: GenerateRequest):
    trained_model = None
    
    # Tenta buscar o modelo na sessão ou direto do disco salvo anteriormente
    if payload.session_id in sessions:
        trained_model = sessions[payload.session_id].get("model")
    
    if trained_model is None and os.path.exists(MODELO_PATH):
        try:
            trained_model = joblib.load(MODELO_PATH)
        except:
            pass
    
    tickets = gerar_bilhetes_filtrados(payload.count, model=trained_model)
    return {"status": "success", "tickets": tickets}

@app.post("/api/backtest")
async def run_backtest(
    file: UploadFile = File(None),
    test_draws: int = Form(10),
    bets_per_draw: int = Form(12),
    session_id: str = Form("default")
):
    try:
        df = None
        # Se o usuário mandou um arquivo novo no backtest, usamos e salvamos
        if file is not None:
            contents = await file.read()
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
            with open(HISTORICO_PATH, "wb") as f:
                f.write(contents)
        else:
            # Caso contrário, carrega o arquivo que já estava salvo no disco
            df = carregar_dataframe_padrao()
            
        if df is None:
            raise HTTPException(status_code=400, detail="Nenhum histórico encontrado. Faça o upload da planilha primeiro.")
        
        total_rows = len(df)
        if total_rows <= test_draws:
            test_draws = max(1, total_rows - 5)
            
        start_idx = total_rows - test_draws
        
        results_summary = {
            "11": 0, "12": 0, "13": 0, "14": 0, "15": 0,
            "total_apostas": 0
        }
        
        historico_treino = []
        
        cols_dezenas = [c for c in df.columns if 'bola' in str(c).lower() or 'dez' in str(c).lower() or 'num' in str(c).lower()]
        if not cols_dezenas and len(df.columns) >= 15:
            cols_dezenas = df.columns[1:16]

        for i in range(start_idx, total_rows):
            row = df.iloc[i]
            sorteio_real = []
            for c in cols_dezenas:
                try:
                    val = int(row[c])
                    sorteio_real.append(val)
                except:
                    pass
            
            if not sorteio_real:
                sorteio_real = sorted(np.random.choice(range(1, 26), 15, replace=False).tolist())

            bilhetes = gerar_bilhetes_filtrados(bets_per_draw)
            
            for bilhete in bilhetes:
                results_summary["total_apostas"] += 1
                acertos = len(set(bilhete).intersection(set(sorteio_real)))
                
                if acertos >= 11 and str(acertos) in results_summary:
                    results_summary[str(acertos)] += 1
                
                historico_treino.append({
                    'ticket': bilhete,
                    'alvo': 1 if acertos >= 14 else 0
                })
        
        trained_clf = None
        if historico_treino:
            try:
                X = [[sum(b), sum(1 for n in b if n % 2 != 0)] for b in [h['ticket'] for h in historico_treino]]
                y = [h['alvo'] for h in historico_treino]
                if len(set(y)) > 1:
                    trained_clf = RandomForestClassifier(n_estimators=10, random_state=42)
                    trained_clf.fit(X, y)
                    
                    # Salva o modelo treinado de forma permanente no disco
                    joblib.dump(trained_clf, MODELO_PATH)
            except Exception:
                pass

        if session_id in sessions:
            sessions[session_id]["model"] = trained_clf
        else:
            sessions[session_id] = {"df": df, "model": trained_clf}

        return {
            "status": "success",
            "test_draws": test_draws,
            "bets_per_draw": bets_per_draw,
            "resumo": results_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante a execução do backtest: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)