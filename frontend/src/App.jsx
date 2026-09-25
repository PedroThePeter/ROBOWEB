import React, { useState, useEffect } from 'react';

const API_BASE = "https://roboweb-cvha.onrender.com";

export default function App() {
  const [estatisticas, setEstatisticas] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingGerar, setLoadingGerar] = useState(false);
  const [loadingRecarregar, setLoadingRecarregar] = useState(false);
  
  const [quantidade, setQuantidade] = useState(1);
  const [resultadoGeracao, setResultadoGeracao] = useState(null);
  const [mensagemErro, setMensagemErro] = useState("");
  const [mensagemSucesso, setMensagemSucesso] = useState("");

  const carregarEstatisticas = async () => {
    setLoadingStats(true);
    setMensagemErro("");
    try {
      const response = await fetch(`${API_BASE}/api/estatisticas`);
      if (!response.ok) throw new Error(`Erro ${response.status} ao carregar dados.`);
      const data = await response.json();
      setEstatisticas(data);
    } catch (err) {
      setMensagemErro(`Falha de conexão com a API: ${err.message}`);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    carregarEstatisticas();
  }, []);

  const handleRecarregarBase = async () => {
    setLoadingRecarregar(true);
    setMensagemSucesso("");
    try {
      const response = await fetch(`${API_BASE}/api/recarregar-base`, {
        method: "POST", headers: { "Content-Type": "application/json" }
      });
      const data = await response.json();
      if (data.sucesso) {
        setMensagemSucesso(data.mensagem);
        carregarEstatisticas();
      } else {
        setMensagemErro(data.mensagem);
      }
    } catch (err) {
      setMensagemErro(`Erro: ${err.message}`);
    } finally {
      setLoadingRecarregar(false);
    }
  };

  const handleGerarJogos = async () => {
    setLoadingGerar(true);
    setMensagemErro("");
    setMensagemSucesso("");
    try {
      const response = await fetch(`${API_BASE}/api/gerar-jogos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quantidade: parseInt(quantidade, 10) || 1
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Erro inesperado.");
      setResultadoGeracao(data);
      setMensagemSucesso("Bilhetes evoluídos e lapidados com sucesso pelo Comitê Genético!");
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingGerar(false);
    }
  };

  return (
    <div style={{ maxWidth: "1005px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
        <h2>🧬 Lotofácil Engine v6.0 - Comitê Genético</h2>
        <div>
          <span style={{ marginRight: "10px", fontWeight: "bold" }}>
            API: {loadingStats ? "Carregando..." : estatisticas ? "🟢 Online" : "🔴 Offline"}
          </span>
          <button 
            onClick={handleRecarregarBase} 
            disabled={loadingRecarregar}
            style={{ padding: "8px 12px", cursor: "pointer", backgroundColor: "#334155", color: "#fff", border: "none", borderRadius: "4px" }}
          >
            {loadingRecarregar ? "Atualizando..." : "📂 Recarregar Planilha"}
          </button>
        </div>
      </div>

      {/* Alertas */}
      {mensagemErro && <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", borderRadius: "6px", marginBottom: "15px" }}>{mensagemErro}</div>}
      {mensagemSucesso && <div style={{ padding: "12px", backgroundColor: "#dcfce7", color: "#166534", borderRadius: "6px", marginBottom: "15px" }}>{mensagemSucesso}</div>}

      {/* Cards de Inteligência do Comitê */}
      {loadingStats ? (
        <p>Avaliando comitê de horizontes temporais (curto e longo prazo)...</p>
      ) : estatisticas ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "15px", marginBottom: "30px" }}>
          <div style={{ border: "1px solid #eab308", padding: "15px", borderRadius: "8px", backgroundColor: "#fefce8" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#854d0e" }}>⚠️ Consenso de Atrasos (Comitê)</h4>
            <p style={{ margin: 0 }}>
              <strong>Dezenas Críticas:</strong> {
                estatisticas.comite_horizontes?.dezenas_criticas?.length > 0 
                ? estatisticas.comite_horizontes.dezenas_criticas.join(", ") 
                : "Nenhuma dezena em alerta crítico."
              }
            </p>
            <small style={{ color: "#a16207" }}>Fusão analítica de 50 + total de concursos.</small>
          </div>
          
          <div style={{ border: "1px solid #3b82f6", padding: "15px", borderRadius: "8px", backgroundColor: "#eff6ff" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#1d4ed8" }}>🤝 Afinidade Cruzada (Pares)</h4>
            <p style={{ margin: 0, fontSize: "14px" }}>
              <strong>Pares de Consenso:</strong> {
                estatisticas.comite_horizontes?.top_pares?.slice(0, 5).map(p => `(${p[0]}&${p[1]})`).join(", ")
              }
            </p>
            <small style={{ color: "#2563eb" }}>Pares validados em múltiplos horizontes.</small>
          </div>
        </div>
      ) : null}

      {/* Gerador Genético */}
      <div style={{ border: "1px solid #1e40af", padding: "20px", borderRadius: "8px", backgroundColor: "#f0f9ff" }}>
        <h3>🧬 Lapidação por Algoritmo Genético (Rigor Fixo: 150)</h3>
        <p style={{ color: "#475569", fontSize: "14px", marginTop:"-5px" }}>
          População de 300 bilhetes em evolução iterativa com cruzamento parental, mutação estocástica (18%) e pontuação mínima fixa em 150 pontos.
        </p>
        
        <div style={{ display: "flex", gap: "20px", alignItems: "center", marginBottom: "15px", marginTop: "15px", flexWrap: "wrap" }}>
          <div>
            <label style={{ marginRight: "10px", fontWeight: "bold" }}>Quantidade de Bilhetes:</label>
            <input 
              type="number" 
              min="1" max="20" 
              value={quantidade} 
              onChange={(e) => setQuantidade(e.target.value)}
              style={{ width: "60px", padding: "6px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>
          
          <div>
            <span style={{ padding: "6px 12px", backgroundColor: "#e2e8f0", color: "#334155", borderRadius: "4px", fontWeight: "bold", border: "1px solid #cbd5e1" }}>
              🔒 Trava Anti-Overfitting: 150 Pts
            </span>
          </div>
        </div>

        <button 
          onClick={handleGerarJogos} 
          disabled={loadingGerar}
          style={{ padding: "10px 20px", backgroundColor: "#1e40af", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
        >
          {loadingGerar ? "Evolvendo Gerações Genéticas..." : "💎 Executar Lapidação Genética"}
        </button>
      </div>

      {/* Exibição dos Bilhetes Diamante */}
      {resultadoGeracao && resultadoGeracao.bilhetes && resultadoGeracao.bilhetes.length > 0 && (
        <div style={{ marginTop: "30px" }}>
          <h3>🏆 Bilhetes Diamante (Gerados via {resultadoGeracao.estrategia})</h3>
          <p style={{ color: "#555", fontSize: "13px" }}>
            ⏱️ Ciclos evolutivos percorridos: <strong>{resultadoGeracao.geracoes_gastas} gerações</strong> | Score aplicado: <strong>{resultadoGeracao.score_aplicado}/180</strong>
          </p>

          {resultadoGeracao.bilhetes.map((bilhete, index) => (
            <div key={index} style={{ border: "1px solid #22c55e", padding: "15px", borderRadius: "8px", marginBottom: "10px", backgroundColor: "#f0fdf4" }}>
              <p style={{ fontSize: "16px", fontWeight: "bold", color: "#166534", margin: "0", letterSpacing: "1px" }}>
                Bilhete {index + 1}: {bilhete.join(" - ")}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}