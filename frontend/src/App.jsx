import React, { useState } from 'react';
import { 
  Play, Upload, Sparkles, CheckCircle2, Search, AlertCircle, Save, Database, TrendingUp, Target
} from 'lucide-react';

export default function App() {
  const [isGerando, setIsGerando] = useState(false);
  const [isAuditando, setIsAuditando] = useState(false);
  const [palpites, setPalpites] = useState(null);
  const [arquivoNome, setArquivoNome] = useState(null);
  
  const [concursoAlvo, setConcursoAlvo] = useState(3784);
  const [concursoAudit, setConcursoAudit] = useState(3783);
  const [resultadoAuditoria, setResultadoAuditoria] = useState(null);

  const [toast, setToast] = useState(null);
  
  // Utiliza a variável de ambiente para flexibilidade de Deploy (Vercel/Local)
  const API_URL = import.meta.env.VITE_API_URL || 'https://roboweb-cvha.onrender.com';

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const response = await fetch(`${API_URL}/api/upload`, { method: 'POST', body: formData });
        const data = await response.json();
        if (response.ok) {
          setArquivoNome(file.name);
          showToast(data.message, 'success');
        } else {
          showToast(data.error || 'Erro no upload.', 'error');
        }
      } catch (error) {
        showToast('Falha de comunicação com o servidor.', 'error');
      }
    }
  };

  const gerarPalpiteDoDia = async () => {
    setIsGerando(true);
    setPalpites(null);
    try {
      const response = await fetch(`${API_URL}/api/gerar_palpites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concurso_alvo: Number(concursoAlvo) })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Erro ao gerar');
      
      setPalpites(data.palpites);
      showToast(`Palpites Diamante gerados em ${data.metricas_ia?.tentativas_processadas} tentativas!`, 'success');
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setIsGerando(false);
    }
  };

  const salvarBilhetesNoBanco = async () => {
    try {
      const response = await fetch(`${API_URL}/api/salvar_bilhetes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concurso: Number(concursoAlvo), palpites })
      });
      const data = await response.json();
      if (response.ok) showToast(data.mensagem, 'success');
      else throw new Error(data.error);
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  const auditarSorteio = async () => {
    setIsAuditando(true);
    setResultadoAuditoria(null);
    try {
      const res = await fetch(`${API_URL}/api/auditar/${concursoAudit}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Erro');
      
      setResultadoAuditoria(data);
      showToast('Auditoria concluída com sucesso!', 'success');
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setIsAuditando(false);
    }
  };

  const renderVolante = (dezenasEscolhidas) => {
    return (
      <div className="grid grid-cols-5 gap-2 mt-4">
        {Array.from({ length: 25 }, (_, i) => i + 1).map(num => {
          const isSelected = dezenasEscolhidas.includes(num);
          return (
            <div 
              key={num} 
              className={`w-10 h-10 flex items-center justify-center rounded-full text-sm font-bold transition-all duration-300 ${
                isSelected 
                  ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.5)] scale-110' 
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {num}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans relative overflow-x-hidden">
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl border backdrop-blur-md transition-all animate-bounce ${toast.type === 'error' ? 'bg-rose-950/90 border-rose-800 text-rose-200' : 'bg-emerald-950/90 border-emerald-800 text-emerald-200'}`}>
          {toast.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle2 size={20} />}
          <span className="text-sm font-medium">{toast.message}</span>
        </div>
      )}

      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex flex-col md:flex-row items-center justify-between gap-6 pb-8 border-b border-slate-800">
          <div>
            <h1 className="text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 flex items-center gap-3">
              <Database size={36} className="text-emerald-400" />
              Lotofácil Master AI
            </h1>
            <p className="text-slate-400 mt-2">Motor Estatístico de Previsão & Auditoria</p>
          </div>
          
          <label className="flex items-center gap-2 bg-slate-900 border border-slate-700 hover:border-emerald-500 px-6 py-3 rounded-full cursor-pointer transition-colors shadow-lg">
            <Upload size={20} className="text-emerald-400" />
            <span className="font-medium">{arquivoNome || 'Atualizar Base Excel'}</span>
            <input type="file" accept=".xlsx" className="hidden" onChange={handleFileUpload} />
          </label>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* COLUNA 1: GERAÇÃO */}
          <section className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <Sparkles className="text-amber-400" />
              <h2 className="text-xl font-bold">Curadoria de Bilhetes</h2>
            </div>
            
            <div className="flex gap-4 mb-8">
              <input 
                type="number" 
                value={concursoAlvo}
                onChange={(e) => setConcursoAlvo(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 w-1/3 focus:border-emerald-500 outline-none text-lg"
                placeholder="Concurso"
              />
              <button 
                onClick={gerarPalpiteDoDia}
                disabled={isGerando}
                className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl px-4 py-3 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {isGerando ? <span className="animate-pulse">Calculando...</span> : <><Play size={20} /> Gerar Palpites IA</>}
              </button>
            </div>

            {palpites && (
              <div className="space-y-8 animate-fade-in">
                {Object.entries(palpites).map(([curador, dezenas]) => (
                  <div key={curador} className="bg-slate-950 rounded-2xl p-6 border border-slate-800 relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-slate-800 text-slate-300 text-xs font-bold px-3 py-1 rounded-bl-lg capitalize">
                      {curador}
                    </div>
                    {renderVolante(dezenas)}
                  </div>
                ))}
                
                <button 
                  onClick={salvarBilhetesNoBanco}
                  className="w-full bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white font-bold rounded-xl px-4 py-4 flex items-center justify-center gap-2 transition-colors"
                >
                  <Save size={20} />
                  Salvar Jogada no Supabase
                </button>
              </div>
            )}
          </section>

          {/* COLUNA 2: AUDITORIA */}
          <section className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-xl flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <Search className="text-cyan-400" />
              <h2 className="text-xl font-bold">Auditoria de Desempenho</h2>
            </div>
            
            <div className="flex gap-4 mb-8">
              <input 
                type="number" 
                value={concursoAudit}
                onChange={(e) => setConcursoAudit(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 w-1/3 focus:border-cyan-500 outline-none text-lg"
                placeholder="Concurso"
              />
              <button 
                onClick={auditarSorteio}
                disabled={isAuditando}
                className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl px-4 py-3 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {isAuditando ? <span className="animate-pulse">Acessando...</span> : <><Target size={20} /> Auditar Sorteio</>}
              </button>
            </div>

            {resultadoAuditoria && resultadoAuditoria.resultados && (
              <div className="space-y-4 flex-1 animate-fade-in">
                {resultadoAuditoria.resultados.map((resultado, index) => (
                  <div 
                    key={index} 
                    className={`p-5 rounded-2xl border flex items-center justify-between ${
                      resultado.acertos >= 14 ? 'bg-amber-500/10 border-amber-500/50' : 
                      resultado.acertos >= 11 ? 'bg-emerald-500/10 border-emerald-500/30' : 
                      'bg-slate-950 border-slate-800'
                    }`}
                  >
                    <div>
                      <h3 className="font-bold text-lg capitalize text-slate-200">{resultado.curador}</h3>
                      <p className="text-sm text-slate-400 mt-1">Acertou {resultado.acertos} de 15 dezenas</p>
                    </div>
                    <div className="flex flex-col items-center justify-center w-16 h-16 rounded-full bg-slate-900 border border-slate-700">
                      <span className={`text-2xl font-black ${
                        resultado.acertos >= 14 ? 'text-amber-400' :
                        resultado.acertos >= 11 ? 'text-emerald-400' : 'text-slate-500'
                      }`}>
                        {resultado.acertos}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!resultadoAuditoria && !isAuditando && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 opacity-50 space-y-4 min-h-[200px]">
                <TrendingUp size={48} />
                <p>Audite um concurso anterior para ver os acertos da IA.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}