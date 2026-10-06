import os
import statistics
from types import SimpleNamespace
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd

import analise_memoria
import engine
import integridade
import diario
import rotina_diaria
import painel_auditoria
from dados import carregar_sorteios

PLANILHA_PADRAO = "Lotofacil.xlsx"

app = FastAPI(
    title="Lotofácil IA - API Estatística (Curadoria Pipeline)",
    description="API REST para geração filtrada, auditoria e conferência da Lotofácil (v8.1)",
    version="8.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = {"base": None}


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"status": "erro", "mensagem": "Rota não encontrada."}
    )

def _caminho_planilha() -> str:
    return os.environ.get("PLANILHA", PLANILHA_PADRAO)

def _obter_proximo_concurso() -> Optional[int]:
    caminho = _caminho_planilha()
    if not os.path.exists(caminho):
        return None
    try:
        xls = pd.ExcelFile(caminho)
        df = pd.read_excel(xls, sheet_name=0)
        coluna_concurso = next((col for col in df.columns if str(col).strip().lower() in ['concurso', 'nº concurso', 'bolão', 'concorrencia']), None)
        if coluna_concurso is None and len(df.columns) > 0:
            coluna_concurso = df.columns[0]
        if coluna_concurso is not None:
            return int(df[coluna_concurso].dropna().iloc[-1]) + 1
    except Exception:
        pass
    try:
        sorteios = carregar_sorteios(caminho)
        if sorteios: return len(sorteios) + 1
    except Exception:
        pass
    return None

def _resumo_memoria(sorteios) -> dict:
    am = analise_memoria
    testes = []
    freq = am.teste_frequencia(sorteios)
    lim = am.z_bonferroni(25)
    dezena, (_, z) = max(freq.items(), key=lambda x: abs(x[1][1]))
    testes.append({
        "nome": "Frequência das dezenas",
        "achado": abs(z) > lim,
        "detalhe": f"maior desvio: dezena {dezena:02d}, z = {z:+.2f}",
    })
    return {"testes": testes, "achados": sum(1 for t in testes if t["achado"]), "total_testes": len(testes)}

def _montar_base() -> dict:
    caminho = _caminho_planilha()
    if not os.path.exists(caminho): return {"disponivel": False, "mensagem": "Planilha não encontrada."}
    try:
        sorteios = carregar_sorteios(caminho)
    except Exception as e:
        return {"disponivel": False, "mensagem": str(e)}
    base = {"disponivel": True, "concursos": len(sorteios), "memoria": None}
    if len(sorteios) >= 100: base["memoria"] = _resumo_memoria(sorteios)
    return base

def _desempenho() -> dict:
    historico = diario.obter_dados_diario()["historico"]
    acertos_geral = [a for r in historico for a in r.get("acertos", [])]
    
    desempenho_por_origem = {}
    for origem in ["espectro_frio", "espectro_morno", "espectro_quente"]:
        acertos_origem = [a for r in historico if r.get("origem") == origem for a in r.get("acertos", [])]
        if acertos_origem:
            desempenho_por_origem[origem] = {
                "conferidos": len(acertos_origem),
                "media": round(statistics.mean(acertos_origem), 3),
                "taxa_11": round(sum(1 for a in acertos_origem if a >= 11) / len(acertos_origem), 4)
            }
        else:
            desempenho_por_origem[origem] = {"conferidos": 0, "media": 0.0, "taxa_11": 0.0}

    if not acertos_geral:
        return {"conferidos": 0, "registros": len(historico), "por_temperatura": desempenho_por_origem}
        
    return {
        "conferidos": len(acertos_geral),
        "registros": len(historico),
        "media": round(statistics.mean(acertos_geral), 3),
        "taxa_11": round(sum(1 for a in acertos_geral if a >= 11) / len(acertos_geral), 4),
        "por_temperatura": desempenho_por_origem
    }

@app.get("/api/estatisticas")
def api_estatisticas():
    try:
        if _cache["base"] is None: _cache["base"] = _montar_base()
        _, trava_valida = integridade.carregar_pesos_para_engine()
        return {
            "status": "sucesso", "base": _cache["base"], "trava_valida": trava_valida,
            "desempenho": _desempenho(), "aviso": engine.AVISO, "proximo_concurso": _obter_proximo_concurso(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recarregar-base")
def api_recarregar_base():
    try:
        caminho = _caminho_planilha()
        try: diario.conferir_resultados(caminho)
        except Exception: pass
        _cache["base"] = _montar_base()
        _, valido = integridade.carregar_pesos_para_engine()
        return {"status": "sucesso", "mensagem": "Planilha relida. Conferência térmica executada.", "trava_valida": valido}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gerar-jogos")
def api_gerar_jogos():
    concurso = _obter_proximo_concurso()
    try:
        portfolio_aprovado = False
        tentativas = 0
        relatorio_c2 = ""
        b_frio, b_morno, b_quente = [], [], []

        # CICLO DO CURADOR 2 (Garante a Diversidade)
        while not portfolio_aprovado and tentativas < 20:
            tentativas += 1
            frio_res = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=0.0)
            morno_res = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=50.0)
            quente_res = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=100.0)
            
            b_frio = frio_res["bilhetes"][0]
            b_morno = morno_res["bilhetes"][0]
            b_quente = quente_res["bilhetes"][0]
            
            aprovado, relatorio_c2 = engine.curador_diversidade(b_frio, b_morno, b_quente)
            if aprovado:
                portfolio_aprovado = True

        # CURADOR 3: Gatekeeper Sistêmico
        def curador_gatekeeper(f, m, q, conc):
            if len(f) != 15 or len(m) != 15 or len(q) != 15:
                raise ValueError("Curador 3 abortou a transação: Anomalia no tamanho dos vetores.")
            
            diario.salvar_palpites({"concurso": conc, "quantidade": 1, "jogos": [f], "hashes": [integridade._hash_bilhete(f)]}, origem="espectro_frio")
            diario.salvar_palpites({"concurso": conc, "quantidade": 1, "jogos": [m], "hashes": [integridade._hash_bilhete(m)]}, origem="espectro_morno")
            diario.salvar_palpites({"concurso": conc, "quantidade": 1, "jogos": [q], "hashes": [integridade._hash_bilhete(q)]}, origem="espectro_quente")
            return "Curador 3: Integridade validada e hashes persistidos no diário."

        relatorio_c3 = curador_gatekeeper(b_frio, b_morno, b_quente, concurso)

        bilhetes = {"frio": b_frio, "morno": b_morno, "quente": b_quente}
        relatorio_final = f"{relatorio_c2} | {relatorio_c3}"

        return {"status": "sucesso", "concurso": concurso, "bilhetes": bilhetes, "curadoria": relatorio_final}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)