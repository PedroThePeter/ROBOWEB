import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'https://roboweb-cvha.onrender.com/api'; // Lembre-se de colocar a sua URL real do Render aqui se necessário

export default function App() {
  const [file, setFile] = useState(null);
  const [session, setSession] = useState(null);
  const [stats, setStats] = useState(null);
  const [lastDraw, setLastDraw] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState(5);

  // Estados do Backtest
  const [testDraws, setTestDraws] = useState(10);
  const [ticketsPerDraw, setTicketsPerDraw] = useState(12);
  const [backtestResults, setBacktestResults] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);

  // Upload da planilha principal
  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;
    setFile(uploadedFile);

    const formData = new FormData();
    formData.append('file', uploadedFile);

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      setSession(res.data.session_id);
      setStats(res.data.stats);
      setLastDraw(res.data.last_draw || []);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao enviar o arquivo.');
    } finally {
      setLoading(false);
    }
  };

  // Gerar Palpites
  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!session) {
      alert('Faça o upload de uma planilha primeiro.');
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/generate`, {
        session_id: session,
        count: parseInt(count),
        total_numbers: 15,
        range: 25
      });
      setTickets(res.data.tickets);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao gerar palpites.');
    } finally {
      setLoading(false);
    }
  };

  // Executar Backtest
  const handleRunBacktest = async (e) => {
    e.preventDefault();
    if (!file) {
      alert('Faça o upload da planilha principal primeiro.');
      return;
    }

    setBacktestLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('test_draws', testDraws);
    formData.append('bets_per_draw', ticketsPerDraw);
    if (session) formData.append('session_id', session);

    try {
      const res = await axios.post(`${API_URL}/backtest`, formData);
      setBacktestResults(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao executar o Backtest.');
    } finally {
      setBacktestLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Topo / Header Simples */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-xl gap-4">
          <div>
            <h1 className="text-xl font-bold text-emerald-400">🎯 Robô Lotofácil Inteligente</h1>
            <p className="text-xs text-slate-400 mt-0.5">Geração de bilhetes baseada em estatísticas e Machine Learning</p>
          </div>
          <div>
            <label className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl cursor-pointer shadow-lg transition">
              <span>{file ? '📁 Alterar Planilha' : '📁 Carregar Histórico (.xlsx/.csv)'}</span>
              <input type="file" accept=".csv, .xlsx, .xls" onChange={handleFileUpload} className="hidden" />
            </label>
            {session && <span className="block text-[10px] text-emerald-400 mt-1 text-center">✓ Conectado e pronto</span>}
          </div>
        </header>

        {/* Grade Principal: Gerador e Resultados */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Coluna Esquerda: Controles de Geração */}
          <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-5">
            <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Configurar Jogos</h2>
            
            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">Quantidade de Jogos</label>
                <input 
                  type="number" 
                  min="1" 
                  max="50" 
                  value={count} 
                  onChange={(e) => setCount(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <button 
                type="submit" 
                disabled={loading || !session}
                className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-800 disabled:text-slate-600 text-white font-semibold py-3 rounded-xl transition shadow-lg text-sm"
              >
                {loading ? 'Processando...' : 'Gerar Palpites 🤖'}
              </button>
            </form>

            {lastDraw.length > 0 && (
              <div className="pt-4 border-t border-slate-800">
                <span className="text-[11px] text-slate-400 block mb-2 uppercase tracking-wider">Último Concurso Analisado</span>
                <div className="flex flex-wrap gap-1">
                  {lastDraw.map((num, idx) => (
                    <span key={idx} className="w-7 h-7 rounded-lg bg-slate-950 border border-slate-800 text-emerald-400 font-bold text-xs flex items-center justify-center">
                      {String(num).padStart(2, '0')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Coluna Direita: Bilhetes Gerados */}
          <div className="lg:col-span-2 bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Bilhetes Recomendados</h2>
            
            {tickets.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-slate-600 text-xs border border-dashed border-slate-800 rounded-xl">
                Nenhum bilhete gerado. Faça o upload da planilha e clique em gerar.
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
                {tickets.map((ticket, i) => (
                  <div key={i} className="flex items-center justify-between bg-slate-950 p-3 rounded-xl border border-slate-800/60">
                    <span className="text-xs font-semibold text-slate-500">#{i + 1}</span>
                    <div className="flex flex-wrap gap-1 justify-end">
                      {ticket.map((n, idx) => (
                        <span key={idx} className="w-7 h-7 rounded-lg bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 font-bold text-xs flex items-center justify-center">
                          {String(n).padStart(2, '0')}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Seção Inferior Compacta: Backtest & Treino de IA */}
        <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
            <div>
              <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Simulação de Backtest & IA</h2>
              <p className="text-xs text-slate-500">Treina o Random Forest usando concursos passados para filtrar os palpites.</p>
            </div>
            
            <form onSubmit={handleRunBacktest} className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Testes:</span>
                <input 
                  type="number" 
                  value={testDraws} 
                  onChange={(e) => setTestDraws(e.target.value)}
                  className="w-20 bg-slate-950 border border-slate-800 rounded-lg p-1.5 text-xs text-white text-center focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Apostas/Concurso:</span>
                <input 
                  type="number" 
                  value={ticketsPerDraw} 
                  onChange={(e) => setTicketsPerDraw(e.target.value)}
                  className="w-20 bg-slate-950 border border-slate-800 rounded-lg p-1.5 text-xs text-white text-center focus:outline-none focus:border-emerald-500"
                />
              </div>
              <button 
                type="submit" 
                disabled={backtestLoading || !file}
                className="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-emerald-400 border border-emerald-500/30 font-semibold text-xs py-2 px-4 rounded-lg transition"
              >
                {backtestLoading ? 'Treinando...' : 'Rodar Backtest 🚀'}
              </button>
            </form>
          </div>

          {backtestResults && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-3 border-t border-slate-800 text-center">
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="block text-[10px] text-slate-500 uppercase">Total Apostas</span>
                <span className="text-sm font-bold text-white">{backtestResults.resumo.total_apostas}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="block text-[10px] text-slate-500 uppercase">11 Pts</span>
                <span className="text-sm font-bold text-slate-300">{backtestResults.resumo["11"]}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="block text-[10px] text-slate-500 uppercase">12 Pts</span>
                <span className="text-sm font-bold text-slate-300">{backtestResults.resumo["12"]}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="block text-[10px] text-slate-500 uppercase">13 / 14 Pts</span>
                <span className="text-sm font-bold text-emerald-400">{backtestResults.resumo["13"]} / {backtestResults.resumo["14"]}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="block text-[10px] text-slate-500 uppercase">15 Pts</span>
                <span className="text-sm font-bold text-yellow-400">{backtestResults.resumo["15"]}</span>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}