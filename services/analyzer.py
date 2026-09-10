import pandas as pd
import numpy as np
import itertools
import random
from collections import Counter

# Armazenamento em memória das sessões (DataFrames originais)
sessions = {}

def process_upload(file_path: str, session_id: str):
    try:
        df = pd.read_excel(file_path)
        # Identificar colunas de dezenas
        ball_cols = [c for c in df.columns if any(keyword in str(c).lower() for keyword in ['bola', 'dezena'])]
        
        if not ball_cols:
            raise ValueError("Não foram encontradas colunas com 'Bola' ou 'Dezena'.")

        # Limpar dados
        df[ball_cols] = df[ball_cols].apply(pd.to_numeric, errors='coerce')
        df = df.dropna(subset=ball_cols)
        
        sessions[session_id] = {'df': df, 'cols': ball_cols}
        
        return {
            "total_concursos": len(df),
            "colunas_identificadas": len(ball_cols)
        }
    except Exception as e:
        raise ValueError(f"Erro ao processar arquivo: {str(e)}")

def calculate_stats(session_id: str):
    data = sessions.get(session_id)
    if not data:
        raise ValueError("Sessão não encontrada.")
        
    df = data['df']
    cols = data['cols']
    
    # Todos os números sorteados
    all_numbers = df[cols].values.flatten()
    all_numbers = all_numbers[~np.isnan(all_numbers)].astype(int)
    
    # 1. Frequência Absoluta
    freq = pd.Series(all_numbers).value_counts().sort_values(ascending=False)
    
    # 2. Atraso (Concursos desde a última aparição)
    atraso = {}
    total_rows = len(df)
    for num in freq.index:
        last_seen = df[df[cols].isin([num]).any(axis=1)].index.max()
        atraso[int(num)] = int((df.index.max() - last_seen) if not pd.isna(last_seen) else total_rows)
        
    # 3. Proporção Par/Ímpar Média
    evens = (df[cols] % 2 == 0).sum(axis=1)
    odds = (df[cols] % 2 != 0).sum(axis=1)
    
    # 4. Intervalo de Soma (Média e Desvio Padrão)
    sums = df[cols].sum(axis=1)
    mean_sum = float(sums.mean())
    std_sum = float(sums.std())
    
    # 5. Top 10 Pares (Coocorrência)
    pairs_counter = Counter()
    for _, row in df[cols].iterrows():
        nums = sorted(row.dropna().astype(int).tolist())
        pairs_counter.update(itertools.combinations(nums, 2))
        
    return {
        "frequencias": freq.to_dict(),
        "atrasos": atraso,
        "par_impar": {"media_pares": float(evens.mean()), "media_impares": float(odds.mean())},
        "soma": {"media": mean_sum, "desvio_padrao": std_sum},
        "top_pares": [{"par": f"{p[0]}-{p[1]}", "freq": c} for p, c in pairs_counter.most_common(10)]
    }

def generate_tickets(config: dict, stats: dict):
    total_numbers = config['total_numbers']
    number_range = config['number_range']
    fixed = config.get('fixed_numbers', [])
    excluded = config.get('excluded_numbers', [])
    ticket_count = config['ticket_count']
    
    freq = stats['frequencias']
    atraso = stats['atrasos']
    
    weights = {}
    valid_pool = [n for n in range(1, number_range + 1) if n not in excluded and n not in fixed]
    
    max_freq = max(freq.values()) if freq else 1
    max_atraso = max(atraso.values()) if atraso else 1
    
    for num in valid_pool:
        f = freq.get(str(num), freq.get(num, 0))
        a = atraso.get(str(num), atraso.get(num, 0))
        
        score = ((f / max_freq) * 0.6) + ((a / max_atraso) * 0.4)
        weights[num] = max(score, 0.01)
        
    tickets = []
    attempts = 0
    
    while len(tickets) < ticket_count and attempts < 10000:
        attempts += 1
        needed = total_numbers - len(fixed)
        if needed <= 0:
            candidate = list(fixed)[:total_numbers]
        else:
            pool, w = zip(*weights.items())
            w_sum = sum(w)
            w_norm = [i/w_sum for i in w]
            drawn = np.random.choice(pool, size=needed, replace=False, p=w_norm).tolist()
            candidate = sorted(fixed + drawn)
            
        soma = sum(candidate)
        pares = sum(1 for x in candidate if x % 2 == 0)
        
        soma_min = stats['soma']['media'] - stats['soma']['desvio_padrao']
        soma_max = stats['soma']['media'] + stats['soma']['desvio_padrao']
        
        if soma_min <= soma <= soma_max:
            tickets.append({
                "numeros": candidate,
                "soma": soma,
                "pares": pares,
                "impares": total_numbers - pares,
                "score_confianca": round(sum(weights.get(n, 1) for n in candidate) / total_numbers * 100, 1)
            })
            
    return tickets