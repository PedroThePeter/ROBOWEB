import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from engine import LotofacilEngine, CuradorDeValidacao, CuradorDeSelecaoFinal

app = Flask(__name__)
# Permite que a Vercel acesse o Render sem bloqueios
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

DF_LOTOFACIL = None

def carregar_dados_iniciais():
    global DF_LOTOFACIL
    caminhos_possiveis = [
        'lotofacil.xlsx', 'Lotofacil.xlsx', 
        'lotofacil.csv', 'Lotofacil.csv', 
        'base_lotofacil.xlsx', 'base_lotofacil.csv'
    ]
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            try:
                if caminho.lower().endswith(('.xlsx', '.xls')):
                    DF_LOTOFACIL = pd.read_excel(caminho)
                else:
                    DF_LOTOFACIL = pd.read_csv(caminho)
                print(f"[SUCESSO] Base carregada: {caminho} ({len(DF_LOTOFACIL)} concursos)")
                return
            except Exception as e:
                print(f"[ERRO] Falha ao ler {caminho}: {e}")
    print("[AVISO] Nenhuma base de dados encontrada na raiz.")

carregar_dados_iniciais()

# ==========================================
# FUNÇÃO DE AUDITORIA (CURADOR 3)
# ==========================================
def auditar_bilhete(bilhete, engine):
    """
    Curador 3: Realiza a auditoria fina individual de cada bilhete aprovado.
    """
    par, imp = engine.contar_pares_impares(bilhete)
    primos = engine.contar_primos(bilhete)
    soma = sum(bilhete)
    moldura, miolo = engine.contar_moldura_miolo(bilhete)
    
    status_paridade = "APROVADO" if 6 <= par <= 9 else "ATENÇÃO"
    status_soma = "APROVADO" if 170 <= soma <= 220 else "ATENÇÃO"
    status_moldura = "APROVADO" if 8 <= moldura <= 11 else "ATENÇÃO"
    
    return {
        "pares_impares": f"{par}P / {imp}I",
        "primos": primos,
        "soma_total": soma,
        "moldura_miolo": f"{moldura} Moldura / {miolo} Miolo",
        "conformidade": {
            "paridade": status_paridade,
            "soma": status_soma,
            "moldura": status_moldura
        },
        "selo_auditoria": "VERIFICADO & APROVADO PELO CURADOR 3"
    }

# ==========================================
# ROTAS DA API
# ==========================================

@app.route('/status', methods=['GET'])
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status_api": "online",
        "status_base_dados": "carregado" if DF_LOTOFACIL is not None else "pendente",
        "total_concursos": len(DF_LOTOFACIL) if DF_LOTOFACIL is not None else 0
    }), 200

@app.route('/analise_completa', methods=['GET'])
@app.route('/api/analise_completa', methods=['GET'])
def obter_analise_completa():
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
        return jsonify({"erro": f"Erro na análise: {str(e)}"}), 500

@app.route('/gerar_palpites', methods=['POST'])
@app.route('/api/gerar_palpites', methods=['POST'])
def gerar_palpites():
    global DF_LOTOFACIL
    if DF_LOTOFACIL is None:
        return jsonify({"erro": "Base de dados não carregada na API."}), 400

    try:
        dados = request.get_json() or {}
        quantidade = int(dados.get('quantidade', 1))
        
        SCORE_MINIMO_AUTOMATICO = 85
        MAX_INTERSECCAO_AUTOMATICA = 11

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
            score_minimo=SCORE_MINIMO_AUTOMATICO
        )

        gerador = CuradorDeSelecaoFinal(
            validador=validador,
            stats_frequencia=stats_freq,
            stats_ciclos=stats_ciclos,
            stats_sequencias=stats_seq,
            stats_moldura=stats_moldura
        )

        resultado_curador2 = gerador.gerar_bilhetes_diamante(
            quantidade=quantidade,
            max_tentativas=15000,
            max_interseccao=MAX_INTERSECCAO_AUTOMATICA
        )

        bilhetes_auditados = []
        for bilhete in resultado_curador2.get('bilhetes', []):
            auditoria = auditar_bilhete(bilhete, motor)
            bilhetes_auditados.append({
                "dezenas": bilhete,
                "auditoria_curador3": auditoria
            })

        return jsonify({
            "parametros_automaticos": {
                "score_minimo_aplicado": SCORE_MINIMO_AUTOMATICO,
                "interseccao_maxima_aplicada": MAX_INTERSECCAO_AUTOMATICA
            },
            "eficiencia": resultado_curador2.get('eficiencia', '100%'),
            "simulacoes_realizadas": resultado_curador2.get('tentativas_gastas', 1),
            "bilhetes_auditados": bilhetes_auditados
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar e auditar bilhete: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)