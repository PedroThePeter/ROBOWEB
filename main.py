import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = Flask(__name__)

# Libera CORS globalmente para evitar erros de bloqueio Vercel <-> Render
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

DF_LOTOFACIL = None

def carregar_dados_iniciais():
    """
    Carrega automaticamente a planilha de histórico do projeto se ela existir na raiz.
    """
    global DF_LOTOFACIL
    caminhos_possiveis = [
        'lotofacil.xlsx', 
        'lotofacil.csv', 
        'base_lotofacil.xlsx', 
        'base_lotofacil.csv'
    ]
    
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            try:
                if caminho.endswith('.xlsx') or caminho.endswith('.xls'):
                    DF_LOTOFACIL = pd.read_excel(caminho)
                else:
                    DF_LOTOFACIL = pd.read_csv(caminho)
                print(f"[SUCESSO] Base de dados carregada automaticamente: {caminho} ({len(DF_LOTOFACIL)} concursos)")
                return
            except Exception as e:
                print(f"[ERRO] Falha ao ler {caminho}: {e}")
            
    print("[AVISO] Nenhuma base de dados encontrada na raiz. Suba 'lotofacil.xlsx' no GitHub para carregamento automático.")

# Executa o carregamento assim que o servidor é iniciado
carregar_dados_iniciais()


# ==========================================
# ROTAS DA API (Aceitam rotas com ou sem /api)
# ==========================================

@app.route('/status', methods=['GET'])
@app.route('/api/status', methods=['GET'])
def status():
    """
    Endpoint para verificação de saúde da API e status da base de dados.
    """
    status_dados = "carregado" if DF_LOTOFACIL is not None else "pendente"
    total_concursos = len(DF_LOTOFACIL) if DF_LOTOFACIL is not None else 0
    
    return jsonify({
        "status_api": "online",
        "status_base_dados": status_dados,
        "total_concursos": total_concursos
    }), 200


@app.route('/upload_dados', methods=['POST'])
@app.route('/api/upload_dados', methods=['POST'])
def upload_dados():
    """
    Endpoint para upload manual da planilha (.xlsx ou .csv).
    """
    global DF_LOTOFACIL
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo foi enviado."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"erro": "Nome de arquivo inválido."}), 400

    try:
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            DF_LOTOFACIL = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            DF_LOTOFACIL = pd.read_csv(file)
        else:
            return jsonify({"erro": "Formato inválido. Envie um arquivo .xlsx ou .csv"}), 400

        return jsonify({
            "mensagem": "Base de dados atualizada com sucesso!",
            "total_concursos": len(DF_LOTOFACIL)
        }), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar arquivo: {str(e)}"}), 500


@app.route('/analise_completa', methods=['GET'])
@app.route('/api/analise_completa', methods=['GET'])
def obter_analise_completa():
    """
    Retorna a análise quantitativa dos 6 Juízes estatísticos.
    """
    global DF_LOTOFACIL
    if DF_LOTOFACIL is None:
        return jsonify({
            "erro": "Base de dados não carregada na API. Adicione o arquivo lotofacil.xlsx na raiz do GitHub ou faça o upload na interface."
        }), 400

    try:
        motor = LotofacilEngine(DF_LOTOFACIL)
        
        relatorio = {
            "frequencia": motor.juiz_de_frequencia(janela=20),
            "ciclos": motor.juiz_de_padroes_e_ciclos(),
            "paridade_primos": motor.juiz_de_paridade_e_primos(),
            "soma_amplitude": motor.juiz_de_soma_e_amplitude(),
            "sequencias_repeticoes": motor.juiz_de_sequencias_e_repeticoes(),
            "moldura_miolo": motor.juiz_de_moldura_e_miolo()
        }
        
        return jsonify(relatorio), 200
    except Exception as e:
        return jsonify({"erro": f"Erro na análise estatística: {str(e)}"}), 500


@app.route('/gerar_palpites', methods=['POST'])
@app.route('/api/gerar_palpites', methods=['POST'])
def gerar_palpites():
    """
    Gera Bilhetes Diamante utilizando pontuação de score, amostragem ponderada e controle de diversidade.
    """
    global DF_LOTOFACIL
    if DF_LOTOFACIL is None:
        return jsonify({
            "erro": "Base de dados não carregada na API."
        }), 400

    try:
        dados = request.get_json() or {}
        
        quantidade = int(dados.get('quantidade', dados.get('qtd_jogos', 3)))
        score_minimo = int(dados.get('score_minimo', 80))
        max_interseccao = int(dados.get('max_interseccao', 12))
        max_tentativas = int(dados.get('max_tentativas', 10000))

        motor = LotofacilEngine(DF_LOTOFACIL)
        stats_freq = motor.juiz_de_frequencia(janela=20)
        stats_ciclos = motor.juiz_de_padroes_e_ciclos()
        stats_par = motor.juiz_de_paridade_e_primos()
        stats_soma = motor.juiz_de_soma_e_amplitude()
        stats_seq = motor.juiz_de_sequencias_e_repeticoes()
        stats_moldura = motor.juiz_de_moldura_e_miolo()

        validador = CuradorDeValidacao(
            stats_ciclos=stats_ciclos,
            stats_paridade=stats_par,
            stats_soma=stats_soma,
            stats_sequencias=stats_seq,
            stats_moldura=stats_moldura,
            score_minimo=score_minimo
        )

        gerador = CuradorDeSelecaoFinal(
            validador=validador,
            stats_frequencia=stats_freq,
            stats_ciclos=stats_ciclos,
            stats_sequencias=stats_seq,
            stats_moldura=stats_moldura
        )

        resultado = gerador.gerar_bilhetes_diamante(
            quantidade=quantidade,
            max_tentativas=max_tentativas,
            max_interseccao=max_interseccao
        )

        return jsonify({
            "parametros_utilizados": {
                "quantidade": quantidade,
                "score_minimo": score_minimo,
                "max_interseccao": max_interseccao
            },
            "resultado": resultado
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar bilhetes: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)