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
import desdobramento
import engine
import integridade
import diario
import rotina_diaria
import painel_auditoria
from dados import carregar_sorteios

PLANILHA_PADRAO = "Lotofacil.xlsx"

app = FastAPI(
    title="Lotofácil IA - API Estatística",
    description="API REST para geração, auditoria e conferência de bilhetes da Lotofácil (v8.0)",
    version="8.0"
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
        content={
            "status": "erro",
            "mensagem": f"A rota [{request.method}] {request.url.path} nao foi encontrada no backend.",
            "detail": "Not Found"
        }
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
        
        coluna_concurso = None
        for col in df.columns:
            if str(col).strip().lower() in ['concurso', 'nº concurso', 'bolão', 'concorrencia']:
                coluna_concurso = col
                break
        if coluna_concurso is None and len(df.columns) > 0:
            coluna_concurso = df.columns[0]
            
        if coluna_concurso is not None:
            ultimo_concurso = int(df[coluna_concurso].dropna().iloc[-1])
            return ultimo_concurso + 1
            
        sorteios = carregar_sorteios(caminho)
        if sorteios:
            return len(sorteios) + 1
    except Exception:
        try:
            sorteios = carregar_sorteios(caminho)
            if sorteios:
                return len(sorteios) + 1
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
        "detalhe": f"maior desvio: dezena {dezena:02d}, z = {z:+.2f} (limite {lim:.2f})",
    })

    achados = sum(1 for t in testes if t["achado"])
    conclusao = "Base estatística mapeada. Sem anomalias severas fora da curva padrão."
    return {"testes": testes, "achados": achados, "total_testes": len(testes), "conclusao": conclusao}


def _montar_base() -> dict:
    caminho = _caminho_planilha()
    if not os.path.exists(caminho):
        return {"disponivel": False, "mensagem": f"Planilha '{caminho}' não encontrada no servidor."}
    try:
        sorteios = carregar_sorteios(caminho)
    except Exception as e:
        return {"disponivel": False, "mensagem": f"Não consegui ler a planilha: {e}"}

    base = {"disponivel": True, "concursos": len(sorteios), "memoria": None}
    if len(sorteios) >= 100:
        base["memoria"] = _resumo_memoria(sorteios)
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
        "media_aleatoria": 9.0,
        "taxa_11_aleatoria": round(painel_auditoria._taxa_premio_teorica(), 4),
        "por_temperatura": desempenho_por_origem
    }


@app.get("/api/estatisticas")
def api_estatisticas():
    try:
        if _cache["base"] is None:
            _cache["base"] = _montar_base()
        _, trava_valida = integridade.carregar_pesos_para_engine()
        return {
            "status": "sucesso",
            "base": _cache["base"],
            "trava_valida": trava_valida,
            "desempenho": _desempenho(),
            "aviso": engine.AVISO,
            "proximo_concurso": _obter_proximo_concurso(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recarregar-base")
def api_recarregar_base():
    try:
        caminho = _caminho_planilha()
        try:
            diario.conferir_resultados(caminho)
        except Exception:
            pass

        _cache["base"] = _montar_base()
        _, valido = integridade.carregar_pesos_para_engine()

        proximo = _obter_proximo_concurso()
        mensagem = f"Planilha relida. Conferência térmica executada. Próximo alvo: {proximo}."
        return {
            "status": "sucesso",
            "sucesso": True,
            "mensagem": mensagem,
            "trava_valida": valido,
            "proximo_concurso": proximo,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gerar-jogos")
def api_gerar_jogos():
    concurso = _obter_proximo_concurso()
    try:
        frio = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=0.0)
        morno = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=50.0)
        quente = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=100.0)

        bilhetes = {
            "frio": frio["bilhetes"][0],
            "morno": morno["bilhetes"][0],
            "quente": quente["bilhetes"][0]
        }

        diario.salvar_palpites({"concurso": concurso, "quantidade": 1, "jogos": [bilhetes["frio"]]}, origem="espectro_frio")
        diario.salvar_palpites({"concurso": concurso, "quantidade": 1, "jogos": [bilhetes["morno"]]}, origem="espectro_morno")
        diario.salvar_palpites({"concurso": concurso, "quantidade": 1, "jogos": [bilhetes["quente"]]}, origem="espectro_quente")

        return {"status": "sucesso", "concurso": concurso, "bilhetes": bilhetes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/desdobramento-espectro")
def api_desdobramento_espectro():
    concurso = _obter_proximo_concurso()
    try:
        pesos_dict, _ = integridade.carregar_pesos_para_engine()
        import secrets
        rng = secrets.SystemRandom()
        lista_pesos = [float(pesos_dict.get(str(i), 1.0)) for i in range(1, 26)]
        peso_medio = sum(lista_pesos) / len(lista_pesos)
        
        # Frio (Top 15 dezenas) - Reduzido de 17 para 15 conforme solicitado
        pares_pesos = [(int(k), float(v)) for k, v in pesos_dict.items()]
        pares_pesos.sort(key=lambda x: x[1], reverse=True)
        grupo_frio = sorted([d for d, _ in pares_pesos[:15]])
        
        # Morno (Sorteio limpo interpolado 50% para Pool de 15 dezenas)
        pesos_morno = [p * 0.5 + peso_medio * 0.5 for p in lista_pesos]
        pop_morno = list(range(1, 26))
        restantes_morno = list(pesos_morno)
        grupo_morno = []
        for _ in range(15):
            i = rng.choices(range(len(pop_morno)), weights=restantes_morno, k=1)[0]
            grupo_morno.append(pop_morno.pop(i))
            restantes_morno.pop(i)
        grupo_morno = sorted(grupo_morno)

        # Quente (Estratificado 7-4-4 para Pool de 15 dezenas)
        def escolher_da_faixa(faixa, k):
            sub_pop = list(faixa)
            sub_pesos = [lista_pesos[d - 1] for d in sub_pop]
            escolhidos = []
            for _ in range(k):
                if sum(sub_pesos) <= 0:
                    idx = rng.randrange(len(sub_pop))
                else:
                    idx = rng.choices(range(len(sub_pop)), weights=sub_pesos, k=1)[0]
                escolhidos.append(sub_pop.pop(idx))
                sub_pesos.pop(idx)
            return escolhidos

        grupo_quente = sorted(escolher_da_faixa(range(1, 12), 7) + escolher_da_faixa(range(12, 19), 4) + escolher_da_faixa(range(19, 26), 4))

        # A matriz extrairá 1 bilhete de cada pool, pois o pool agora tem exatos 15 números.
        res_frio = desdobramento.gerar_desdobramento(grupo_frio, garantia=14)
        res_morno = desdobramento.gerar_desdobramento(grupo_morno, garantia=14)
        res_quente = desdobramento.gerar_desdobramento(grupo_quente, garantia=14)

        # Captura o bilhete (o próprio array de 15)
        bilhetes_desd = {
            "frio": res_frio["bilhetes"][0] if res_frio.get("bilhetes") else grupo_frio,
            "morno": res_morno["bilhetes"][0] if res_morno.get("bilhetes") else grupo_morno,
            "quente": res_quente["bilhetes"][0] if res_quente.get("bilhetes") else grupo_quente
        }

        diario.salvar_palpites({"concurso": concurso, "quantidade": 1, "jogos": [bilhetes_desd["frio"]]}, origem="espectro_frio")
        diario.salvar_palpites({"concurso": concurso, "quantidade": 1, "jogos": [bilhetes_desd["morno"]]}, origem="espectro_morno")
        diario.salvar_palpites({"concurso": concurso, "quantidade": 1, "jogos": [bilhetes_desd["quente"]]}, origem="espectro_quente")

        return {"status": "sucesso", "concurso": concurso, "bilhetes": bilhetes_desd}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)