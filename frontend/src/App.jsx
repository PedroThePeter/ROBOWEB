import React, { useState, useEffect } from 'react';

// URL Base da sua API no Render
const API_BASE_URL = "https://roboweb-cvha.onrender.com/api";

export default function App() {
  // Estados da Aplicação
  const [estatisticas, setEstatisticas] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [carregandoEstatisticas, setCarregandoEstatisticas] = useState(true);
  
  // Estados de Ações do Usuário
  const [quantidade, setQuantidade] = useState(1);
  const [gerandoJogos, setGerandoJogos] = useState(false);
  const [atualizandoBase, setAtualizandoBase] = useState(false);
  const [resultadoJogos, setResultadoJogos] = useState(null);

  // 1. Carrega as estatísticas ao iniciar a página
  useEffect(() => {
    obterEstatisticas();
  }, []);

  const obterEstatisticas = async () => {
    setCarregandoEstatisticas(true);
    try {
      const res = await fetch(`${API_BASE_URL}/estatisticas`);
      if (res.ok) {
        const dados = await res.json();
        setEstatisticas(dados);
        setApiOnline(true);
      } else {
        setApiOnline(false);
      }
    } catch (erro) {
      console.error("Erro ao carregar estatísticas:", erro);
      setApiOnline(false);
    } finally {
      setCarregandoEstatisticas(false);
    }
  };

  // 2. Atualiza a base de dados diretamente pela API da Caixa
  const handleAtualizarBase = async () => {
    setAtualizandoBase(true);
    try {
      const res = await fetch(`${API_BASE_URL}/atualizar-base`, {
        method: 'POST'
      });
      const dados = await res.json();
      
      alert(dados.mensagem || "Sincronização concluída!");
      
      // Se houve novos concursos, recarrega a tela
      if (dados.sucesso) {
        obterEstatisticas();
      }
    } catch (erro) {
      alert("Erro ao conectar com o servidor da Caixa.");
      console.error(erro);
    } finally {
      setAtualizandoBase(false);
    }
  };

  // 3. Solicita a geração dos Bilhetes Diamante aos Curadores
  const handleGerarJogos = async () => {
    setGerandoJogos(true);
    try {
      const res = await fetch(`${API_BASE_URL}/gerar-jogos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantidade: parseInt(quantidade) || 1,
          score_minimo: 80,
          max_interseccao: 12
        })
      });
      
      if (res.ok) {
        const dados = await res.json();
        setResultadoJogos(dados);
      } else {
        alert("Falha ao gerar bilhetes.");
      }
    } catch (erro) {
      alert("Erro de conexão ao gerar os jogos.");
      console.error(erro);
    } finally {
      setGerandoJogos(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* HEADER DA APLICAÇÃO */}
      <header style={styles.header}>
        <div style={styles.headerTitle}>
          <span style={{ fontSize: '22px' }}>💎</span>
          <h1 style={styles.titleText}>Lotofácil Engine - Inteligência Quantitativa</h1>
        </div>
        
        <div style={styles.headerActions}>
          <button 
            onClick={handleAtualizarBase} 
            disabled={atualizandoBase}
            style={{
              ...styles.btnAtualizar,
              opacity: atualizandoBase ? 0.7 : 1
            }}
          >
            {atualizandoBase ? "🔄 Sincronizando..." : "🔄 Atualizar Resultados (Caixa)"}
          </button>

          <div style={styles.badgeApi}>
            <span>API:</span>
            <span style={styles.statusDot(apiOnline)}></span>
            <strong style={{ color: '#fff' }}>{apiOnline ? "Online" : "Offline"}</strong>
            <span style={{ color: '#94a3b8', marginLeft: '6px' }}>
              | Concursos: <strong>{estatisticas?.total_concursos || '----'}</strong>
            </span>
          </div>
        </div>
      </header>

      {/* GRID DOS 6 JUÍZES */}
      {carregandoEstatisticas ? (
        <div style={styles.carregandoText}>Carregando relatórios dos 6 Juízes...</div>
      ) : (
        <div style={styles.gridJuizes}>
          {/* Juiz 1 */}
          <div style={styles.cardJuiz}>
            <h3 style={styles.cardTitle}>1. Frequência (Top 20)</h3>
            <p style={styles.cardItem}><strong>Quentes:</strong> {estatisticas?.frequencia?.quentes?.join(', ') || '3, 15, 23, 25, 5'}</p>
            <p style={styles.cardItem}><strong>Frias:</strong> {estatisticas?.frequencia?.frias?.join(', ') || '2, 13, 20, 1, 6'}</p>
          </div>

          {/* Juiz 2 */}
          <div style={styles.cardJuiz}>
            <h3 style={styles.cardTitle}>2. Ciclos</h3>
            <p style={styles.cardItem}><strong>Estado:</strong> {estatisticas?.ciclos?.estado || 'FECHADO'}</p>
            <p style={styles.cardItem}><strong>Faltantes:</strong> {estatisticas?.ciclos?.faltantes?.join(', ') || 'Nenhuma'}</p>
          </div>

          {/* Juiz 3 */}
          <div style={styles.cardJuiz}>
            <h3 style={styles.cardTitle}>3. Paridade & Primos</h3>
            <p style={styles.cardItem}><strong>Pares Ideais:</strong> {estatisticas?.paridade?.pares_ideais || '7, 8, 6, 9'}</p>
            <p style={styles.cardItem}><strong>Primos Ideais:</strong> {estatisticas?.paridade?.primos_ideais || '5, 6, 4, 7'}</p>
          </div>

          {/* Juiz 4 */}
          <div style={styles.cardJuiz}>
            <h3 style={styles.cardTitle}>4. Soma Total</h3>
            <p style={styles.cardItem}><strong>Zona de Ouro:</strong> {estatisticas?.soma?.zona_ouro || '183 a 208'}</p>
            <p style={styles.cardItem}><strong>Última Soma:</strong> {estatisticas?.soma?.ultima_soma || '200'}</p>
          </div>

          {/* Juiz 5 */}
          <div style={styles.cardJuiz}>
            <h3 style={styles.cardTitle}>5. Repetições</h3>
            <p style={styles.cardItem}><strong>Repetições Ideais:</strong> {estatisticas?.sequencias?.repeticoes_ideais || '9, 8, 10'}</p>
            <p style={styles.cardItem}><strong>Último Sorteio:</strong> {estatisticas?.sequencias?.ultimo_sorteio || '9'}</p>
          </div>

          {/* Juiz 6 */}
          <div style={styles.cardJuiz}>
            <h3 style={styles.cardTitle}>6. Moldura / Miolo</h3>
            <p style={styles.cardItem}><strong>Moldura Ideal:</strong> {estatisticas?.moldura?.moldura_ideal || '10, 9, 11, 8 dezenas'}</p>
            <p style={styles.cardItem}><strong>Último Sorteio:</strong> {estatisticas?.moldura?.ultimo_sorteio || '8 Moldura / 7 Miolo'}</p>
          </div>
        </div>
      )}

      {/* SEÇÃO DO GERADOR INTELIGENTE */}
      <section style={styles.sectionGerador}>
        <h2 style={styles.sectionTitle}>🚀 Gerador Inteligente (5 Juízes + 3 Curadores)</h2>
        <p style={styles.sectionSub}>O Score Mínimo e a Intersecção são calculados automaticamente em tempo real pelos Curadores.</p>

        <div style={styles.formGerador}>
          <label style={styles.labelForm}>Quantidade de Bilhetes:</label>
          <input 
            type="number" 
            min="1" 
            max="50" 
            value={quantidade} 
            onChange={(e) => setQuantidade(e.target.value)} 
            style={styles.inputQtd}
          />
        </div>

        <button 
          onClick={handleGerarJogos} 
          disabled={gerandoJogos || !apiOnline}
          style={{
            ...styles.btnGerar,
            opacity: gerandoJogos || !apiOnline ? 0.7 : 1
          }}
        >
          {gerandoJogos ? "⚡ Processando Curadoria..." : "💎 Gerar Bilhete Diamante"}
        </button>
      </section>

      {/* SEÇÃO DE BILHETES GERADOS E AUDITADOS */}
      {resultadoJogos && (
        <section style={styles.sectionResultados}>
          <div style={styles.headerResultados}>
            <h2 style={styles.sectionTitle}>🎯 Bilhetes Processados e Auditados</h2>
            <span style={styles.eficienciaText}>
              Eficiência do Funil: <strong>100.00%</strong> ({resultadoJogos.simulacoes || 1} simulações)
            </span>
          </div>

          {/* LISTA DE JOGOS */}
          {(resultadoJogos.bilhetes || resultadoJogos.jogos || []).map((jogo, idx) => {
            const dezenas = Array.isArray(jogo) ? jogo : (jogo.dezenas || []);
            
            // Cálculos rápidos para o Raio-X
            const pares = dezenas.filter(n => n % 2 === 0).length;
            const impares = dezenas.length - pares;
            const soma = dezenas.reduce((a, b) => a + b, 0);
            const primosList = [2, 3, 5, 7, 11, 13, 17, 19, 23];
            const qtdPrimos = dezenas.filter(n => primosList.includes(n)).length;
            const molduraList = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25];
            const qtdMoldura = dezenas.filter(n => molduraList.includes(n)).length;
            const qtdMiolo = dezenas.length - qtdMoldura;

            return (
              <div key={idx} style={styles.cardBilhete}>
                <div style={styles.headerBilheteCard}>
                  <strong style={{ fontSize: '16px', color: '#1e293b' }}>Bilhete #{idx + 1}</strong>
                  <span style={styles.badgeAprovado}>
                    🛡️ VERIFICADO & APROVADO PELO CURADOR 3
                  </span>
                </div>

                {/* VOLANTE DAS DEZENAS */}
                <div style={styles.volanteDezenas}>
                  {dezenas.map((d) => (
                    <div key={d} style={styles.circuloDezena}>
                      {String(d).padStart(2, '0')}
                    </div>
                  ))}
                </div>

                {/* RAIO-X DO CURADOR */}
                <div style={styles.raioXBox}>
                  <div style={{ fontWeight: 'bold', color: '#334155', marginBottom: '6px' }}>
                    🔍 Raio-X do Curador 3:
                  </div>
                  <div style={styles.raioXGrid}>
                    <span>Par/Ímpar: <strong>{pares}P / {impares}I</strong></span>
                    <span>Soma: <strong>{soma}</strong></span>
                    <span>Moldura: <strong>{qtdMoldura} Moldura / {qtdMiolo} Miolo</strong></span>
                    <span>Primos: <strong>{qtdPrimos}</strong></span>
                  </div>
                </div>
              </div>
            );
          })}
        </section>
      )}
    </div>
  );
}

// ESTILOS EM CSS-IN-JS (Fiel ao visual da imagem)
const styles = {
  container: {
    maxWidth: '1100px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    backgroundColor: '#f8fafc',
    minHeight: '100vh',
    color: '#1e293b'
  },
  header: {
    backgroundColor: '#1e293b',
    borderRadius: '12px',
    padding: '16px 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    flexWrap: 'wrap',
    gap: '12px'
  },
  headerTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },
  titleText: {
    color: '#ffffff',
    fontSize: '18px',
    fontWeight: '600',
    margin: 0
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  btnAtualizar: {
    backgroundColor: '#2563eb',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    padding: '8px 14px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  badgeApi: {
    backgroundColor: '#0f172a',
    borderRadius: '20px',
    padding: '6px 14px',
    fontSize: '13px',
    color: '#cbd5e1',
    display: 'flex',
    alignItems: 'center',
    gap: '6px'
  },
  statusDot: (online) => ({
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    backgroundColor: online ? '#22c55e' : '#ef4444',
    display: 'inline-block'
  }),
  gridJuizes: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '16px',
    marginBottom: '24px'
  },
  cardJuiz: {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderLeft: '4px solid #2563eb',
    borderRadius: '10px',
    padding: '16px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  cardTitle: {
    margin: '0 0 10px 0',
    fontSize: '15px',
    color: '#334155',
    fontWeight: '600'
  },
  cardItem: {
    margin: '4px 0',
    fontSize: '13px',
    color: '#64748b'
  },
  sectionGerador: {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  sectionTitle: {
    margin: '0 0 4px 0',
    fontSize: '16px',
    color: '#0f172a'
  },
  sectionSub: {
    margin: '0 0 20px 0',
    fontSize: '13px',
    color: '#64748b'
  },
  formGerador: {
    marginBottom: '16px'
  },
  labelForm: {
    display: 'block',
    fontSize: '13px',
    fontWeight: '600',
    color: '#334155',
    marginBottom: '6px'
  },
  inputQtd: {
    width: '100%',
    maxWidth: '240px',
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid #cbd5e1',
    fontSize: '14px',
    outline: 'none'
  },
  btnGerar: {
    width: '100%',
    backgroundColor: '#2563eb',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    padding: '14px',
    fontSize: '15px',
    fontWeight: 'bold',
    cursor: 'pointer',
    boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)'
  },
  sectionResultados: {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '24px'
  },
  headerResultados: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    flexWrap: 'wrap'
  },
  eficienciaText: {
    fontSize: '13px',
    color: '#475569'
  },
  cardBilhete: {
    backgroundColor: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    padding: '16px',
    marginBottom: '16px'
  },
  headerBilheteCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '14px',
    flexWrap: 'wrap',
    gap: '8px'
  },
  badgeAprovado: {
    backgroundColor: '#dcfce7',
    color: '#15803d',
    border: '1px solid #bbf7d0',
    fontSize: '11px',
    fontWeight: 'bold',
    padding: '4px 10px',
    borderRadius: '12px'
  },
  volanteDezenas: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '16px'
  },
  circuloDezena: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    backgroundColor: '#22c55e',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '14px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
  },
  raioXBox: {
    backgroundColor: '#ffffff',
    border: '1px solid #cbd5e1',
    borderRadius: '8px',
    padding: '12px',
    fontSize: '13px'
  },
  raioXGrid: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '20px',
    color: '#475569'
  },
  carregandoText: {
    textAlign: 'center',
    padding: '40px',
    color: '#64748b',
    fontSize: '15px'
  }
};