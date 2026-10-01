import json
import integridade
from integridade import PESOS_PADRAO


def test_trava_ida_e_volta(tmp_path):
    alvo = str(tmp_path / "t.json")
    pesos = {str(i): float(i) for i in range(1, 26)}
    integridade.gravar_trava(pesos, alvo)
    lidos, ok = integridade.carregar_pesos_para_engine(alvo)
    assert ok is True and lidos == pesos


def test_json_sem_chave_pesos_nao_e_valido(tmp_path):
    alvo = tmp_path / "t.json"
    alvo.write_text(json.dumps({"qualquer": "coisa"}))
    lidos, ok = integridade.carregar_pesos_para_engine(str(alvo))
    assert ok is False and lidos == PESOS_PADRAO


def test_trava_adulterada_cai_no_padrao(tmp_path):
    alvo = tmp_path / "t.json"
    integridade.gravar_trava({str(i): 2.0 for i in range(1, 26)}, str(alvo))
    dados = json.loads(alvo.read_text())
    dados["pesos"]["1"] = 99.0
    alvo.write_text(json.dumps(dados))
    lidos, ok = integridade.carregar_pesos_para_engine(str(alvo))
    assert ok is False and lidos == PESOS_PADRAO


def test_json_quebrado_cai_no_padrao(tmp_path):
    alvo = tmp_path / "t.json"
    alvo.write_text("nao e json")
    lidos, ok = integridade.carregar_pesos_para_engine(str(alvo))
    assert ok is False and lidos == PESOS_PADRAO


def test_comprovantes_sem_duplicar(tmp_path):
    alvo = str(tmp_path / "c.csv")
    bilhetes = [list(range(1, 16)), list(range(11, 26))]
    assert integridade.registrar_comprovantes(3800, bilhetes, alvo) == (2, 0)
    assert integridade.registrar_comprovantes(3800, bilhetes, alvo) == (0, 2)
    linhas = integridade._ler_comprovantes(alvo)
    assert len(linhas) == 2 and linhas[0]["concurso"] == "3800"