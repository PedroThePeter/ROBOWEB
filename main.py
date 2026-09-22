import os
import glob
import traceback
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def sanitize_for_json(data):
    if isinstance(data, dict):
        return {str(k): sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple, set)):
        return [sanitize_for_json(v) for v in data]
    elif isinstance(data, (np.integer, np.int64, np.int32)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32)):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    return data

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "API Lotofácil IA Online"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum ficheiro enviado"}), 400
    
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    try:
        df = pd.read_excel(filepath)
        col_concurso = [c for c in df.columns if str(c).strip().lower() == 'concurso']
        if col_concurso:
            ultimo_concurso = int(df[col_concurso[0]].max())
        else:
            ultimo_concurso = 0
            
    except Exception as e:
        return jsonify({"error": f"Erro ao processar Excel: {str(e)}"}), 500

    return jsonify({
        "message": "Base atualizada com sucesso!",
        "ultimo_concurso": ultimo_concurso,
        "proximo_concurso": ultimo_concurso + 1
    })

@app.route('/api/gerar_palpites', methods=['POST'])
def gerar_palpites():
    try:
        arquivos_excel = glob.glob(os.path.join(UPLOAD_FOLDER, '*.xlsx'))
        if not arquivos_excel:
            return jsonify({"error": "Faça upload do Excel primeiro."}), 400
        
        df = pd.read_excel(arquivos_excel[0])
        col_concurso = [c for c in df.columns if str(c).strip().lower() == 'concurso']
        concurso_alvo = int(df[col_concurso[0]].max()) + 1 if col_concurso else 0
        
        # 1. IA Trabalha
        motor = LotofacilEngine(df)
        stats_freq = motor.juiz_de_frequencia(janela=20)
        stats_ciclos = motor.juiz_de_padroes_e_ciclos()
        stats_par = motor.juiz_de_paridade_e_primos()
        stats_soma = motor.juiz_de_soma_e_amplitude()
        stats_seq = motor.juiz_de_sequencias_e_repeticoes()

        validador = CuradorDeValidacao(stats_ciclos, stats_par, stats_soma, stats_seq)
        gerador = CuradorDeSelecaoFinal(validador, stats_freq, stats_ciclos, stats_seq)

        resultado = gerador.gerar_bilhetes_diamante(quantidade=3)

        if not resultado["bilhetes"]:
            return jsonify({"error": "Os juízes rejeitaram todos os palpites."}), 500

        palpites_finais = {
            f"curador{i+1}": [int(n) for n in bilhete]
            for i, bilhete in enumerate(resultado["bilhetes"])
        }
        
        # Gravação automática no Supabase após gerar
        if supabase:
            registos = [
                {"concurso": concurso_alvo, "curador": curador, "dezenas": dezenas}
                for curador, dezenas in palpites_finais.items()
            ]
            supabase.table("bilhetes_gerados").insert(registos).execute()

        resposta = {
            "status": "sucesso",
            "concurso": concurso_alvo,
            "palpites": palpites_finais,
            "metricas_ia": {
                "tentativas": int(resultado["tentativas_gastas"]),
                "eficiencia": resultado["eficiencia"]
            },
            "relatorio_juizes": {
                "ciclo_estado": stats_ciclos["estado_ciclo_atual"],
                "ciclo_faltam": stats_ciclos["dezenas_faltantes_para_fechar"],
                "quentes": stats_freq["top_5_quentes"],
                "frias": stats_freq["top_5_frias"]
            }
        }
        return jsonify(sanitize_for_json(resposta))

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/auditar/<int:concurso_alvo>', methods=['GET'])
def auditar_resultado(concurso_alvo):
    if not supabase:
        return jsonify({"error": "Supabase não configurado."}), 500
        
    try:
        res_db = supabase.table("bilhetes_gerados").select("*").eq("concurso", concurso_alvo).execute()
        bilhetes_salvos = res_db.data
        if not bilhetes_salvos:
            return jsonify({"error": f"Sem histórico para auditar o concurso {concurso_alvo}."}), 404

        arquivos_excel = glob.glob(os.path.join(UPLOAD_FOLDER, '*.xlsx'))
        df = pd.read_excel(arquivos_excel[0])
        col_concurso = [c for c in df.columns if str(c).strip().lower() == 'concurso']
        linha_resultado = df[df[col_concurso[0]] == concurso_alvo]
        
        if linha_resultado.empty:
            return jsonify({"error": "Sorteio ainda não consta no Excel."}), 404
            
        colunas_dezenas = [col for col in df.columns if 'Bola' in str(col) or 'Dezena' in str(col)]
        if not colunas_dezenas or len(colunas_dezenas) != 15:
            colunas_dezenas = df.columns[-15:]
            
        dezenas_sorteadas = set(linha_resultado.iloc[0][colunas_dezenas].astype(int).tolist())

        resultados = []
        for bilhete in bilhetes_salvos:
            acertos = len(dezenas_sorteadas.intersection(set(bilhete['dezenas'])))
            resultados.append({
                "curador": bilhete['curador'],
                "acertos": acertos,
                "dezenas_apostadas": bilhete['dezenas']
            })
            
        return jsonify(sanitize_for_json({
            "status": "sucesso",
            "concurso": concurso_alvo,
            "sorteadas": list(dezenas_sorteadas),
            "resultados": resultados
        }))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))