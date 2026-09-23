import React, { useState, useEffect } from 'react';

const API_BASE = "https://roboweb-cvha.onrender.com";

export default function App() {
  const [estatisticas, setEstatisticas] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingGerar, setLoadingGerar] = useState(false);
  const [loadingRecarregar, setLoadingRecarregar] = useState(false);
  
  const [quantidade, setQuantidade] = useState(1);
  const [jogosGerados, setJogosGerados] = useState([]);
  const [mensagemErro, setMensagemErro] = useState("");
  const [mensagemSucesso, setMensagemSucesso] = useState("");

  const carregarEstatisticas = async () => {
    setLoadingStats(true);
    setMensagemErro("");
    try {
      const response = await fetch(`${API_BASE}/api/estatisticas`);
      if (!response.ok) {
        throw new Error(`Erro ${response.status} ao carregar dados do servidor.`);
      }
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
    setMensagemErro("");
    try {
      const response = await fetch(`${API_BASE}/api/recarregar-base`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const data = await response.json();
      
      if (data.sucesso) {
        setMensagemSucesso(data.mensagem);
        carregarEstatisticas();
      } else {
        setMensagemErro(data.mensagem);
      }
    } catch (err) {
      setMensagemErro(`Erro ao recarregar base: ${err.message}`);
    } finally {
      setLoadingRecarregar(false);
    }
  };

  const handleGerarJogos = async () => {
    setLoadingGerar(true);
    setMensagemErro("");
    setMensagemSucesso("");
    try {
      const payload = {
        quantidade: parseInt(quantidade, 10) || 1,
        score_minimo: 80,
        max_interseccao: 12
      };

      const response = await fetch(`${API_BASE}/api/gerar-jogos`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Erro inesperado ao gerar os jogos.");
      }

      setJogosGerados(Array.isArray(data) ? data : [data]);
      setMensagemSucesso("Bilhete Diamante gerado com sucesso!");
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingGerar(false);
    }
  };

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
        <h2>💎 Lotofácil Engine - Inteligência Estatística</h2>
        <div>
          <span style={{ marginRight: "10px", fontWeight: "bold" }}>
            API: {loadingStats ? "Carregando..." : estatisticas ? "🟢 Online" : "🔴 Offline"}
          </span>
          {estatisticas && <span>| Concursos: {estatisticas.total_concursos}</span>}
          <button 
            onClick={handleRecarregarBase} 
            disabled={loadingRecarregar}
            style={{ marginLeft: "15px", padding: "8px 12px", cursor: "pointer", backgroundColor: "#334155", color: "#fff", border: "none", borderRadius: "4px" }}
            title="Atualiza a leitura após enviar uma nova planilha Lotofacil.xlsx"
          >
            {loadingRecarregar ? "Atualizando..." : "📂 Recarregar Planilha Local"}
          </button>
        </div>
      </div>

      {/* Alertas */}
      {mensagemErro && (
        <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", borderRadius: "6px", marginBottom: "15px" }}>
          {mensagemErro}
        </div>
      )}
      {mensagemSucesso && (
        <div style={{ padding: "12px", backgroundColor: "#dcfce7", color: "#166534", borderRadius: "6px", marginBottom: "15px" }}>
          {mensagemSucesso}
        </div>
      )}

      {/* Cards Estatísticos */}
      {loadingStats ? (
        <p>Carregando análises dos 6 Juízes...</p>
      ) : estatisticas ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "15px", marginBottom: "30px" }}>
          <div style={{ border: "1px solid #ccc", padding: "15px", borderRadius: "8px" }}>
            <h4>1. Frequência (Top 20)</h4>
            <p><strong>Quentes:</strong> {Array.isArray(estatisticas.frequencia?.quentes) ? estatisticas.frequencia.quentes.join(", ") : "N/A"}</p>
          </div>
          <div style={{ border: "1px solid #ccc", padding: "15px", borderRadius: "8px" }}>
            <h4>2. Ciclos</h4>
            <p><strong>Estado:</strong> {estatisticas.ciclos?.estado || "N/A"}</p>
          </div>
          <div style={{ border: "1px solid #ccc", padding: "15px", borderRadius: "8px" }}>
            <h4>3. Paridade & Primos</h4>
            <p><strong>Pares Ideais:</strong> {Array.isArray(estatisticas.paridade?.pares_ideais) ? estatisticas.paridade.pares_ideais.join(", ") : "N/A"}</p>
          </div>
        </div>
      ) : null}

      {/* Gerador de Jogos */}
      <div style={{ border: "1px solid #1e40af", padding: "20px", borderRadius: "8px", backgroundColor: "#f0f9ff" }}>
        <h3>🚀 Gerador Inteligente (Juízes + Curadores)</h3>
        <div style={{ marginBottom: "15px" }}>
          <label style={{ marginRight: "10px" }}>Quantidade de Bilhetes:</label>
          <input 
            type="number" 
            min="1" 
            max="10" 
            value={quantidade} 
            onChange={(e) => setQuantidade(e.target.value)}
            style={{ width: "60px", padding: "5px" }}
          />
        </div>
        <button 
          onClick={handleGerarJogos} 
          disabled={loadingGerar}
          style={{ padding: "10px 20px", backgroundColor: "#1e40af", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer" }}
        >
          {loadingGerar ? "Processando Curadoria..." : "💎 Gerar Bilhete Diamante"}
        </button>
      </div>

      {/* Exibição dos Jogos */}
      {jogosGerados.length > 0 && (
        <div style={{ marginTop: "30px" }}>
          <h3>🎟️ Bilhetes Gerados</h3>
          {jogosGerados.map((jogo, index) => (
            <div key={index} style={{ border: "1px solid #22c55e", padding: "15px", borderRadius: "8px", marginBottom: "10px", backgroundColor: "#f0fdf4" }}>
              <p><strong>Bilhete {index + 1}:</strong> {Array.isArray(jogo.dezenas) ? jogo.dezenas.join(" - ") : JSON.stringify(jogo)}</p>
              {jogo.score && <p><small>Score de Validação: {jogo.score} pontos</small></p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}