"""
Fecha o ciclo do fim do dia: gera os bilhetes na API, registra o comprovante
de que foram gerados ANTES do sorteio (integridade.py) e já alimenta o diário
de palpites (diario.py) — tudo num só comando, sem copiar e colar nada à mão.

O QUE ELE FAZ, EM ORDEM
  1. Chama POST /api/gerar-jogos na API (Render) pedindo a quantidade de
     bilhetes de sempre.
  2. Para cada bilhete recebido, grava um comprovante de hash em
     comprovantes.csv (via integridade.py) com o horário exato.
  3. Registra os mesmos bilhetes em palpites.csv (via diario.py), prontos
     para conferir com 'python backtest.py' ou 'python diario.py conferir'
     assim que a planilha for atualizada com o resultado.

Nada disso manda as dezenas para lugar nenhum além do seu computador — o
comprovante é só um hash, e o diário fica local.

USO
    python rotina_diaria.py --concurso 3800
    python rotina_diaria.py --concurso 3800 --quantidade 10
    python rotina_diaria.py --concurso 3800 --api-base http://localhost:8000
    python rotina_diaria.py --concurso 3800 --sem-commit      (pula o comprovante)
    python rotina_diaria.py --concurso 3800 --sem-diario      (pula o diário)
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List

import diario
import integridade

API_BASE_PADRAO = "https://roboweb-cvha.onrender.com"


def gerar_bilhetes(api_base: str, quantidade: int) -> Dict[str, Any]:
    url = f"{api_base}/api/gerar-jogos"
    corpo = json.dumps({"quantidade": quantidade}).encode("utf-8")
    req = urllib.request.Request(
        url, data=corpo, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"A API respondeu erro {e.code}: {detalhe}")
    except urllib.error.URLError as e:
        raise SystemExit(
            f"Não consegui falar com a API em {url} ({e.reason}). "
            f"Ela pode estar dormindo (planos gratuitos do Render hibernam) — tente de novo em 1 minuto."
        )


def formatar_bilhete(dezenas: List[int]) -> str:
    return ",".join(str(d) for d in sorted(dezenas))


def rodar(args) -> None:
    print(f"Pedindo {args.quantidade} bilhetes para {args.api_base} (concurso {args.concurso})...")
    resultado = gerar_bilhetes(args.api_base, args.quantidade)

    bilhetes = resultado.get("bilhetes", [])
    if not bilhetes:
        print("A API não retornou nenhum bilhete.")
        if resultado.get("aviso"):
            print(f"Aviso da API: {resultado['aviso']}")
        return

    print(f"\n{len(bilhetes)} bilhete(s) recebido(s):")
    for i, b in enumerate(bilhetes, 1):
        print(f"  Bilhete {i:2d}: {formatar_bilhete(b)}")
    if resultado.get("aviso"):
        print(f"\nAviso da API: {resultado['aviso']}")

    if not args.sem_commit:
        print("\n--- Registrando comprovantes de integridade ---")
        linhas = integridade._ler_comprovantes()
        novos = 0
        for b in bilhetes:
            h = integridade._hash_bilhete(b)
            if any(l["concurso"] == str(args.concurso) and l["hash"] == h for l in linhas):
                print(f"  (já existia) {h}")
                continue
            linhas.append({
                "concurso": str(args.concurso),
                "hash": h,
                "quantidade_bilhetes": "15",
                "registrado_em": integridade.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            novos += 1
        integridade._gravar_comprovantes(linhas)
        print(f"  {novos} comprovante(s) novo(s) gravado(s) em {integridade.ARQUIVO_COMPROVANTES}.")

    if not args.sem_diario:
        print("\n--- Registrando no diário de palpites ---")
        textos = [formatar_bilhete(b) for b in bilhetes]
        diario.registrar(args.concurso, textos, origem="robo")

    print("\nPronto. Quando a planilha tiver o resultado do concurso "
          f"{args.concurso}, rode 'python diario.py conferir Lotofacil.xlsx' para conferir.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera bilhetes, registra comprovante e alimenta o diário, tudo num comando")
    parser.add_argument("--concurso", type=int, required=True, help="Número do concurso alvo (o próximo a sortear)")
    parser.add_argument("--quantidade", type=int, default=10, help="Quantidade de bilhetes a gerar (padrão: 10)")
    parser.add_argument("--api-base", default=API_BASE_PADRAO, help="URL base da API (padrão: produção no Render)")
    parser.add_argument("--sem-commit", action="store_true", help="Não grava comprovante de integridade")
    parser.add_argument("--sem-diario", action="store_true", help="Não registra no diário de palpites")
    args = parser.parse_args()

    if args.quantidade < 1:
        sys.exit("--quantidade precisa ser pelo menos 1.")

    rodar(args)
import painel_auditoria

# No final da execução da rotina diária:
painel_auditoria.main()