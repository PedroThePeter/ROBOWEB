from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uuid
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    session_id: str
    count: int = 5
    total_numbers: int = 15
    range: int = 25

PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23}

def validate_ticket(ticket):
    """Filtros Restritivos de IA (Padrão Lotofácil)"""
    odds = sum(1 for n in ticket if n % 2 != 0)
    primes_count = sum(1 for n in ticket if n in PRIMES)
    total_sum = sum(ticket)

    if not (6 <= odds <= 9):
        return False
    if not (4 <= primes_count <= 7):
        return False
    if not (160 <= total_sum <= 220):
        return False
    return True

@app.get("/")
def read_root():
    return {"status": "LottoAI API Lotofácil rodando com sucesso!"}

@app.post("/api/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)

        if df.empty:
            raise HTTPException(status_code=400, detail="A planilha está vazia.")

        # 1. Extrai o último sorteio
        last_row = df.iloc[-1]
        last_draw = []
        for val in last_row.values:
            try:
                num = int(val)
                if 1 <= num <= 25:
                    last_draw.append(num)
            except (ValueError, TypeError):
                continue
        last_draw = sorted(list(set(last_draw)))[:15]

        # 2. Frequência total e parsing de sorteios
        all_numbers = []
        rows_list = []
        for _, row in df.iterrows():
            row_nums = []
            for val in row.values:
                try:
                    n = int(val)
                    if 1 <= n <= 25:
                        all_numbers.append(n)
                        row_nums.append(n)
                except (ValueError, TypeError):
                    continue
            if len(row_nums) >= 15:
                rows_list.append(row_nums[:15])

        counts = pd.Series(all_numbers).value_counts()
        frequencies = [
            {"number": i, "count": int(counts.get(i, 0))}
            for i in range(1, 26)
        ]

        # 3. Termômetro de Atraso
        delays = []
        for i in range(1, 26):
            delay_count = 0
            for row in reversed(rows_list):
                if i in row:
                    break
                delay_count += 1
            delays.append({"number": i, "delay": delay_count})

        # 4. Análise de Ciclo
        seen_in_cycle = set()
        for row in reversed(rows_list):
            new_seen = seen_in_cycle | set(row)
            if len(new_seen) == 25:
                break
            seen_in_cycle = new_seen
        
        missing_in_cycle = sorted(list(set(range(1, 26)) - seen_in_cycle))

        session_id = str(uuid.uuid4())

        return {
            "session_id": session_id,
            "stats": {
                "frequencies": frequencies,
                "delays": delays,
                "missing_in_cycle": missing_in_cycle
            },
            "last_draw": last_draw
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar planilha: {str(e)}")

@app.post("/api/generate")
async def generate_tickets(req: GenerateRequest):
    tickets = []
    attempts = 0
    max_attempts = 1000

    while len(tickets) < req.count and attempts < max_attempts:
        attempts += 1
        candidate = sorted(random.sample(range(1, req.range + 1), req.total_numbers))
        
        if validate_ticket(candidate) and candidate not in tickets:
            tickets.append(candidate)

    return {"tickets": tickets}

@app.post("/api/backtest")
async def run_backtest(
    file: UploadFile = File(...), 
    test_draws: int = Form(10), 
    tickets_per_draw: int = Form(12)
):
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)

        # Extrai todos os sorteios válidos
        all_draws = []
        for _, row in df.iterrows():
            row_nums = []
            for val in row.values:
                try:
                    n = int(val)
                    if 1 <= n <= 25:
                        row_nums.append(n)
                except (ValueError, TypeError):
                    continue
            if len(row_nums) >= 15:
                all_draws.append(sorted(list(set(row_nums))[:15]))

        if len(all_draws) <= test_draws:
            raise HTTPException(status_code=400, detail="Planilha muito pequena para o tamanho do teste.")

        # Separa os últimos N sorteios para a simulação cega
        future_draws = all_draws[-test_draws:]

        results = {
            "11_pontos": 0,
            "12_pontos": 0,
            "13_pontos": 0,
            "14_pontos": 0,
            "15_pontos": 0,
            "total_bilhetes_gerados": test_draws * tickets_per_draw,
            "simulations": []
        }

        # Simula a validação para cada concurso retido
        for i, actual_draw in enumerate(future_draws):
            tickets = []
            attempts = 0
            
            while len(tickets) < tickets_per_draw and attempts < 2000:
                attempts += 1
                candidate = sorted(random.sample(range(1, 26), 15))
                if validate_ticket(candidate) and candidate not in tickets:
                    tickets.append(candidate)

            draw_hits = []
            for t in tickets:
                hits = len(set(t) & set(actual_draw))
                draw_hits.append(hits)
                
                if hits == 11: results["11_pontos"] += 1
                elif hits == 12: results["12_pontos"] += 1
                elif hits == 13: results["13_pontos"] += 1
                elif hits == 14: results["14_pontos"] += 1
                elif hits == 15: results["15_pontos"] += 1

            results["simulations"].append({
                "concurso_simulado": f"Concurso Retido #{i+1}",
                "melhor_acerto": max(draw_hits) if draw_hits else 0,
                "acertos_detalhados": draw_hits
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no backtest: {str(e)}")