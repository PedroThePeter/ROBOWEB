"""
Rotina do fim do dia, num só comando:
  1. Gera os bilhetes com o motor local.
  2. Grava o comprovante de hash (comprovantes.csv) ANTES do sorteio.
  3. Registra os bilhetes no diário (palpites.json).
  4. Atualiza o painel de auditoria (auditoria.html).

USO
    python rotina_diaria.py --concurso 3800
    python rotina_diaria.py --concurso 3800 --quantidade 10
    python rotina_diaria.py --concurso 3800 --sem-commit    (pula o comprovante)
    python rotina_diaria.py --concurso 3800 --sem-diario    (pula o diário)

Depois do sorteio:  python diario.py conferir Lotofacil.xlsx

Importar este módulo (como o main.py faz) não executa nada: tudo roda só dentro de
executar() ou do bloco __main__.
"""

import argparse
import sys
from datetime import datetime

import diario
import engine
import integridade
import painel_auditoria


def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def executar(args) -> dict:
    """Pipeline diário. Aceita argparse.Namespace ou qualquer objeto com os mesmos atributos."""
    concurso = getattr(args, "concurso", None)
    quantidade = getattr(args, "quantidade", 10) or 10
    sem_commit = getattr(args, "sem_commit", False)
    sem_diario = getattr(args, "sem_diario", False)

    _log("Iniciando rotina diária...")
    try:
        _log(f"Gerando {quantidade} bilhetes para o concurso {concurso or 'não informado'}...")
        dados = engine.gerar_jogos_genetico(quantidade=quantidade, concurso=concurso)

        comprovantes = None
        if sem_commit:
            _log("Comprovante de integridade ignorado (--sem-commit).")
        elif concurso is None:
            _log("AVISO: sem número de concurso não há como gravar comprovante.")
        else:
            novos, repetidos = integridade.registrar_comprovantes(concurso, dados["bilhetes"])
            comprovantes = {"novos": novos, "ja_existiam": repetidos}
            _log(f"Comprovantes: {novos} novo(s), {repetidos} já existia(m).")

        if sem_diario:
            _log("Diário ignorado (--sem-diario).")
        elif diario.salvar_palpites(dados, origem="rotina"):
            _log("Bilhetes registrados no diário.")
        else:
            _log("AVISO: não consegui gravar o diário.")

        if painel_auditoria.gerar_relatorio_html():
            _log("Painel de auditoria atualizado.")
        else:
            _log("AVISO: não consegui gravar o painel de auditoria.")

        _log("Rotina diária concluída.")
        return {
            "status": "sucesso",
            "concurso": concurso,
            "quantidade": quantidade,
            "jogos_gerados": dados["jogos"],
            "comprovantes": comprovantes,
        }
    except Exception as e:
        msg = f"Erro durante a rotina diária: {e}"
        _log(msg)
        return {"status": "erro", "mensagem": msg}


def rodar(args) -> dict:
    """Alias de compatibilidade."""
    return executar(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotina diária - Lotofácil IA v8.0")
    parser.add_argument("--concurso", type=int, required=True, help="Número do concurso alvo (o próximo a sortear)")
    parser.add_argument("--quantidade", type=int, default=10, help="Quantidade de bilhetes (1 a 100)")
    parser.add_argument("--sem-commit", action="store_true", help="Não grava o comprovante de integridade")
    parser.add_argument("--sem-diario", action="store_true", help="Não registra no diário de palpites")
    argumentos = parser.parse_args()

    if not (1 <= argumentos.quantidade <= engine.QUANTIDADE_MAXIMA):
        sys.exit(f"--quantidade precisa estar entre 1 e {engine.QUANTIDADE_MAXIMA}.")

    resultado = executar(argumentos)
    if resultado["status"] != "sucesso":
        sys.exit(1)
    for i, b in enumerate(resultado["jogos_gerados"], 1):
        print(f"  Bilhete {i:2d}: {','.join(str(d) for d in b)}")