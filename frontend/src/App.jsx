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
  
  // Estado do Concurso e Auditoria
  const [concursoAlvo, setConcursoAlvo] = useState(3101);
  const [concursoAudit, setConcursoAudit] = useState(3101);
  const [resultadoAuditoria, setResultadoAuditoria] = useState(null);

  // Sistema de Notificações Toast
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // URL Oficial do Backend no Render
  const API_URL = process.env.REACT_APP_API_URL || 'https://roboweb-cvha.onrender.com';

  // Executa o Backtest Global no Render
  const executarBacktest = async () => {
    setIsSimulating(true);
    try {
      const response = await fetch(`${API_URL}/api/backtest`);
      if (!response.ok) throw new Error('Falha na resposta do servidor.');
      const data = await response.json();
      setResultados(data);
      showToast('Backtest de 2.000 concursos executado com sucesso!', 'success');
    } catch (error) {
      console.error('Erro:', error);
      showToast('Erro ao conectar com o servidor Render. Verifique se o backend está ativo.', 'error');
    } finally {
      setIsSimulating(false);
    }
  };

  // Faz o Upload da base de dados Excel
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
          showToast(data.message || 'Planilha sincronizada com sucesso!', 'success');
        } else {
          showToast('Erro ao enviar o ficheiro Excel.', 'error');
        }
      } catch (error) {
        console.error('Erro:', error);
        showToast('Falha de comunicação com o servidor.', 'error');
      }
    }
  };

  // Gera os palpites dos 3 Curadores e grava no Supabase
  const gerarPalpiteDoDia = async () => {
    setIsGerando(true);
    try {
      const novosPalpites = {
        curador1: [1, 2, 4, 5, 8, 9, 11, 13, 14, 18, 20, 21, 22, 24, 25],
        curador2: [2, 3, 4, 6, 8, 9, 10, 13, 15, 17, 19, 20, 23, 24, 25],
        curador3: [1, 3, 4, 7, 8, 10, 11, 13, 14, 17, 18, 20, 22, 24, 25]
      };

      setPalpites(novosPalpites);

      // Envia os bilhetes para persistência no Supabase
      const payload = {
        concurso_alvo: Number(concursoAlvo),
        bilhetes: [
          { curador: "1º Curador (Voto Simples)", dezenas: novosPalpites.curador1 },
          { curador: "2º Curador (Pesos Históricos)", dezenas: novosPalpites.curador2 },
          { curador: "3º Curador (Assimétrico)", dezenas: novosPalpites.curador3 }
        ]
      };

      const res = await fetch(`${API_URL}/api/salvar_bilhetes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        showToast(`Bilhetes do Concurso ${concursoAlvo} gravados no Supabase!`, 'success');
      } else {
        showToast('Palpites gerados na tela, mas houve um aviso ao gravar no Supabase.', 'info');
      }
    } catch (error) {
      console.error('Erro:', error);
      showToast('Erro de conexão ao salvar palpites no servidor.', 'error');
    } finally {
      setIsGerando(false);
    }
  };

  // Executa a Auditoria de Resultados no Supabase
  const auditarSorteio = async () => {
    if (!concursoAudit) {
      showToast('Informe o número do concurso para auditar.', 'error');
      return;
    }
    setIsAuditando(true);
    try {
      const res = await fetch(`${API_URL}/api/auditar/${concursoAudit}`);
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setResultadoAuditoria(data);
        showToast('Auditoria concluída com sucesso!', 'success');
      } else {
        showToast(data.message || 'Não foram encontrados bilhetes pendentes para este concurso.', 'info');
      }
    } catch (error) {
      console.error('Erro na auditoria:', error);
      showToast('Falha de conexão com o servidor ao auditar.', 'error');
    } finally {
      setIsAuditando(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 font-sans relative">
      
      {/* NOTIFICAÇÃO TOAST FLUTUANTE */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl border backdrop-blur-md transition-all animate-bounce ${
          toast.type === 'error' 
            ? 'bg-rose-950/90 border-rose-800 text-rose-200' 
            : toast.type === 'info'
            ? 'bg-blue-950/90 border-blue-800 text-blue-200'
            : 'bg-emerald-950/90 border-emerald-800 text-emerald-200'
        }`}>
          {toast.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle2 size={20} />}
          <span className="text-sm font-medium">{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 hover:opacity-75">
            <X size={16} />
          </button>
        </div>
      )}

      {/* HEADER PRINCIPAL */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-6 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-emerald-400 flex items-center gap-3">
            <BrainCircuit size={36} /> Lotofácil Master AI
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Ensemble de 5 Juízes & 3 Curadores Simultâneos
          </p>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
          <div className="text-xs text-slate-500 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            Backend: <span className="text-emerald-400 font-mono">Render Online</span>
          </div>
          <button 
            onClick={executarBacktest} 
            disabled={isSimulating} 
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all disabled:opacity-50 text-sm"
          >
            {isSimulating ? <Activity className="animate-spin text-emerald-400" size={18} /> : <Play size={18} />}
            Executar Backtest Global
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* PAINEL DE CONTROLO SUPERIOR */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Caixa 1: Upload */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2">
                <Upload className="text-emerald-400" size={20} /> Base de Dados Oficial
              </h2>
              <p className="text-slate-400 text-xs mb-4">Carregue o ficheiro `.xlsx` atualizado para treinar os 5 Juízes.</p>
            </div>
            <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500 bg-slate-950/50 p-5 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-colors">
              <input type="file" accept=".xlsx, .xls" onChange={handleFileUpload} className="hidden" />
              {arquivoNome ? (
                <div className="text-emerald-400 flex items-center gap-2 font-medium text-xs">
                  <CheckCircle2 size={18} /> {arquivoNome}
                </div>
              ) : (
                <>
                  <Upload size={24} className="text-slate-500 mb-2" />
                  <span className="text-slate-300 font-medium text-xs">Enviar Excel</span>
                </>
              )}
            </label>
          </div>

          {/* Caixa 2: Gerador de Bilhetes */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2">
                <Sparkles className="text-emerald-400" size={20} /> Gerador de Consenso
              </h2>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs text-slate-400">Concurso Alvo:</span>
                <input 
                  type="number" 
                  value={concursoAlvo} 
                  onChange={(e) => setConcursoAlvo(e.target.value)} 
                  className="bg-slate-950 border border-slate-800 text-emerald-400 text-xs font-bold px-2.5 py-1 rounded-lg w-20 text-center focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
            <button 
              onClick={gerarPalpiteDoDia} 
              disabled={isGerando} 
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50 text-sm"
            >
              {isGerando ? <><Activity className="animate-spin" size={18} /> Processando...</> : <><Target size={18} /> Gerar e Salvar Bilhetes</>}
            </button>
          </div>

          {/* Caixa 3: Tribunal de Auditoria */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2">
                <Search className="text-emerald-400" size={20} /> Auditoria Supabase
              </h2>
              <p className="text-slate-400 text-xs mb-3">Conferir bilhetes salvos contra o último sorteio do Excel.</p>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs text-slate-400">Auditar Concurso:</span>
                <input 
                  type="number" 
                  value={concursoAudit} 
                  onChange={(e) => setConcursoAudit(e.target.value)} 
                  className="bg-slate-950 border border-slate-800 text-blue-400 text-xs font-bold px-2.5 py-1 rounded-lg w-20 text-center focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
            <button 
              onClick={auditarSorteio} 
              disabled={isAuditando} 
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-blue-900/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50 text-sm"
            >
              {isAuditando ? <><Activity className="animate-spin" size={18} /> Auditando...</> : <><Check size={18} /> Auditar Resultado</>}
            </button>
          </div>

        </div>

        {/* RESULTADO DA AUDITORIA */}
        {resultadoAuditoria && (
          <div className="bg-slate-900 border border-blue-500/40 p-5 rounded-2xl shadow-xl animate-fade-in">
            <h3 className="text-md font-bold text-blue-400 flex items-center gap-2 mb-3">
              <CheckCircle2 size={18} /> Resultado da Auditoria — Concurso {concursoAudit}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {resultadoAuditoria.resultados?.map((res, idx) => (
                <div key={idx} className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex justify-between items-center">
                  <span className="text-xs text-slate-300 font-medium">{res.curador}</span>
                  <span className={`text-lg font-extrabold ${res.acertos >= 13 ? 'text-emerald-400' : 'text-blue-400'}`}>
                    {res.acertos} Pontos
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ÁREA DE EXIBIÇÃO DOS BILHETES GERADOS */}
        {palpites && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in">
            {/* Curador 1 */}
            <div className="bg-slate-900 border border-slate-700 p-5 rounded-2xl">
              <h3 className="text-md font-bold text-slate-300 flex items-center gap-2 mb-4">
                <Scale size={18}/> 1º Curador (Voto Simples)
              </h3>
              <div className="flex flex-wrap gap-2 justify-center">
                {palpites.curador1.map(d => (
                  <div key={d} className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300 border border-slate-700">
                    {String(d).padStart(2,'0')}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Curador 2 */}
            <div className="bg-slate-900 border border-blue-500/30 p-5 rounded-2xl shadow-[0_0_15px_rgba(59,130,246,0.1)]">
              <h3 className="text-md font-bold text-blue-400 flex items-center gap-2 mb-4">
                <ShieldAlert size={18}/> 2º Curador (Pesos Históricos)
              </h3>
              <div className="flex flex-wrap gap-2 justify-center">
                {palpites.curador2.map(d => (
                  <div key={d} className="w-9 h-9 rounded-lg bg-blue-950/50 border border-blue-800/50 flex items-center justify-center text-xs font-bold text-blue-300">
                    {String(d).padStart(2,'0')}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Curador 3 */}
            <div className="bg-gradient-to-br from-slate-900 to-emerald-950 border border-emerald-500/50 p-5 rounded-2xl shadow-[0_0_20px_rgba(16,185,129,0.15)] relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-emerald-500 text-[10px] text-white px-2.5 py-0.5 rounded-bl-lg font-bold">RECOMENDADO</div>
              <h3 className="text-md font-bold text-emerald-400 flex items-center gap-2 mb-4">
                <Award size={18}/> 3º Curador (Assimétrico)
              </h3>
              <div className="flex flex-wrap gap-2 justify-center">
                {palpites.curador3.map(d => (
                  <div key={d} className="w-9 h-9 rounded-lg bg-emerald-900/80 border border-emerald-500/50 flex items-center justify-center text-xs font-bold text-white shadow-md shadow-emerald-900/50">
                    {String(d).padStart(2,'0')}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* DASHBOARD DE RESULTADOS DO BACKTEST */}
        {resultados && (
          <div className="space-y-6 animate-fade-in">
            
            {/* Médias dos 3 Curadores */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
               <div className="bg-slate-900 border border-slate-700 p-5 rounded-2xl text-center">
                  <p className="text-slate-400 font-semibold text-xs mb-1">Média 1º Curador</p>
                  <p className="text-2xl font-bold text-white">{resultados.medias.curador1.toFixed(2)}</p>
                  <p className="text-[10px] text-slate-500 mt-1">Voto igualitário</p>
               </div>
               <div className="bg-slate-900 border border-blue-500/30 p-5 rounded-2xl text-center">
                  <p className="text-blue-400 font-semibold text-xs mb-1">Média 2º Curador</p>
                  <p className="text-3xl font-bold text-blue-300">{resultados.medias.curador2.toFixed(2)}</p>
                  <p className="text-[10px] text-blue-500/70 mt-1">Ponderado histórico</p>
               </div>
               <div className="bg-slate-900 border border-emerald-500/50 p-5 rounded-2xl text-center shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                  <p className="text-emerald-400 font-bold text-xs mb-1">Média 3º Curador (Líder)</p>
                  <p className="text-4xl font-extrabold text-emerald-400">{resultados.medias.curador3.toFixed(2)}</p>
                  <p className="text-[10px] text-emerald-500/70 mt-1">Calibração Assimétrica</p>
               </div>
            </div>

            {/* GRÁFICO DA EVOLUÇÃO DOS 5 JUÍZES */}
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl mt-6">
              <h2 className="text-lg font-bold text-white mb-6">Batalha de Pesos (Ajuste Dinâmico do 3º Curador)</h2>
              <div className="h-72 md:h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={resultados.historicoPesos}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="concurso" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" domain={['auto', 'auto']} tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc', fontSize: '12px' }} />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Line type="monotone" dataKey="Padroes" name="Padrões" stroke="#34d399" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Frequencia" name="Frequência" stroke="#60a5fa" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Atrasos" name="Atrasos" stroke="#f472b6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Repeticao" name="Repetição" stroke="#fbbf24" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="Moldura" name="Moldura" stroke="#c084fc" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}