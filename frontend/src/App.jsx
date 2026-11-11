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

  return (
    <div style={{ maxWidth: "800px", margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>🎲 Lotofácil - 20 Juízes & 10 Curadores</h2>
      
      {erro && <div style={{ background: "#fee2e2", padding: "12px", color: "red", marginBottom: "20px" }}>⚠️ {erro}</div>}
      
      <button 
        onClick={gerar} 
        disabled={loading}
        style={{ padding: "12px 24px", background: "#2563eb", color: "#fff", border: "none", cursor: "pointer" }}
      >
        {loading ? "Auditando RAM..." : "Forjar Portfólio"}
      </button>

      {res && (
        <div style={{ marginTop: "30px", padding: "20px", background: "#f0fdf4", border: "1px solid green" }}>
          <h3>✅ Aprovado por 30 Agentes (Concurso {res.concurso})</h3>
          <p><strong>🧊 Frio:</strong> {res.bilhetes.frio.map(d2).join(" - ")}</p>
          <p><strong>🌤️ Morno:</strong> {res.bilhetes.morno.map(d2).join(" - ")}</p>
          <p><strong>🔥 Quente (7-4-4):</strong> {res.bilhetes.quente.map(d2).join(" - ")}</p>
        </div>
      )}
    </div>
  );
}