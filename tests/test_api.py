from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_desdobramento_ok():
    r = client.post("/api/desdobramento", json={"dezenas": list(range(1, 18)), "garantia": 14})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["garantia_verificada"] is True
    assert corpo["quantidade_bilhetes"] == len(corpo["bilhetes"])
    assert all(len(b) == 15 for b in corpo["bilhetes"])


def test_desdobramento_grupo_invalido():
    r = client.post("/api/desdobramento", json={"dezenas": list(range(1, 11)), "garantia": 14})
    assert r.status_code == 400


def test_desdobramento_dezenas_repetidas():
    dezenas = list(range(1, 17)) + [1]
    r = client.post("/api/desdobramento", json={"dezenas": dezenas, "garantia": 14})
    assert r.status_code == 400


def test_estatisticas_sem_planilha_nao_quebra(tmp_path, monkeypatch):
    monkeypatch.setenv("PLANILHA", str(tmp_path / "nao_existe.xlsx"))
    main._cache["base"] = None
    r = client.get("/api/estatisticas")
    assert r.status_code == 200
    assert r.json()["base"]["disponivel"] is False
    main._cache["base"] = None


def test_recarregar_base_aceita_status_e_sucesso(tmp_path, monkeypatch):
    monkeypatch.setenv("PLANILHA", str(tmp_path / "nao_existe.xlsx"))
    r = client.post("/api/recarregar-base")
    assert r.status_code == 200
    assert r.json()["status"] == "sucesso" and r.json()["sucesso"] is True
    main._cache["base"] = None