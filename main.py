import os
import statistics
from types import SimpleNamespace
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

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
            "detail": "Not Found",
            "sugestao": "Verifique se a URL no frontend possui prefixo /api/ e o metodo HTTP correto (GET/POST)."
        }
    )


class RequisicaoGerarJogos(BaseModel):
    concurso: Optional[int] = None


class RequisicaoDesdobramentoEspectro(BaseModel):
    concurso: Optional[int] = None


def _caminho_planilha() -> str:
    return os.environ.get("PLANILHA", PLANILHA_PADRAO)


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

    rep = am.teste_repeticao(sorteios)
    lim_rep = am.z_bonferroni(2)
    achado_rep = abs(rep["z"]) > lim_rep or rep["p_qui2"] < 0.025
    testes.append({
        "nome": "Repetição do concurso anterior",
        "achado": achado_rep,
        "detalhe": f"média {rep['media']:.3f} (esperado {am.MEDIA_REPETIDAS:.1f}), z = {rep['z']:+.2f}",
    })

    atraso = am.teste_atraso(sorteios)
    lim_a = am.z_bonferroni(len(atraso))
    rotulo, _, taxa, za = max(atraso, key=lambda x: abs(x[3]))
    testes.append({
        "nome": "Atraso (dívida das dezenas)",
        "achado": abs(za) > lim_a,
        "detalhe": f"maior desvio em K={rotulo}: taxa {taxa:.1%} (esperado 60%), z = {za:+.2f} (limite {lim_a:.2f})",
    })

    pares = am.teste_pares(sorteios)
    lim_p = am.z_bonferroni(len(pares))
    (a, b), cont, zp = pares[0]
    testes.append({
        "nome": "Pares de dezenas",
        "achado": abs(zp) > lim_p,
        "detalhe": f"par mais extremo {a:02d}&{b:02d}: {cont}x, z = {zp:+.2f} (limite {lim_p:.2f})",
    })

    achados = sum(1 for t in testes if t["achado"])
    if achados == 0:
        conclusao = ("Nenhum dos 4 testes encontrou padrão além do acaso. "
                     "Não há o que aprender do histórico para prever o próximo sorteio.")
    else:
        conclusao = (f"{achados} teste(s) apontaram desvio. Isso merece investigação, mas não prova "
                     "que dá para prever: valide fora da amostra (backtest walk-forward).")
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
    if len(sorteios) < 100:
        base["mensagem"] = "Base pequena demais (menos de 100 concursos) para testes confiáveis."
        return base
    base["memoria"] = _resumo_memoria(sorteios)
    return base


def _desempenho() -> dict:
    historico = diario.obter_dados_diario()["historico"]
    acertos = [a for r in historico for a in r.get("acertos", [])]
    if not acertos:
        return {"conferidos": 0, "registros": len(historico)}
    return {
        "conferidos": len(acertos),
        "registros": len(historico),
        "media": round(statistics.mean(acertos), 3),
        "taxa_11": round(sum(1 for a in acertos if a >= 11) / len(acertos), 4),
        "media_aleatoria": 9.0,
        "taxa_11_aleatoria": round(painel_auditoria._taxa_premio_teorica(), 4),
    }


@app.get("/")
@app.get("/api")
def root():
    return {
        "status": "online",
        "sistema": "Lotofácil IA v8.0",
        "modulos_carregados": [
            "engine", "integridade", "diario", "rotina_diaria",
            "painel_auditoria", "analise_memoria", "desdobramento",
        ]
    }


@app.get("/api/status")
@app.get("/status")
def api_status():
    return {"status": "online", "sistema": "Lotofácil IA v8.0"}


@app.get("/api/estatisticas")
@app.get("/api/estatisticas/")
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao montar as estatísticas: {e}")


@app.post("/api/recarregar-base")
@app.post("/api/recarregar-base/")
def api_recarregar_base():
    try:
        _cache["base"] = None
        base = _montar_base()
        _cache["base"] = base
        _, valido = integridade.carregar_pesos_para_engine()
        painel_auditoria.gerar_relatorio_html()

        mensagem = f"Planilha relida ({base.get('concursos', 0)} concursos) e trava verificada."
        return {
            "status": "sucesso",
            "sucesso": True,
            "mensagem": mensagem,
            "trava_valida": valido,
            "concursos": base.get("concursos"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recarregar a base: {e}")


@app.post("/api/gerar-jogos")
@app.post("/api/gerar-jogos/")
def api_gerar_jogos(req: Optional[RequisicaoGerarJogos] = None):
    """Gera exatamente 3 bilhetes automáticos: Frio, Morno e Quente."""
    concurso = req.concurso if req else None
    try:
        frio = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=0.0)
        morno = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=50.0)
        quente = engine.gerar_jogos_genetico(quantidade=1, concurso=concurso, temperatura=100.0)

        bilhetes_triplos = {
            "frio": frio["bilhetes"][0],
            "morno": morno["bilhetes"][0],
            "quente": quente["bilhetes"][0]
        }

        resultado = {
            "status": "sucesso",
            "concurso": concurso,
            "bilhetes": bilhetes_triplos,
            "aviso": engine.AVISO
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha na geração dos bilhetes: {e}")

    try:
        todos_jogos = [bilhetes_triplos["frio"], bilhetes_triplos["morno"], bilhetes_triplos["quente"]]
        todos_hashes = [integridade._hash_bilhete(b) for b in todos_jogos]
        dados_diario = {
            "concurso": concurso,
            "quantidade": 3,
            "jogos": todos_jogos,
            "hashes": todos_hashes,
            "trava_valida": True
        }
        resultado["diario_salvo"] = diario.salvar_palpites(dados_diario, origem="espectro_termico_3")
    except Exception:
        resultado["diario_salvo"] = False
    return resultado


@app.post("/api/desdobramento-espectro")
@app.post("/api/desdobramento-espectro/")
@app.post("/api/desdobramento")
@app.post("/api/desdobramento/")
def api_desdobramento_espectro(req: Optional[RequisicaoDesdobramentoEspectro] = None):
    """Gera exatamente 3 bilhetes de desdobramento térmico automático (Frio, Morno e Quente)."""
    concurso = req.concurso if req and req.concurso else None
    try:
        pesos_dict, _ = integridade.carregar_pesos_para_engine()
        
        # 1. Grupo Frio (Top 17 por peso histórico)
        pares_pesos = [(int(k), float(v)) for k, v in pesos_dict.items()]
        pares_pesos.sort(key=lambda x: x[1], reverse=True)
        grupo_frio = sorted([d for d, _ in pares_pesos[:17]])

        # 2. Grupo Morno (Superposição 50%)
        import secrets
        rng = secrets.SystemRandom()
        lista_pesos = [float(pesos_dict.get(str(i), 1.0)) for i in range(1, 26)]
        peso_medio = sum(lista_pesos) / len(lista_pesos)
        pesos_morno = [p * 0.5 + peso_medio * 0.5 for p in lista_pesos]
        pop = list(range(1, 26))
        restantes = list(pesos_morno)
        grupo_morno = []
        for _ in range(17):
            i = rng.choices(range(len(pop)), weights=restantes, k=1)[0]
            grupo_morno.append(pop.pop(i))
            restantes.pop(i)
        grupo_morno = sorted(grupo_morno)

        # 3. Grupo Quente (Caos / Uniforme)
        grupo_quente = sorted(rng.sample(list(range(1, 26)), 17))

        res_frio = desdobramento.gerar_desdobramento(grupo_frio, garantia=14)
        res_morno = desdobramento.gerar_desdobramento(grupo_morno, garantia=14)
        res_quente = desdobramento.gerar_desdobramento(grupo_quente, garantia=14)

        # Retorna o primeiro bilhete de cada desdobramento espectral para entregar exatamente 3 bilhetes térmicos
        bilhetes_desd = {
            "frio": res_frio["bilhetes"][0],
            "morno": res_morno["bilhetes"][0],
            "quente": res_quente["bilhetes"][0]
        }

        return {
            "status": "sucesso",
            "concurso": concurso,
            "bilhetes": bilhetes_desd,
            "pools": {
                "frio": grupo_frio,
                "morno": grupo_morno,
                "quente": grupo_quente
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha no desdobramento espectral: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)