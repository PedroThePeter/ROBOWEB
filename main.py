import os
from types import SimpleNamespace
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
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
    description="API REST para geração, auditoria e conferência de bilhetes da Lotofácil (v8.0)",
    version="8.0"
)

# CORS aberto para o frontend. allow_credentials=False porque a API não usa cookies
# (navegadores rejeitam "*" combinado com credenciais).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 404 informando a rota exata pedida pelo frontend ---

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            "status": "erro",
            "mensagem": f"A rota [{request.method}] {request.url.path} nao foi encontrada no backend.",
            "detail": "Not Found",
            "sugestao": "Verifique se a URL no frontend possui prefixo /api/ e o metodo HTTP correto (GET/POST)."
        }
    )


# --- Schemas ---

class RequisicaoGerarJogos(BaseModel):
    concurso: Optional[int] = None
    quantidade: Optional[int] = 10


class RequisicaoRotinaDiaria(BaseModel):
    concurso: Optional[int] = None
    quantidade: Optional[int] = 10
    sem_commit: Optional[bool] = False
    sem_diario: Optional[bool] = False


def _quantidade_segura(valor: Optional[int]) -> int:
    """Padrão 10; nunca acima do limite (evita pedido gigante derrubar o servidor)."""
    if not valor or valor < 1:
        return 10
    return min(valor, engine.QUANTIDADE_MAXIMA)


# --- Endpoints ---

@app.get("/")
@app.get("/api")
def root():
    """Verificação de estado do servidor."""
    return {
        "status": "online",
        "sistema": "Lotofácil IA v8.0",
        "modulos_carregados": ["engine", "integridade", "diario", "rotina_diaria", "painel_auditoria"]
    }


@app.get("/api/status")
@app.get("/status")
def api_status():
    return {"status": "online", "sistema": "Lotofácil IA v8.0"}


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
    """Dados consolidados do diário e últimos palpites."""
    try:
        dados = diario.obter_dados_diario()
        return {
            "status": "sucesso",
            "historico": dados["historico"],
            "ultimos_palpites": dados["ultimos_palpites"],
            "jogos": dados["ultimos_palpites"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar histórico do diário: {e}")


@app.post("/api/recarregar-base")
@app.post("/api/recarregar-base/")
@app.post("/api/recarregar-planilha")
@app.post("/api/recarregar-planilha/")
@app.get("/api/recarregar-base")
@app.get("/api/recarregar-planilha")
def api_recarregar_base():
    """
    Relê a trava de pesos e regenera o painel de auditoria.
    Este endpoint NÃO lê a planilha de resultados (o motor atual não usa a planilha).
    """
    try:
        _, valido = integridade.carregar_pesos_para_engine()
        painel_auditoria.gerar_relatorio_html()
        return {
            "status": "sucesso",
            "mensagem": "Trava de pesos relida e painel de auditoria atualizado.",
            "trava_valida": valido
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recarregar a base: {e}")


@app.post("/api/gerar-jogos")
@app.post("/api/gerar-jogos/")
@app.post("/api/gerar-bilhetes")
@app.post("/api/gerar-bilhetes/")
@app.post("/api/lapidacao")
@app.post("/api/lapidacao/")
def api_gerar_jogos(req: Optional[RequisicaoGerarJogos] = None):
    """Gera bilhetes pelos pesos ativos e registra no diário."""
    qtd = _quantidade_segura(req.quantidade if req else None)
    concurso = req.concurso if req else None
    try:
        resultado = engine.gerar_jogos_genetico(quantidade=qtd, concurso=concurso)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha na geração dos bilhetes: {e}")

    # Falha ao gravar o diário (ex.: disco somente leitura) não deve perder os bilhetes gerados.
    try:
        resultado["diario_salvo"] = diario.salvar_palpites(resultado, origem="api")
    except Exception:
        resultado["diario_salvo"] = False
    return resultado


@app.post("/api/rotina-diaria")
@app.post("/api/rotina-diaria/")
def api_executar_rotina_diaria(req: RequisicaoRotinaDiaria):
    """Executa gerar + comprovante + diário + painel."""
    args = SimpleNamespace(
        concurso=req.concurso,
        quantidade=_quantidade_segura(req.quantidade),
        sem_commit=bool(req.sem_commit),
        sem_diario=bool(req.sem_diario),
    )
    resultado = rotina_diaria.executar(args)
    if resultado.get("status") != "sucesso":
        raise HTTPException(status_code=500, detail=resultado.get("mensagem", "Erro na rotina diária."))
    return {
        "status": "sucesso",
        "mensagem": "Rotina diária concluída e painel de auditoria atualizado.",
        "concurso": resultado["concurso"],
        "jogos": resultado["jogos_gerados"],
        "comprovantes": resultado["comprovantes"],
    }


@app.get("/api/pesos")
@app.get("/api/pesos/")
def api_obter_pesos():
    """Pesos ativos e status da trava."""
    try:
        pesos, valido = integridade.carregar_pesos_para_engine()
        return {
            "trava_valida": valido,
            "hash_sha256": integridade._hash_pesos(pesos),
            "pesos": pesos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar os pesos ativos: {e}")


@app.get("/auditoria", response_class=HTMLResponse)
def api_exibir_painel_auditoria():
    """Mostra o painel estático de auditoria (gera na hora se ainda não existir)."""
    caminho = painel_auditoria.CAMINHO_PADRAO
    if not os.path.exists(caminho):
        painel_auditoria.gerar_relatorio_html(caminho)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(
        content="<h2>Painel de Auditoria</h2><p>Não foi possível gerar o relatório 'auditoria.html'.</p>",
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)