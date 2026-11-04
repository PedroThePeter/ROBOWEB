import random

AVISO = "Operando na V9.0 (20 Juízes e Curadores em Escala). Modo 100% Local."
PLANILHA_PADRAO = "Lotofacil.xlsx"

# ==========================================
# ⚖️ MÓDULO A, B e C: OS 15 JUÍZES HEURÍSTICOS
# ==========================================
def _juiz_paridade(b): return 6 <= sum(1 for x in b if x % 2 == 0) <= 9
def _juiz_soma(b): return 160 <= sum(b) <= 210
def _juiz_primos(b): 
    primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    return 4 <= sum(1 for x in b if x in primos) <= 7
def _juiz_fibonacci(b): 
    fib = {1, 2, 3, 5, 8, 13, 21}
    return 3 <= sum(1 for x in b if x in fib) <= 6
def _juiz_mult3(b): return 3 <= sum(1 for x in b if x % 3 == 0) <= 6
def _juiz_moldura(b): 
    moldura = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    return 8 <= sum(1 for x in b if x in moldura) <= 11
def _juiz_amplitude(b): return b[0] <= 5 and b[-1] >= 21
def _juiz_terminais(b):
    from collections import Counter
    counts = Counter([x % 10 for x in b]).values()
    return all(v <= 4 for v in counts) # Máximo 4 números terminados no mesmo dígito
def _juiz_linhas(b):
    for r in range(5):
        qtd = sum(1 for x in b if (r*5 + 1) <= x <= (r*5 + 5))
        if qtd == 0 or qtd == 5: return False
    return True
def _juiz_colunas(b):
    for c in range(1, 6):
        qtd = sum(1 for x in b if (x - c) % 5 == 0)
        if qtd == 0 or qtd == 5: return False
    return True
def _juiz_diagonais(b):
    diag = {1, 7, 13, 19, 25, 5, 9, 17, 21}
    return 3 <= sum(1 for x in b if x in diag) <= 7
def _juiz_consecutividade(b):
    max_cons = 1; curr_cons = 1
    for i in range(1, 15):
        if b[i] == b[i-1] + 1:
            curr_cons += 1
            if curr_cons > max_cons: max_cons = curr_cons
        else:
            curr_cons = 1
    return max_cons <= 5
def _juiz_gaps(b):
    max_gap = 0
    for i in range(1, 15):
        gap = b[i] - b[i-1] - 1
        if gap > max_gap: max_gap = gap
    return max_gap <= 6
def _juiz_retencao(b, sorteios):
    if not sorteios: return True
    ult = sorteios[-1]
    return 7 <= sum(1 for x in b if x in ult) <= 10
def _juiz_frias(b, sorteios):
    if not sorteios or len(sorteios) < 3: return True
    saidos = set(sorteios[-1]) | set(sorteios[-2]) | set(sorteios[-3])
    frias = set(range(1, 26)) - saidos
    if len(frias) >= 1:
        return sum(1 for x in b if x in frias) <= 3
    return True

# ==========================================
# 🎛️ CAMADA 1: CURADOR DE MICROANÁLISE
# ==========================================
def curador_1_aprova_bilhete(b, sorteios):
    if not _juiz_paridade(b): return False
    if not _juiz_soma(b): return False
    if not _juiz_primos(b): return False
    if not _juiz_fibonacci(b): return False
    if not _juiz_mult3(b): return False
    if not _juiz_moldura(b): return False
    if not _juiz_amplitude(b): return False
    if not _juiz_terminais(b): return False
    if not _juiz_linhas(b): return False
    if not _juiz_colunas(b): return False
    if not _juiz_diagonais(b): return False
    if not _juiz_consecutividade(b): return False
    if not _juiz_gaps(b): return False
    if not _juiz_retencao(b, sorteios): return False
    if not _juiz_frias(b, sorteios): return False
    return True

# ==========================================
# 🔄 ALGORITMOS DE SELEÇÃO
# ==========================================
def pesos_por_frequencia(sorteios):
    frequencias = {str(i): 0 for i in range(1, 26)}
    if not sorteios: return {k: 1.0 for k in frequencias}
    for s in sorteios:
        for num in s: frequencias[str(num)] += 1
    total = len(sorteios)
    return {k: (v / total if total > 0 else 0) for k, v in frequencias.items()}

def _escolher_15_roleta(lista_pesos, temperatura):
    import secrets
    rng = secrets.SystemRandom()
    peso_medio = sum(lista_pesos) / len(lista_pesos) if lista_pesos else 1.0
    
    if temperatura == 0.0:
        # Micro-ruído térmico para evitar loop infinito nos juízes estritos
        pesos = [p + (rng.random() * p * 0.1) for p in lista_pesos]
    elif temperatura == 50.0:
        pesos = [p * 0.5 + peso_medio * 0.5 for p in lista_pesos]
    else:
        pesos = [1.0 for _ in lista_pesos]
        
    populacao = list(range(1, 26))
    escolhidos = []
    for _ in range(15):
        idx = rng.choices(range(len(populacao)), weights=pesos, k=1)[0]
        escolhidos.append(populacao.pop(idx))
        pesos.pop(idx)
    return sorted(escolhidos)

def _escolher_15_geometria(lista_pesos, temperatura):
    import secrets
    rng = secrets.SystemRandom()
    peso_medio = sum(lista_pesos) / len(lista_pesos) if lista_pesos else 1.0
    
    if temperatura == 0.0:
        pesos = [p + (rng.random() * p * 0.1) for p in lista_pesos]
    elif temperatura == 50.0:
        pesos = [p * 0.5 + peso_medio * 0.5 for p in lista_pesos]
    else:
        pesos = [1.0 for _ in lista_pesos]
        
    def escolher_da_faixa(faixa, k):
        sub_pop = list(faixa)
        sub_pesos = [pesos[d - 1] for d in sub_pop]
        esc = []
        for _ in range(k):
            if sum(sub_pesos) <= 0: idx = rng.randrange(len(sub_pop))
            else: idx = rng.choices(range(len(sub_pop)), weights=sub_pesos, k=1)[0]
            esc.append(sub_pop.pop(idx))
            sub_pesos.pop(idx)
        return esc

    return sorted(escolher_da_faixa(range(1, 12), 7) + 
                  escolher_da_faixa(range(12, 19), 4) + 
                  escolher_da_faixa(range(19, 26), 4))

def gerar_jogos_genetico(quantidade, concurso, pesos, temperatura, sorteios=None):
    lista_pesos = [float(pesos.get(str(i), 1.0)) for i in range(1, 26)]
    bilhetes_validos = []
    for _ in range(quantidade):
        aprovado = False
        tentativas = 0
        while not aprovado and tentativas < 30000:
            tentativas += 1
            if temperatura >= 100.0:
                b = _escolher_15_geometria(lista_pesos, temperatura)
            else:
                b = _escolher_15_roleta(lista_pesos, temperatura)
                
            if curador_1_aprova_bilhete(b, sorteios):
                aprovado = True
                bilhetes_validos.append(b)
        if not aprovado:
            bilhetes_validos.append(b) # Fallback extremo
    return {"bilhetes": bilhetes_validos}

# ==========================================
# 🔀 CAMADA 2: MACROCURADORIA E PORTFÓLIO
# ==========================================
def curador_diversidade(frio, morno, quente):
    todas = set(frio + morno + quente)
    # Curador 16: Cobertura Global
    if len(todas) < 20: return False, "Baixa cobertura global"
    # Curador 17 e 18: Interseção e Simetria
    if len(set(frio) & set(morno)) > 11: return False, "Frio e Morno similares"
    if len(set(frio) & set(quente)) > 11: return False, "Frio e Quente similares"
    if len(set(morno) & set(quente)) > 11: return False, "Morno e Quente similares"
    return True, "Portfólio aprovado"