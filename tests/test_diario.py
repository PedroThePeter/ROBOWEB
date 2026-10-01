import diario
import engine


def _dados(concurso=100):
    return engine.gerar_jogos_genetico(quantidade=5, concurso=concurso)


def test_salvar_e_nao_duplicar(tmp_path):
    alvo = str(tmp_path / "p.json")
    dados = _dados()
    assert diario.salvar_palpites(dados, alvo)
    assert diario.salvar_palpites(dados, alvo)  # mesma geração: ignorada
    assert len(diario.carregar_palpites(alvo)) == 1


def test_arquivo_corrompido_e_preservado(tmp_path):
    alvo = tmp_path / "p.json"
    alvo.write_text("{{ nao e json")
    assert diario.carregar_palpites(str(alvo)) == []
    assert (tmp_path / "p.json.corrompido").exists()


def test_conferir(tmp_path):
    alvo = str(tmp_path / "p.json")
    dados = {
        "concurso": 100, "quantidade": 2, "hashes": ["a", "b"],
        "jogos": [list(range(1, 16)), list(range(11, 26))],
    }
    diario.salvar_palpites(dados, alvo)
    resumo = diario.conferir(caminho_arquivo=alvo, resultados={100: list(range(1, 16))})
    assert resumo == [{"concurso": 100, "acertos": [15, 5]}]
    # segunda conferência não repete
    assert diario.conferir(caminho_arquivo=alvo, resultados={100: list(range(1, 16))}) == []


def test_obter_dados_diario_vazio(tmp_path):
    d = diario.obter_dados_diario(str(tmp_path / "nada.json"))
    assert d == {"historico": [], "ultimos_palpites": []}