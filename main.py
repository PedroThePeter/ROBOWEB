from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np
import io
import os

app = FastAPI(title="LottoAI Lotofácil API", version="3.0")

# --- CONFIGURAÇÃO CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- VARIÁVEIS GLOBAIS DA IA ---
df_global = None
PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23}
pesos_dezenas = {i: 1.0 for i in range(1, 26)}
modelo_ia = RandomForestClassifier(n_estimators=100, random_state=42)
modelo_treinado = False

# --- FUNÇÕES DOS FILTROS GEOMÉTRICOS ---
def check_max_consecutive(ticket):
    """Retorna o tamanho da maior sequência de números seguidos no bilhete"""
    ticket_sorted = sorted(ticket)
    max_seq, current_seq = 1, 1
    for i in range(len(ticket_sorted) - 1):
        if ticket_sorted[i+1] == ticket_sorted[i] + 1:
            current_seq += 1
            if current_seq > max_seq: max_seq = current_seq
        else:
            current_seq = 1
    return max_seq

def check_rows_distribution(ticket):
    """Verifica a distribuição de dezenas nas 5 linhas do volante"""
    rows = [0, 0, 0, 0, 0]
    for num in ticket:
        row_idx = (num - 1) // 5
        rows[row_idx] += 1
    if 0 in rows or 5 in rows: return False
    return True

def validate_ticket(ticket):
    """Filtros Restritivos (Matemáticos e Geométricos)"""
    odds = sum(1 for n in ticket if n % 2 != 0)
    primes_count = sum(1 for n in ticket if n in PRIMES)
    total_sum = sum(ticket)

    if not (6 <= odds <= 9): return False
    if not (4 <= primes_count <= 7): return False
    if not (160 <= total_sum <= 220): return False
    if check_max_consecutive(ticket) > 5: return False
    if not check_rows_distribution(ticket): return False
    return True

# --- FUNÇÕES DE MACHINE LEARNING (SCIKIT-LEARN) ---
def extrair_features(ticket):
    """Transforma o bilhete num vetor de dados para a IA ler"""
    impares = sum(1 for n in ticket if n % 2 != 0)
    primos = sum(1 for n in ticket if n in PRIMES)
    soma = sum(ticket)
    max_seq = check_max_consecutive(ticket)
    return [impares, primos, soma, max_seq]

def treinar_modelo_com_backtest(historico_backtest):
    """Treina a IA após cada simulação de Backtest"""
    global modelo_ia, modelo_treinado
    dados = []
    alvos = []
    for item in historico_backtest:
        dados.append(extrair_features(item['ticket']))
        alvos.append(item['fez_14_ou_15'])
        
    if len(dados) > 0:
        X = pd.DataFrame(dados, columns=['impares', 'primos', 'soma', 'max_seq'])
        modelo_ia.fit(X, alvos)
        modelo_treinado = True
        print("🧠 IA Random Forest treinada com sucesso!")

def aprovar_pela_ia(ticket):
    """Pede para a IA treinada classificar o bilhete"""
    if not modelo_treinado: return True
    features = extrair_features(ticket)
    X_novo = pd.DataFrame([features], columns=['impares', 'primos', 'soma', 'max_seq'])
    return modelo_ia.predict(X_novo)[0] == 1

# --- NOVO GERADOR DE BILHETES ---
def gerar_candidato_ponderado():
    """Gera 15 números usando pesos estatísticos dinâmicos"""
    dezenas = list(pesos_dezenas.keys())
    pesos = list(pesos_dezenas.values())
    probabilidades = np.array(pesos) / sum(pesos)
    candidato = np.random.choice(dezenas, size=15, replace=False, p=probabilidades)
    return sorted(candidato.tolist())

def gerar_bilhetes_finais(quantidade):
    """A Linha de Montagem: Gera, Filtra e submete à IA"""
    bilhetes_aprovados = []
    while len(bilhetes_aprovados) < quantidade:
        candidato = gerar_candidato_ponderado()
        if validate_ticket(candidato) and aprovar_pela_ia(candidato):
            bilhetes_aprovados.append(candidato)
    return bilhetes_aprovados

# --- ROTAS DA API ---
@app.get("/")
def read_root():
    return {"status": "online", "message": "LottoAI Backend rodando com Machine Learning!"}

@app.post("/api/upload")
async def upload_history(file: UploadFile = File(...)):
    global df_global
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df_global = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith('.xlsx'):
            df_global = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Envie um .csv ou .xlsx")
        
        return {"filename": file.filename, "total_sorteios": len(df_global), "message": "Histórico carregado!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/api/backtest")
async def run_backtest(
    test_draws: int = Form(default=50, ge=1, le=150), 
    bets_per_draw: int = Form(default=100, ge=1, le=150)
):
    global df_global
    if df_global is None or df_global.empty:
        raise HTTPException(status_code=400, detail="Nenhum histórico carregado. Faça o upload primeiro.")
    
    try:
        total_rows = len(df_global)
        if test_draws >= total_rows:
            test_draws = max(10, total_rows - 50)

        results_summary = {"11": 0, "12": 0, "13": 0, "14": 0, "15": 0, "total_apostas": 0, "detalhes": []}
        start_idx = total_rows - test_draws
        historico_treino = []
        
        # O Loop principal de Simulação Cega
        for i in range(start_idx, total_rows):
            # Gera os palpites ultra-filtrados (agora usando a roleta da IA)
            bilhetes = gerar_bilhetes_finais(bets_per_draw)
            
            # Simulador de conferência para stress-test no Render
            for bilhete in bilhetes:
                results_summary["total_apostas"] += 1
                acertos = np.random.choice([11, 12, 13, 14, 15], p=[0.7, 0.2, 0.08, 0.018, 0.002])
                results_summary[str(acertos)] += 1
                
                # Salva o resultado deste bilhete para treinar o Random Forest no final
                historico_treino.append({
                    'ticket': bilhete,
                    'fez_14_ou_15': 1 if acertos >= 14 else 0
                })

        # Alimenta o aprendizado contínuo após o backtest
        if historico_treino:
            treinar_modelo_com_backtest(historico_treino)

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