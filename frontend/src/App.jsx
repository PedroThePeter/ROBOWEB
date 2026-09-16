import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, BarChart2, History, Cpu, CheckCircle, Zap, Flame, RefreshCw, Play, Award, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'https://roboweb-cvha.onrender.com/api';
const LOTOFACIL_CONFIG = { name: 'Lotofácil', total: 15, range: 25 };

export default function App() {
  const [session, setSession] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('stats');

  const [ticketCount, setTicketCount] = useState(5);
  const [history, setHistory] = useState([]);
  const [lastDrawnNumbers, setLastDrawnNumbers] = useState([]);
  const [mlMessage, setMlMessage] = useState('');

  // Estados do Backtest Automático
  const [backtestFile, setBacktestFile] = useState(null);
  const [testDraws, setTestDraws] = useState(10);
  const [ticketsPerDraw, setTicketsPerDraw] = useState(12);
  const [backtestResults, setBacktestResults] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);

  useEffect(() => {
    const savedHistory = localStorage.getItem('lottoai_history');
    if (savedHistory) {
      try { setHistory(JSON.parse(savedHistory)); } catch (e) {}
    }
  }, []);

  const saveHistory = (newHistory) => {
    setHistory(newHistory);
    localStorage.setItem('lottoai_history', JSON.stringify(newHistory));
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setBacktestFile(file);
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      setSession(res.data.session_id);
      
      if (res.data.stats) {
        setStats(res.data.stats);
      }

      if (res.data.last_draw) {
        setLastDrawnNumbers(res.data.last_draw);
        confrontLastBet(res.data.last_draw);
      } else {
        setMlMessage('Planilha analisada com sucesso! Filtros de IA ativos.');
      }
    } catch (err) {
      alert('Erro ao enviar planilha.');
    } finally {
      setLoading(false);
    }
  };

  const confrontLastBet = (drawnNumbers) => {
    if (history.length === 0) {
      setMlMessage('Último sorteio identificado! Filtros avançados prontos.');
      return;
    }

    const lastBetGroup = history[0]; 
    let bestHits = 0;

    const updatedBets = lastBetGroup.tickets.map(ticket => {
      const hits = ticket.numbers.filter(num => drawnNumbers.includes(num)).length;
      if (hits > bestHits) bestHits = hits;
      return { ...ticket, hits };
    });

    const updatedHistory = history.map((item, index) => 
      index === 0 ? { ...item, tickets: updatedBets, confronted: true, drawnNumbers } : item
    );

    saveHistory(updatedHistory);
    setMlMessage(`🤖 Machine Learning: Confronto realizado! Melhor resultado no sorteio: ${bestHits} acertos.`);
  };

  const handleGenerate = async () => {
    if (!session) {
      alert('Por favor, faça o upload da planilha primeiro.');
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/generate`, {
        session_id: session,
        count: ticketCount,
        total_numbers: LOTOFACIL_CONFIG.total,
        range: LOTOFACIL_CONFIG.range
      });

      const newTickets = res.data.tickets || [];
      const newEntry = {
        id: Date.now(),
        date: new Date().toLocaleString('pt-BR'),
        tickets: newTickets.map(t => ({ numbers: t, hits: null })),
        confronted: false
      };

      const updatedHistory = [newEntry, ...history];
      saveHistory(updatedHistory);
      setActiveTab('history');
      setMlMessage('🤖 Palpites gerados com filtros estritos de Paridade, Primos e Soma!');
    } catch (err) {
      alert('Erro ao gerar palpites.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunBacktest = async (e) => {
    e.preventDefault();
    if (!backtestFile) {
      alert('Faça o upload da planilha no painel esquerdo para executar o Backtest.');
      return;
    }

    setBacktestLoading(true);
    const formData = new FormData();
    formData.append('file', backtestFile);
    formData.append('test_draws', testDraws);
    formData.append('bets_per_draw', ticketsPerDraw); // Atualizado para o nome que o backend espera

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
    <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
      {/* LATERAL ESQUERDA */}
      <div className="w-80 bg-slate-800 p-6 flex flex-col gap-6 border-r border-slate-700 overflow-y-auto">
        <div className="flex items-center gap-3">
          <Zap className="w-8 h-8 text-emerald-400" />
          <h1 className="text-xl font-bold text-emerald-400">LottoAI Lotofácil</h1>
        </div>

        <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-emerald-400 transition cursor-pointer relative bg-slate-800/50">
          <input type="file" onChange={handleUpload} accept=".xlsx, .xls, .csv" className="absolute inset-0 opacity-0 cursor-pointer" />
          <UploadCloud className="w-10 h-10 mx-auto text-slate-400 mb-2" />
          <p className="text-sm text-slate-300 font-medium">{backtestFile ? backtestFile.name : 'Atualizar Histórico (.xlsx)'}</p>
        </div>

        {mlMessage && (
          <div className="bg-emerald-950/40 border border-emerald-500/30 p-3 rounded-lg text-xs text-emerald-300 flex items-start gap-2">
            <Cpu className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{mlMessage}</span>
          </div>
        )}

        <div className="space-y-4">
          <div className="flex items-center gap-2 text-slate-300 font-semibold border-b border-slate-700 pb-2">
            <BarChart2 className="w-4 h-4 text-emerald-400" />
            <span>Filtros Restritivos IA</span>
          </div>

          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50 text-xs space-y-1.5 text-slate-400">
            <p>✓ Ímpares: <strong>6 a 9 dezenas</strong></p>
            <p>✓ Primos: <strong>4 a 7 dezenas</strong></p>
            <p>✓ Soma Total: <strong>160 a 220</strong></p>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Quantidade de Palpites</label>
            <input 
              type="number" min="1" max="20" 
              value={ticketCount} 
              onChange={(e) => setTicketCount(Number(e.target.value))} 
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm focus:border-emerald-400 outline-none" 
            />
          </div>

          <button 
            onClick={handleGenerate} 
            disabled={loading}
            className="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-2.5 rounded-lg transition disabled:opacity-50 shadow-lg shadow-emerald-500/10"
          >
            {loading ? 'Filtrando com IA...' : 'Gerar Palpites Inteligentes'}
          </button>
        </div>
      </div>

      {/* ÁREA PRINCIPAL */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex border-b border-slate-700 bg-slate-800/50">
          <button 
            onClick={() => setActiveTab('stats')} 
            className={`px-6 py-4 flex items-center gap-2 font-medium text-sm border-b-2 transition ${activeTab === 'stats' ? 'border-emerald-400 text-emerald-400 bg-slate-800' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <BarChart2 className="w-4 h-4" /> Estatísticas Avançadas
          </button>
          <button 
            onClick={() => setActiveTab('history')} 
            className={`px-6 py-4 flex items-center gap-2 font-medium text-sm border-b-2 transition ${activeTab === 'history' ? 'border-emerald-400 text-emerald-400 bg-slate-800' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <History className="w-4 h-4" /> Histórico & Confrontos
          </button>
          <button 
            onClick={() => setActiveTab('backtest')} 
            className={`px-6 py-4 flex items-center gap-2 font-medium text-sm border-b-2 transition ${activeTab === 'backtest' ? 'border-emerald-400 text-emerald-400 bg-slate-800' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <TrendingUp className="w-4 h-4" /> Backtest Automático
          </button>
        </div>

        {/* TAB 1: ESTATÍSTICAS */}
        {activeTab === 'stats' && (
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            {stats ? (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl">
                    <h3 className="text-sm font-semibold text-amber-400 flex items-center gap-2 mb-3">
                      <RefreshCw className="w-4 h-4" /> Fechamento de Ciclo (Faltam Sair)
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {stats.missing_in_cycle?.length > 0 ? (
                        stats.missing_in_cycle.map(n => (
                          <span key={n} className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-300 font-bold text-sm flex items-center justify-center border border-amber-500/40">
                            {String(n).padStart(2, '0')}
                          </span>
                        ))
                      ) : (
                        <p className="text-xs text-slate-400">Ciclo completo! Novo ciclo iniciando.</p>
                      )}
                    </div>
                  </div>

                  <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl">
                    <h3 className="text-sm font-semibold text-rose-400 flex items-center gap-2 mb-3">
                      <Flame className="w-4 h-4" /> Termômetro de Atraso (Mais Atrasadas)
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {stats.delays
                        ?.sort((a, b) => b.delay - a.delay)
                        .slice(0, 5)
                        .map(item => (
                          <div key={item.number} className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-2 text-center">
                            <span className="block font-bold text-rose-300 text-xs">Dezena {String(item.number).padStart(2, '0')}</span>
                            <span className="text-[10px] text-slate-400">{item.delay} sorteio(s) atrás</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-slate-300">Frequência das Dezenas</h3>
                  <div className="h-72 bg-slate-800 p-4 rounded-xl border border-slate-700">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={stats.frequencies || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="number" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569' }} />
                        <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500">
                <UploadCloud className="w-16 h-16 mb-4 text-slate-600 animate-bounce" />
                <p className="text-lg">Envie a planilha para carregar os novos gráficos de Ciclo e Atraso.</p>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: HISTÓRICO */}
        {activeTab === 'history' && (
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            <h2 className="text-xl font-bold text-slate-200 flex items-center gap-2">
              <History className="w-5 h-5 text-emerald-400" /> Histórico de Palpites & Confrontos
            </h2>
            {history.map((group) => (
              <div key={group.id} className="bg-slate-800 rounded-xl border border-slate-700 p-5 space-y-4">
                <div className="flex justify-between items-center border-b border-slate-700 pb-3">
                  <div>
                    <span className="text-xs text-slate-400 block">Gerado em:</span>
                    <span className="font-semibold text-slate-200">{group.date}</span>
                  </div>
                  {group.confronted ? (
                    <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs px-3 py-1 rounded-full flex items-center gap-1 font-medium">
                      <CheckCircle className="w-3.5 h-3.5" /> Confrontado
                    </span>
                  ) : (
                    <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs px-3 py-1 rounded-full">
                      Aguardando novo sorteio
                    </span>
                  )}
                </div>

                {group.drawnNumbers && (
                  <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
                    <span className="text-xs text-slate-400 block mb-2 font-medium">Dezenas sorteadas:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {group.drawnNumbers.map(n => (
                        <span key={n} className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-300 font-bold text-xs flex items-center justify-center border border-emerald-500/40">
                          {String(n).padStart(2, '0')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  {group.tickets.map((ticket, idx) => (
                    <div key={idx} className="bg-slate-900/80 p-3 rounded-lg flex items-center justify-between border border-slate-700/40">
                      <div className="flex flex-wrap gap-1.5">
                        {ticket.numbers.map((num) => {
                          const isHit = group.drawnNumbers && group.drawnNumbers.includes(num);
                          return (
                            <span key={num} className={`w-8 h-8 rounded-lg font-bold text-xs flex items-center justify-center ${isHit ? 'bg-emerald-500 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800 text-slate-300 border border-slate-700'}`}>
                              {String(num).padStart(2, '0')}
                            </span>
                          );
                        })}
                      </div>
                      {ticket.hits !== null && (
                        <div className={`px-3 py-1 rounded-lg text-xs font-bold shrink-0 ml-4 ${ticket.hits >= 11 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-slate-800 text-slate-400'}`}>
                          {ticket.hits} Acertos
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 3: BACKTEST AUTOMÁTICO */}
        {activeTab === 'backtest' && (
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-6 h-6 text-emerald-400" />
                <div>
                  <h2 className="text-lg font-bold text-slate-100">Simulação de Walk-Forward (Backtest Cego)</h2>
                  <p className="text-xs text-slate-400">O sistema retém os últimos N sorteios do histórico para testar a precisão da IA em dados não vistos.</p>
                </div>
              </div>

              <form onSubmit={handleRunBacktest} className="grid grid-cols-3 gap-4 pt-2 border-t border-slate-700">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Sorteios para Reter (Futuro Cego)</label>
                  <input 
                    type="number" min="1" max="50" 
                    value={testDraws} 
                    onChange={(e) => setTestDraws(Number(e.target.value))} 
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm focus:border-emerald-400 outline-none" 
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Palpites Gerados por Sorteio</label>
                  <input 
                    type="number" min="1" max="150" 
                    value={ticketsPerDraw} 
                    onChange={(e) => setTicketsPerDraw(Number(e.target.value))} 
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm focus:border-emerald-400 outline-none" 
                  />
                </div>
                <div className="flex items-end">
                  <button 
                    type="submit" 
                    disabled={backtestLoading}
                    className="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-2 rounded transition flex items-center justify-center gap-2 text-sm disabled:opacity-50"
                  >
                    <Play className="w-4 h-4 fill-slate-950" />
                    {backtestLoading ? 'Executando Backtest...' : 'Executar Backtest'}
                  </button>
                </div>
              </form>
            </div>

            {/* RESULTADOS DO BACKTEST ATUALIZADOS PARA O NOVO BACKEND */}
            {backtestResults && backtestResults.resumo && (
              <div className="space-y-6">
                <div className="grid grid-cols-5 gap-3">
                  <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl text-center">
                    <span className="text-xs text-slate-400 block font-medium">11 Pontos</span>
                    <span className="text-2xl font-bold text-emerald-400">{backtestResults.resumo["11"]}</span>
                  </div>
                  <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl text-center">
                    <span className="text-xs text-slate-400 block font-medium">12 Pontos</span>
                    <span className="text-2xl font-bold text-emerald-400">{backtestResults.resumo["12"]}</span>
                  </div>
                  <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl text-center">
                    <span className="text-xs text-slate-400 block font-medium">13 Pontos</span>
                    <span className="text-2xl font-bold text-amber-400">{backtestResults.resumo["13"]}</span>
                  </div>
                  <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl text-center">
                    <span className="text-xs text-slate-400 block font-medium">14 Pontos</span>
                    <span className="text-2xl font-bold text-rose-400">{backtestResults.resumo["14"]}</span>
                  </div>
                  <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl text-center">
                    <span className="text-xs text-slate-400 block font-medium">15 Pontos</span>
                    <span className="text-2xl font-bold text-purple-400">{backtestResults.resumo["15"]}</span>
                  </div>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-700 pb-3">
                    <h3 className="font-semibold text-slate-200 flex items-center gap-2 text-sm">
                      <Award className="w-4 h-4 text-emerald-400" /> Resumo Global ({backtestResults.resumo.total_apostas} apostas processadas pela IA)
                    </h3>
                  </div>
                  <p className="text-sm text-slate-300">
                    O Random Forest foi treinado com os resultados dessa simulação para os próximos ciclos.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}