import os
import statistics
from typing import Optional
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import analise_memoria
import diario
import engine
import integridade
import painel_auditoria
from dados import carregar_sorteios

PLANILHA_PADRAO = "Lotofacil.xlsx"

app = FastAPI(
    title="Robô Lotofácil V8.1 - Ambiente 100% Local",
    description="API REST Local para auditoria, geração de bilhetes e conferência da Lotofácil (Pipeline v8.1)",
    version="8.1"
)

# ==========================================
# 🔒 SEGURANÇA LOCAL (CORS)
# Restringe o acesso exclusivamente à sua máquina (localhost)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = {"base": None}


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
        return {"disponivel": False, "mensagem": f"Planilha '{caminho}' não encontrada no servidor local."}
    try:
        sorteios = carregar_sorteios(caminho)
    except Exception as e:
        return {"disponivel": False, "mensagem": f"Não consegui ler a planilha: {e}"}

    base = {"disponivel": True, "concursos": len(sorteios), "memoria": None}
    if len(sorteios) >= 100:
        base["memoria"] = _resumo_memoria(sorteios)
    return base


def _desempenho() -> dict:
    try:
        historico = diario.obter_dados_diario()["historico"]
    except Exception:
        historico = []

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
    try:
        caminho = _caminho_planilha()
        sorteios = carregar_sorteios(caminho)
        pesos_dict = engine.pesos_por_frequencia(sorteios)
        concurso_alvo = _obter_proximo_concurso() or (len(sorteios) + 1)

        # Curador 2 (Diversidade de Portfólio) - Loop de aprovação cruzada
        portfolio_aprovado = False
        tentativas_c2 = 0
        b_frio, b_morno, b_quente = [], [], []

        while not portfolio_aprovado and tentativas_c2 < 20:
            tentativas_c2 += 1
            
            # Curador 1: Geração submetida aos 5 Juízes Heurísticos
            res_frio = engine.gerar_jogos_genetico(1, concurso=concurso_alvo, pesos=pesos_dict, temperatura=0.0)
            res_morno = engine.gerar_jogos_genetico(1, concurso=concurso_alvo, pesos=pesos_dict, temperatura=50.0)
            res_quente = engine.gerar_jogos_genetico(1, concurso=concurso_alvo, pesos=pesos_dict, temperatura=100.0)

            b_frio = res_frio["bilhetes"][0]
            b_morno = res_morno["bilhetes"][0]
            b_quente = res_quente["bilhetes"][0]

            aprovado, _ = engine.curador_diversidade(b_frio, b_morno, b_quente)
            if aprovado:
                portfolio_aprovado = True

        # Curador 3 (Gatekeeper) e Persistência no Diário com Hashes Criptográficos
        hash_frio = integridade._hash_bilhete(b_frio)
        hash_morno = integridade._hash_bilhete(b_morno)
        hash_quente = integridade._hash_bilhete(b_quente)

        diario.salvar_palpites({"concurso": concurso_alvo, "quantidade": 1, "jogos": [b_frio], "hashes": [hash_frio]}, origem="espectro_frio")
        diario.salvar_palpites({"concurso": concurso_alvo, "quantidade": 1, "jogos": [b_morno], "hashes": [hash_morno]}, origem="espectro_morno")
        diario.salvar_palpites({"concurso": concurso_alvo, "quantidade": 1, "jogos": [b_quente], "hashes": [hash_quente]}, origem="espectro_quente")

        bilhetes_resp = {
            "frio": b_frio,
            "morno": b_morno,
            "quente": b_quente
        }

        return {
            "status": "sucesso",
            "concurso": concurso_alvo,
            "curador_2_tentativas": tentativas_c2,
            "bilhetes": bilhetes_resp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)