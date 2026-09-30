import pytest
from backtest import calcular_ic95_t_student

def test_ic95_t_student_simetrico():
    """Valida a margem de erro t-Student para amostra de acertos."""
    acertos_amostra = [9, 10, 8, 9, 11, 9, 8, 10, 9, 9]  # Média = 9.2
    media, limite_inf, limite_sup, margem = calcular_ic95_t_student(acertos_amostra)
    
    assert media == pytest.approx(9.2, abs=1e-2)
    assert limite_inf < media
    assert limite_sup > media
    assert pytest.approx(media - limite_inf) == margem