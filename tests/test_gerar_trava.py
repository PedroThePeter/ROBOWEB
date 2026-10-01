import gerar_trava
import integridade


def _csv(tmp_path, n=5):
    cabecalho = ",".join(["Concurso"] + [f"Bola{i}" for i in range(1, 16)])
    linhas = [cabecalho]
    for c in range(1, n + 1):
        linhas.append(",".join([str(c)] + [str(d) for d in range(1, 16)]))
    caminho = tmp_path / "resultados.csv"
    caminho.write_text("\n".join(linhas), encoding="utf-8")
    return str(caminho)


def test_gerar_trava_ida_e_volta(tmp_path):
    planilha = _csv(tmp_path, n=5)
    alvo = str(tmp_path / "trava.json")
    r = gerar_trava.gerar_trava(planilha, janela=3, caminho_trava=alvo)
    assert r["concursos"] == 5
    # dezenas 1..15 saíram nos 3 últimos concursos (+1); as demais só têm a suavização
    assert r["pesos"]["1"] == 4.0 and r["pesos"]["25"] == 1.0

    lidos, ok = integridade.carregar_pesos_para_engine(alvo)
    assert ok is True and lidos == r["pesos"]


def test_janela_zero_usa_toda_a_base(tmp_path):
    planilha = _csv(tmp_path, n=5)
    r = gerar_trava.gerar_trava(planilha, janela=0, caminho_trava=str(tmp_path / "t.json"))
    assert r["pesos"]["1"] == 6.0


def test_trava_uniforme(tmp_path):
    alvo = str(tmp_path / "t.json")
    gerar_trava.gerar_trava_uniforme(alvo)
    lidos, ok = integridade.carregar_pesos_para_engine(alvo)
    assert ok is True and lidos == integridade.PESOS_PADRAO