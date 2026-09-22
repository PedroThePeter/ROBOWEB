import React, { useState } from 'react';
import { Play, Upload, BrainCircuit, Activity, Target, ShieldAlert, CheckCircle2, ChevronRight, Terminal } from 'lucide-react';

export default function App() {
  const [isGerando, setIsGerando] = useState(false);
  const [arquivoNome, setArquivoNome] = useState(null);
  
  // Estados automáticos
  const [infoSistema, setInfoSistema] = useState({ ultimo: 0, proximo: 0 });
  const [palpites, setPalpites] = useState(null);
  const [relatorioIA, setRelatorioIA] = useState(null);
  const [auditoria, setAuditoria] = useState(null);
  const [toast, setToast] = useState(null);

  const API_URL = 'https://roboweb-cvha.onrender.com'; // O seu URL do Render

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);
    showToast('A carregar base de dados...', 'success');
    
    try {
      const res = await fetch(`${API_URL}/api/upload`, { method: 'POST', body: formData });
      const data = await res.json();
      
      if (res.ok) {
        setArquivoNome(file.name);
        setInfoSistema({ ultimo: data.ultimo_concurso, proximo: data.proximo_concurso });
        showToast(`Base sincronizada! Último concurso: ${data.ultimo_concurso}`, 'success');
        
        // Auto-Auditoria instantânea do último concurso!
        auditarAutomático(data.ultimo_concurso);
      } else {
        showToast(data.error, 'error');
      }
    } catch (error) {
      showToast('Erro de comunicação com o servidor.', 'error');
    }
  };

  const auditarAutomático = async (concurso) => {
    try {
      const res = await fetch(`${API_URL}/api/auditar/${concurso}`);
      if (res.ok) {
        const data = await res.json();
        setAuditoria(data);
        showToast(`Auditoria do concurso ${concurso} concluída!`, 'success');
      }
    } catch (error) {
      console.log('Sem auditoria prévia.');
    }
  };

  const gerarPalpiteDoDia = async () => {
    if (infoSistema.proximo === 0) return showToast('Carregue a planilha primeiro!', 'error');
    
    setIsGerando(true);
    setPalpites(null);
    setRelatorioIA(null);
    
    try {
      const res = await fetch(`${API_URL}/api/gerar_palpites`, { method: 'POST' });
      const data = await res.json();
      
      if (res.ok) {
        setPalpites(data.palpites);
        setRelatorioIA({ juizes: data.relatorio_juizes, metricas: data.metricas_ia });
        showToast(`Sorteio ${data.concurso} previsto com sucesso e guardado na base!`, 'success');
      } else {
        showToast(data.error, 'error');
      }
    } catch (error) {
      showToast('Falha ao acionar a IA.', 'error');
    } finally {
      setIsGerando(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3 rounded-lg shadow-2xl border transition-all animate-bounce ${toast.type === 'error' ? 'bg-rose-950/90 border-rose-800 text-rose-200' : 'bg-emerald-950/90 border-emerald-800 text-emerald-200'}`}>
          <span className="text-sm font-medium">{toast.message}</span>
        </div>
      )}

      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Cabeçalho */}
        <div className="flex flex-col md:flex-row justify-between items-center bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 flex items-center gap-3">
              <BrainCircuit className="text-emerald-400 w-8 h-8" />
              Lotofácil Master AI
            </h1>
            <p className="text-slate-400 mt-1">Motor Estatístico Autónomo & Auditoria em Tempo Real</p>
          </div>
          
          <label className="mt-4 md:mt-0 flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-6 py-3 rounded-xl cursor-pointer transition-colors border border-slate-700">
            <Upload className="w-5 h-5" />
            <span className="font-semibold">{arquivoNome ? arquivoNome : '1. Carregar Base (Excel)'}</span>
            <input type="file" accept=".xlsx" className="hidden" onChange={handleFileUpload} />
          </label>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Coluna 1 e 2: Previsão e Cérebro da IA */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Bloco do Cérebro da IA (Logs) */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold flex items-center gap-2 text-cyan-400">
                  <Terminal className="w-5 h-5" /> Cérebro da IA (Logs Internos)
                </h2>
                {infoSistema.proximo > 0 && (
                  <button 
                    onClick={gerarPalpiteDoDia}
                    disabled={isGerando}
                    className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-emerald-900/20 ${isGerando ? 'bg-emerald-800/50 text-emerald-400 animate-pulse' : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950'}`}
                  >
                    {isGerando ? <Activity className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                    {isGerando ? 'A processar juízes...' : `2. Prever Sorteio ${infoSistema.proximo}`}
                  </button>
                )}
              </div>

              {relatorioIA ? (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                    <p className="text-slate-400 mb-1">Juiz de Ciclos</p>
                    <p className="font-mono text-emerald-400">Estado: {relatorioIA.juizes.ciclo_estado}</p>
                    <p className="font-mono text-cyan-400 mt-1">Faltam: [{relatorioIA.juizes.ciclo_faltam.join(', ')}]</p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                    <p className="text-slate-400 mb-1">Juiz de Frequência (Top 5)</p>
                    <p className="font-mono text-rose-400">Quentes: [{relatorioIA.juizes.quentes.join(', ')}]</p>
                    <p className="font-mono text-blue-400 mt-1">Frias: [{relatorioIA.juizes.frias.join(', ')}]</p>
                  </div>
                  <div className="col-span-2 bg-slate-950 p-4 rounded-lg border border-slate-800 flex justify-between items-center">
                    <span className="text-slate-400">Tentativas brute-force guiada:</span>
                    <span className="font-mono text-emerald-400">{relatorioIA.metricas.tentativas} bilhetes gerados</span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-600 font-mono text-sm border-2 border-dashed border-slate-800 rounded-xl">
                  Aguardando comando para iniciar a rede de Curadores...
                </div>
              )}
            </div>

            {/* Bilhetes Gerados */}
            {palpites && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-emerald-400">Bilhetes Diamante (Aprovados)</h3>
                {Object.entries(palpites).map(([curador, dezenas]) => (
                  <div key={curador} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                    <div className="flex items-center gap-2 mb-4">
                      <ShieldAlert className="text-emerald-500 w-5 h-5" />
                      <span className="font-semibold capitalize text-slate-300">{curador}</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {dezenas.map(d => (
                        <span key={d} className="w-10 h-10 flex items-center justify-center bg-emerald-950 border border-emerald-800 text-emerald-400 rounded-full font-bold shadow-inner">
                          {d.toString().padStart(2, '0')}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Coluna 3: Auditoria Automática */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg h-fit">
            <h2 className="text-xl font-semibold flex items-center gap-2 text-rose-400 mb-6">
              <Target className="w-5 h-5" /> Auditoria: Concurso {infoSistema.ultimo || '---'}
            </h2>
            
            {auditoria ? (
              <div className="space-y-6">
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                  <p className="text-slate-400 text-sm mb-2">Dezenas Reais Sorteadas</p>
                  <div className="flex flex-wrap gap-1.5">
                    {auditoria.sorteadas.map(d => (
                      <span key={d} className="w-8 h-8 flex items-center justify-center bg-slate-800 text-slate-300 rounded-md text-xs font-bold">
                        {d.toString().padStart(2, '0')}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  {auditoria.resultados.map((res, i) => (
                    <div key={i} className="flex justify-between items-center bg-slate-950 p-3 rounded-lg border border-slate-800">
                      <span className="capitalize font-medium text-slate-300">{res.curador}</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-lg font-bold ${res.acertos >= 14 ? 'text-yellow-400' : res.acertos >= 11 ? 'text-emerald-400' : 'text-slate-500'}`}>
                          {res.acertos} Acertos
                        </span>
                        {res.acertos >= 14 && <CheckCircle2 className="w-5 h-5 text-yellow-400" />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-600 flex flex-col items-center">
                <Activity className="w-10 h-10 mb-3 opacity-20" />
                <p>Auditoria será exibida automaticamente após carregar a base.</p>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </div>
  );
}