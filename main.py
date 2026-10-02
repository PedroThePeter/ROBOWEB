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

# CORS aberto para o frontend. allow_credentials=False porque a API não usa cookies
# (navegadores rejeitam "*" combinado com credenciais).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache da parte cara (ler a planilha + testes de memória). Limpo em /api/recarregar-base.
_cache = {"base": None}


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
    temperatura: Optional[float] = 0.0  # NOVA VARIÁVEL QUÂNTICA/TERMODINÂMICA


class RequisicaoRotinaDiaria(BaseModel):
    concurso: Optional[int] = None
    quantidade: Optional[int] = 10
    sem_commit: Optional[bool] = False
    sem_diario: Optional[bool] = False


class RequisicaoDesdobramento(BaseModel):
    dezenas: List[int]
    garantia: int = 14
    concurso: Optional[int] = None  # se informado, grava comprovantes e registra no diário


def _quantidade_segura(valor: Optional[int]) -> int:
    """Padrão 10; nunca acima do limite (evita pedido gigante derrubar o servidor)."""
    if not valor or valor < 1:
        return 10
    return min(valor, engine.QUANTIDADE_MAXIMA)


# --- Estatísticas reais (planilha + testes de memória + desempenho conferido) ---

def _caminho_planilha() -> str:
    return os.environ.get("PLANILHA", PLANILHA_PADRAO)


def _resumo_memoria(sorteios) -> dict:
    """Roda os 4 testes do analise_memoria e resume cada um (sem imprimir nada)."""
    am = analise_memoria
    testes = []

    # 1) Frequência das dezenas
    freq = am.teste_frequencia(sorteios)
    lim = am.z_bonferroni(25)
    dezena, (_, z) = max(freq.items(), key=lambda x: abs(x[1][1]))
    testes.append({
        "nome": "Frequência das dezenas",
        "achado": abs(z) > lim,
        "detalhe": f"maior desvio: dezena {dezena:02d}, z = {z:+.2f} (limite {lim:.2f})",
    })

    # 2) Repetição do concurso anterior
    rep = am.teste_repeticao(sorteios)
    lim_rep = am.z_bonferroni(2)
    achado_rep = abs(rep["z"]) > lim_rep or rep["p_qui2"] < 0.025
    testes.append({
        "nome": "Repetição do concurso anterior",
        "achado": achado_rep,
        "detalhe": f"média {rep['media']:.3f} (esperado {am.MEDIA_REPETIDAS:.1f}), z = {rep['z']:+.2f}",
    })

    # 3) Atraso
    atraso = am.teste_atraso(sorteios)
    lim_a = am.z_bonferroni(len(atraso))
    rotulo, _, taxa, za = max(atraso, key=lambda x: abs(x[3]))
    testes.append({
        "nome": "Atraso (dívida das dezenas)",
        "achado": abs(za) > lim_a,
        "detalhe": f"maior desvio em K={rotulo}: taxa {taxa:.1%} (esperado 60%), z = {za:+.2f} (limite {lim_a:.2f})",
    })

    # 4) Pares
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


def _registrar_desdobramento(concurso: int, bilhetes: List[List[int]]) -> dict:
    """Grava comprovantes (hash) e diário para os bilhetes do desdobramento."""
    registro = {"comprovantes": None, "diario_salvo": False}
    try:
        novos, repetidos = integridade.registrar_comprovantes(concurso, bilhetes)
        registro["comprovantes"] = {"novos": novos, "ja_existiam": repetidos}
    except Exception:
        pass
    try:
        registro["diario_salvo"] = diario.salvar_palpites(
            {
                "concurso": concurso,
                "quantidade": len(bilhetes),
                "jogos": bilhetes,
                "hashes": [integridade._hash_bilhete(b) for b in bilhetes],
                "trava_valida": False,
            },
            origem="desdobramento",
        )
    except Exception:
        pass
    return registro


# --- Endpoints ---

@app.get("/")
@app.get("/api")
def root():
    """Verificação de estado do servidor."""
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
    """Painel do frontend: base histórica, testes de memória, trava e desempenho real."""
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
    """Relê a planilha (refaz os testes de memória), a trava de pesos e o painel de auditoria."""
    try:
        _cache["base"] = None
        base = _montar_base()
        _cache["base"] = base
        _, valido = integridade.carregar_pesos_para_engine()
        painel_auditoria.gerar_relatorio_html()

        if base.get("disponivel"):
            mensagem = f"Planilha relida ({base['concursos']} concursos), trava verificada e painel atualizado."
        else:
            mensagem = f"Trava verificada e painel atualizado. Atenção: {base['mensagem']}"
        return {
            "status": "sucesso",
            "sucesso": True,  # compatibilidade com frontends antigos
            "mensagem": mensagem,
            "trava_valida": valido,
            "concursos": base.get("concursos"),
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
    """Gera bilhetes pelos pesos ativos (modulados pela temperatura) e registra no diário."""
    qtd = _quantidade_segura(req.quantidade if req else None)
    concurso = req.concurso if req else None
    temperatura = req.temperatura if req else 0.0 # Aplicação da Temperatura
    try:
        resultado = engine.gerar_jogos_genetico(quantidade=qtd, concurso=concurso, temperatura=temperatura)
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


@app.post("/api/desdobramento")
@app.post("/api/desdobramento/")
def api_desdobramento(req: RequisicaoDesdobramento):
    """
    Desdobramento com garantia para um grupo de 16 a 18 dezenas.
    Se 'concurso' vier preenchido, grava comprovantes e registra os bilhetes no diário.
    """
    try:
        resultado = desdobramento.gerar_desdobramento(req.dezenas, req.garantia)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha no desdobramento: {e}")

    resultado["melhor_acerto_se_pool_conter_sorteio"] = {
        str(k): v for k, v in resultado["melhor_acerto_se_pool_conter_sorteio"].items()
    }
    resultado["status"] = "sucesso"
    resultado["concurso"] = req.concurso
    resultado["registro"] = (
        _registrar_desdobramento(req.concurso, resultado["bilhetes"])
        if req.concurso is not None else None
    )
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