from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Permite que qualquer frontend (ex: Vercel) aceda a esta API
CORS(app)

@app.route('/')
def home():
    return "API Lotofácil Master AI está online!"

# Rota 1: Backtest Global (GET)
@app.route('/api/backtest', methods=['GET'])
def backtest():
    # AQUI ENTRA A SUA LÓGICA DE BACKTEST REAL
    
    # Exemplo do formato que o React espera receber:
    dados_mock = {
        "medias": {
            "curador1": 11.15,
            "curador2": 11.42,
            "curador3": 12.08
        },
        "historicoPesos": [
            {"concurso": 3780, "Padroes": 10, "Frequencia": 12, "Atrasos": 8, "Repeticao": 15, "Moldura": 9},
            {"concurso": 3781, "Padroes": 11, "Frequencia": 13, "Atrasos": 7, "Repeticao": 14, "Moldura": 10},
            {"concurso": 3782, "Padroes": 12, "Frequencia": 14, "Atrasos": 6, "Repeticao": 16, "Moldura": 11},
            {"concurso": 3783, "Padroes": 13, "Frequencia": 15, "Atrasos": 5, "Repeticao": 17, "Moldura": 12}
        ]
    }
    return jsonify(dados_mock), 200

# Rota 2: Upload de Excel (POST)
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum ficheiro enviado"}), 400
    file = request.files['file']
    # Lógica para guardar/processar o ficheiro .xlsx
    return jsonify({"message": f"Ficheiro {file.filename} sincronizado com sucesso!"}), 200

# Rota 3: Gerar Palpites Dinâmicos (POST) - A ROTA QUE DEU ERRO 404
@app.route('/api/gerar_palpites', methods=['POST'])
def gerar_palpites():
    dados = request.get_json()
    concurso_alvo = dados.get('concurso_alvo', 0)
    
    # AQUI CHAMA A SUA LÓGICA DE INTELIGÊNCIA ARTIFICIAL E ALGORITMOS
    # Abaixo está a estrutura de resposta que o Frontend precisa:
    palpites_gerados = {
        "palpites": {
            "curador1": [1, 2, 4, 5, 8, 9, 11, 13, 14, 18, 20, 21, 22, 24, 25],
            "curador2": [2, 3, 4, 6, 8, 9, 10, 13, 15, 17, 19, 20, 23, 24, 25],
            "curador3": [1, 3, 4, 7, 8, 10, 11, 13, 14, 17, 18, 20, 22, 24, 25]
        }
    }
    return jsonify(palpites_gerados), 200

# Rota 4: Salvar Bilhetes no Supabase (POST)
@app.route('/api/salvar_bilhetes', methods=['POST'])
def salvar_bilhetes():
    dados = request.get_json()
    # AQUI ENTRA A INTEGRAÇÃO COM O SEU BANCO DE DADOS (Supabase, etc)
    return jsonify({"message": "Bilhetes guardados no Supabase com sucesso!"}), 200

# Rota 5: Auditar Resultado (GET)
@app.route('/api/auditar/<int:concurso>', methods=['GET'])
def auditar_resultado(concurso):
    # AQUI ENTRA A LÓGICA DE CONFERÊNCIA COM O SUPABASE E O EXCEL
    resultado = {
        "status": "success",
        "resultados": [
            {"curador": "1º Curador", "acertos": 11},
            {"curador": "2º Curador", "acertos": 12},
            {"curador": "3º Curador", "acertos": 14}
        ]
    }
    return jsonify(resultado), 200

if __name__ == '__main__':
    # No Render, a porta 10000 é frequentemente usada ou definida pelas variáveis de ambiente
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)