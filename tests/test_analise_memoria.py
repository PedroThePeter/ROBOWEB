import pytest
from analise_memoria import (
    calcular_z_bonferroni,
    validar_frequencia_repetidas_esperada
)

def test_calcular_z_bonferroni_multiplos_testes():
    """Garante que o limite de significância z aumenta com o número de testes simutâneos."""
    z_1_teste = calcular_z_bonferroni(num_testes=1, alpha=0.05)
    z_300_testes = calcular_z_bonferroni(num_testes=300, alpha=0.05)
    
    # Com 300 testes (ex: pares), o limiar z deve ser bem mais rigoroso (~3.6) do que com 1 teste (~1.96)
    assert z_300_testes > z_1_teste
    assert z_300_testes > 3.5

def test_media_teorica_repetidas_concurso_anterior():
    """Valida a média esperada teórica de 9,0 dezenas repetidas."""
    media_teorica = validar_frequencia_repetidas_esperada()
    assert media_teorica == 9.0