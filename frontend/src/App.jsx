import React, { useState, useEffect } from 'react';

// ATENÇÃO: Substitua a URL abaixo pela URL do seu projeto no Render
const RAW_URL = import.meta.env?.VITE_API_URL || 'https://roboweb-cvha.onrender.com/api';
const API_BASE_URL = RAW_URL.replace(/\/$/, '');

export default function App() {
  const [statusApi, setStatusApi] = useState({ carregando: true, online: false, concursos: 0 });
  const [analise, setAnalise] = useState(null);
  const [resultadoGeracao, setResultadoGeracao] = useState(null);
  const [quantidade, setQuantidade] = useState(1);
  const [loadingGeracao, setLoadingGeracao] = useState(false);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    verificarStatusEAnalise();
  }, []);

  const getUrl = (endpoint) => `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

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
      }
    } catch (err) {
      setStatusApi({ carregando: false, online: false, concursos: 0 });
      setErro("Conectando ao servidor no Render. Aguarde alguns segundos...");
    }
  };

  const carregarAnaliseEstatistica = async () => {
    try {
      const res = await fetch(getUrl('/analise_completa'));
      const data = await res.json();
      if (res.ok) setAnalise(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGerarPalpites = async () => {
    setLoadingGeracao(true);
    setErro(null);

    try {
      const res = await fetch(getUrl('/gerar_palpites'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantidade: Number(quantidade) }),
      });

      const data = await res.json();

      if (res.ok) {
        setResultadoGeracao(data);
      } else {
        setErro(data.erro || "Falha no processamento dos Curadores.");
      }
    } catch (err) {
      setErro("Erro de comunicação com os Curadores da API.");
    } finally {
      setLoadingGeracao(false);
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>💎 Lotofácil Engine - Inteligência Quantitativa</h1>
        <div style={styles.statusBadge}>
          API: {statusApi.online ? '🟢 Online' : '🔴 Offline'} | Concursos: <strong>{statusApi.concursos}</strong>
        </div>
      </header>

      {erro && <div style={styles.errorBox}>{erro}</div>}

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

      <section style={styles.card}>
        <h2 style={{ marginTop: 0 }}>🚀 Gerador Inteligente (5 Juízes + 3 Curadores)</h2>
        <p style={styles.subtext}>O Score Mínimo e a Intersecção são calculados automaticamente em tempo real pelos Curadores.</p>
        
        <div style={{ margin: '15px 0', maxWidth: '250px' }}>
          <label style={styles.label}>
            Quantidade de Bilhetes:
            <input 
              type="number" 
              value={quantidade} 
              onChange={(e) => setQuantidade(e.target.value)} 
              min="1" max="20"
              style={styles.input}
            />
          </label>
        </div>

        <button 
          onClick={handleGerarPalpites} 
          disabled={loadingGeracao || !statusApi.online}
          style={loadingGeracao ? {...styles.button, opacity: 0.6} : styles.button}
        >
          {loadingGeracao ? 'Processando Funil dos 3 Curadores...' : '💎 Gerar Bilhete Diamante'}
        </button>
      </section>

      {resultadoGeracao && (
        <section style={styles.card}>
          <div style={styles.resultsHeader}>
            <h2 style={{ margin: 0 }}>🎯 Bilhetes Processados e Auditados</h2>
            <span>Eficiência do Funil: <strong>{resultadoGeracao.eficiencia}</strong> ({resultadoGeracao.simulacoes_realizadas} simulações)</span>
          </div>

          <div style={styles.gamesList}>
            {resultadoGeracao.bilhetes_auditados.map((item, idx) => (
              <div key={idx} style={styles.gameCardContainer}>
                <div style={styles.gameHeaderRow}>
                  <span style={styles.gameTitle}>Bilhete #{idx + 1}</span>
                  <span style={styles.auditBadge}>🛡️ {item.auditoria_curador3.selo_auditoria}</span>
                </div>

                <div style={styles.ballsContainer}>
                  {item.dezenas.map((num) => (
                    <span key={num} style={styles.ball}>{num.toString().padStart(2, '0')}</span>
                  ))}
                </div>

                <div style={styles.auditDetails}>
                  <strong>🔍 Raio-X do Curador 3:</strong>
                  <div style={styles.auditGrid}>
                    <span>Par/Ímpar: <strong>{item.auditoria_curador3.pares_impares}</strong></span>
                    <span>Soma: <strong>{item.auditoria_curador3.soma_total}</strong></span>
                    <span>Moldura: <strong>{item.auditoria_curador3.moldura_miolo}</strong></span>
                    <span>Primos: <strong>{item.auditoria_curador3.primos}</strong></span>
                  </div>
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
  container: { fontFamily: 'Segoe UI, sans-serif', maxWidth: '1100px', margin: '0 auto', padding: '20px', backgroundColor: '#f4f7f6', minHeight: '100vh' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', background: '#1e293b', color: '#fff', padding: '20px', borderRadius: '10px' },
  title: { margin: 0, fontSize: '1.2rem' },
  statusBadge: { backgroundColor: '#334155', padding: '8px 15px', borderRadius: '20px', fontSize: '0.85rem' },
  errorBox: { backgroundColor: '#fef2f2', border: '1px solid #f87171', color: '#991b1b', padding: '15px', borderRadius: '8px', marginBottom: '20px' },
  card: { background: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)', marginBottom: '20px' },
  subtext: { color: '#64748b', fontSize: '0.85rem' },
  gridJudges: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px', marginBottom: '20px' },
  judgeCard: { background: '#fff', padding: '15px', borderRadius: '10px', borderLeft: '4px solid #3b82f6', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' },
  label: { display: 'flex', flexDirection: 'column', gap: '5px', fontWeight: 'bold', fontSize: '0.9rem', color: '#334155' },
  input: { padding: '8px', borderRadius: '5px', border: '1px solid #cbd5e1', fontSize: '1rem' },
  button: { width: '100%', padding: '14px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '1rem', cursor: 'pointer' },
  resultsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', borderBottom: '1px solid #e2e8f0', paddingBottom: '10px' },
  gamesList: { display: 'flex', flexDirection: 'column', gap: '15px' },
  gameCardContainer: { background: '#f8fafc', padding: '15px', borderRadius: '8px', border: '1px solid #cbd5e1' },
  gameHeaderRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' },
  gameTitle: { fontWeight: 'bold', color: '#1e293b' },
  auditBadge: { background: '#dcfce7', color: '#15803d', padding: '4px 10px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold' },
  ballsContainer: { display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' },
  ball: { width: '36px', height: '36px', borderRadius: '50%', background: '#22c55e', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' },
  auditDetails: { background: '#fff', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '0.85rem' },
  auditGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', marginTop: '5px' }
};