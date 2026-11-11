import React, { useState } from 'react';

const API = "http://localhost:8000/api";
const d2 = (n) => String(n).padStart(2, "0");

export default function App() {
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState(null);
  const [erro, setErro] = useState("");

  const gerar = async () => {
    setLoading(true); setErro(""); setRes(null);
    try {
      const req = await fetch(`${API}/gerar-jogos`, { method: "POST" });
      const data = await req.json();
      if (!req.ok) throw new Error(data.detail || "Erro no motor.");
      setRes(data);
    } catch (e) {
      setErro(e.message);
    } finally {
      setLoading(false);
    }
  };

  const baixarTXT = () => {
    if (!res || !res.bilhetes) return;
    let texto = "========================================\n";
    texto += ` LOTOFÁCIL IA - PORTFÓLIO AUDITADO (Concurso ${res.concurso})\n`;
    texto += "========================================\n\n";
    texto += `[🧊 FRIO (T=0%)]:    ${res.bilhetes.frio.map(d2).join(" - ")}\n`;
    texto += `[🌤️ MORNO (T=50%)]:  ${res.bilhetes.morno.map(d2).join(" - ")}\n`;
    texto += `[🔥 QUENTE (7-4-4)]: ${res.bilhetes.quente.map(d2).join(" - ")}\n\n`;
    texto += "----------------------------------------\n";
    texto += "Gerado pelo Sistema Local - 20 Juízes & 10 Curadores\n";

    const blob = new Blob([texto], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `portfolio_lotofacil_conc_${res.concurso}.txt`;
    link.click();
  };

  return (
    <div style={{ 
      maxWidth: "850px", 
      margin: "40px auto", 
      padding: "30px", 
      fontFamily: "'Inter', sans-serif", 
      backgroundColor: "#0f172a", 
      color: "#f8fafc",
      borderRadius: "12px",
      boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #334155", paddingBottom: "15px", marginBottom: "25px" }}>
        <h2 style={{ margin: 0, fontSize: "22px", color: "#38bdf8", display: "flex", alignItems: "center", gap: "10px" }}>
          🛡️ Lotofácil Cyber Lab <span style={{ fontSize: "12px", background: "#1e293b", padding: "4px 8px", borderRadius: "4px", color: "#94a3b8" }}>v9.0 (30 Agentes)</span>
        </h2>
      </div>
      
      {erro && (
        <div style={{ background: "#7f1d1d", border: "1px solid #f87171", padding: "14px", borderRadius: "8px", color: "#fca5a5", marginBottom: "20px", fontSize: "14px" }}>
          ⚠️ <strong>Aviso do Sistema:</strong> {erro}
        </div>
      )}
      
      <div style={{ display: "flex", gap: "15px", alignItems: "center" }}>
        <button 
          onClick={gerar} 
          disabled={loading}
          style={{ 
            padding: "12px 24px", 
            backgroundColor: loading ? "#475569" : "#2563eb", 
            color: "#fff", 
            border: "none", 
            borderRadius: "8px", 
            cursor: loading ? "not-allowed" : "pointer",
            fontWeight: "bold",
            fontSize: "15px",
            boxShadow: "0 4px 6px -1px rgba(37, 99, 235, 0.3)",
            transition: "all 0.2s"
          }}
        >
          {loading ? "⚙️ Processando em RAM (30 Agentes)..." : "🎯 Forjar Novo Portfólio"}
        </button>

        {res && (
          <button 
            onClick={baixarTXT}
            style={{ 
              padding: "12px 20px", 
              backgroundColor: "#059669", 
              color: "#fff", 
              border: "none", 
              borderRadius: "8px", 
              cursor: "pointer",
              fontWeight: "bold",
              fontSize: "15px",
              boxShadow: "0 4px 6px -1px rgba(5, 150, 105, 0.3)"
            }}
          >
            📥 Baixar Bilhetes (.txt)
          </button>
        )}
      </div>

      {res && (
        <div style={{ marginTop: "30px", padding: "20px", background: "#1e293b", border: "1px solid #334155", borderRadius: "10px" }}>
          <h3 style={{ margin: "0 0 15px 0", color: "#34d399", fontSize: "18px" }}>
            ✨ Portfólio Homologado (Concurso Alvo: {res.concurso})
          </h3>
          <div style={{ display: "grid", gap: "12px", fontSize: "16px" }}>
            <div style={{ padding: "10px", background: "#0f172a", borderRadius: "6px", borderLeft: "4px solid #38bdf8" }}>
              🧊 <strong>Frio (T=0%):</strong> {res.bilhetes.frio.map(d2).join(" - ")}
            </div>
            <div style={{ padding: "10px", background: "#0f172a", borderRadius: "6px", borderLeft: "4px solid #facc15" }}>
              🌤️ <strong>Morno (T=50%):</strong> {res.bilhetes.morno.map(d2).join(" - ")}
            </div>
            <div style={{ padding: "10px", background: "#0f172a", borderRadius: "6px", borderLeft: "4px solid #f87171" }}>
              🔥 <strong>Quente (7-4-4):</strong> {res.bilhetes.quente.map(d2).join(" - ")}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}