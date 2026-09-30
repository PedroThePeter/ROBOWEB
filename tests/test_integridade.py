import os
import json
import pytest
from integridade import _hash_bilhete, _hash_pesos, carregar_pesos_para_engine, PESOS_PADRAO

def test_hash_bilhete_determinismo():
    """Garante que a ordem das dezenas não altera a hash SHA-256 gerada."""
    bilhete_a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    bilhete_b = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    
    assert _hash_bilhete(bilhete_a) == _hash_bilhete(bilhete_b)
    assert len(_hash_bilhete(bilhete_a)) == 64  # SHA-256 produz 64 caracteres hexa

def test_hash_pesos_alteracao_detectada():
    """Valida se qualquer modificação nos pesos altera a hash de verificação."""
    pesos_1 = {"soma": 1.0, "pares": 0.8}
    pesos_2 = {"soma": 1.0, "pares": 0.81}  # Pequena alteração
    
    assert _hash_pesos(pesos_1) != _hash_pesos(pesos_2)

def test_carregar_pesos_fallback_sem_arquivo(tmp_path, monkeypatch):
    """Garante fallback para PESOS_PADRAO se o arquivo de trava não existir."""
    falso_json = tmp_path / "pesos_inexistentes.json"
    monkeypatch.setattr("integridade.ARQUIVO_TRAVA", str(falso_json))
    
    pesos_carregados, ativo = carregar_pesos_para_engine()
    assert pesos_carregados == PESOS_PADRAO
    assert ativo is False

def test_violacao_de_hash_na_trava(tmp_path, monkeypatch):
    """Verifica se o sistema rejeita pesos cuja hash não bate com o registro da trava."""
    falso_json = tmp_path / "pesos_adulterados.json"
    dados_adulterados = {
        "pesos": {"soma": 1.5},
        "hash_pesos": "hash_falsa_invalida_1234567890abcdef",
        "data_trava": "2026-01-01T00:00:00",
        "dias_validade": 90
    }
    falso_json.write_text(json.dumps(dados_adulterados))
    monkeypatch.setattr("integridade.ARQUIVO_TRAVA", str(falso_json))
    
    pesos_carregados, ativo = carregar_pesos_para_engine()
    # Deve rejeitar e cair no padrão
    assert pesos_carregados == PESOS_PADRAO
    assert ativo is False