import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import engine
import integridade
import diario
import rotina_diaria
import painel_auditoria

app = FastAPI(
    title="Lotofácil IA - API Estatística",
    description="Servidor API REST para o ecossistema de inteligência estatística, auditoria e geração genética da Lotofácil (v8.0)",
    version="8.0"
)

# Permite chamadas CORS de qualquer origem (frontend React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Trata Erros 404 Retornando a Rota Exata Solicitada pelo React ---

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            "status": "erro",
            "mensagem": f"A rota [{request.method}] {request.url.path} nao foi encontrada no backend.",
            "detail": "Not Found",
            "sugestao": "Verifique se a URL no frontend possui barra no final, prefixo /api/ ou metodo HTTP correto (GET/POST)."
        }
    )


# --- Modelos de Dados (Schemas Pydantic) ---

class RequisicaoGerarJogos(BaseModel):
    concurso: Optional[int] = None
    quantidade: Optional[int] = 10

class RequisicaoRotinaDiaria(BaseModel):
    concurso: Optional[int] = None
    quantidade: Optional[int] = 10
    sem_commit: Optional[bool] = False
    sem_diario: Optional[bool] = False


# --- Endpoints da API ---

@app.get("/")
@app.get("/api")
def root():
    """Endpoint de verificação de integridade e estado do servidor."""
    return {
        "status": "online",
        "sistema": "Lotofácil IA v8.0",
        "modulos_carregados": [
            "engine",
            "integridade",
            "backtest",
            "desdobramento",
            "diario",
            "rotina_diaria",
            "analise_memoria",
            "painel_auditoria"
        ]
    }

@app.get("/api/status")
@app.get("/status")
def api_status():
    """Retorna o status simplificado da API para validação do frontend."""
    return {"status": "online", "sistema": "Lotofácil IA v8.0"}

# Mapeamento de rotas de historico/dados com suporte a barra no final
@app.get("/api/historico")
@app.get("/api/historico/")
@app.get("/api/palpites")
@app.get("/api/palpites/")
@app.get("/api/diario")
@app.get("/api/diario/")
@app.get("/api/dados")
@app.get("/api/dados/")
@app.get("/api/carregar-dados")
@app.get("/api/carregar-dados/")
@app.post("/api/historico")
@app.post("/api/palpites")
@app.post("/api/diario")
@app.post("/api/dados")
@app.post("/api/carregar-dados")
def api_obter_historico():
    """Retorna os dados consolidados do diário e últimos palpites registrados."""
    try:
        dados = diario.obter_dados_diario()
        return {
            "status": "sucesso",
            "historico": dados.get("historico", []),
            "ultimos_palpites": dados.get("ultimos_palpites", [])
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar histórico do diário: {str(e)}"
        )

# Mapeamento para os botões "Recarregar Planilha" e "Recarregar Base"
@app.post("/api/recarregar-base")
@app.post("/api/recarregar-base/")
@app.post("/api/recarregar-planilha")
@app.post("/api/recarregar-planilha/")
@app.get("/api/recarregar-base")
@app.get("/api/recarregar-planilha")
def api_recarregar_base():
    """
    Recarrega a base de dados histórica, reavalia os pesos estatísticos
    e atualiza a trava criptográfica.
    """
    try:
        pesos, valido = integridade.carregar_pesos_para_engine()
        
        if hasattr(painel_auditoria, "gerar_relatorio_html"):
            painel_auditoria.gerar_relatorio_html()
            
        return {
            "status": "sucesso",
            "mensagem": "Base estatística e trava criptográfica recarregadas com sucesso.",
            "trava_valida": valido
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao recarregar a base: {str(e)}"
        )

# Mapeamento de geração de jogos e lapidação genética
@app.post("/api/gerar-jogos")
@app.post("/api/gerar-jogos/")
@app.post("/api/gerar-bilhetes")
@app.post("/api/gerar-bilhetes/")
@app.post("/api/lapidacao")
@app.post("/api/lapidacao/")
def api_gerar_jogos(req: Optional[RequisicaoGerarJogos] = None):
    """
    Gera combinações estatísticas baseadas na seleção ponderada pelos pesos ativos
    e validação de integridade criptográfica SHA-256.
    """
    try:
        qtd = req.quantidade if (req and req.quantidade and req.quantidade > 0) else 10
        concurso = req.concurso if req else None
        resultado = engine.gerar_jogos_genetico(quantidade=qtd, concurso=concurso)
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Falha na geração genética: {str(e)}"
        )

@app.post("/api/rotina-diaria")
@app.post("/api/rotina-diaria/")
def api_executar_rotina_diaria(req: RequisicaoRotinaDiaria):
    """Executa o pipeline diário de simulação, salvamento de diário e atualização do painel."""
    try:
        class Args:
            concurso = req.concurso
            quantidade = req.quantidade or 10
            sem_commit = req.sem_commit
            sem_diario = req.sem_diario
            api_base = "https://api.caixa.gov.br"

        args = Args()
        
        if hasattr(rotina_diaria, "rodar"):
            rotina_diaria.rodar(args)
        elif hasattr(rotina_diaria, "executar"):
            rotina_diaria.executar(args)

        if hasattr(painel_auditoria, "gerar_relatorio_html"):
            painel_auditoria.gerar_relatorio_html()

        return {
            "status": "sucesso",
            "mensagem": "Rotina diária e painel de auditoria atualizados.",
            "concurso": req.concurso
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante a execução da rotina diária: {str(e)}"
        )

@app.get("/api/pesos")
@app.get("/api/pesos/")
def api_obter_pesos():
    """Retorna o estado atual do dicionário de pesos e o status de validação da trava."""
    try:
        pesos, valido = integridade.carregar_pesos_para_engine()
        pesos_dict = engine.extrair_pesos_dict(pesos)
        
        return {
            "trava_valida": valido,
            "hash_sha256": integridade._hash_pesos(pesos_dict),
            "pesos": pesos_dict
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar os pesos ativos: {str(e)}"
        )

@app.get("/auditoria", response_class=HTMLResponse)
def api_exibir_painel_auditoria():
    """Exibe diretamente no navegador o painel estático HTML de auditoria consolidado."""
    caminho_html = "auditoria.html"
    
    if os.path.exists(caminho_html):
        with open(caminho_html, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
            
    try:
        if hasattr(painel_auditoria, "gerar_relatorio_html"):
            painel_auditoria.gerar_relatorio_html()
            if os.path.exists(caminho_html):
                with open(caminho_html, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read(), status_code=200)
    except Exception:
        pass
        
    return HTMLResponse(
        content="<h2>Painel de Auditoria</h2><p>O relatório 'auditoria.html' ainda não foi gerado.</p>",
        status_code=404
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)