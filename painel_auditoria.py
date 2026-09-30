#!/usr/bin/env python3
"""
painel_auditoria.py — Gerador de Painel Único de Auditoria Estática (HTML)
Consolida os dados de integridade.py, backtest.py e diario.py num único arquivo estático.
"""

import os
import json
import csv
from datetime import datetime

# Módulos do Ecossistema
import integridade
import backtest
import diario

ARQUIVO_SAIDA_HTML = "auditoria.html"

def coletar_dados_integridade():
    """Coleta o estado atual do congelamento de pesos e comprovantes."""
    pesos, ativo = integridade.carregar_pesos_para_engine()
    hash_atual = integridade._hash_pesos(pesos)
    
    info_trava = {"ativo": ativo, "hash": hash_atual, "data_trava": "N/A", "dias_validade": "N/A"}
    
    if os.path.exists(integridade.ARQUIVO_TRAVA):
        try:
            with open(integridade.ARQUIVO_TRAVA, "r", encoding="utf-8") as f:
                dados = json.load(f)
                info_trava["data_trava"] = dados.get("data_trava", "N/A")
                info_trava["dias_validade"] = dados.get("dias_validade", "N/A")
        except Exception:
            pass
            
    total_comprovantes = 0
    if os.path.exists(integridade.ARQUIVO_COMPROVANTES):
        try:
            with open(integridade.ARQUIVO_COMPROVANTES, "r", encoding="utf-8") as f:
                total_comprovantes = sum(1 for line in f) - 1
        except Exception:
            pass

    return {
        "status_trava": info_trava,
        "pesos_ativos": pesos,
        "total_comprovantes": max(0, total_comprovantes)
    }

def coletar_dados_diario():
    """Coleta estatísticas do diário de apostas acumuladas."""
    if not os.path.exists(diario.ARQUIVO_PALPITES):
        return {"total_palpites": 0, "media_acertos": 0.0, "desvio_baseline": 0.0, "historico": []}
    
    palpites = []
    acertos_totais = []
    
    try:
        with open(diario.ARQUIVO_PALPITES, "r", encoding="utf-8") as f:
            leitor = csv.DictReader(f)
            for row in leitor:
                palpites.append(row)
                if row.get("acertos") and row["acertos"] != "N/A":
                    acertos_totais.append(int(row["acertos"]))
    except Exception:
        pass
        
    total = len(acertos_totais)
    media = sum(acertos_totais) / total if total > 0 else 0.0
    desvio = media - 9.0  # Baseline teórica
    
    return {
        "total_palpites": len(palpites),
        "total_auditados": total,
        "media_acertos": round(media, 3),
        "desvio_baseline": round(desvio, 3),
        "ultimos_palpites": palpites[-10:]  # Últimos 10
    }

def gerar_html_estatico(dados_int, dados_dia):
    """Gera o HTML estático autocontido com CSS inline profissional."""
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status_trava_badge = (
        '<span class="badge success">ATIVO / ATRELADO</span>' 
        if dados_int["status_trava"]["ativo"] 
        else '<span class="badge warning">DESATIVADO (PESOS PADRÃO)</span>'
    )

    linhas_pesos = "".join([
        f"<tr><td><code>{k}</code></td><td><strong>{v}</strong></td></tr>" 
        for k, v in dados_int["pesos_ativos"].items()
    ])
    
    linhas_historico = "".join([
        f"<tr><td>{p.get('concurso','N/A')}</td><td>{p.get('data','N/A')}</td>"
        f"<td><code>{p.get('hash_bilhete','N/A')[:16]}...</code></td>"
        f"<td><strong>{p.get('acertos','N/A')}</strong></td></tr>"
        for p in reversed(dados_dia["ultimos_palpites"])
    ]) or "<tr><td colspan='4'>Nenhum palpite registrado.</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Painel Consolidador de Auditoria — Lotofácil v8.0</title>
    <style>
        :root {{
            --bg: #0f172a; --card-bg: #1e293b; --text: #f8fafc; 
            --muted: #94a3b8; --border: #334155; --accent: #38bdf8;
            --success: #22c55e; --warning: #f59e0b;
        }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 2rem; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }}
        .card h3 {{ margin-top: 0; color: var(--accent); font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
        .metric {{ font-size: 2rem; font-weight: bold; margin: 0.5rem 0; }}
        .subtext {{ color: var(--muted); font-size: 0.85rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }}
        th, td {{ text-align: left; padding: 0.6rem; border-bottom: 1px solid var(--border); }}
        th {{ color: var(--muted); font-weight: 600; }}
        code {{ background: #0f172a; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; }}
        .badge {{ padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
        .success {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .warning {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h2>Painel de Auditoria e Governança</h2>
            <div class="subtext">Ecossistema Lotofácil v8.0 — Somente Leitura</div>
        </div>
        <div class="subtext">Gerado em: <strong>{agora}</strong></div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Integridade & Governança</h3>
            <div>Status da Trava: {status_trava_badge}</div>
            <div style="margin-top: 1rem;">
                <div class="subtext">Hash Atual dos Pesos:</div>
                <code>{dados_int['status_trava']['hash']}</code>
            </div>
            <div style="margin-top: 0.8rem;" class="subtext">
                Data Trava: {dados_int['status_trava']['data_trava']}<br>
                Validade: {dados_int['status_trava']['dias_validade']} dias<br>
                Comprovantes Pré-Sorteio: <strong>{dados_int['total_comprovantes']}</strong>
            </div>
        </div>

        <div class="card">
            <h3>Desempenho Real Acumulado</h3>
            <div class="metric">{dados_dia['media_acertos']} <span style="font-size: 1rem; color: var(--muted);">acertos/jogo</span></div>
            <div class="subtext">
                Baseline Teórica: <strong>9.000</strong><br>
                Desvio Acumulado: <strong style="color: {'var(--success)' if dados_dia['desvio_baseline'] >= 0 else 'var(--warning)'};">
                    {'+' if dados_dia['desvio_baseline'] > 0 else ''}{dados_dia['desvio_baseline']}
                </strong><br>
                Total Jogos Auditados: <strong>{dados_dia['total_auditados']}</strong> / {dados_dia['total_palpites']}
            </div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Pesos do Motor (Congelados)</h3>
            <table>
                <thead><tr><th>Parâmetro</th><th>Peso Activo</th></tr></thead>
                <tbody>{linhas_pesos}</tbody>
            </table>
        </div>

        <div class="card">
            <h3>Últimos 10 Palpites Auditados</h3>
            <table>
                <thead><tr><th>Concurso</th><th>Data</th><th>Hash Compromisso</th><th>Acertos</th></tr></thead>
                <tbody>{linhas_historico}</tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
    
    with open(ARQUIVO_SAIDA_HTML, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"[+] Painel de auditoria gerado com sucesso: {ARQUIVO_SAIDA_HTML}")

def main():
    dados_int = coletar_dados_integridade()
    dados_dia = coletar_dados_diario()
    gerar_html_estatico(dados_int, dados_dia)

if __name__ == "__main__":
    main()