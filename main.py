import os
import glob
import pandas as pd
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = Flask(__name__)

# --- CONFIGURAÇÃO DE CORS BLINDADA PARA A VERCEL ---
# Permite que qualquer link de preview ou produção da Vercel aceda à API sem bloqueios
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURAÇÃO SUPABASE (VIA REST API) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Lotofácil Master AI Backend a funcionar!"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum ficheiro enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome de ficheiro inválido"}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    try:
        df = pd.read_excel(filepath)
        total_linhas = len(df)
    except Exception as e:
        return jsonify({"error": f"Erro ao ler Excel: {str(e)}"}), 500

    return jsonify({
        "message": "Base atualizada com sucesso!",
        "filename": file.filename,
        "total_concursos": total_linhas
    })

@app.route('/api/gerar_palpites', methods=['POST'])
def gerar_palpites():
    dados = request.get_json() or {}
    concurso_alvo = dados.get('concurso_alvo', 0)
    
    arquivos_excel = glob.glob(os.path.join(UPLOAD_FOLDER, '*.xlsx'))
    if not arquivos_excel:
        return jsonify({"error": "Base de dados não encontrada. Faça upload do Excel."}), 400
    
    try:
        df = pd.read_excel(arquivos_excel[0])
        
        motor = LotofacilEngine(df)
        stats_frequencia = motor.juiz_de_frequencia(janela=20)
        stats_ciclos = motor.juiz_de_padroes_e_ciclos()
        stats_paridade = motor.juiz_de_paridade_e_primos()
        stats_soma = motor.juiz_de_soma_e_amplitude()
        stats_sequencias = motor.juiz_de_sequencias_e_repeticoes()

        validador = CuradorDeValidacao(
            stats_ciclos, stats_paridade, stats_soma, stats_sequencias
        )
        
        gerador = CuradorDeSelecaoFinal(
            validador, stats_frequencia, stats_ciclos, stats_sequencias
        )

        resultado_geracao = gerador.gerar_bilhetes_diamante(quantidade=3)

        if len(resultado_geracao["bilhetes"]) == 0:
            return jsonify({"error": "Filtros demasiado restritos. Nenhum bilhete sobreviveu ao Validador."}), 500

        palpites_finais = {
            f"curador{i+1}": bilhete 
            for i, bilhete in enumerate(resultado_geracao["bilhetes"])
        }

        return jsonify({
            "status": "sucesso",
            "palpites": palpites_finais,
            "concurso": concurso_alvo,
            "metricas_ia": {
                "tentativas_processadas": resultado_geracao["tentativas_gastas"],
                "taxa_aprovacao_validador": resultado_geracao["eficiencia"]
            }
        })

    except Exception as e:
        return jsonify({"error": f"Erro interno do Motor AI: {str(e)}"}), 500

@app.route('/api/salvar_bilhetes', methods=['POST'])
def salvar_bilhetes():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "Supabase não está configurado."}), 500
        
    dados = request.json or {}
    concurso = dados.get("concurso")
    palpites = dados.get("palpites", {})
    
    if not concurso or not palpites:
        return jsonify({"error": "Dados incompletos para salvar."}), 400

    registros = [
        {"concurso": concurso, "curador": curador, "dezenas": dezenas}
        for curador, dezenas in palpites.items()
    ]
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    url = f"{SUPABASE_URL}/rest/v1/bilhetes_gerados"
    
    try:
        response = requests.post(url, json=registros, headers=headers)
        if response.status_code in [200, 201]:
            return jsonify({"status": "sucesso", "mensagem": f"Bilhetes do concurso {concurso} salvos!"})
        else:
            return jsonify({"error": f"Erro do Supabase: {response.text}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao salvar no banco: {str(e)}"}), 500

@app.route('/api/auditar/<int:concurso_alvo>', methods=['GET'])
def auditar_resultado(concurso_alvo):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "Supabase não configurado."}), 500
        
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{SUPABASE_URL}/rest/v1/bilhetes_gerados?concurso=eq.{concurso_alvo}"
    
    try:
        res_db = requests.get(url, headers=headers)
        if res_db.status_code != 200:
            return jsonify({"error": f"Erro ao buscar no Supabase: {res_db.text}"}), 500
            
        bilhetes_salvos = res_db.json()
        
        if not bilhetes_salvos:
            return jsonify({"error": f"Nenhum palpite salvo para o concurso {concurso_alvo}."}), 404

        arquivos_excel = glob.glob(os.path.join(UPLOAD_FOLDER, '*.xlsx'))
        if not arquivos_excel:
            return jsonify({"error": "Base de dados Excel não encontrada."}), 400
            
        df = pd.read_excel(arquivos_excel[0])
        
        col_concurso = [c for c in df.columns if str(c).strip().lower() == 'concurso']
        if not col_concurso:
            return jsonify({"error": "Coluna 'Concurso' não encontrada no Excel."}), 400
            
        linha_resultado = df[df[col_concurso[0]] == concurso_alvo]
        if linha_resultado.empty:
            return jsonify({"error": f"O resultado do concurso {concurso_alvo} ainda não existe no Excel."}), 404
            
        colunas_dezenas = [col for col in df.columns if 'Bola' in str(col) or 'Dezena' in str(col)]
        if not colunas_dezenas or len(colunas_dezenas) != 15:
            colunas_dezenas = df.columns[-15:]
            
        dezenas_sorteadas = set(linha_resultado.iloc[0][colunas_dezenas].astype(int).tolist())

        resultados_auditoria = []
        for bilhete in bilhetes_salvos:
            dezenas_apostadas = set(bilhete['dezenas'])
            acertos = len(dezenas_sorteadas.intersection(dezenas_apostadas))
            
            resultados_auditoria.append({
                "curador": bilhete['curador'],
                "acertos": acertos,
                "dezenas_sorteadas": list(dezenas_sorteadas),
                "dezenas_apostadas": list(dezenas_apostadas)
            })
            
        return jsonify({
            "status": "sucesso",
            "concurso": concurso_alvo,
            "resultados": resultados_auditoria
        })

    except Exception as e:
        return jsonify({"error": f"Erro na auditoria: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)