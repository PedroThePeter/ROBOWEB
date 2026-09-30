import pytest
import numpy as np
from desdobramento import (
    dezenas_para_mask,
    contar_intersecao_mask,
    calcular_probabilidade_grupo
)

def test_dezenas_para_mask_e_intersecao():
    """Testa conversão para bitmask e contagem de interseção acelerada."""
    jogo_1 = [1, 2, 3, 4, 5]
    jogo_2 = [4, 5, 6, 7, 8]
    
    mask_1 = dezenas_para_mask(jogo_1)
    mask_2 = dezenas_para_mask(jogo_2)
    
    # Interseção esperada: {4, 5} = 2 dezenas
    intersecao = contar_intersecao_mask(mask_1, mask_2)
    assert intersecao == 2

def test_calcular_probabilidade_grupo_limites():
    """Testa a probabilidade combinatória C(K,15)/C(25,15)."""
    # Grupo de 15 dezenas em 25 -> C(15,15)/C(25,15) = 1 / 3.268.760
    prob_15 = calcular_probabilidade_grupo(15)
    assert pytest.approx(prob_15, rel=1e-5) == 1 / 3268760
    
    # Grupo de 25 dezenas em 25 -> 100% de chance
    prob_25 = calcular_probabilidade_grupo(25)
    assert prob_25 == 1.0

def test_grupo_invalido_raises():
    """Garante exceção para grupos com menos de 15 ou mais de 25 dezenas."""
    with pytest.raises(ValueError):
        calcular_probabilidade_grupo(14)
    with pytest.raises(ValueError):
        calcular_probabilidade_grupo(26)