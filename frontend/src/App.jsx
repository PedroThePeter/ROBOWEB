import React, { useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  Play, Target, Award, BrainCircuit, Activity, Upload, Sparkles, CheckCircle2, ShieldAlert, Scale, Search, Check, AlertCircle, X 
} from 'lucide-react';

export default function App() {
  const [isSimulating, setIsSimulating] = useState(false);
  const [isGerando, setIsGerando] = useState(false);
  const [isAuditando, setIsAuditando] = useState(false);
  const [resultados, setResultados] = useState(null);
  const [palpites, setPalpites] = useState(null);
  const [arquivoNome, setArquivoNome] = useState(null);
  
  // Estado do Concurso
  const [concursoAlvo, setConcursoAlvo] = useState(3784);
  const [concursoAudit, setConcursoAudit] = useState(3783);
  const [resultadoAuditoria, setResultadoAuditoria] = useState(null);

  // Sistema de Notificações Toast
  const [toast, setToast] = useState(null);
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // URL OFICIAL DO SEU BACKEND NO RENDER
  const API_URL = 'https://roboweb-cvha.onrender.com';

  // 1. Backtest
  const executarBacktest = async () => {
    setIsSimulating(true);
    try {
      const response = await fetch(`${API_URL}/api/backtest`);
      if (!response.ok) throw new Error('Falha na resposta do servidor.');
      const data = await response.json();
      setResultados(data);
      showToast('Backtest executado com sucesso!', 'success');
    } catch (error) {
      showToast('Erro ao conectar com o servidor Render.', 'error');
    } finally {
      setIsSimulating(false);
    }
  };

  // 2. Upload Excel
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const response = await fetch(`${API_URL}/api/upload`, { 
          method: 'POST', 
          body: formData 
        });
        const data = await response.json();
        if (response.ok) {
          setArquivoNome(file.name);
          showToast(data.message, 'success');
        } else {
          showToast('Erro ao enviar o ficheiro Excel.', 'error');
        }
      } catch (error) {
        showToast('Falha de comunicação com o servidor.', 'error');
      }
    }
  };

  // 3. Gerar e Salvar Palpites Dinâmicos
  const gerarPalpiteDoDia = async () => {
    setIsGerando(true);
    try {
      // Pede os números ao Python
      const resPalpites = await fetch(`${API_URL}/api/gerar_palpites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concurso_alvo: Number(concursoAlvo) })
      });

      if (!resPalpites.ok) throw new Error('Erro ao obter palpites (404 ou 500).');
      const dataPalpites = await resPalpites.json();
      
      const bilhetesGerados = dataPalpites.palpites;
      setPalpites(bilhetesGerados);

      // Envia para salvar no Supabase através do backend
      const payloadSalvar = {
        concurso_alvo: Number(concursoAlvo),
        bilhetes: [
          { curador: "1º Curador (Voto Simples)", dezenas: bilhetesGerados.curador1 },
          { curador: "2º Curador (Pesos Históricos)", dezenas: bilhetesGerados.curador2 },
          { curador: "3º Curador (Assimétrico)", dezenas: bilhetesGerados.curador3 }
        ]
      };

      await fetch(`${API_URL}/api/salvar_bilhetes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadSalvar)
      });

      showToast(`Palpites do Concurso ${concursoAlvo} gerados e guardados!`, 'success');
    } catch (error) {
      showToast('Erro ao gerar/salvar palpites no backend.', 'error');
    } finally {
      setIsGerando(false);
    }
  };

  // 4. Auditoria
  const auditarSorteio = async () => {
    setIsAuditando(true);
    try {
      const res = await fetch(`${API_URL}/api/auditar/${concursoAudit}`);
      if (!res.ok) throw new Error('Erro na auditoria.');
      const data = await res.json();
      setResultadoAuditoria(data);
      showToast(`Auditoria do concurso ${concursoAudit} concluída!`, 'success');
    } catch (error) {
      showToast('Falha ao auditar no servidor.', 'error');
    } finally {
      setIsAuditando(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 font-sans relative">
      
      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl border backdrop-blur-md transition-all animate-bounce ${
          toast.type === 'error' ? 'bg-rose-950/90 border-rose-800 text-rose-200' : 'bg-emerald-950/90 border-emerald-800 text-emerald-200'
        }`}>
          {toast.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle2 size={20} />}
          <span className="text-sm font-medium">{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 hover:opacity-75"><X size={16} /></button>
        </div>
      )}

      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-6 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-emerald-400 flex items-center gap-3">
            <BrainCircuit size={36} /> Lotofácil Master AI
          </h1>
          <p className="text-slate-400 text-sm mt-1">Ensemble de 5 Juízes & 3 Curadores Simultâneos</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs text-slate-500 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            Backend: <span className="text-emerald-400 font-mono">Render Online</span>
          </div>
          <button onClick={executarBacktest} disabled={isSimulating} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 text-sm">
            {isSimulating ? <Activity className="animate-spin text-emerald-400" size={18} /> : <Play size={18} />} Backtest Global
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Controlos */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4"><Upload className="text-emerald-400" size={20} /> Base de Dados</h2>
            <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500 bg-slate-950/50 p-5 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-colors h-24">
              <input type="file" accept=".xlsx, .xls" onChange={handleFileUpload} className="hidden" />
              {arquivoNome ? <span className="text-emerald-400 text-xs font-bold">{arquivoNome}</span> : <span className="text-slate-300 text-xs">Enviar Excel</span>}
            </label>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2"><Sparkles className="text-emerald-400" size={20} /> Gerador Dinâmico</h2>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xs text-slate-400">Concurso Alvo:</span>
              <input type="number" value={concursoAlvo} onChange={(e) => setConcursoAlvo(e.target.value)} className="bg-slate-950 border border-slate-800 text-emerald-400 text-xs font-bold px-2 py-1 rounded w-20 text-center" />
            </div>
            <button onClick={gerarPalpiteDoDia} disabled={isGerando} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 text-sm">
              {isGerando ? <Activity className="animate-spin" size={18} /> : <Target size={18} />} Gerar e Salvar
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2"><Search className="text-emerald-400" size={20} /> Auditoria</h2>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xs text-slate-400">Auditar Concurso:</span>
              <input type="number" value={concursoAudit} onChange={(e) => setConcursoAudit(e.target.value)} className="bg-slate-950 border border-slate-800 text-blue-400 text-xs font-bold px-2 py-1 rounded w-20 text-center" />
            </div>
            <button onClick={auditarSorteio} disabled={isAuditando} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 text-sm">
              {isAuditando ? <Activity className="animate-spin" size={18} /> : <Check size={18} />} Auditar Resultado
            </button>
          </div>
        </div>

        {/* Auditoria Result */}
        {resultadoAuditoria && (
          <div className="bg-slate-900 border border-blue-500/40 p-5 rounded-2xl">
            <h3 className="text-md font-bold text-blue-400 flex items-center gap-2 mb-3">Resultado: Concurso {concursoAudit}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {resultadoAuditoria.resultados?.map((res, idx) => (
                <div key={idx} className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex justify-between">
                  <span className="text-xs text-slate-300">{res.curador}</span>
                  <span className={`text-lg font-bold ${res.acertos >= 13 ? 'text-emerald-400' : 'text-blue-400'}`}>{res.acertos} pts</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bilhetes */}
        {palpites && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['curador1', 'curador2', 'curador3'].map((curador, idx) => (
              <div key={curador} className={`bg-slate-900 border p-5 rounded-2xl ${idx === 2 ? 'border-emerald-500/50 relative' : 'border-slate-700'}`}>
                {idx === 2 && <div className="absolute top-0 right-0 bg-emerald-500 text-[10px] text-white px-2 py-0.5 rounded-bl-lg font-bold">RECOMENDADO</div>}
                <h3 className={`text-md font-bold flex items-center gap-2 mb-4 ${idx === 2 ? 'text-emerald-400' : 'text-slate-300'}`}>
                  {idx === 0 ? '1º Curador (Simples)' : idx === 1 ? '2º Curador (Pesos)' : '3º Curador (Assimétrico)'}
                </h3>
                <div className="flex flex-wrap gap-2 justify-center">
                  {palpites[curador]?.map(d => (
                    <div key={d} className={`w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold border ${idx === 2 ? 'bg-emerald-900/80 border-emerald-500/50 text-white' : 'bg-slate-800 border-slate-700 text-slate-300'}`}>
                      {String(d).padStart(2,'0')}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Backtest Result */}
        {resultados && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-700 p-5 rounded-2xl text-center">
                 <p className="text-slate-400 font-semibold text-xs mb-1">Média 1º Curador</p>
                 <p className="text-2xl font-bold text-white">{resultados.medias.curador1.toFixed(2)}</p>
              </div>
              <div className="bg-slate-900 border border-blue-500/30 p-5 rounded-2xl text-center">
                 <p className="text-blue-400 font-semibold text-xs mb-1">Média 2º Curador</p>
                 <p className="text-3xl font-bold text-blue-300">{resultados.medias.curador2.toFixed(2)}</p>
              </div>
              <div className="bg-slate-900 border border-emerald-500/50 p-5 rounded-2xl text-center">
                 <p className="text-emerald-400 font-bold text-xs mb-1">Média 3º Curador</p>
                 <p className="text-4xl font-extrabold text-emerald-400">{resultados.medias.curador3.toFixed(2)}</p>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={resultados.historicoPesos}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="concurso" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" domain={['auto', 'auto']} tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Line type="monotone" dataKey="Padroes" stroke="#34d399" dot={false} />
                  <Line type="monotone" dataKey="Frequencia" stroke="#60a5fa" dot={false} />
                  <Line type="monotone" dataKey="Atrasos" stroke="#f472b6" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}