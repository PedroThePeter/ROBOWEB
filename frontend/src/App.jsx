import React, { useState, useEffect } from 'react';
import { Upload, Play, Trophy, BarChart, History, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

// 🔴 IMPORTANTE: Substitua pela URL real do seu backend no Render!
// Não deixe a barra "/" no final do link.
const API_URL = "https://roboweb-cvha.onrender.com";

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);

  // Estados do Gerador
  const [qtdJogos, setQtdJogos] = useState(5);
  const [ticketsGerados, setTicketsGerados] = useState([]);
  const [rankingDezenas, setRankingDezenas] = useState([]);

  // Estados do Backtest
  const [testDraws, setTestDraws] = useState(10);
  const [betsPerDraw, setBetsPerDraw] = useState(12);
  const [backtestResult, setBacktestResult] = useState(null);

  // Carrega o status ao abrir o app
  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (error) {
      console.error("Erro ao buscar status do servidor:", error);
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setUploadMessage(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });
      
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        setUploadMessage({ type: 'success', text: 'Planilha enviada e salva no Supabase com sucesso!' });
      } else {
        setUploadMessage({ type: 'error', text: 'Erro ao processar planilha.' });
      }
    } catch (error) {
      setUploadMessage({ type: 'error', text: 'Erro de conexão com o servidor.' });
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count: qtdJogos })
      });
      
      if (res.ok) {
        const data = await res.json();
        setTicketsGerados(data.tickets);
        setRankingDezenas(data.ranking);
      }
    } catch (error) {
      alert("Erro ao gerar jogos. Verifique a conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  const handleBacktest = async () => {
    setLoading(true);
    setBacktestResult(null);
    
    const formData = new FormData();
    formData.append("test_draws", testDraws);
    formData.append("bets_per_draw", betsPerDraw);

    try {
      const res = await fetch(`${API_URL}/api/backtest`, {
        method: "POST",
        body: formData,
      });
      
      if (res.ok) {
        const data = await res.json();
        setBacktestResult(data.resumo);
      }
    } catch (error) {
      alert("Erro ao executar backtest.");
    } finally {
      setLoading(false);
    }
  };

  const renderTicket = (ticket, index) => (
    <div key={index} className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-bold text-slate-700">Jogo #{index + 1}</h4>
        <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full font-medium">
          IA Otimizado
        </span>
      </div>
      <div className="grid grid-cols-5 gap-2">
        {Array.from({ length: 25 }, (_, i) => i + 1).map(num => {
          const isSelected = ticket.includes(num);
          return (
            <div
              key={num}
              className={`w-10 h-10 flex items-center justify-center rounded-full text-sm font-bold ${
                isSelected ? 'bg-emerald-500 text-white shadow-md' : 'bg-slate-100 text-slate-400'
              }`}
            >
              {num.toString().padStart(2, '0')}
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800">
      {/* HEADER */}
      <header className="bg-emerald-600 text-white p-6 shadow-md">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Trophy className="w-8 h-8" />
            <h1 className="text-2xl font-bold">Robô Lotofácil IA</h1>
          </div>
          <div className="text-sm bg-emerald-700 px-4 py-2 rounded-lg flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${status ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'}`}></div>
            {status ? 'Servidor Conectado' : 'Conectando...'}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6 mt-4 flex flex-col md:flex-row gap-6">
        
        {/* SIDEBAR DE NAVEGAÇÃO */}
        <aside className="w-full md:w-64 flex flex-col gap-2">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-3 p-4 rounded-xl font-medium transition-all ${activeTab === 'dashboard' ? 'bg-emerald-500 text-white shadow-md' : 'bg-white text-slate-600 hover:bg-emerald-50'}`}
          >
            <BarChart className="w-5 h-5" /> Painel Geral
          </button>
          <button 
            onClick={() => setActiveTab('gerador')}
            className={`flex items-center gap-3 p-4 rounded-xl font-medium transition-all ${activeTab === 'gerador' ? 'bg-emerald-500 text-white shadow-md' : 'bg-white text-slate-600 hover:bg-emerald-50'}`}
          >
            <Play className="w-5 h-5" /> Gerar Jogos
          </button>
          <button 
            onClick={() => setActiveTab('backtest')}
            className={`flex items-center gap-3 p-4 rounded-xl font-medium transition-all ${activeTab === 'backtest' ? 'bg-emerald-500 text-white shadow-md' : 'bg-white text-slate-600 hover:bg-emerald-50'}`}
          >
            <History className="w-5 h-5" /> Simulador (Backtest)
          </button>
        </aside>

        {/* ÁREA DE CONTEÚDO PRINCIPAL */}
        <section className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          
          {/* TAB: DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-slate-800 border-b pb-2">Status da Base de Dados</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-50 p-5 rounded-xl border border-slate-100 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500 font-medium">Total de Concursos Lidos</p>
                    <p className="text-3xl font-bold text-emerald-600">{status?.stats?.total_concursos || 0}</p>
                  </div>
                  <BarChart className="w-10 h-10 text-slate-200" />
                </div>
                <div className="bg-slate-50 p-5 rounded-xl border border-slate-100 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500 font-medium">Último Concurso Registrado</p>
                    <p className="text-3xl font-bold text-blue-600">#{status?.stats?.ultimo_concurso || '---'}</p>
                  </div>
                  <Trophy className="w-10 h-10 text-slate-200" />
                </div>
              </div>

              <div className="bg-blue-50 p-5 rounded-xl border border-blue-100 mt-4">
                <h3 className="font-bold text-blue-900 mb-3">Dezenas do Último Concurso</h3>
                <div className="flex flex-wrap gap-2">
                  {status?.last_draw?.length > 0 ? (
                    status.last_draw.map(num => (
                      <span key={num} className="bg-blue-500 text-white w-9 h-9 flex items-center justify-center rounded-full font-bold text-sm shadow-sm">
                        {num.toString().padStart(2, '0')}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-blue-700">Nenhum dado disponível. Envie uma planilha atualizada.</p>
                  )}
                </div>
              </div>

              <div className="mt-8 border-t pt-6">
                <h3 className="font-bold text-slate-800 mb-2">Atualizar Base (Upload)</h3>
                <p className="text-sm text-slate-500 mb-4">Envie uma nova planilha (Excel ou CSV) com os resultados mais recentes. Isso substituirá a base atual no Supabase e forçará a IA a aprender com os novos dados.</p>
                
                <div className="flex items-center gap-4">
                  <label className="bg-slate-800 hover:bg-slate-700 text-white px-5 py-3 rounded-xl cursor-pointer flex items-center gap-2 font-medium transition-colors">
                    <Upload className="w-5 h-5" />
                    Escolher Arquivo e Enviar
                    <input type="file" accept=".xlsx, .xls, .csv" className="hidden" onChange={handleUpload} disabled={loading} />
                  </label>
                  {loading && <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />}
                </div>

                {uploadMessage && (
                  <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-sm font-medium ${uploadMessage.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                    {uploadMessage.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                    {uploadMessage.text}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB: GERADOR DE JOGOS */}
          {activeTab === 'gerador' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center border-b pb-4">
                <div>
                  <h2 className="text-xl font-bold text-slate-800">Gerar Palpites com IA</h2>
                  <p className="text-sm text-slate-500">O robô aplicará Machine Learning + Filtros de Ouro (Primos, Moldura, etc).</p>
                </div>
              </div>

              <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-center gap-4">
                <div className="flex flex-col w-full sm:w-auto">
                  <label className="text-sm font-bold text-slate-700 mb-1">Quantidade de Jogos:</label>
                  <input 
                    type="number" 
                    min="1" max="50" 
                    value={qtdJogos} 
                    onChange={(e) => setQtdJogos(e.target.value)}
                    className="border border-slate-300 rounded-lg px-4 py-2 w-full sm:w-32 focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>
                <button 
                  onClick={handleGenerate} 
                  disabled={loading}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-bold flex items-center gap-2 w-full sm:w-auto mt-6 sm:mt-0"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                  {loading ? 'Processando IA...' : 'Gerar Jogos Agora'}
                </button>
              </div>

              {ticketsGerados.length > 0 && (
                <div className="mt-8">
                  <h3 className="font-bold text-lg mb-4">Seus Palpites Otimizados:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {ticketsGerados.map((ticket, idx) => renderTicket(ticket, idx))}
                  </div>
                </div>
              )}

              {rankingDezenas.length > 0 && (
                <div className="mt-10 border-t pt-6">
                  <h3 className="font-bold text-lg mb-4">Top 10 Dezenas Mais Quentes (Segundo a IA)</h3>
                  <div className="flex flex-wrap gap-3">
                    {rankingDezenas.slice(0, 10).map((item, idx) => (
                      <div key={idx} className="bg-white border border-emerald-200 px-4 py-2 rounded-lg shadow-sm flex flex-col items-center">
                        <span className="text-2xl font-black text-emerald-600">{item.dezena.toString().padStart(2, '0')}</span>
                        <span className="text-xs text-slate-500 font-medium">{item.probabilidade}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: BACKTEST */}
          {activeTab === 'backtest' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Simulador de Estratégia (Backtest)</h2>
                <p className="text-sm text-slate-500 mt-1">Veja como a IA teria se saído nos concursos passados se você tivesse apostado nela.</p>
              </div>

              <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-bold text-slate-700 block mb-1">Qtd de Concursos Passados:</label>
                  <input 
                    type="number" 
                    value={testDraws} 
                    onChange={(e) => setTestDraws(e.target.value)}
                    className="border border-slate-300 rounded-lg px-4 py-2 w-full focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <p className="text-xs text-slate-400 mt-1">Ex: Últimos 10 concursos.</p>
                </div>
                <div>
                  <label className="text-sm font-bold text-slate-700 block mb-1">Jogos gerados por concurso:</label>
                  <input 
                    type="number" 
                    value={betsPerDraw} 
                    onChange={(e) => setBetsPerDraw(e.target.value)}
                    className="border border-slate-300 rounded-lg px-4 py-2 w-full focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <p className="text-xs text-slate-400 mt-1">Ex: 12 bilhetes por sorteio simulado.</p>
                </div>
                <div className="sm:col-span-2 mt-2">
                  <button 
                    onClick={handleBacktest} 
                    disabled={loading}
                    className="w-full bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-lg font-bold flex items-center justify-center gap-2"
                  >
                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <History className="w-5 h-5" />}
                    {loading ? 'Rodando simulação no tempo...' : 'Iniciar Backtest'}
                  </button>
                </div>
              </div>

              {backtestResult && (
                <div className="mt-6 animate-fade-in">
                  <h3 className="font-bold text-lg mb-4 text-center">Resultados da Simulação</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
                    <div className="bg-white border p-3 rounded-lg shadow-sm">
                      <p className="text-xs text-slate-500 font-bold uppercase">11 Acertos</p>
                      <p className="text-2xl font-black text-slate-700">{backtestResult['11']}</p>
                    </div>
                    <div className="bg-white border p-3 rounded-lg shadow-sm">
                      <p className="text-xs text-slate-500 font-bold uppercase">12 Acertos</p>
                      <p className="text-2xl font-black text-slate-700">{backtestResult['12']}</p>
                    </div>
                    <div className="bg-white border p-3 rounded-lg shadow-sm">
                      <p className="text-xs text-slate-500 font-bold uppercase">13 Acertos</p>
                      <p className="text-2xl font-black text-emerald-600">{backtestResult['13']}</p>
                    </div>
                    <div className="bg-white border-2 border-yellow-400 p-3 rounded-lg shadow-md bg-yellow-50">
                      <p className="text-xs text-yellow-700 font-bold uppercase">14 Acertos</p>
                      <p className="text-3xl font-black text-yellow-600">{backtestResult['14']}</p>
                    </div>
                    <div className="bg-white border-2 border-purple-500 p-3 rounded-lg shadow-md bg-purple-50">
                      <p className="text-xs text-purple-700 font-bold uppercase">15 Acertos</p>
                      <p className="text-3xl font-black text-purple-600">{backtestResult['15']}</p>
                    </div>
                  </div>
                  <p className="text-center text-sm text-slate-500 mt-4">
                    Foram gerados e conferidos um total de <b>{backtestResult.total_apostas}</b> bilhetes virtuais nesta simulação.
                  </p>
                </div>
              )}
            </div>
          )}

        </section>
      </main>
    </div>
  );
}