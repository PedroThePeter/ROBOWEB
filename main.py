import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importa o seu arquivo de lógica
from services import analyzer

app = FastAPI()

# --- CONFIGURAÇÃO DE SEGURANÇA (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS ---
class GenerateRequest(BaseModel):
    session_id: str
    total_numbers: int
    number_range: int
    fixed_numbers: list[int] = []
    excluded_numbers: list[int] = []
    ticket_count: int = 5

# --- ROTAS DA API ---

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie um arquivo .xlsx")
    
    session_id = str(uuid.uuid4())
    temp_path = f"temp_{session_id}.xlsx"
    
    # Salva o arquivo temporariamente
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        # AQUI É O SEGREDO: Chama a SUA função para salvar a planilha na memória do analyzer
        info = analyzer.process_upload(temp_path, session_id)
        return {"session_id": session_id, "message": "Upload realizado com sucesso!", "info": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/{session_id}")
async def get_stats(session_id: str):
    try:
        # Puxa os dados estatísticos usando o ID da sessão
        stats = analyzer.calculate_stats(session_id) 
        return stats
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-tickets")
async def generate_tickets(req: GenerateRequest):
    try:
        # O seu código precisa das estatísticas ('stats') para gerar os pesos
        stats = analyzer.calculate_stats(req.session_id)
        
        # O seu código espera um dicionário 'config', então montamos ele aqui:
        config = {
            'total_numbers': req.total_numbers,
            'number_range': req.number_range,
            'fixed_numbers': req.fixed_numbers,
            'excluded_numbers': req.excluded_numbers,
            'ticket_count': req.ticket_count
        }
        
        # Chama a função de gerar passando o config e os stats
        tickets = analyzer.generate_tickets(config, stats)
        return {"tickets": tickets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))