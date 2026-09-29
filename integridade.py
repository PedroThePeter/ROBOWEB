"""
Guardas de integridade para o robô: trava os pesos contra ajuste por impulso e
prova que um bilhete foi gerado ANTES do sorteio sair (não ajustado depois de
ver o resultado).

POR QUE ISSO EXISTE
O maior risco de um robô "estatístico" não é o código, é o hábito de mexer nos
pesos toda vez que um resultado ruim (ou bom) mexe com a paciência de quem
opera. Isso não é falha de caráter, é um viés bem documentado (data snooping /
p-hacking incremental) que qualquer time cai se não tiver uma barreira
mecânica. Este módulo não decide se um peso é bom ou ruim — só impede que ele
mude fora de um processo deliberado e datado.

SUBCOMANDOS
  travar     Congela os pesos atuais do engine.py por N dias. Enquanto
             travado, o engine ignora qualquer pesos_ativos.json alterado à
             mão e cai de volta nos pesos travados, avisando no console.
  status     Mostra se há trava ativa, até quando, e se o arquivo de pesos
             está consistente com o que foi travado.
  destravar  Libera a trava antes do prazo (pede confirmação explícita).
  commit     Salva um comprovante (hash) dos bilhetes de um concurso ANTES do
             sorteio sair. Não guarda os números em texto puro no comprovante
             público — só o hash, a contagem e o timestamp.
  provar     Depois do sorteio, confere um bilhete contra um comprovante
             salvo, provando que ele já existia antes do resultado.

ARQUIVOS GERADOS (ambos na mesma pasta, versionáveis no git)
  pesos_ativos.json   Pesos em uso + metadados da trava (se houver).
  comprovantes.csv    Um hash por linha, com concurso, timestamp e contagem.

USO
    python integridade.py travar --dias 90
    python integridade.py status
    python integridade.py destravar
    python integridade.py commit --concurso 3800 --bilhete 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
    python integridade.py provar --concurso 3800 --bilhete 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
"""

import argparse
import csv
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from engine import PESOS_PADRAO

ARQUIVO_PESOS = "pesos_ativos.json"
ARQUIVO_COMPROVANTES = "comprovantes.csv"
CAMPOS_COMPROVANTE = ["concurso", "hash", "quantidade_bilhetes", "registrado_em"]


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def _hash_pesos(pesos: Dict[str, int]) -> str:
    canonico = json.dumps(pesos, sort_keys=True)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()[:16]


def _hash_bilhete(dezenas: List[int]) -> str:
    canonico = "-".join(f"{d:02d}" for d in sorted(dezenas))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()[:16]


def _parse_bilhete(texto: str) -> List[int]:
    partes = [p for p in re.split(r"[,\s;-]+", texto.strip()) if p]
    dezenas = sorted(int(p) for p in partes)
    if len(dezenas) != 15 or len(set(dezenas)) != 15:
        raise ValueError(f"Bilhete inválido (precisa de 15 dezenas diferentes): {texto!r}")
    if dezenas[0] < 1 or dezenas[-1] > 25:
        raise ValueError(f"Dezenas devem estar entre 1 e 25: {texto!r}")
    return dezenas


def _ler_config() -> Optional[dict]:
    if not os.path.exists(ARQUIVO_PESOS):
        return None
    with open(ARQUIVO_PESOS, encoding="utf-8") as f:
        return json.load(f)


def _gravar_config(cfg: dict) -> None:
    with open(ARQUIVO_PESOS, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------
# Trava de pesos
# ----------------------------------------------------------------------
def carregar_pesos_para_engine() -> Dict[str, int]:
    """
    Chamada pelo engine.py. Devolve os pesos que devem valer AGORA:
      - Sem pesos_ativos.json: os padrões do código (PESOS_PADRAO).
      - Com trava ativa: os pesos travados, MESMO que alguém tenha editado
        o campo "pesos" do arquivo à mão (detecta pelo hash e avisa).
      - Com trava expirada ou sem trava: os pesos do arquivo, como estão.
    """
    cfg = _ler_config()
    if cfg is None:
        return dict(PESOS_PADRAO)

    pesos_arquivo = cfg.get("pesos", PESOS_PADRAO)
    trava = cfg.get("trava")

    if trava and datetime.fromisoformat(trava["ate"]) > datetime.now():
        pesos_travados = trava["pesos_congelados"]
        if _hash_pesos(pesos_arquivo) != trava["hash_congelado"]:
            print(
                f"[integridade] AVISO: pesos_ativos.json foi editado manualmente, mas há uma "
                f"trava válida até {trava['ate'][:10]}. Usando os pesos TRAVADOS, ignorando a edição.",
            )
        return dict(pesos_travados)

    return dict(pesos_arquivo)


def cmd_travar(args) -> None:
    cfg = _ler_config() or {"pesos": dict(PESOS_PADRAO)}
    pesos_atuais = cfg.get("pesos", PESOS_PADRAO)

    trava_existente = cfg.get("trava")
    if trava_existente and datetime.fromisoformat(trava_existente["ate"]) > datetime.now():
        print(f"Já existe uma trava ativa até {trava_existente['ate'][:10]}. Use 'destravar' antes de travar de novo.")
        return

    ate = datetime.now() + timedelta(days=args.dias)
    cfg["pesos"] = pesos_atuais
    cfg["trava"] = {
        "desde": datetime.now().isoformat(timespec="seconds"),
        "ate": ate.isoformat(timespec="seconds"),
        "pesos_congelados": pesos_atuais,
        "hash_congelado": _hash_pesos(pesos_atuais),
        "motivo": args.motivo or "(não informado)",
    }
    _gravar_config(cfg)
    print(f"Pesos travados até {ate.strftime('%d/%m/%Y')} ({args.dias} dias).")
    print("Enquanto a trava estiver ativa, qualquer edição manual dos pesos será ignorada pelo engine,")
    print("mesmo que alguém edite o arquivo — assim decisões de ajuste não são tomadas no calor de um resultado.")


def cmd_destravar(args) -> None:
    cfg = _ler_config()
    if not cfg or not cfg.get("trava"):
        print("Não há trava ativa.")
        return
    trava = cfg["trava"]
    if datetime.fromisoformat(trava["ate"]) <= datetime.now():
        print("A trava já tinha expirado sozinha.")
        cfg.pop("trava", None)
        _gravar_config(cfg)
        return

    if not args.confirmar:
        print(f"Há uma trava ativa até {trava['ate'][:10]} (motivo: {trava.get('motivo', '?')}).")
        print("Destravar antes do prazo é exatamente o tipo de decisão no calor do momento que a trava existe para evitar.")
        print("Se ainda assim quiser destravar agora, rode de novo com --confirmar.")
        return

    cfg.pop("trava", None)
    _gravar_config(cfg)
    print("Trava removida antes do prazo, por confirmação explícita.")


def cmd_status(args) -> None:
    cfg = _ler_config()
    if cfg is None:
        print("Nenhum pesos_ativos.json encontrado. O engine está usando PESOS_PADRAO do código.")
        return

    pesos = cfg.get("pesos", {})
    print("Pesos atuais no arquivo:")
    for k, v in pesos.items():
        print(f"  {k:22s} {v:3d}")

    trava = cfg.get("trava")
    if not trava:
        print("\nSem trava ativa: os pesos acima valem exatamente como estão no arquivo.")
        return

    ate = datetime.fromisoformat(trava["ate"])
    if ate > datetime.now():
        dias_restantes = (ate - datetime.now()).days
        print(f"\nTRAVADO até {ate.strftime('%d/%m/%Y')} ({dias_restantes} dia(s) restantes).")
        print(f"Motivo registrado: {trava.get('motivo', '?')}")
        if _hash_pesos(pesos) != trava["hash_congelado"]:
            print("ATENÇÃO: o campo 'pesos' do arquivo NÃO bate com o que foi travado.")
            print("O engine está ignorando essa edição e usando os pesos travados originais.")
        else:
            print("Os pesos do arquivo batem com os pesos travados. Tudo consistente.")
    else:
        print(f"\nHavia uma trava, mas expirou em {ate.strftime('%d/%m/%Y')}. Os pesos do arquivo já valem normalmente.")


# ----------------------------------------------------------------------
# Comprovante de geração prévia (commit hash)
# ----------------------------------------------------------------------
def _ler_comprovantes() -> List[Dict[str, str]]:
    if not os.path.exists(ARQUIVO_COMPROVANTES):
        return []
    with open(ARQUIVO_COMPROVANTES, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _gravar_comprovantes(linhas: List[Dict[str, str]]) -> None:
    with open(ARQUIVO_COMPROVANTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_COMPROVANTE)
        w.writeheader()
        w.writerows(linhas)


def cmd_commit(args) -> None:
    linhas = _ler_comprovantes()
    novos = 0
    for txt in args.bilhete:
        dezenas = _parse_bilhete(txt)
        h = _hash_bilhete(dezenas)
        if any(l["concurso"] == str(args.concurso) and l["hash"] == h for l in linhas):
            print(f"  (comprovante já existia) {h}")
            continue
        linhas.append({
            "concurso": str(args.concurso),
            "hash": h,
            "quantidade_bilhetes": "15",
            "registrado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        novos += 1
        print(f"  comprovante gerado: {h}  (concurso {args.concurso})")
    _gravar_comprovantes(linhas)
    print(f"\n{novos} comprovante(s) novo(s). O hash não revela as dezenas — guarde o bilhete original em separado")
    print("(no diario.py, por exemplo) para depois provar com 'python integridade.py provar'.")


def cmd_provar(args) -> None:
    linhas = _ler_comprovantes()
    dezenas = _parse_bilhete(args.bilhete[0]) if args.bilhete else None
    if dezenas is None:
        raise SystemExit("Informe --bilhete para provar.")
    h = _hash_bilhete(dezenas)
    achou = [l for l in linhas if l["concurso"] == str(args.concurso) and l["hash"] == h]
    if achou:
        print(f"CONFERE: este bilhete tem um comprovante registrado em {achou[0]['registrado_em']}")
        print(f"para o concurso {args.concurso}, ou seja, ele já existia antes desse horário.")
    else:
        print("NÃO ENCONTRADO: não há comprovante para exatamente este bilhete e concurso.")
        print("Isso não prova má-fé — pode ser um bilhete que nunca foi commitado antes do sorteio.")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Guardas de integridade do robô: trava de pesos e comprovante de geração prévia")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_tr = sub.add_parser("travar", help="Congela os pesos atuais por N dias")
    p_tr.add_argument("--dias", type=int, default=90, help="Duração da trava em dias (padrão: 90)")
    p_tr.add_argument("--motivo", default=None, help="Anotação livre do porquê da trava (opcional)")

    sub.add_parser("status", help="Mostra o estado atual da trava e dos pesos")

    p_dt = sub.add_parser("destravar", help="Remove a trava antes do prazo")
    p_dt.add_argument("--confirmar", action="store_true", help="Confirma a remoção antecipada da trava")

    p_co = sub.add_parser("commit", help="Salva o hash de bilhetes ANTES do sorteio sair")
    p_co.add_argument("--concurso", type=int, required=True)
    p_co.add_argument("--bilhete", action="append", required=True, help="15 dezenas separadas por vírgula (repita para vários)")

    p_pr = sub.add_parser("provar", help="Confere um bilhete contra um comprovante salvo")
    p_pr.add_argument("--concurso", type=int, required=True)
    p_pr.add_argument("--bilhete", action="append", required=True)

    args = parser.parse_args()

    try:
        if args.comando == "travar":
            cmd_travar(args)
        elif args.comando == "status":
            cmd_status(args)
        elif args.comando == "destravar":
            cmd_destravar(args)
        elif args.comando == "commit":
            cmd_commit(args)
        elif args.comando == "provar":
            cmd_provar(args)
    except ValueError as erro:
        raise SystemExit(f"Erro: {erro}")