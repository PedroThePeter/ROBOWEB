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
          quantidade: parseInt(quantidade, 10) || 1,
          max_interseccao: 12
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Erro inesperado.");
      setJogosGerados(Array.isArray(data) ? data : [data]);
      setMensagemSucesso("Bilhetes gerados com sucesso baseados na Matriz Preditiva!");
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
        <h2>🧠 Lotofácil Engine v5.0 - Dinâmica Preditiva</h2>
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

      {/* Cards Estatísticos (Agora Mostrando a Inteligência Dinâmica) */}
      {loadingStats ? (
        <p>Avaliando matriz de co-ocorrência e dezenas em atraso...</p>
      ) : estatisticas ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "15px", marginBottom: "30px" }}>
          <div style={{ border: "1px solid #eab308", padding: "15px", borderRadius: "8px", backgroundColor: "#fefce8" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#854d0e" }}>⚠️ Alerta de Atraso (Pressão)</h4>
            <p style={{ margin: 0 }}>
              <strong>Dezenas Críticas:</strong> {
                estatisticas.atrasos_reais?.dezenas_criticas?.length > 0 
                ? estatisticas.atrasos_reais.dezenas_criticas.join(", ") 
                : "Nenhuma dezena em atraso grave."
              }
            </p>
            <small style={{ color: "#a16207" }}>Têm alta propensão a sair no próximo.</small>
          </div>
          
          <div style={{ border: "1px solid #3b82f6", padding: "15px", borderRadius: "8px", backgroundColor: "#eff6ff" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#1d4ed8" }}>🤝 Matriz de Afinidade (Duplas)</h4>
            <p style={{ margin: 0, fontSize: "14px" }}>
              <strong>Top 5 Pares:</strong> {
                estatisticas.co_ocorrencia?.top_pares?.slice(0, 5).map(p => `(${p[0]}&${p[1]})`).join(", ")
              }
            </p>
            <small style={{ color: "#2563eb" }}>Costumam ser sorteadas juntas.</small>
          </div>
        </div>
      ) : null}

      {/* Gerador de Jogos */}
      <div style={{ border: "1px solid #1e40af", padding: "20px", borderRadius: "8px", backgroundColor: "#f0f9ff" }}>
        <h3>🚀 Gerador de Atrasos e Afinidade (Rigor Fixo)</h3>
        <p style={{ color: "#475569", fontSize: "14px", marginTop:"-5px" }}>
          O Score foi <strong>matematicamente cravado em 150 pontos (Teto 180)</strong>. Isso exige do robô alinhamento com padrões reais, mas preserva a folga de entropia necessária para os sorteios anômalos.
        </p>
        
        <div style={{ display: "flex", gap: "20px", alignItems: "center", marginBottom: "15px", marginTop: "15px", flexWrap: "wrap" }}>
          <div>
            <label style={{ marginRight: "10px", fontWeight: "bold" }}>Quantidade de Bilhetes:</label>
            <input 
              type="number" 
              min="1" max="10" 
              value={quantidade} 
              onChange={(e) => setQuantidade(e.target.value)}
              style={{ width: "60px", padding: "6px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>
          
          <div>
            <span style={{ padding: "6px 12px", backgroundColor: "#e2e8f0", color: "#334155", borderRadius: "4px", fontWeight: "bold", border: "1px solid #cbd5e1" }}>
              🔒 Filtro Trava: 150 Pontos
            </span>
          </div>
        </div>

        <button 
          onClick={handleGerarJogos} 
          disabled={loadingGerar}
          style={{ padding: "10px 20px", backgroundColor: "#1e40af", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
        >
          {loadingGerar ? "Processando Matriz Preditiva..." : "💎 Gerar Bilhete(s)"}
        </button>
      </div>

      {/* Exibição Formatada dos Jogos */}
      {jogosGerados.length > 0 && (
        <div style={{ marginTop: "30px" }}>
          <h3>🎟️ Bilhetes Filtrados</h3>
          {jogosGerados.map((item, index) => {
            const dezenasLista = item.bilhetes && Array.isArray(item.bilhetes[0]) 
              ? item.bilhetes[0] : [];

            return (
              <div key={index} style={{ border: "1px solid #22c55e", padding: "15px", borderRadius: "8px", marginBottom: "10px", backgroundColor: "#f0fdf4" }}>
                <p style={{ fontSize: "16px", fontWeight: "bold", color: "#166534", margin: "0 0 8px 0", letterSpacing: "1px" }}>
                  Bilhete {index + 1}: {dezenasLista.length > 0 ? dezenasLista.join(" - ") : ""}
                </p>
                {item.tentativas_gastas !== undefined && (
                  <p style={{ margin: "0", color: "#374151" }}>
                    <small>⚡ Tentativas gastas: <strong>{item.tentativas_gastas}</strong> | Score: <strong>150/{item.score_maximo_arquitetura}</strong></small>
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}