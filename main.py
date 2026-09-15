from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uuid
import random

app = FastAPI()

# 1. Configuração do CORS (permite que a Vercel acesse este backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para a requisição de geração de palpites
class GenerateRequest(BaseModel):
    session_id: str
    count: int = 5
    total_numbers: int = 15
    range: int = 25

# "Banco de dados" temporário na memória
sessions_db = {}

@app.get("/")
def read_root():
    return {"status": "LottoAI API Lotofácil rodando com sucesso!"}

# 2. ROTA DE UPLOAD DO EXCEL / CONFRONTO
@app.post("/api/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        # Lê o arquivo enviado (Excel ou CSV)
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)

        if df.empty:
            raise HTTPException(status_code=400, detail="A planilha enviada está vazia.")

        # EXTRAI O ÚLTIMO SORTEIO (Última linha da planilha)
        last_row = df.iloc[-1]
        last_draw = []
        for val in last_row.values:
            try:
                num = int(val)
                if 1 <= num <= 25:
                    last_draw.append(num)
            except (ValueError, TypeError):
                continue
        
        # Garante exatamente 15 dezenas únicas e ordenadas
        last_draw = sorted(list(set(last_draw)))[:15]

        # CALCULA A FREQUÊNCIA DAS DEZENAS (1 a 25)
        all_numbers = []
        for col in df.columns:
            for val in df[col].values:
                try:
                    num = int(val)
                    if 1 <= num <= 25:
                        all_numbers.append(num)
                except (ValueError, TypeError):
                    continue

        counts = pd.Series(all_numbers).value_counts()
        frequencies = [
            {"number": i, "count": int(counts.get(i, 0))}
            for i in range(1, 26)
        ]

        # Cria a sessão
        session_id = str(uuid.uuid4())
        sessions_db[session_id] = {
            "frequencies": frequencies,
            "last_draw": last_draw
        }

        # ESTRUTURA DO JSON RETORNADO PARA O REACT
        return {
            "session_id": session_id,
            "stats": {
                "frequencies": frequencies
            },
            "last_draw": last_draw
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar planilha: {str(e)}")

# 3. ROTA PARA GERAR PALPITES DA LOTOFÁCIL
@app.post("/api/generate")
async def generate_tickets(req: GenerateRequest):
    tickets = []
    
    # Gera cartões com 15 dezenas entre 1 e 25
    for _ in range(req.count):
        ticket = sorted(random.sample(range(1, req.range + 1), req.total_numbers))
        tickets.append(ticket)

    return {"tickets": tickets}