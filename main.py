import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = Flask(__name__)

# Configuração de CORS para permitir requisições do Frontend local ou em produção
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Variável global para armazenar o DataFrame em memória
DF_LOTOFACIL = None

def carregar_dados_iniciais():
    """
    Tenta carregar o arquivo excel/csv do histórico da Lotofácil na inicialização.
    Procura por arquivos 'lotofacil.xlsx' ou 'lotofacil.csv' na raiz.
    """
    global DF_LOTOFACIL
    caminhos_possiveis = ['lotofacil.xlsx', 'lotofacil.csv', 'base_lotofacil.xlsx']
    
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            try:
                if caminho.endswith('.xlsx'):
                    DF_LOTOFACIL = pd.read_excel(caminho)
                else:
                    DF_LOTOFACIL = pd.read_csv(caminho)
                print(f"[INFO] Base de dados carregada com sucesso a partir de: {caminho}")
                return
            except Exception as e:
                print(f"[ERRO] Falha ao ler {caminho}: {e}")
    
    print("[AVISO] Nenhum arquivo base encontrado na inicialização. Aguardando upload via API.")

# Carrega os dados assim que o servidor é iniciado
carregar_dados_iniciais()


# ==========================================
# ROTAS DA API
# ==========================================

@app.route('/api/status', methods=['GET'])
def status():
    """
    Endpoint para verificar a saúde da API e status do arquivo carregado.
    """
    status_dados = "carregado" if DF_LOTOFACIL is not None else "pendente"
    total_concursos = len(DF_LOTOFACIL) if DF_LOTOFACIL is not None else 0
    
    return jsonify({
        "status_api": "online",
        "status_base_dados": status_dados,
        "total_concursos": total_concursos
    }), 200


@app.route('/api/upload_dados', methods=['POST'])
def upload_dados():
    """
    Endpoint para envio do arquivo Excel ou CSV com o histórico de sorteios.
    """
    global DF_LOTOFACIL
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

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
        return jsonify({"erro": f"Erro ao processar o arquivo: {str(e)}"}), 500


@app.route('/api/analise_completa', methods=['GET'])
def obter_analise_completa():
    """
    Retorna o diagnóstico estatístico consolidado dos 6 Juízes.
    """
    global DF_LOTOFACIL
    if DF_LOTOFACIL is None:
        return jsonify({"erro": "Base de dados não carregada na API."}), 400

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
        return jsonify({"erro": f"Erro ao processar análise estatística: {str(e)}"}), 500


@app.route('/api/gerar_palpites', methods=['POST'])
def gerar_palpites():
    """
    Gera Bilhetes Diamante utilizando os 6 Juízes, Score de Qualidade,
    Amostragem Ponderada e Controle de Diversidade.
    """
    global DF_LOTOFACIL
    if DF_LOTOFACIL is None:
        return jsonify({"erro": "Base de dados não carregada na API."}), 400

    try:
        dados = request.get_json() or {}
        
        # Parâmetros customizáveis via frontend com valores padrão
        quantidade = int(dados.get('quantidade', 3))
        score_minimo = int(dados.get('score_minimo', 80))
        max_interseccao = int(dados.get('max_interseccao', 12))
        max_tentativas = int(dados.get('max_tentativas', 10000))

        # Execução das análises dos 6 Juízes
        motor = LotofacilEngine(DF_LOTOFACIL)
        stats_freq = motor.juiz_de_frequencia(janela=20)
        stats_ciclos = motor.juiz_de_padroes_e_ciclos()
        stats_par = motor.juiz_de_paridade_e_primos()
        stats_soma = motor.juiz_de_soma_e_amplitude()
        stats_seq = motor.juiz_de_sequencias_e_repeticoes()
        stats_moldura = motor.juiz_de_moldura_e_miolo()

        # Instanciação do Validador por Score e do Gerador
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

        # Geração dos bilhetes
        resultado = gerador.gerar_bilhetes_diamante(
            quantidade=quantidade,
            max_tentativas=max_tentativas,
            max_interseccao=max_interseccao
        )

        return jsonify({
            "parametros_utilizados": {
                "quantidade_solicitada": quantidade,
                "score_minimo": score_minimo,
                "max_interseccao": max_interseccao
            },
            "resultado": resultado
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar bilhetes: {str(e)}"}), 500


if __name__ == '__main__':
    # Configuração de porta dinâmica para nuvem (ex: Render/Heroku) ou 5000 local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)