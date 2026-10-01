import html
import math
import statistics

import diario
import integridade

CAMINHO_PADRAO = "auditoria.html"


def _taxa_premio_teorica() -> float:
    """Chance de um bilhete aleatório fazer 11+ pontos (~10,6%)."""
    total = math.comb(25, 15)
    return sum(math.comb(15, k) * math.comb(10, 15 - k) for k in range(11, 16)) / total


def _tags(jogo) -> str:
    try:
        return "".join(f'<span class="tag">{int(d):02d}</span>' for d in jogo)
    except (TypeError, ValueError):
        return html.escape(str(jogo))


def gerar_relatorio_html(caminho_saida: str = CAMINHO_PADRAO) -> bool:
    """Gera o relatório estático de auditoria. Retorna True se gravou o arquivo."""
    dados = diario.obter_dados_diario()
    historico = dados["historico"]
    ultimos = dados["ultimos_palpites"]

    try:
        _, trava_valida = integridade.carregar_pesos_para_engine()
    except Exception:
        trava_valida = False

    try:
        n_comprovantes = len(integridade._ler_comprovantes())
    except Exception:
        n_comprovantes = 0

    status_class = "status-ok" if trava_valida else "status-alert"
    status_text = "VALIDADA (Ativa)" if trava_valida else "NÃO ATIVA (usando pesos padrão)"

    if ultimos:
        jogos_html = "".join(
            f'<div style="margin-bottom:0.5rem;"><strong>Jogo {i}:</strong> {_tags(j)}</div>'
            for i, j in enumerate(ultimos, 1)
        )
    else:
        jogos_html = "<p>Nenhum palpite registrado recentemente.</p>"

    acertos = [a for r in historico for a in r.get("acertos", [])]
    if acertos:
        media = statistics.mean(acertos)
        taxa = sum(1 for a in acertos if a >= 11) / len(acertos)
        desempenho_html = (
            f"<p>Bilhetes conferidos: <strong>{len(acertos)}</strong></p>"
            f"<p>Média de acertos: <strong>{media:.2f}</strong> (um bilhete aleatório faz 9,00)</p>"
            f"<p>Bilhetes com 11+: <strong>{taxa:.1%}</strong> "
            f"(um bilhete aleatório faz {_taxa_premio_teorica():.1%})</p>"
        )
    else:
        desempenho_html = (
            "<p>Nenhum bilhete conferido ainda. Rode <code>python diario.py conferir Lotofacil.xlsx</code> "
            "depois que o sorteio sair.</p>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Auditoria - Lotofácil IA v8.0</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 0.5rem; }}
        .card {{ background: #1e293b; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #334155; }}
        .status-ok {{ color: #4ade80; font-weight: bold; }}
        .status-alert {{ color: #f87171; font-weight: bold; }}
        .tag {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; background: #334155; font-size: 0.875rem; margin: 0.1rem; color: #38bdf8; font-weight: bold; }}
        code {{ background: #334155; padding: 0.1rem 0.3rem; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Painel de Auditoria e Governança (v8.0)</h1>

        <div class="card">
            <h2>Integridade da Trava SHA-256</h2>
            <p>Status: <span class="{status_class}">{status_text}</span></p>
            <p>Registros no diário: <strong>{len(historico)}</strong> | Comprovantes de hash: <strong>{n_comprovantes}</strong></p>
        </div>

        <div class="card">
            <h2>Desempenho real conferido</h2>
            {desempenho_html}
        </div>

        <div class="card">
            <h2>Últimos Palpites Registrados ({len(ultimos)})</h2>
            {jogos_html}
        </div>
    </div>
</body>
</html>"""

    try:
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True
    except OSError:
        return False


def main():
    """Ponto de entrada para chamadas externas a painel_auditoria.main()."""
    return gerar_relatorio_html()


if __name__ == "__main__":
    main()