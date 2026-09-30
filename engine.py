import random
from integridade import carregar_pesos_para_engine, _hash_bilhete

def extrair_pesos_dict(pesos_input):
    """Garante a extração do dicionário de pesos, mesmo que venha em formato de tupla (pesos, valido)."""
    if isinstance(pesos_input, tuple):
        return pesos_input[0]
    return pesos_input

def gerar_jogos_genetico(quantidade=10, concurso=None, caminho_pesos=None):
    """
    Gera palpites da Lotofácil utilizando seleção ponderada baseada nos pesos estatísticos ativos.
    Retorna um dicionário com os jogos, as respetivas hashes SHA-256 e a validade da trava.
    """
    retorno_pesos = carregar_pesos_para_engine(caminho_pesos)
    
    # Trata o retorno da tupla (pesos, valido)
    if isinstance(retorno_pesos, tuple):
        pesos_dict, valido = retorno_pesos
    else:
        pesos_dict, valido = retorno_pesos, True
        
    pesos = extrair_pesos_dict(pesos_dict)
    
    dezenas_disponiveis = list(range(1, 26))
    jogos_gerados = []
    hashes = []
    
    for _ in range(quantidade):
        # Mapeia os pesos para cada dezena de 1 a 25 com suporte a chaves string ou int
        pesos_lista = []
        for d in dezenas_disponiveis:
            val_peso = pesos.get(str(d)) if str(d) in pesos else pesos.get(d, 1.0)
            pesos_lista.append(float(val_peso))
            
        soma_pesos = sum(pesos_lista)
        
        # Fallback para amostragem aleatória simples se os pesos forem inválidos/nulos
        if soma_pesos <= 0:
            bilhete = sorted(random.sample(dezenas_disponiveis, 15))
        else:
            # Seleção ponderada sem reposição
            populacao = list(dezenas_disponiveis)
            pesos_temp = list(pesos_lista)
            bilhete = []
            
            for _ in range(15):
                escolhido = random.choices(populacao, weights=pesos_temp, k=1)[0]
                idx = populacao.index(escolhido)
                bilhete.append(escolhido)
                populacao.pop(idx)
                pesos_temp.pop(idx)
                
            bilhete.sort()
            
        h = _hash_bilhete(bilhete)
        jogos_gerados.append(bilhete)
        hashes.append(h)
        
    return {
        "status": "sucesso",
        "concurso": concurso,
        "quantidade": quantidade,
        "jogos": jogos_gerados,
        "hashes": hashes,
        "trava_valida": valido
    }