import React, { useState, useEffect } from 'react';

// Tratamento flexível do endereço base da API
const RAW_URL = import.meta.env?.VITE_API_URL || 'http://localhost:5000/api';
const API_BASE_URL = RAW_URL.replace(/\/$/, '');

export default function App() {
  const [statusApi, setStatusApi] = useState({ carregando: true, online: false, concursos: 0 });
  const [analise, setAnalise] = useState(null);
  const [palpites, setPalpites] = useState(null);
  
  // Parâmetros do Gerador
  const [quantidade, setQuantidade] = useState(3);
  const [scoreMinimo, setScoreMinimo] = useState(80);
  const [maxInterseccao, setMaxInterseccao] = useState(12);
  
  // Estados de controle da interface
  const [loadingGeracao, setLoadingGeracao] = useState(false);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    verificarStatusEAnalise();
  }, []);

  const getUrl = (endpoint) => {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${API_BASE_URL}${cleanEndpoint}`;
  };

  const verificarStatusEAnalise = async () => {
    setErro(null);
    try {
      const resStatus = await fetch(getUrl('/status'));
      const dataStatus = await resStatus.json();
      
      if (resStatus.ok) {
        setStatusApi({
          carregando: false,
          online: dataStatus.status_api === 'online',
          concursos: dataStatus.total_concursos
        });

        if (dataStatus.status_base_dados === 'carregado') {
          carregarAnaliseEstatistica();
        }
      } else {
        throw new Error("Falha ao comunicar com o servidor.");
      }
    } catch (err) {
      setStatusApi({ carregando: false, online: false, concursos: 0 });
      setErro("Servidor offline ou hibernando no Render. Aguarde alguns segundos e atualize.");
    }
  };

  const carregarAnaliseEstatistica = async () => {
    try {
      const res = await fetch(getUrl('/analise_completa'));
      const data = await res.json();
      if (res.ok) {
        setAnalise(data);
      } else {
        setErro(data.erro || "Não foi possível carregar o diagnóstico dos 6 Juízes.");
      }
    } catch (err) {
      setErro("Erro de comunicação com a API ao buscar relatórios.");
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setErro(null);
    try {
      const res = await fetch(getUrl('/upload_dados'), {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        alert(data.mensagem);
        verificarStatusEAnalise();
      } else {
        setErro(data.erro || "Falha ao importar o arquivo.");
      }
    } catch (err) {
      setErro("Erro ao enviar arquivo de dados para a API.");
    }
  };

  const handleGerarPalpites = async () => {
    setLoadingGeracao(true);
    setErro(null);

    try {
      const res = await fetch(getUrl('/gerar_palpites'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantidade: Number(quantidade),
          score_minimo: Number(scoreMinimo),
          max_interseccao: Number(maxInterseccao)
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setPalpites(data.resultado);
      } else {
        setErro(data.erro || "Não foi possível gerar bilhetes com os parâmetros definidos.");
      }
    } catch (err) {
      setErro("Erro ao processar a requisição de geração dos jogos.");
    } finally {
      setLoadingGeracao(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* CABEÇALHO */}
      <header style={styles.header}>
        <h1 style={styles.title}>💎 Lotofácil Engine - Inteligência Quantitativa</h1>
        <div style={styles.statusBadge}>
          API: {statusApi.online ? '🟢 Online' : '🔴 Offline'} | 
          Concursos: <strong>{statusApi.concursos}</strong>
        </div>
      </header>

      {/* PAINEL DE ERRO */}
      {erro && <div style={styles.errorBox}>{erro}</div>}

      {/* PAINEL DE BASE DE DADOS */}
      <section style={styles.card}>
        <div style={styles.uploadRow}>
          <div>
            <h3 style={{ margin: 0 }}>📁 Base de Dados do Histórico</h3>
            <p style={styles.subtext}>Faça o upload do seu arquivo de concursos (.xlsx ou .csv) caso a base esteja pendente.</p>
          </div>
          <input type="file" accept=".xlsx, .xls, .csv" onChange={handleFileUpload} style={styles.fileInput} />
        </div>
      </section>

      {/* PAINEL DOS 6 JUÍZES */}
      {analise && (
        <section style={styles.gridJudges}>
          <div style={styles.judgeCard}>
            <h4>1. Frequência (Top 20)</h4>
            <p><strong>Quentes:</strong> {analise.frequencia.top_5_quentes.join(', ')}</p>
            <p><strong>Frias:</strong> {analise.frequencia.top_5_frias.join(', ')}</p>
          </div>

          <div style={styles.judgeCard}>
            <h4>2. Ciclos</h4>
            <p><strong>Estado:</strong> {analise.ciclos.estado_ciclo_atual}</p>
            <p><strong>Faltantes:</strong> {analise.ciclos.dezenas_faltantes_para_fechar.join(', ') || 'Nenhuma'}</p>
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
            <p><strong>Último Sorteio:</strong> {analise.sequencias_repeticoes.ultimo_concurso.repetidas_do_anterior}</p>
          </div>

          <div style={styles.judgeCard}>
            <h4>6. Moldura / Miolo</h4>
            <p><strong>Moldura Ideal:</strong> {analise.moldura_miolo.padroes_ideais.quantidades_moldura.join(', ')} dezenas</p>
            <p><strong>Último Sorteio:</strong> {analise.moldura_miolo.ultimo_concurso.moldura} Moldura / {analise.moldura_miolo.ultimo_concurso.miolo} Miolo</p>
          </div>
        </section>
      )}

      {/* FORMULÁRIO DE GERAÇÃO */}
      <section style={styles.card}>
        <h2 style={{ marginTop: 0 }}>⚙️ Gerador de Bilhetes Diamante</h2>
        <div style={styles.paramsGrid}>
          <label style={styles.label}>
            Quantidade de Bilhetes:
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
            Máx. Intersecção (Diversidade):
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
          {loadingGeracao ? 'Simulando com Algoritmo Quantitativo...' : '🚀 Gerar Bilhetes Diamante'}
        </button>
      </section>

      {/* BILHETES SELECIONADOS */}
      {palpites && (
        <section style={styles.card}>
          <div style={styles.resultsHeader}>
            <h2 style={{ margin: 0 }}>🎯 Jogos Aprovados ({palpites.bilhetes.length})</h2>
            <span>Eficiência: <strong>{palpites.eficiencia}</strong> ({palpites.tentativas_gastas} simulações)</span>
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

const styles = {
  container: { fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', maxWidth: '1100px', margin: '0 auto', padding: '20px', backgroundColor: '#f4f7f6', minHeight: '100vh' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', background: '#1e293b', color: '#fff', padding: '20px', borderRadius: '10px' },
  title: { margin: 0, fontSize: '1.3rem' },
  statusBadge: { backgroundColor: '#334155', padding: '8px 15px', borderRadius: '20px', fontSize: '0.85rem' },
  errorBox: { backgroundColor: '#fef2f2', border: '1px solid #f87171', color: '#991b1b', padding: '15px', borderRadius: '8px', marginBottom: '20px' },
  card: { background: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)', marginBottom: '20px' },
  uploadRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' },
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