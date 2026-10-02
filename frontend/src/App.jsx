import React, { useState, useEffect } from 'react';

const API_BASE = "https://roboweb-cvha.onrender.com"; // Preservando sua conexão com o Render

const pct = (v) => `${(v * 100).toFixed(1).replace(".", ",")}%`;
const dois = (d) => String(d).padStart(2, "0");

export default function App() {
  const [estatisticas, setEstatisticas] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingGerar, setLoadingGerar] = useState(false);
  const [loadingRecarregar, setLoadingRecarregar] = useState(false);

  const [concurso, setConcurso] = useState("");
  const [resultadoGeracao, setResultadoGeracao] = useState(null);
  const [mensagemErro, setMensagemErro] = useState("");
  const [mensagemSucesso, setMensagemSucesso] = useState("");

  // Desdobramento Espectral
  const [concursoDesd, setConcursoDesd] = useState("");
  const [loadingDesd, setLoadingDesd] = useState(false);
  const [resultadoDesd, setResultadoDesd] = useState(null);
  const [erroDesd, setErroDesd] = useState("");

  const carregarEstatisticas = async () => {
    setLoadingStats(true);
    try {
      const response = await fetch(`${API_BASE}/api/estatisticas`);
      if (!response.ok) throw new Error(`Erro ${response.status} ao carregar dados.`);
      const data = await response.json();
      setEstatisticas(data);
    } catch (err) {
      setEstatisticas(null);
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
        method: "POST", headers: { "Content-Type": "application/json" }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.mensagem || "Erro inesperado.");
      if (data.status === "sucesso" || data.sucesso) {
        setMensagemSucesso(data.mensagem);
        carregarEstatisticas();
      } else {
        setMensagemErro(data.mensagem || "Não foi possível recarregar a base.");
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
      const corpo = {};
      const numConcurso = parseInt(concurso, 10);
      if (numConcurso > 0) corpo.concurso = numConcurso;

      const response = await fetch(`${API_BASE}/api/gerar-jogos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Erro inesperado.");
      setResultadoGeracao(data);
      setMensagemSucesso("3 bilhetes térmicos gerados automaticamente.");
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingGerar(false);
    }
  };

  const handleDesdobrarEspectro = async () => {
    setLoadingDesd(true);
    setErroDesd("");
    setResultadoDesd(null);
    try {
      const corpo = {};
      const numConcurso = parseInt(concursoDesd, 10);
      if (numConcurso > 0) corpo.concurso = numConcurso;

      const response = await fetch(`${API_BASE}/api/desdobramento-espectro`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Erro inesperado.");
      setResultadoDesd(data);
    } catch (err) {
      setErroDesd(err.message);
    } finally {
      setLoadingDesd(false);
    }
  };

  const handleDownloadTXT = (bilhetesObj, tipoOrigem, numConcurso) => {
    if (!bilhetesObj) return;
    
    let texto = `========================================\n`;
    texto += ` LOTOFÁCIL IA v8.0 - REGISTRO DE JOGOS\n`;
    texto += `========================================\n`;
    texto += `Origem: ${tipoOrigem}\n`;
    texto += `Concurso Alvo: ${numConcurso || "Não informado"}\n`;
    texto += `Data de Exportação: ${new Date().toLocaleString('pt-BR')}\n\n`;
    
    texto += `[FRIO - T=0%]:   ${bilhetesObj.frio.map(dois).join(" - ")}\n`;
    texto += `[MORNO - T=50%]:  ${bilhetesObj.morno.map(dois).join(" - ")}\n`;
    texto += `[QUENTE - T=100%]: ${bilhetesObj.quente.map(dois).join(" - ")}\n`;
    
    texto += `\n========================================\n`;
    texto += `Boa sorte! Espectro térmico aplicado.\n`;

    const blob = new Blob([texto], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const sufixoConcurso = numConcurso ? `_conc_${numConcurso}` : "";
    link.download = `lotofacil_${tipoOrigem.toLowerCase().replace(/[\s()]+/g, '_')}${sufixoConcurso}.txt`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const base = estatisticas?.base;
  const memoria = base?.memoria;
  const desempenho = estatisticas?.desempenho;

  return (
    <div style={{ maxWidth: "1005px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
        <h2>🎲 Lotofácil Engine v8.0 - Espectro Térmico Automático (3 Bilhetes)</h2>
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

      {/* Cards de estatísticas reais */}
      {loadingStats ? (
        <p>Carregando estatísticas da base histórica...</p>
      ) : estatisticas ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "15px", marginBottom: "30px" }}>
          <div style={{ border: "1px solid #3b82f6", padding: "15px", borderRadius: "8px", backgroundColor: "#eff6ff" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#1d4ed8" }}>📊 Teste de memória do histórico</h4>
            {!base?.disponivel ? (
              <p style={{ margin: 0, fontSize: "14px" }}>{base?.mensagem}</p>
            ) : !memoria ? (
              <p style={{ margin: 0, fontSize: "14px" }}>{base?.mensagem}</p>
            ) : (
              <>
                <p style={{ margin: "0 0 8px 0", fontSize: "14px" }}>
                  <strong>{base.concursos}</strong> concursos analisados.{" "}
                  <strong>{memoria.achados}/{memoria.total_testes}</strong> testes acima do acaso.
                </p>
                <ul style={{ margin: "0 0 8px 0", paddingLeft: "18px", fontSize: "13px" }}>
                  {memoria.testes.map((t) => (
                    <li key={t.nome}>
                      {t.achado ? "⚠️" : "✅"} <strong>{t.nome}</strong>: {t.detalhe}
                    </li>
                  ))}
                </ul>
                <small style={{ color: "#2563eb" }}>{memoria.conclusao}</small>
              </>
            )}
          </div>

          <div style={{ border: "1px solid #eab308", padding: "15px", borderRadius: "8px", backgroundColor: "#fefce8" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#854d0e" }}>🧾 Desempenho real conferido</h4>
            {desempenho && desempenho.conferidos > 0 ? (
              <p style={{ margin: 0, fontSize: "14px" }}>
                Bilhetes conferidos: <strong>{desempenho.conferidos}</strong><br />
                Média de acertos: <strong>{desempenho.media.toFixed(2)}</strong> (aleatório: 9,00)<br />
                Com 11+: <strong>{pct(desempenho.taxa_11)}</strong> (aleatório: {pct(desempenho.taxa_11_aleatoria)})
              </p>
            ) : (
              <p style={{ margin: 0, fontSize: "14px" }}>
                Nenhum bilhete conferido ainda. Informe o concurso ao gerar e rode{" "}
                <code>python diario.py conferir Lotofacil.xlsx</code> depois do sorteio.
              </p>
            )}
            <small style={{ color: "#a16207" }}>
              Trava de pesos: {estatisticas.trava_valida ? "🔒 validada" : "não ativa (pesos uniformes)"}
            </small>
          </div>
        </div>
      ) : null}

      {/* Gerador Automático (Sorteio Ponderado - 3 Bilhetes) */}
      <div style={{ border: "1px solid #1e40af", padding: "20px", borderRadius: "8px", backgroundColor: "#f0f9ff" }}>
        <h3>🎲 Gerador Automático de Sorteio Ponderado</h3>
        <p style={{ color: "#475569", fontSize: "14px", marginTop: "-5px" }}>
          Ao clicar no botão, o robô gera automaticamente <strong>exatamente 3 bilhetes</strong> com as 3 temperaturas térmicas (Frio, Morno e Quente).
        </p>

        <div style={{ marginBottom: "15px", marginTop: "15px" }}>
          <label style={{ marginRight: "10px", fontWeight: "bold" }}>Concurso (opcional):</label>
          <input
            type="number"
            min="1"
            value={concurso}
            onChange={(e) => setConcurso(e.target.value)}
            placeholder="ex.: 3800"
            style={{ width: "100px", padding: "6px", borderRadius: "4px", border: "1px solid #ccc" }}
          />
        </div>

        <button
          onClick={handleGerarJogos}
          disabled={loadingGerar}
          style={{ padding: "12px 24px", backgroundColor: "#1d4ed8", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold", fontSize: "15px" }}
        >
          {loadingGerar ? "Gerando 3 Bilhetes Térmicos..." : "🎯 Gerar Bilhetes (Frio, Morno, Quente)"}
        </button>
      </div>

      {/* Exibição dos 3 Bilhetes de Sorteio */}
      {resultadoGeracao && resultadoGeracao.bilhetes && (
        <div style={{ marginTop: "30px", border: "1px solid #22c55e", padding: "20px", borderRadius: "8px", backgroundColor: "#f0fdf4" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", marginBottom: "15px" }}>
            <h3 style={{ margin: 0, color: "#166534" }}>🎟️ 3 Bilhetes Térmicos Gerados (Concurso: {resultadoGeracao.concurso ?? "Não informado"})</h3>
            <button
              onClick={() => handleDownloadTXT(resultadoGeracao.bilhetes, "Sorteio Ponderado Triplo", resultadoGeracao.concurso)}
              style={{ padding: "8px 16px", backgroundColor: "#15803d", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
            >
               📥 Salvar os 3 em TXT
            </button>
          </div>

          <div style={{ padding: "10px", margin: "8px 0", backgroundColor: "#fff", borderRadius: "6px", border: "1px solid #bae6fd" }}>
            <strong style={{ color: "#0369a1" }}>🧊 Bilhete Frio (T = 0% - Histórico):</strong>
            <p style={{ fontSize: "16px", fontWeight: "bold", margin: "5px 0 0 0", letterSpacing: "1px" }}>
              {resultadoGeracao.bilhetes.frio.map(dois).join(" - ")}
            </p>
          </div>

          <div style={{ padding: "10px", margin: "8px 0", backgroundColor: "#fff", borderRadius: "6px", border: "1px solid #fef08a" }}>
            <strong style={{ color: "#a16207" }}>🌤️ Bilhete Morno (T = 50% - Superposição):</strong>
            <p style={{ fontSize: "16px", fontWeight: "bold", margin: "5px 0 0 0", letterSpacing: "1px" }}>
              {resultadoGeracao.bilhetes.morno.map(dois).join(" - ")}
            </p>
          </div>

          <div style={{ padding: "10px", margin: "8px 0", backgroundColor: "#fff", borderRadius: "6px", border: "1px solid #fecaca" }}>
            <strong style={{ color: "#b91c1c" }}>🔥 Bilhete Quente (T = 100% - Caos):</strong>
            <p style={{ fontSize: "16px", fontWeight: "bold", margin: "5px 0 0 0", letterSpacing: "1px" }}>
              {resultadoGeracao.bilhetes.quente.map(dois).join(" - ")}
            </p>
          </div>
        </div>
      )}

      {/* Desdobramento Automático Espectral */}
      <div style={{ border: "1px solid #7c3aed", padding: "20px", borderRadius: "8px", backgroundColor: "#faf5ff", marginTop: "30px" }}>
        <h3>🧩 Gerador Automático de Desdobramento Espectral</h3>
        <p style={{ color: "#475569", fontSize: "14px", marginTop: "-5px" }}>
          Ao clicar no botão abaixo, o robô seleciona automaticamente os pools térmicos e entrega <strong>exatamente 3 bilhetes</strong> de desdobramento (Frio, Morno e Quente).
        </p>

        <div style={{ marginBottom: "15px", marginTop: "15px" }}>
          <label style={{ marginRight: "10px", fontWeight: "bold" }}>Concurso (opcional):</label>
          <input
            type="number"
            min="1"
            value={concursoDesd}
            onChange={(e) => setConcursoDesd(e.target.value)}
            placeholder="ex.: 3800"
            style={{ width: "100px", padding: "6px", borderRadius: "4px", border: "1px solid #ccc" }}
          />
        </div>

        <button
          onClick={handleDesdobrarEspectro}
          disabled={loadingDesd}
          style={{ padding: "12px 24px", backgroundColor: "#4f46e5", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold", fontSize: "15px" }}
        >
          {loadingDesd ? "Calculando Desdobramento..." : "🧩 Gerar Desdobramento (Frio, Morno, Quente)"}
        </button>

        {erroDesd && <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", borderRadius: "6px", marginTop: "15px" }}>{erroDesd}</div>}
      </div>

      {/* Exibição dos 3 Bilhetes de Desdobramento */}
      {resultadoDesd && resultadoDesd.bilhetes && (
        <div style={{ marginTop: "30px", border: "1px solid #a78bfa", padding: "20px", borderRadius: "8px", backgroundColor: "#faf5ff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", marginBottom: "15px" }}>
            <h3 style={{ margin: 0, color: "#5b21b6" }}>🧩 3 Bilhetes de Desdobramento Gerados (Concurso: {resultadoDesd.concurso ?? "Não informado"})</h3>
            <button
              onClick={() => handleDownloadTXT(resultadoDesd.bilhetes, "Desdobramento Espectral Triplo", resultadoDesd.concurso)}
              style={{ padding: "8px 16px", backgroundColor: "#6d28d9", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
            >
               📥 Salvar os 3 em TXT
            </button>
          </div>

          <div style={{ padding: "10px", margin: "8px 0", backgroundColor: "#fff", borderRadius: "6px", border: "1px solid #bae6fd" }}>
            <strong style={{ color: "#0369a1" }}>🧊 Desdobramento Frio:</strong>
            <p style={{ fontSize: "16px", fontWeight: "bold", margin: "5px 0 0 0", letterSpacing: "1px" }}>
              {resultadoDesd.bilhetes.frio.map(dois).join(" - ")}
            </p>
          </div>

          <div style={{ padding: "10px", margin: "8px 0", backgroundColor: "#fff", borderRadius: "6px", border: "1px solid #fef08a" }}>
            <strong style={{ color: "#a16207" }}>🌤️ Desdobramento Morno:</strong>
            <p style={{ fontSize: "16px", fontWeight: "bold", margin: "5px 0 0 0", letterSpacing: "1px" }}>
              {resultadoDesd.bilhetes.morno.map(dois).join(" - ")}
            </p>
          </div>

          <div style={{ padding: "10px", margin: "8px 0", backgroundColor: "#fff", borderRadius: "6px", border: "1px solid #fecaca" }}>
            <strong style={{ color: "#b91c1c" }}>🔥 Desdobramento Quente:</strong>
            <p style={{ fontSize: "16px", fontWeight: "bold", margin: "5px 0 0 0", letterSpacing: "1px" }}>
              {resultadoDesd.bilhetes.quente.map(dois).join(" - ")}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}