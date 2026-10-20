import React, { useState, useEffect } from 'react';

// ==========================================
// 🔗 CONEXÃO LOCAL DIRETA (API_BASE)
// ==========================================
const API_BASE = "http://localhost:8000";

const pct = (v) => `${(v * 100).toFixed(1).replace(".", ",")}%`;
const dois = (d) => String(d).padStart(2, "0");

export default function App() {
  const [estatisticas, setEstatisticas] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingGerar, setLoadingGerar] = useState(false);
  const [loadingRecarregar, setLoadingRecarregar] = useState(false);
  const [resultadoGeracao, setResultadoGeracao] = useState(null);
  const [mensagemErro, setMensagemErro] = useState("");
  const [mensagemSucesso, setMensagemSucesso] = useState("");

  const carregarEstatisticas = async () => {
    setLoadingStats(true);
    try {
      const response = await fetch(`${API_BASE}/api/estatisticas`);
      if (!response.ok) throw new Error(`Erro ${response.status} ao carregar dados do servidor local.`);
      const data = await response.json();
      setEstatisticas(data);
    } catch (err) {
      setMensagemErro(`Falha de conexão com a API local: ${err.message}`);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    carregarEstatisticas();
  }, []);

  const handleRecarregarBase = async () => {
    setLoadingRecarregar(true);
    setMensagemSucesso(""); setMensagemErro("");
    try {
      const response = await fetch(`${API_BASE}/api/recarregar-base`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.mensagem || "Erro inesperado.");
      setMensagemSucesso(data.mensagem);
      carregarEstatisticas();
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingRecarregar(false);
    }
  };

  const handleGerarJogos = async () => {
    setLoadingGerar(true);
    setMensagemErro(""); setMensagemSucesso("");
    try {
      const response = await fetch(`${API_BASE}/api/gerar-jogos`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error("Erro inesperado ao gerar os jogos.");
      setResultadoGeracao(data);
      setMensagemSucesso(`Portfólio de 3 bilhetes térmicos gerado e auditado para o Concurso ${data.concurso}.`);
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingGerar(false);
    }
  };

  const handleDownloadTXT = (bilhetesObj, numConcurso) => {
    if (!bilhetesObj) return;
    let texto = `========================================\n LOTOFÁCIL IA v8.1 - PORTFÓLIO AUDITADO\n========================================\nAmbiente: 100% Local (Localhost)\nConcurso Alvo: ${numConcurso || "Indefinido"}\n\n`;
    texto += `[🧊 FRIO - T=0%]:   ${bilhetesObj.frio.map(dois).join(" - ")}\n`;
    texto += `[🌤️ MORNO - T=50%]: ${bilhetesObj.morno.map(dois).join(" - ")}\n`;
    texto += `[🔥 QUENTE (7-4-4)]: ${bilhetesObj.quente.map(dois).join(" - ")}\n`;
    
    const blob = new Blob([texto], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `lotofacil_portfolio_conc_${numConcurso}.txt`;
    link.click();
  };

  const desempenho = estatisticas?.desempenho;
  const porTemp = desempenho?.por_temperatura;

  return (
    <div style={{ maxWidth: "1005px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif", color: "#1e293b" }}>
      {/* CABEÇALHO PRINCIPAL */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2>🎲 Lotofácil Engine v8.1 - Curadoria Múltipla Local</h2>
        <button 
          onClick={handleRecarregarBase} 
          disabled={loadingRecarregar} 
          style={{ padding: "10px 16px", backgroundColor: "#334155", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}
        >
          {loadingRecarregar ? "Atualizando..." : "📂 Recarregar Planilha"}
        </button>
      </div>

      {/* FEEDBACKS VISUAIS */}
      {mensagemErro && <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", borderRadius: "6px", marginBottom: "15px", border: "1px solid #fca5a5" }}>⚠️ {mensagemErro}</div>}
      {mensagemSucesso && <div style={{ padding: "12px", backgroundColor: "#dcfce7", color: "#166534", borderRadius: "6px", marginBottom: "15px", border: "1px solid #86efac" }}>✅ {mensagemSucesso}</div>}

      {/* QUADRO DE DESEMPENHO REAL */}
      {estatisticas && (
        <div style={{ border: "1px solid #eab308", padding: "18px", borderRadius: "8px", backgroundColor: "#fefce8", marginBottom: "30px" }}>
          <h4 style={{ margin: "0 0 12px 0", fontSize: "16px", color: "#854d0e" }}>
            📊 Desempenho do Diário Térmico (Concurso Alvo: {estatisticas.proximo_concurso || "Buscando..."})
          </h4>
          {desempenho && desempenho.conferidos > 0 ? (
            <div style={{ display: "grid", gap: "8px" }}>
              <div style={{ padding: "8px 12px", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd", borderRadius: "4px" }}>
                🧊 <strong>Frio (T=0% - Determinístico):</strong> {porTemp?.espectro_frio?.conferidos || 0} jogos conferidos | Média: <strong>{porTemp?.espectro_frio?.media || 0}</strong> acertos | Taxa 11+: {pct(porTemp?.espectro_frio?.taxa_11 || 0)}
              </div>
              <div style={{ padding: "8px 12px", backgroundColor: "#fefce8", border: "1px solid #fef08a", borderRadius: "4px" }}>
                🌤️ <strong>Morno (T=50% - Calculado):</strong> {porTemp?.espectro_morno?.conferidos || 0} jogos conferidos | Média: <strong>{porTemp?.espectro_morno?.media || 0}</strong> acertos | Taxa 11+: {pct(porTemp?.espectro_morno?.taxa_11 || 0)}
              </div>
              <div style={{ padding: "8px 12px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "4px" }}>
                🔥 <strong>Quente (T=100% - Geometria 7-4-4):</strong> {porTemp?.espectro_quente?.conferidos || 0} jogos conferidos | Média: <strong>{porTemp?.espectro_quente?.media || 0}</strong> acertos | Taxa 11+: {pct(porTemp?.espectro_quente?.taxa_11 || 0)}
              </div>
            </div>
          ) : (
            <p style={{ margin: 0, color: "#713f12", fontSize: "14px" }}>
              Nenhum palpite conferido na base ainda. Atualize o arquivo <code>Lotofacil.xlsx</code> e clique no botão acima para conferir os resultados anteriores.
            </p>
          )}
        </div>
      )}

      {/* ÁREA DE GERAÇÃO AUDITADA */}
      <div style={{ border: "1px solid #2563eb", padding: "20px", borderRadius: "8px", backgroundColor: "#eff6ff", marginBottom: "30px" }}>
        <h3 style={{ margin: "0 0 10px 0", color: "#1e40af" }}>🛡️ Gerador Auditado por Curadores (5 Juízes)</h3>
        <p style={{ margin: "0 0 15px 0", fontSize: "14px", color: "#1e3a8a" }}>
          Ao clicar, os 3 bilhetes (Frio, Morno e Quente 7-4-4) serão gerados sob a Esteira dos 5 Juízes Heurísticos e validados pelo Curador 2 para diversidade máxima de portfólio.
        </p>
        <button 
          onClick={handleGerarJogos} 
          disabled={loadingGerar} 
          style={{ padding: "12px 24px", backgroundColor: "#2563eb", color: "#fff", border: "none", borderRadius: "6px", fontSize: "16px", cursor: "pointer", fontWeight: "bold" }}
        >
          {loadingGerar ? "Processando Curadoria..." : "🎯 Gerar Portfólio (Frio, Morno, Quente)"}
        </button>
      </div>

      {/* EXIBIÇÃO DOS RESULTADOS APROVADOS */}
      {resultadoGeracao && resultadoGeracao.bilhetes && (
        <div style={{ border: "1px solid #16a34a", padding: "20px", borderRadius: "8px", backgroundColor: "#f0fdf4", marginBottom: "30px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
            <h3 style={{ margin: 0, color: "#15803d" }}>🎟️ Portfólio Térmico Aprovado (Concurso {resultadoGeracao.concurso})</h3>
            <button 
              onClick={() => handleDownloadTXT(resultadoGeracao.bilhetes, resultadoGeracao.concurso)} 
              style={{ padding: "8px 16px", backgroundColor: "#16a34a", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}
            >
              📥 Salvar TXT
            </button>
          </div>
          <div style={{ fontSize: "15px", lineHeight: "1.8" }}>
            <p style={{ margin: "8px 0" }}>
              <strong>🧊 Frio (T=0%):</strong> {resultadoGeracao.bilhetes.frio.map(dois).join(" - ")}
            </p>
            <p style={{ margin: "8px 0" }}>
              <strong>🌤️ Morno (T=50%):</strong> {resultadoGeracao.bilhetes.morno.map(dois).join(" - ")}
            </p>
            <p style={{ margin: "8px 0" }}>
              <strong>🔥 Quente (7-4-4):</strong> {resultadoGeracao.bilhetes.quente.map(dois).join(" - ")}
            </p>
          </div>
          {resultadoGeracao.curador_2_tentativas && (
            <p style={{ fontSize: "12px", color: "#166534", marginTop: "12px", marginBottom: 0 }}>
              ℹ️ Aprovado pelo Curador 2 após {resultadoGeracao.curador_2_tentativas} ciclo(s) de validação de diversidade cruzada.
            </p>
          )}
        </div>
      )}
    </div>
  );
}