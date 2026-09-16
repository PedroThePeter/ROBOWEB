import os
import io
import joblib
import pandas as pd
import numpy as np
import requests
import urllib3
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier

# Desativa avisos de segurança SSL (o site da Caixa às vezes tem certificados antigos)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def sincronizar_com_caixa(df, filepath):
    """Busca novos resultados na API da Caixa e atualiza a planilha salva."""
    try:
        # Descobre qual é a coluna do número do concurso
        col_concurso = [c for c in df.columns if 'concurso' in str(c).lower()]
        if not col_concurso:
            print("Não foi possível achar a coluna de Concurso. Sincronização ignorada.")
            return df
        
        nome_col_concurso = col_concurso[0]
        # Pega o número do último concurso que temos salvo
        ultimo_concurso_salvo = int(df.iloc[-1][nome_col_concurso])
        concurso_a_buscar = ultimo_concurso_salvo + 1
        
        novos_dados = []
        print(f"Verificando se existem novos sorteios após o concurso {ultimo_concurso_salvo}...")

        while True:
            # URL oficial da API da Caixa para um concurso específico
            url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/{concurso_a_buscar}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            
            resposta = requests.get(url, headers=headers, verify=False, timeout=10)
            
            if resposta.status_code == 200:
                dados = resposta.json()
                
                # Formata as dezenas recebidas da internet
                dezenas = sorted([int(x) for x in dados['dezenasSorteadasOrdemSorteio']])
                print(f"✅ Novo concurso {concurso_a_buscar} encontrado na internet! Dezenas: {dezenas}")
                
                # Prepara a nova linha para a planilha
                nova_linha = {c: '' for c in df.columns} # Começa vazia
                nova_linha[nome_col_concurso] = dados['numero']
                
                # Adiciona a data se a coluna existir
                col_data = [c for c in df.columns if 'data' in str(c).lower()]
                if col_data:
                    nova_linha[col_data[0]] = dados['dataApuracao']
                
                # Mapeia as 15 bolas para as respectivas colunas
                cols_dezenas = [c for c in df.columns if 'bola' in str(c).lower() or 'dez' in str(c).lower() or 'num' in str(c).lower()]
                if len(cols_dezenas) >= 15:
                    for i in range(15):
                        nova_linha[cols_dezenas[i]] = dezenas[i]
                
                novos_dados.append(nova_linha)
                concurso_a_buscar += 1 # Prepara para buscar o próximo
            else:
                # Se der erro 404, significa que não tem mais concursos novos. Chegamos no dia de hoje.
                break
                
        # Se encontrou resultados novos, junta tudo e salva no disco
        if novos_dados:
            df_novos = pd.DataFrame(novos_dados)
            df = pd.concat([df, df_novos], ignore_index=True)
            
            if filepath.endswith('.csv'):
                df.to_csv(filepath, index=False)
            else:
                df.to_excel(filepath, index=False)
            print("🚀 Planilha atualizada e salva no disco com os sorteios mais recentes!")
            
        return df
    except Exception as e:
        print(f"Erro durante a sincronização automática: {e}")
        return df

def carregar_dataframe_padrao():
    """Carrega o histórico do disco e já tenta baixar as novidades da internet."""
    if os.path.exists(HISTORICO_PATH):
        try:
            if HISTORICO_PATH.endswith('.csv'):
                df = pd.read_csv(HISTORICO_PATH)
            else:
                df = pd.read_excel(HISTORICO_PATH)
                
            # Chama a função mágica que atualiza a planilha usando a API da Caixa
            df = sincronizar_com_caixa(df, HISTORICO_PATH)
            return df
        except Exception as e:
            print(f"Erro ao carregar planilha padrão: {e}")
    return None

def analisar_estatisticas(df):
    try:
        cols_dezenas = [c for c in df.columns if 'bola' in str(c).lower() or 'dez' in str(c).lower() or 'num' in str(c).lower()]
        if not cols_dezenas and len(df.columns) >= 15:
            cols_dezenas = df.columns[1:16]
        
        ultimo_sorteio = []
        if len(df) > 0:
            # Pega a ÚLTIMA linha (concurso mais recente da vida real)
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
            # Pega os últimos 15 concursos de baixo para cima
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

# EVENTO DE INICIALIZAÇÃO DO SERVIDOR
@app.on_event("startup")
async def startup_event():
    """Roda automaticamente toda vez que você liga o servidor."""
    print("Iniciando robô e verificando atualizações...")
    df = carregar_dataframe_padrao()
    
    saved_model = None
    if os.path.exists(MODELO_PATH):
        try:
            saved_model = joblib.load(MODELO_PATH)
        except:
            pass
            
    if df is not None:
        sessions["default"] = {
            "df": df,
            "model": saved_model
        }
        print("✅ Base de dados e IA carregadas e atualizadas com sucesso!")

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
        if file is not None:
            contents = await file.read()
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
            with open(HISTORICO_PATH, "wb") as f:
                f.write(contents)
        else:
            df = None
            if "default" in sessions:
                df = sessions["default"]["df"]
            if df is None:
                df = carregar_dataframe_padrao()
            
        if df is None:
            raise HTTPException(status_code=400, detail="Nenhum histórico encontrado. Faça o upload da planilha pela primeira vez.")
        
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
                    
                    # Salva no disco permanentemente
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

# Rota extra só para forçar atualização pela internet (se quiser usar futuramente no botão do front-end)
@app.get("/api/sincronizar")
async def forcar_sincronizacao():
    df = carregar_dataframe_padrao()
    if df is not None:
        stats = analisar_estatisticas(df)
        return {"status": "success", "msg": "Planilha atualizada com os dados da Caixa!", "last_draw": stats["last_draw"]}
    return {"status": "error", "msg": "Faça o upload do primeiro histórico antes de sincronizar."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)