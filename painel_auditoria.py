import os
import json
import integridade
import diario

def gerar_relatorio_html(caminho_saida="auditoria.html"):
    """
    Gera o relatório estático de auditoria HTML de forma segura,
    evitando KeyError caso a chave 'ultimos_palpites' ou arquivos estejam ausentes.
    """
    # Carrega dados do diário de forma tolerante a falhas
    palpites_raw = diario.carregar_palpites()
    
    ultimos_palpites = []
    historico_total = []

    if isinstance(palpites_raw, dict):
        ultimos_palpites = palpites_raw.get("ultimos_palpites") or palpites_raw.get("jogos") or []
        historico_total = palpites_raw.get("historico", [])
    elif isinstance(palpites_raw, list):
        historico_total = palpites_raw
        if palpites_raw:
            ultimo_registro = palpites_raw[-1]
            if isinstance(ultimo_registro, dict):
                ultimos_palpites = ultimo_registro.get("jogos", [])
            elif isinstance(ultimo_registro, list):
                ultimos_palpites = ultimo_registro

    # Carrega pesos e estado da trava criptográfica
    try:
        retorno_pesos = integridade.carregar_pesos_para_engine()
        if isinstance(retorno_pesos, tuple):
            pesos, trava_valida = retorno_pesos
        else:
            pesos, trava_valida = retorno_pesos, True
    except Exception:
        pesos, trava_valida = {}, False

    # Renderiza o HTML estático
    status_class = "status-ok" if trava_valida else "status-alert"
    status_text = "VALIDADA (Ativa)" if trava_valida else "VIOLADA / FALLBACK ATIVO"

    jogos_html = ""
    if ultimos_palpites:
        for idx, jogo in enumerate(ultimos_palpites, 1):
            if isinstance(jogo, list):
                dezenas_tags = "".join([f'<span class="tag">{d:02d}</span>' for d in jogo])
                jogos_html += f'<div style="margin-bottom:0.5rem;"><strong>Jogo {idx}:</strong> {dezenas_tags}</div>'
    else:
        jogos_html = "<p>Nenhum palpite registrado recentemente.</p>"

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
    </style>
</head>
<body>
    <div class="container">
        <h1>Painel de Auditoria e Governança (v8.0)</h1>
        
        <div class="card">
            <h2>Integridade da Trava SHA-256</h2>
            <p>Status: <span class="{status_class}">{status_text}</span></p>
            <p>Total de Registros no Diário: <strong>{len(historico_total)}</strong></p>
        </div>

        <div class="card">
            <h2>Últimos Palpites Registrados ({len(ultimos_palpites)})</h2>
            {jogos_html}
        </div>
    </div>
</body>
</html>"""

    try:
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    gerar_relatorio_html()