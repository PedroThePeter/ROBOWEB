import React, { useState, useEffect } from 'react';

const API_BASE = "https://roboweb-cvha.onrender.com";

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
  const [loadingDesd, setLoadingDesd] = useState(false);
  const [resultadoDesd, setResultadoDesd] = useState(null);

  const carregarEstatisticas = async () => {
    setLoadingStats(true);
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
      if (!response.ok) throw new Error("Erro inesperado.");
      setResultadoGeracao(data);
      setMensagemSucesso(`3 bilhetes térmicos gerados para o concurso ${data.concurso}.`);
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingGerar(false);
    }
  };

  const handleDesdobrarEspectro = async () => {
    setLoadingDesd(true);
    try {
      const response = await fetch(`${API_BASE}/api/desdobramento-espectro`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error("Erro inesperado.");
      setResultadoDesd(data);
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingDesd(false);
    }
  };

  const handleDownloadTXT = (bilhetesObj, tipoOrigem, numConcurso) => {
    if (!bilhetesObj) return;
    let texto = `========================================\n LOTOFÁCIL IA v8.0 - REGISTRO DE JOGOS\n========================================\nOrigem: ${tipoOrigem}\nConcurso Alvo: ${numConcurso || "Indefinido"}\n\n`;
    texto += `[FRIO - T=0%]:   ${bilhetesObj.frio.map(dois).join(" - ")}\n`;
    texto += `[MORNO - T=50%]:  ${bilhetesObj.morno.map(dois).join(" - ")}\n`;
    texto += `[QUENTE - T=100%]: ${bilhetesObj.quente.map(dois).join(" - ")}\n`;
    
    const blob = new Blob([texto], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `lotofacil_${tipoOrigem}_conc_${numConcurso}.txt`;
    link.click();
  };

  const desempenho = estatisticas?.desempenho;
  const porTemp = desempenho?.por_temperatura;

  return (
    <div style={{ maxWidth: "1005px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
        <h2>🎲 Lotofácil Engine v8.0 - Espectro Térmico Isolado</h2>
        <button onClick={handleRecarregarBase} disabled={loadingRecarregar} style={{ padding: "8px 12px", backgroundColor: "#334155", color: "#fff", border: "none", borderRadius: "4px" }}>
          {loadingRecarregar ? "Atualizando..." : "📂 Recarregar Planilha"}
        </button>
      </div>

      {mensagemErro && <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", marginBottom: "15px" }}>{mensagemErro}</div>}
      {mensagemSucesso && <div style={{ padding: "12px", backgroundColor: "#dcfce7", color: "#166534", marginBottom: "15px" }}>{mensagemSucesso}</div>}

      {estatisticas && (
        <div style={{ border: "1px solid #eab308", padding: "15px", borderRadius: "8px", backgroundColor: "#fefce8", marginBottom: "30px" }}>
          <h4 style={{ margin: "0 0 10px 0" }}>🧾 Desempenho Real Isolado por Temperatura (Alvo: {estatisticas.proximo_concurso})</h4>
          {desempenho && desempenho.conferidos > 0 ? (
            <div style={{ display: "grid", gap: "6px" }}>
              <div style={{ padding: "6px", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd" }}>
                🧊 <strong>Frio (T=0%):</strong> {porTemp?.espectro_frio?.conferidos || 0} jog. | Média: <strong>{porTemp?.espectro_frio?.media || 0}</strong> | 11+: {pct(porTemp?.espectro_frio?.taxa_11 || 0)}
              </div>
              <div style={{ padding: "6px", backgroundColor: "#fefce8", border: "1px solid #fef08a" }}>
                🌤 <strong>Morno (T=50% - 7/4/4):</strong> {porTemp?.espectro_morno?.conferidos || 0} jog. | Média: <strong>{porTemp?.espectro_morno?.media || 0}</strong> | 11+: {pct(porTemp?.espectro_morno?.taxa_11 || 0)}
              </div>
              <div style={{ padding: "6px", backgroundColor: "#fef2f2", border: "1px solid #fecaca" }}>
                🔥 <strong>Quente (T=100%):</strong> {porTemp?.espectro_quente?.conferidos || 0} jog. | Média: <strong>{porTemp?.espectro_quente?.media || 0}</strong> | 11+: {pct(porTemp?.espectro_quente?.taxa_11 || 0)}
              </div>
            </div>
          ) : (
            <p>Nenhum bilhete conferido ainda. Atualize a planilha com o novo resultado.</p>
          )}
        </div>
      )}

      <div style={{ border: "1px solid #1e40af", padding: "20px", borderRadius: "8px", backgroundColor: "#f0f9ff", marginBottom: "30px" }}>
        <h3>🎲 Gerador Automático de Sorteio Ponderado</h3>
        <button onClick={handleGerarJogos} disabled={loadingGerar} style={{ padding: "12px 24px", backgroundColor: "#1d4ed8", color: "#fff", border: "none", borderRadius: "5px" }}>
          {loadingGerar ? "Gerando..." : "🎯 Gerar Bilhetes (Frio, Morno, Quente)"}
        </button>
      </div>

      {resultadoGeracao && resultadoGeracao.bilhetes && (
        <div style={{ border: "1px solid #22c55e", padding: "20px", borderRadius: "8px", backgroundColor: "#f0fdf4", marginBottom: "30px" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>🎟️ 3 Bilhetes Térmicos Gerados</h3>
            <button onClick={() => handleDownloadTXT(resultadoGeracao.bilhetes, "Sorteio Ponderado", resultadoGeracao.concurso)} style={{ padding: "8px 16px", backgroundColor: "#15803d", color: "#fff", border: "none", borderRadius: "5px" }}>📥 Salvar TXT</button>
          </div>
          <p><strong>🧊 Frio:</strong> {resultadoGeracao.bilhetes.frio.map(dois).join(" - ")}</p>
          <p><strong>🌤️ Morno (7/4/4):</strong> {resultadoGeracao.bilhetes.morno.map(dois).join(" - ")}</p>
          <p><strong>🔥 Quente:</strong> {resultadoGeracao.bilhetes.quente.map(dois).join(" - ")}</p>
        </div>
      )}

      <div style={{ border: "1px solid #7c3aed", padding: "20px", borderRadius: "8px", backgroundColor: "#faf5ff" }}>
        <h3>🧩 Gerador Automático de Desdobramento Espectral</h3>
        <button onClick={handleDesdobrarEspectro} disabled={loadingDesd} style={{ padding: "12px 24px", backgroundColor: "#4f46e5", color: "#fff", border: "none", borderRadius: "5px" }}>
          {loadingDesd ? "Calculando..." : "🧩 Gerar Desdobramento (Frio, Morno, Quente)"}
        </button>
      </div>

      {resultadoDesd && resultadoDesd.bilhetes && (
        <div style={{ border: "1px solid #a78bfa", padding: "20px", borderRadius: "8px", backgroundColor: "#faf5ff", marginTop: "30px" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>🧩 3 Bilhetes de Desdobramento</h3>
            <button onClick={() => handleDownloadTXT(resultadoDesd.bilhetes, "Desdobramento", resultadoDesd.concurso)} style={{ padding: "8px 16px", backgroundColor: "#6d28d9", color: "#fff", border: "none", borderRadius: "5px" }}>📥 Salvar TXT</button>
          </div>
          <p><strong>🧊 Frio:</strong> {resultadoDesd.bilhetes.frio.map(dois).join(" - ")}</p>
          <p><strong>🌤️ Morno (8/5/4):</strong> {resultadoDesd.bilhetes.morno.map(dois).join(" - ")}</p>
          <p><strong>🔥 Quente:</strong> {resultadoDesd.bilhetes.quente.map(dois).join(" - ")}</p>
        </div>
      )}
    </div>
  );
}