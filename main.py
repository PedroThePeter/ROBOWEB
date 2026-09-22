import os
import glob
import traceback
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================================
# CONFIGURAÇÃO SUPABASE
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        "message": "Ficheiro carregado com sucesso!",
        "filename": file.filename,
        "total_concursos": total_linhas
    })

@app.route('/api/gerar_palpites', methods=['POST'])
def gerar_palpites():
    try:
        dados = request.get_json() or {}
        concurso_alvo = dados.get('concurso_alvo', 0)
        
        arquivos_excel = glob.glob(os.path.join(UPLOAD_FOLDER, '*.xlsx'))
        if not arquivos_excel:
            return jsonify({"error": "Base de dados não encontrada. Faça upload do Excel."}), 400
        
        df = pd.read_excel(arquivos_excel[0])
        
        # 1. Convoca os 5 Juízes
        motor = LotofacilEngine(df)
        stats_frequencia = motor.juiz_de_frequencia(janela=20)
        stats_ciclos = motor.juiz_de_padroes_e_ciclos()
        stats_paridade = motor.juiz_de_paridade_e_primos()
        stats_soma = motor.juiz_de_soma_e_amplitude()
        stats_sequencias = motor.juiz_de_sequencias_e_repeticoes()

        # 2. Instancia a IA de Decisão (Os Curadores)
        validador = CuradorDeValidacao(
            stats_ciclos, stats_paridade, stats_soma, stats_sequencias
        )
        
        gerador = CuradorDeSelecaoFinal(
            validador, stats_frequencia, stats_ciclos, stats_sequencias
        )

        # 3. Gera 3 Bilhetes Diamante
        resultado_geracao = gerador.gerar_bilhetes_diamante(quantidade=3)

        if len(resultado_geracao["bilhetes"]) == 0:
            return jsonify({"error": "Filtros demasiado restritos. Nenhum bilhete sobreviveu ao Validador."}), 500

        # Formata para o Frontend React consumir
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
        # AQUI ESTÁ A MAGIA DE DEBUG
        print("\n" + "="*50)
        print("🚨 ERRO FATAL NO MOTOR AI 🚨")
        print(traceback.format_exc())
        print("="*50 + "\n")
        return jsonify({"error": f"Erro interno do Motor AI: {str(e)}"}), 500


@app.route('/api/salvar_bilhetes', methods=['POST'])
def salvar_bilhetes():
    if not supabase:
        return jsonify({"error": "Supabase não está configurado no servidor."}), 500
        
    dados = request.json or {}
    concurso = dados.get("concurso")
    palpites = dados.get("palpites", {})
    
    if not concurso or not palpites:
        return jsonify({"error": "Dados incompletos para salvar."}), 400

    registros = [
        {"concurso": concurso, "curador": curador, "dezenas": dezenas}
        for curador, dezenas in palpites.items()
    ]
    
    try:
        supabase.table("bilhetes_gerados").insert(registros).execute()
        return jsonify({"status": "sucesso", "mensagem": f"Bilhetes do concurso {concurso} salvos com sucesso!"})
    except Exception as e:
        print("\n" + "="*50)
        print("🚨 ERRO AO SALVAR NO SUPABASE 🚨")
        print(traceback.format_exc())
        print("="*50 + "\n")
        return jsonify({"error": f"Erro ao salvar no banco: {str(e)}"}), 500


@app.route('/api/auditar/<int:concurso_alvo>', methods=['GET'])
def auditar_resultado(concurso_alvo):
    if not supabase:
        return jsonify({"error": "Supabase não configurado."}), 500
        
    try:
        res_db = supabase.table("bilhetes_gerados").select("*").eq("concurso", concurso_alvo).execute()
        bilhetes_salvos = res_db.data
        
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
            return jsonify({"error": f"O resultado do concurso {concurso_alvo} ainda não foi adicionado ao Excel."}), 404
            
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
        # AQUI ESTÁ A MAGIA DE DEBUG
        print("\n" + "="*50)
        print("🚨 ERRO FATAL NA AUDITORIA 🚨")
        print(traceback.format_exc())
        print("="*50 + "\n")
        return jsonify({"error": f"Erro interno na auditoria: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)