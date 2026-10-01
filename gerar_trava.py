"""
Gera a trava de pesos (trava.json) a partir da planilha de resultados.

Os pesos são os mesmos que o backtest usa: vezes que cada dezena saiu nos últimos
--janela concursos (+1 de suavização). Use a MESMA janela no backtest e aqui, para
testar exatamente o que vai para produção.

ATENÇÃO: o backtest e o analise_memoria existem para dizer se isso supera o acaso.
Se o backtest disser "indistinguível do acaso", esses pesos não aumentam a chance
de acerto: servem apenas para variar a distribuição dos bilhetes.

USO
    python gerar_trava.py Lotofacil.xlsx --janela 100
    python gerar_trava.py Lotofacil.xlsx --janela 0        (usa toda a base)
    python gerar_trava.py --uniforme                       (volta a pesos iguais)
"""

import argparse
from typing import Dict, List, Optional

import engine
import integridade
from dados import carregar_sorteios


def montar_pesos(sorteios: List[List[int]], janela: int = 100) -> Dict[str, float]:
    """Pesos por frequência na janela dos últimos concursos (0 = toda a base)."""
    return engine.pesos_por_frequencia(sorteios, janela or None)


def gerar_trava(planilha: str, janela: int = 100, caminho_trava: Optional[str] = None) -> dict:
    """Lê a planilha, calcula os pesos e grava a trava. Retorna um resumo."""
    sorteios = carregar_sorteios(planilha)
    if not sorteios:
        raise ValueError("A planilha não tem nenhum concurso válido.")
    pesos = montar_pesos(sorteios, janela)
    hash_pesos = integridade.gravar_trava(pesos, caminho_trava)
    return {
        "concursos": len(sorteios),
        "janela": janela,
        "hash": hash_pesos,
        "pesos": pesos,
    }


def gerar_trava_uniforme(caminho_trava: Optional[str] = None) -> str:
    """Grava uma trava com todos os pesos iguais (sorteio uniforme). Retorna o hash."""
    return integridade.gravar_trava(integridade.PESOS_PADRAO.copy(), caminho_trava)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Gera a trava de pesos da Lotofácil a partir da planilha")
    parser.add_argument("planilha", nargs="?", help="Caminho para Lotofacil.xlsx")
    parser.add_argument("--janela", type=int, default=100,
                        help="Concursos recentes usados nos pesos (0 = toda a base). Padrão: 100")
    parser.add_argument("--uniforme", action="store_true",
                        help="Grava a trava com pesos iguais, em vez de ler a planilha")
    parser.add_argument("--saida", default=None, help="Caminho da trava (padrão: trava.json)")
    args = parser.parse_args()

    if args.janela < 0:
        parser.error("--janela não pode ser negativa.")

    if args.uniforme:
        h = gerar_trava_uniforme(args.saida)
        print("Trava uniforme gravada (todas as dezenas com peso 1,0).")
        print(f"Hash SHA-256: {h}")
        return

    if not args.planilha:
        parser.error("Informe a planilha (ou use --uniforme).")

    r = gerar_trava(args.planilha, args.janela, args.saida)
    ordenadas = sorted(r["pesos"].items(), key=lambda x: x[1], reverse=True)

    print(f"Trava gravada com {r['concursos']} concursos | janela: {r['janela'] or 'toda a base'}")
    print(f"Hash SHA-256: {r['hash']}")
    print("Mais pesadas : " + ", ".join(f"{int(d):02d} ({p:.0f})" for d, p in ordenadas[:5]))
    print("Mais leves   : " + ", ".join(f"{int(d):02d} ({p:.0f})" for d, p in ordenadas[-5:]))
    print()
    print("Lembrete: confirme com o backtest (mesma --janela) se isso supera o acaso.")
    print(f"    python backtest.py {args.planilha} --janela {args.janela} --semente 42")


if __name__ == "__main__":
    _main()