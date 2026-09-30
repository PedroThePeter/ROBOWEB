import os
import argparse
from datetime import datetime

# Importa os módulos do ecossistema
import engine
import diario
import painel_auditoria
import integridade

def executar(args):
    """
    Executa o pipeline diário:
    1. Gera novos jogos usando o motor genético.
    2. Salva os resultados no diário (palpites.json).
    3. Atualiza o painel de auditoria estático (auditoria.html).
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando Rotina Diária...")

    # Extrai os parâmetros recebidos (da API no main.py ou do terminal)
    concurso = getattr(args, 'concurso', None)
    quantidade = getattr(args, 'quantidade', 10)
    sem_diario = getattr(args, 'sem_diario', False)
    
    try:
        # Passo 1: Gerar os jogos com o motor genético (já com o novo contrato que retorna 'jogos' e 'bilhetes')
        print(f"Gerando {quantidade} jogos para o concurso {concurso or 'atual'}...")
        dados_gerados = engine.gerar_jogos_genetico(quantidade=quantidade, concurso=concurso)
        
        # Passo 2: Salvar no diário (se a flag --sem-diario não estiver ativa)
        if not sem_diario:
            sucesso_diario = diario.salvar_palpites(dados_gerados)
            if sucesso_diario:
                print("✅ Jogos salvos no diário de palpites com sucesso.")
            else:
                print("⚠️ Aviso: Falha ao salvar no diário de palpites.")
        else:
            print("⏭️ Salvamento no diário ignorado (--sem-diario).")

        # Passo 3: Atualizar o painel de auditoria de forma segura
        # A chamada OCORRE APENAS AQUI DENTRO, nunca na raiz do arquivo.
        print("Atualizando Painel de Auditoria...")
        if hasattr(painel_auditoria, "gerar_relatorio_html"):
            painel_auditoria.gerar_relatorio_html()
        elif hasattr(painel_auditoria, "main"):
            painel_auditoria.main()
            
        print("🚀 Rotina Diária concluída com sucesso!")
        return {
            "status": "sucesso",
            "concurso": concurso,
            "quantidade": quantidade,
            "jogos_gerados": dados_gerados.get("jogos", [])
        }

    except Exception as e:
        erro_msg = f"Erro durante a rotina diária: {str(e)}"
        print(f"❌ {erro_msg}")
        return {
            "status": "erro",
            "mensagem": erro_msg
        }

def rodar(args):
    """Alias para manter compatibilidade com módulos antigos que chamem rotina_diaria.rodar()"""
    return executar(args)

# ==============================================================================
# Bloco de execução via Terminal / Linha de Comando
# Tudo o que está aqui dentro SÓ RODA se você digitar `python rotina_diaria.py`
# Ignorado completamente durante imports (como o import feito pelo main.py)
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotina Diária - Lotofácil IA v8.0")
    parser.add_argument("--concurso", type=int, default=None, help="Número do concurso alvo")
    parser.add_argument("--quantidade", type=int, default=10, help="Quantidade de bilhetes a gerar")
    parser.add_argument("--sem-commit", action="store_true", help="Ignorar commit no git (legado)")
    parser.add_argument("--sem-diario", action="store_true", help="Não salvar os jogos gerados no diário")
    
    argumentos_cli = parser.parse_args()
    
    executar(argumentos_cli)