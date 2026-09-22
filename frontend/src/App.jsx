import React, { useState, useEffect } from 'react';

// ==========================================================
// CONFIGURAÇÃO DE URLS DE ENDPOINT DA API
// ==========================================================
// Se houver uma variável de ambiente VITE_API_URL, ela é usada.
// Caso contrário, assume o endereço local http://localhost:5000/api
const API_BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:5000/api';

export default function App() {
  const [statusApi, setStatusApi] = useState({ carregando: true, online: false, concursos: 0 });
  const [analise, setAnalise] = useState(null);
  const [palpites, setPalpites] = useState(null);
  
  // Parâmetros do Gerador
  const [quantidade, setQuantidade] = useState(3);
  const [scoreMinimo, setScoreMinimo] = useState(80);
  const [maxInterseccao, setMaxInterseccao] = useState(12);
  
  // Estados de carregamento e mensagem de erro
  const [loadingGeracao, setLoadingGeracao] = useState(false);
  const [erro, setErro] = useState(null);

  // 1. Checagem inicial do status da API e carregamento da Análise Completa
  useEffect(() => {
    verificarStatusEAnalise();
  }, []);

  const verificarStatusEAnalise = async () => {
    setErro(null);
    try {
      // Checa Status
      const resStatus = await fetch(`${API_BASE_URL}/status`);
      const dataStatus = await resStatus.json();
      
      if (resStatus.ok) {
        setStatusApi({
          carregando: false,
          online: dataStatus.status_api === 'online',
          concursos: dataStatus.total_concursos
        });

        // Se a base de dados estiver carregada, busca a análise estatística
        if (dataStatus.status_base_dados === 'carregado') {
          carregarAnaliseEstatistica();
        }
      } else {
        throw new Error("Erro ao conectar à API.");
      }
    } catch (err) {
      setStatusApi({ carregando: false, online: false, concursos: 0 });
      setErro("Não foi possível conectar ao servidor backend. Verifique se o main.py está em execução.");
    }
  };

  const carregarAnaliseEstatistica = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/analise_completa`);
      const data = await res.json();
      if (res.ok) {
        setAnalise(data);
      } else {
        setErro(data.erro || "Falha ao carregar análise estatística.");
      }
    } catch (err) {
      setErro("Erro de rede ao carregar análise.");
    }
  };

  // 2. Upload manual de novo arquivo Excel/CSV
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setErro(null);
    try {
      const res = await fetch(`${API_BASE_URL}/upload_dados`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        alert(data.mensagem);
        verificarStatusEAnalise();
      } else {
        setErro(data.erro || "Erro no upload.");
      }
    } catch (err) {
      setErro("Falha ao enviar arquivo para a API.");
    }
  };

  // 3. Executar Geração dos Bilhetes Diamante
  const handleGerarPalpites = async () => {
    setLoadingGeracao(true);
    setErro(null);

    try {
      const res = await fetch(`${API_BASE_URL}/gerar_palpites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantidade: parseInt(quantidade),
          score_minimo: parseInt(scoreMinimo),
          max_interseccao: parseInt(maxInterseccao)
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setPalpites(data.resultado);
      } else {
        setErro(data.erro || "Erro ao gerar bilhetes.");
      }
    } catch (err) {
      setErro("Erro de comunicação ao solicitar geração de bilhetes.");
    } finally {
      setLoadingGeracao(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* CABEÇALHO */}
      <header style={styles.header}>
        <h1 style={styles.title}>💎 Lotofácil Engine - Inteligência Estatística</h1>
        <div style={styles.statusBadge}>
          API: {statusApi.online ? '🟢 Online' : '🔴 Offline'} | 
          Concursos Carregados: <strong>{statusApi.concursos}</strong>
        </div>
      </header>

      {/* MENSAGEM DE ERRO */}
      {erro && <div style={styles.errorBox}>{erro}</div>}

      {/* PAINEL DE UPLOAD E CONTROLES */}
      <section style={styles.card}>
        <div style={styles.uploadRow}>
          <div>
            <h3>📁 Base de Dados do Histórico</h3>
            <p style={styles.subtext}>Envie uma planilha (.xlsx) ou (.csv) para atualizar a análise estatística.</p>
          </div>
          <input type="file" accept=".xlsx, .xls, .csv" onChange={handleFileUpload} style={styles.fileInput} />
        </div>
      </section>

      {/* RESUMO DOS 6 JUÍZES */}
      {analise && (
        <section style={styles.gridJudges}>
          <div style={styles.judgeCard}>
            <h4>1. Frequência</h4>
            <p><strong>Quentes:</strong> {analise.frequencia.top_5_quentes.join(', ')}</p>
            <p><strong>Frias:</strong> {analise.frequencia.top_5_frias.join(', ')}</p>
          </div>

          <div style={styles.judgeCard}>
            <h4>2. Ciclos</h4>
            <p><strong>Estado:</strong> {analise.ciclos.estado_ciclo_atual}</p>
            <p><strong>Faltam p/ Fechar:</strong> {analise.ciclos.dezenas_faltantes_para_fechar.join(', ') || 'Nenhuma'}</p>
          </div>

          <div style={styles.judgeCard}>
            <h4>3. Paridade & Primos</h4>
            <p><strong>Pares Ideais:</strong> {analise.paridade_primos.padroes_ideais.pares_impares.join(', ')}</p>
            <p><strong>Primos Ideais:</strong> {analise.paridade_primos.padroes_ideais.quantidades_primos.join(', ')}</p>
          </div>

          <div style={styles.judgeCard}>
            <h4>4. Soma Total</h4>
            <p><strong>Zona de Ouro:</strong> {analise.soma_amplitude.padroes_ideais.soma_zona_de_ouro.join(' a ')}</p>
            <p><strong>Última Soma:</strong> {analise.soma_amplitude.ultimo_concurso.soma}</p>
          </div>

          <div style={styles.judgeCard}>
            <h4>5. Repetições</h4>
            <p><strong>Repetições Ideais:</strong> {analise.sequencias_repeticoes.padroes_ideais.top_3_quantidades_repetidas.join(', ')}</p>
            <p><strong>Última Repetição:</strong> {analise.sequencias_repeticoes.ultimo_concurso.repetidas_do_anterior}</p>
          </div>

          <div style={styles.judgeCard}>
            <h4>6. Moldura / Miolo</h4>
            <p><strong>Moldura Ideal:</strong> {analise.moldura_miolo.padroes_ideais.quantidades_moldura.join(', ')} dezenas</p>
            <p><strong>Último Sorteio:</strong> {analise.moldura_miolo.ultimo_concurso.moldura} na Moldura / {analise.moldura_miolo.ultimo_concurso.miolo} no Miolo</p>
          </div>
        </section>
      )}

      {/* CONTROLES DO GERADOR DIAMANTE */}
      <section style={styles.card}>
        <h2>⚙️ Gerador de Bilhetes Diamante</h2>
        <div style={styles.paramsGrid}>
          <label style={styles.label}>
            Qtd. de Bilhetes:
            <input 
              type="number" 
              value={quantidade} 
              onChange={(e) => setQuantidade(e.target.value)} 
              min="1" max="50"
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            Score Mínimo (0-100):
            <input 
              type="number" 
              value={scoreMinimo} 
              onChange={(e) => setScoreMinimo(e.target.value)} 
              min="50" max="100"
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            Max Intersecção (Diversidade):
            <input 
              type="number" 
              value={maxInterseccao} 
              onChange={(e) => setMaxInterseccao(e.target.value)} 
              min="9" max="14"
              style={styles.input}
            />
          </label>
        </div>

        <button 
          onClick={handleGerarPalpites} 
          disabled={loadingGeracao || !statusApi.online}
          style={loadingGeracao ? {...styles.button, opacity: 0.6} : styles.button}
        >
          {loadingGeracao ? 'Gerando Jogos com IA Estatística...' : '🚀 Gerar Bilhetes Diamante'}
        </button>
      </section>

      {/* RESULTADO DOS BILHETES GERADOS */}
      {palpites && (
        <section style={styles.card}>
          <div style={styles.resultsHeader}>
            <h2>🎯 Bilhetes Selecionados ({palpites.bilhetes.length})</h2>
            <span>Eficiência do Processamento: <strong>{palpites.eficiencia}</strong> ({palpites.tentativas_gastas} simulações)</span>
          </div>

          <div style={styles.gamesList}>
            {palpites.bilhetes.map((bilhete, idx) => (
              <div key={idx} style={styles.gameCard}>
                <span style={styles.gameTitle}>Jogo #{idx + 1}</span>
                <div style={styles.ballsContainer}>
                  {bilhete.map((num) => (
                    <span key={num} style={styles.ball}>
                      {num.toString().padStart(2, '0')}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ESTILOS EM CSS-IN-JS SIMPLES E RESPONSIVO
const styles = {
  container: { fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', maxWidth: '1100px', margin: '0 auto', padding: '20px', backgroundColor: '#f4f7f6', minHeight: '100vh' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', background: '#1e293b', color: '#fff', padding: '20px', borderRadius: '10px' },
  title: { margin: 0, fontSize: '1.4rem' },
  statusBadge: { backgroundColor: '#334155', padding: '8px 15px', borderRadius: '20px', fontSize: '0.9rem' },
  errorBox: { backgroundColor: '#fef2f2', border: '1px solid #f87171', color: '#991b1b', padding: '15px', borderRadius: '8px', marginBottom: '20px' },
  card: { background: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)', marginBottom: '20px' },
  uploadRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  subtext: { color: '#64748b', fontSize: '0.85rem', margin: '5px 0 0 0' },
  fileInput: { padding: '8px' },
  gridJudges: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px', marginBottom: '20px' },
  judgeCard: { background: '#fff', padding: '15px', borderRadius: '10px', borderLeft: '4px solid #3b82f6', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' },
  paramsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', margin: '15px 0' },
  label: { display: 'flex', flexDirection: 'column', gap: '5px', fontWeight: 'bold', fontSize: '0.9rem', color: '#334155' },
  input: { padding: '8px', borderRadius: '5px', border: '1px solid #cbd5e1', fontSize: '1rem' },
  button: { width: '100%', padding: '12px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer', marginTop: '10px' },
  resultsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', borderBottom: '1px solid #e2e8f0', paddingBottom: '10px' },
  gamesList: { display: 'flex', flexDirection: 'column', gap: '15px' },
  gameCard: { background: '#f8fafc', padding: '15px', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '15px' },
  gameTitle: { fontWeight: 'bold', color: '#475569', minWidth: '70px' },
  ballsContainer: { display: 'flex', flexWrap: 'wrap', gap: '8px' },
  ball: { width: '36px', height: '36px', borderRadius: '50%', background: '#22c55e', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.9rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }
};