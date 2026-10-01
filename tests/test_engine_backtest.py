import pytest
import engine


def test_bilhetes_validos():
    r = engine.gerar_jogos_genetico(quantidade=20, pesos={str(i): 1.0 for i in range(1, 26)})
    assert len(r["bilhetes"]) == 20
    for b in r["bilhetes"]:
        assert len(b) == 15 and len(set(b)) == 15
        assert all(1 <= d <= 25 for d in b)
        assert b == sorted(b)


def test_hashes_correspondem_aos_bilhetes():
    from integridade import _hash_bilhete
    r = engine.gerar_jogos_genetico(quantidade=5)
    assert r["hashes"] == [_hash_bilhete(b) for b in r["bilhetes"]]


def test_pesos_todos_zero_nao_quebra():
    r = engine.gerar_jogos_genetico(quantidade=5, pesos={str(i): 0 for i in range(1, 26)})
    assert all(len(b) == 15 for b in r["bilhetes"])


def test_poucos_pesos_positivos_nao_quebra():
    pesos = {str(i): (1.0 if i <= 10 else 0) for i in range(1, 26)}
    r = engine.gerar_jogos_genetico(quantidade=5, pesos=pesos)
    assert all(len(set(b)) == 15 for b in r["bilhetes"])


def test_dezena_com_peso_zero_nunca_sai():
    pesos = {str(i): 1.0 for i in range(1, 26)}
    pesos["1"] = 0
    r = engine.gerar_jogos_genetico(quantidade=100, pesos=pesos)
    assert all(1 not in b for b in r["bilhetes"])


@pytest.mark.parametrize("q", [0, -1, 101, "10", None])
def test_quantidade_invalida(q):
    with pytest.raises(ValueError):
        engine.gerar_jogos_genetico(quantidade=q)


def test_pesos_por_frequencia():
    vazio = engine.pesos_por_frequencia([])
    assert set(vazio.values()) == {1.0}
    pesos = engine.pesos_por_frequencia([list(range(1, 16))])
    assert pesos["1"] == 2.0 and pesos["16"] == 1.0