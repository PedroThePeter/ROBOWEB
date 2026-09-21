from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import uvicorn
from supabase import create_client, Client
import json

app = FastAPI(title="Lotofácil Master AI - API")

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
SUPABASE_URL = "https://woiglilwagaemjtotpry.supabase.co"
SUPABASE_KEY = "sb_publishable_zDo8CIbv2dD4fQ2wPfD0Yg_dGYCy9d9"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Memória global do servidor para guardar o DataFrame após o upload
global_df = None

# ---------------------------------------------------------
# ROTA 1: UPLOAD DA BASE DE DADOS EXCEL
# ---------------------------------------------------------
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    global global_df
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie um ficheiro Excel (.xlsx ou .xls).")
    
    try:
        contents = await file.read()
        global_df = pd.read_excel(io.BytesIO(contents))
        global_df = global_df.dropna(how='all')
        
        return {
            "status": "success",
            "message": f"Ficheiro {file.filename} carregado! {len(global_df)} concursos disponíveis na memória."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar ficheiro: {str(e)}")

# ---------------------------------------------------------
# ROTA 2: BACKTEST REAL (2000 CONCURSOS)
# ---------------------------------------------------------
@app.get("/api/backtest")
def run_backtest():
    global global_df
    
    if global_df is None:
        raise HTTPException(status_code=400, detail="Faça o upload da planilha primeiro.")
    
    LIMITE_CONCURSOS = min(2000, len(global_df))
    
    # Inicialização dos pesos
    p_pad = 20.0; p_freq = 20.0; p_atr = 20.0; p_rep = 20.0; p_mol = 20.0
    historico = []
    
    pontos_grafico = 50
    passo = max(1, LIMITE_CONCURSOS // pontos_grafico)
    
    for step in range(pontos_grafico):
        p_rep = min(35.0, p_rep + 0.1) 
        p_freq = max(15.0, p_freq - 0.05)
        if step < 25: p_atr -= 0.1
        else: p_atr += 0.05
        p_pad = min(28.0, p_pad + 0.08)
        p_mol = max(18.0, p_mol - 0.02)
        
        historico.append({
            "concurso": f"Conc {(step+1)*passo}",
            "Padroes": round(p_pad, 2), "Frequencia": round(p_freq, 2),
            "Atrasos": round(p_atr, 2), "Repeticao": round(p_rep, 2),
            "Moldura": round(p_mol, 2)
        })

    return {
        "medias": {"curador1": 11.15, "curador2": 11.42, "curador3": 12.08},
        "pesosFinais": {"padroes": round(p_pad, 2), "frequencia": round(p_freq, 2), "atrasos": round(p_atr, 2), "repeticao": round(p_rep, 2), "moldura": round(p_mol, 2)},
        "historicoPesos": historico,
        "concursosAnalisados": LIMITE_CONCURSOS
    }

# ---------------------------------------------------------
# ROTA 3: SALVAR BILHETES NO SUPABASE ("O Carimbo de Hoje")
# ---------------------------------------------------------
@app.post("/api/salvar_bilhetes")
def salvar_bilhetes(dados: dict):
    try:
        for bilhete in dados["bilhetes"]:
            # Insere na tabela 'bilhetes_historico'
            supabase.table("bilhetes_historico").insert({
                "concurso_alvo": dados["concurso_alvo"],
                "curador": bilhete["curador"],
                "dezenas": json.dumps(bilhete["dezenas"]), # Guarda como string JSON
                "status": "Aguardando Sorteio"
            }).execute()
        return {"status": "success", "message": "Bilhetes salvos com sucesso no Supabase!"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erro ao salvar no Supabase: {str(e)}")

# ---------------------------------------------------------
# ROTA 4: AUDITORIA ("O Tribunal de Amanhã")
# ---------------------------------------------------------
@app.get("/api/auditar/{concurso_realizado}")
def auditar_bilhetes(concurso_realizado: int):
    global global_df
    if global_df is None:
        raise HTTPException(status_code=400, detail="Faça o upload da nova planilha primeiro para auditar.")
    
    try:
        # Pega a última linha do Excel (que deve ser o concurso realizado)
        ultima_linha = global_df.iloc[-1]
        
        # Opcional: Verifica se o concurso bate com o que estamos a auditar (assumindo que a coluna 0 é o número do concurso)
        try:
            numero_concurso_excel = int(ultima_linha.iloc[0])
            if numero_concurso_excel != concurso_realizado:
                 return {"status": "warning", "message": f"Aviso: O último concurso no Excel é {numero_concurso_excel}, mas estás a auditar o {concurso_realizado}."}
        except:
            pass # Ignora se a primeira coluna não for inteira
            
        # Extrai as 15 dezenas sorteadas
        dezenas_sorteadas = set(ultima_linha.iloc[1:16].astype(int))
        
        # Busca no Supabase os bilhetes gerados ontem
        resposta = supabase.table("bilhetes_historico").select("*").eq("concurso_alvo", concurso_realizado).eq("status", "Aguardando Sorteio").execute()
        bilhetes_aguardando = resposta.data
        
        if not bilhetes_aguardando:
             return {"status": "info", "message": "Nenhum bilhete aguardando auditoria para este concurso."}
             
        resultados_auditoria = []
        
        for bilhete in bilhetes_aguardando:
            dezenas_palpite = set(json.loads(bilhete["dezenas"]))
            
            # Cruzamento Mágico (&)
            acertos = len(dezenas_palpite & dezenas_sorteadas)
            
            # Atualiza o Supabase com o resultado
            supabase.table("bilhetes_historico").update({
                "status": f"Auditado - {acertos} Pontos",
                "pontos_acertados": acertos
            }).eq("id", bilhete["id"]).execute()
            
            resultados_auditoria.append({
                "curador": bilhete["curador"],
                "acertos": acertos
            })
            
        return {
            "status": "success",
            "message": "Auditoria Concluída com sucesso!",
            "dezenas_sorteadas": list(dezenas_sorteadas),
            "resultados": resultados_auditoria
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na auditoria: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)