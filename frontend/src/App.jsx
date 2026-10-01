import React, { useState, useEffect } from 'react';

const API_BASE = "https://roboweb-cvha.onrender.com";

const pct = (v) => `${(v * 100).toFixed(1).replace(".", ",")}%`;
const dois = (d) => String(d).padStart(2, "0");
const TODAS = Array.from({ length: 25 }, (_, i) => i + 1);

export default function App() {
  const [estatisticas, setEstatisticas] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingGerar, setLoadingGerar] = useState(false);
  const [loadingRecarregar, setLoadingRecarregar] = useState(false);

  const [quantidade, setQuantidade] = useState(10);
  const [concurso, setConcurso] = useState("");
  const [resultadoGeracao, setResultadoGeracao] = useState(null);
  const [mensagemErro, setMensagemErro] = useState("");
  const [mensagemSucesso, setMensagemSucesso] = useState("");

  // Desdobramento
  const [selecionadas, setSelecionadas] = useState([]);
  const [garantia, setGarantia] = useState(14);
  const [concursoDesd, setConcursoDesd] = useState("");
  const [tamanhoSorteio, setTamanhoSorteio] = useState(17);
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
      const corpo = { quantidade: Math.min(100, Math.max(1, parseInt(quantidade, 10) || 1)) };
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
      setMensagemSucesso(
        data.diario_salvo
          ? "Bilhetes gerados e registrados no diário."
          : "Bilhetes gerados (não consegui gravar no diário)."
      );
    } catch (err) {
      setMensagemErro(err.message);
    } finally {
      setLoadingGerar(false);
    }
  };

  // --- Desdobramento ---
  const alternarDezena = (d) => {
    setResultadoDesd(null);
    setErroDesd("");
    setSelecionadas((atual) => {
      if (atual.includes(d)) return atual.filter((x) => x !== d);
      if (atual.length >= 18) return atual;
      return [...atual, d].sort((a, b) => a - b);
    });
  };

  const sortearGrupo = () => {
    setResultadoDesd(null);
    setErroDesd("");
    const embaralhadas = [...TODAS];
    for (let i = embaralhadas.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [embaralhadas[i], embaralhadas[j]] = [embaralhadas[j], embaralhadas[i]];
    }
    setSelecionadas(embaralhadas.slice(0, tamanhoSorteio).sort((a, b) => a - b));
  };

  const handleDesdobrar = async () => {
    setLoadingDesd(true);
    setErroDesd("");
    setResultadoDesd(null);
    try {
      const corpo = { dezenas: selecionadas, garantia: parseInt(garantia, 10) };
      const numConcurso = parseInt(concursoDesd, 10);
      if (numConcurso > 0) corpo.concurso = numConcurso;

      const response = await fetch(`${API_BASE}/api/desdobramento`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo)
      });
      const data = await response.json();
      if (!response.ok) {
        const detalhe = Array.isArray(data.detail) ? "Dados inválidos." : data.detail;
        throw new Error(detalhe || "Erro inesperado.");
      }
      setResultadoDesd(data);
    } catch (err) {
      setErroDesd(err.message);
    } finally {
      setLoadingDesd(false);
    }
  };

  const base = estatisticas?.base;
  const memoria = base?.memoria;
  const desempenho = estatisticas?.desempenho;
  const grupoValido = selecionadas.length >= 16 && selecionadas.length <= 18;

  return (
    <div style={{ maxWidth: "1005px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
        <h2>🎲 Lotofácil Engine v8.0 - Sorteio ponderado + Desdobramento + Auditoria</h2>
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

      {/* Gerador */}
      <div style={{ border: "1px solid #1e40af", padding: "20px", borderRadius: "8px", backgroundColor: "#f0f9ff" }}>
        <h3>🎲 Gerador de bilhetes (sorteio ponderado)</h3>
        <p style={{ color: "#475569", fontSize: "14px", marginTop: "-5px" }}>
          Sorteia 15 dezenas distintas com probabilidade proporcional aos pesos ativos da trava
          (sem trava, todas as dezenas têm o mesmo peso). Cada bilhete é registrado com hash SHA-256.
        </p>

        <div style={{ display: "flex", gap: "20px", alignItems: "center", marginBottom: "15px", marginTop: "15px", flexWrap: "wrap" }}>
          <div>
            <label style={{ marginRight: "10px", fontWeight: "bold" }}>Quantidade de Bilhetes:</label>
            <input
              type="number"
              min="1" max="100"
              value={quantidade}
              onChange={(e) => setQuantidade(e.target.value)}
              style={{ width: "70px", padding: "6px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          <div>
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
        </div>

        <button
          onClick={handleGerarJogos}
          disabled={loadingGerar}
          style={{ padding: "10px 20px", backgroundColor: "#1e40af", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
        >
          {loadingGerar ? "Gerando..." : "🎯 Gerar Bilhetes"}
        </button>
      </div>

      {/* Exibição dos bilhetes */}
      {resultadoGeracao && resultadoGeracao.bilhetes && resultadoGeracao.bilhetes.length > 0 && (
        <div style={{ marginTop: "30px" }}>
          <h3>🎟️ Bilhetes gerados ({resultadoGeracao.bilhetes.length})</h3>
          <p style={{ color: "#555", fontSize: "13px" }}>
            Concurso: <strong>{resultadoGeracao.concurso ?? "não informado"}</strong> {" | "}
            Trava de pesos: <strong>{resultadoGeracao.trava_valida ? "validada" : "não ativa (pesos uniformes)"}</strong>
          </p>

          {resultadoGeracao.bilhetes.map((bilhete, index) => (
            <div key={index} style={{ border: "1px solid #22c55e", padding: "15px", borderRadius: "8px", marginBottom: "10px", backgroundColor: "#f0fdf4" }}>
              <p style={{ fontSize: "16px", fontWeight: "bold", color: "#166534", margin: "0", letterSpacing: "1px" }}>
                Bilhete {index + 1}: {bilhete.map(dois).join(" - ")}
              </p>
            </div>
          ))}

          {resultadoGeracao.aviso && (
            <div style={{ padding: "12px", backgroundColor: "#f1f5f9", color: "#334155", borderRadius: "6px", marginTop: "15px", fontSize: "13px" }}>
              ℹ️ {resultadoGeracao.aviso}
            </div>
          )}
        </div>
      )}

      {/* Desdobramento */}
      <div style={{ border: "1px solid #7c3aed", padding: "20px", borderRadius: "8px", backgroundColor: "#faf5ff", marginTop: "30px" }}>
        <h3>🧩 Desdobramento com garantia</h3>
        <p style={{ color: "#475569", fontSize: "14px", marginTop: "-5px" }}>
          Escolha de 16 a 18 dezenas. O sistema monta o menor conjunto que ele encontra de bilhetes de 15 dezenas
          que garante o mínimo de acertos escolhido, <strong>desde que as 15 sorteadas estejam todas dentro do seu grupo</strong>.
          Isso não aumenta o valor esperado da aposta; só organiza como o dinheiro é distribuído.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 44px)", gap: "6px", margin: "15px 0" }}>
          {TODAS.map((d) => {
            const ativa = selecionadas.includes(d);
            return (
              <button
                key={d}
                onClick={() => alternarDezena(d)}
                style={{
                  height: "40px", cursor: "pointer", borderRadius: "50%", fontWeight: "bold",
                  border: ativa ? "2px solid #6d28d9" : "1px solid #cbd5e1",
                  backgroundColor: ativa ? "#7c3aed" : "#fff",
                  color: ativa ? "#fff" : "#334155"
                }}
              >
                {dois(d)}
              </button>
            );
          })}
        </div>

        <p style={{ fontSize: "14px", margin: "0 0 12px 0" }}>
          Selecionadas: <strong>{selecionadas.length}</strong> (precisa de 16 a 18)
          {selecionadas.length > 0 && <> {" | "}{selecionadas.map(dois).join(" ")}</>}
        </p>

        <div style={{ display: "flex", gap: "15px", alignItems: "center", flexWrap: "wrap", marginBottom: "15px" }}>
          <div>
            <label style={{ marginRight: "8px", fontWeight: "bold" }}>Garantia:</label>
            <select
              value={garantia}
              onChange={(e) => { setGarantia(e.target.value); setResultadoDesd(null); }}
              style={{ padding: "6px", borderRadius: "4px", border: "1px solid #ccc" }}
            >
              {[11, 12, 13, 14].map((g) => <option key={g} value={g}>{g} acertos</option>)}
            </select>
          </div>

          <div>
            <label style={{ marginRight: "8px", fontWeight: "bold" }}>Concurso (opcional):</label>
            <input
              type="number"
              min="1"
              value={concursoDesd}
              onChange={(e) => setConcursoDesd(e.target.value)}
              placeholder="ex.: 3800"
              style={{ width: "100px", padding: "6px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          <div>
            <select
              value={tamanhoSorteio}
              onChange={(e) => setTamanhoSorteio(parseInt(e.target.value, 10))}
              style={{ padding: "6px", borderRadius: "4px", border: "1px solid #ccc", marginRight: "6px" }}
            >
              {[16, 17, 18].map((k) => <option key={k} value={k}>{k} dezenas</option>)}
            </select>
            <button
              onClick={sortearGrupo}
              style={{ padding: "8px 12px", cursor: "pointer", backgroundColor: "#e2e8f0", color: "#334155", border: "1px solid #cbd5e1", borderRadius: "4px" }}
            >
              🎲 Sortear grupo
            </button>
            <button
              onClick={() => { setSelecionadas([]); setResultadoDesd(null); setErroDesd(""); }}
              style={{ padding: "8px 12px", cursor: "pointer", marginLeft: "6px", backgroundColor: "#fff", color: "#334155", border: "1px solid #cbd5e1", borderRadius: "4px" }}
            >
              Limpar
            </button>
          </div>
        </div>

        <button
          onClick={handleDesdobrar}
          disabled={loadingDesd || !grupoValido}
          style={{
            padding: "10px 20px", backgroundColor: grupoValido ? "#6d28d9" : "#a78bfa", color: "#fff",
            border: "none", borderRadius: "5px", cursor: grupoValido ? "pointer" : "not-allowed", fontWeight: "bold"
          }}
        >
          {loadingDesd ? "Calculando e verificando..." : "🧩 Gerar Desdobramento"}
        </button>

        {erroDesd && (
          <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", borderRadius: "6px", marginTop: "15px" }}>
            {erroDesd}
          </div>
        )}
      </div>

      {resultadoDesd && resultadoDesd.bilhetes && (
        <div style={{ marginTop: "20px" }}>
          <h3>🧩 {resultadoDesd.quantidade_bilhetes} bilhetes para garantir {resultadoDesd.garantia_pedida} acertos</h3>
          <p style={{ color: "#555", fontSize: "13px" }}>
            Garantia verificada por força bruta: <strong>{resultadoDesd.garantia_verificada ? "sim ✅" : "não ❌"}</strong> {" | "}
            Chance de as 15 sorteadas caírem no seu grupo: <strong>1 em {Number(resultadoDesd.um_em).toLocaleString("pt-BR")}</strong>
          </p>
          <p style={{ color: "#555", fontSize: "13px" }}>
            Se isso acontecer, melhor resultado por sorteio possível:{" "}
            {Object.entries(resultadoDesd.melhor_acerto_se_pool_conter_sorteio)
              .map(([acertos, qtd]) => `${acertos} acertos em ${qtd} sorteios`)
              .join(" | ")}
          </p>

          {resultadoDesd.registro && (
            <p style={{ color: "#166534", fontSize: "13px" }}>
              Concurso {resultadoDesd.concurso}: comprovantes{" "}
              {resultadoDesd.registro.comprovantes
                ? `gravados (${resultadoDesd.registro.comprovantes.novos} novos)`
                : "não gravados"}
              {" | "}diário {resultadoDesd.registro.diario_salvo ? "registrado" : "não registrado"}.
            </p>
          )}

          {resultadoDesd.bilhetes.map((bilhete, index) => (
            <div key={index} style={{ border: "1px solid #a78bfa", padding: "12px", borderRadius: "8px", marginBottom: "8px", backgroundColor: "#faf5ff" }}>
              <p style={{ fontSize: "15px", fontWeight: "bold", color: "#5b21b6", margin: 0, letterSpacing: "1px" }}>
                Bilhete {index + 1}: {bilhete.map(dois).join(" - ")}
              </p>
            </div>
          ))}

          <div style={{ padding: "12px", backgroundColor: "#f1f5f9", color: "#334155", borderRadius: "6px", marginTop: "10px", fontSize: "13px" }}>
            ℹ️ {resultadoDesd.observacao}
          </div>
        </div>
      )}
    </div>
  );
}