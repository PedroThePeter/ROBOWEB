import React, { useState, useEffect } from 'react';

// URL do backend no Render (ou localhost se estiver testando local)
const API_URL = 'https://roboweb-cvha.onrender.com';

export default function App() {
  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  
  // Estado das Abas
  const [activeTab, setActiveTab] = useState('generator'); // 'generator' | 'ranking' | 'backtest'
  
  // Gerador
  const [count, setCount] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [ranking, setRanking] = useState([]);
  
  // Backtest
  const [testDraws, setTestDraws] = useState(10);
  const [betsPerDraw, setBetsPerDraw] = useState(12);
  const [backtesting, setBacktesting] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);

  // Copiar bilhete
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Upload de arquivo
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoadingStatus(true);
    try {
      const res = await fetch(`${API_URL}/api/status`);
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      console.error('Erro ao buscar status:', err);
    } finally {
      setLoadingStatus(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: parseInt(count) })
      });
      const data = await res.json();
      setTickets(data.tickets || []);
      setRanking(data.ranking || []);
    } catch (err) {
      alert('Erro ao gerar bilhetes. Verifique o servidor.');
    } finally {
      setGenerating(false);
    }
  };

  const handleBacktest = async () => {
    setBacktesting(true);
    setBacktestResult(null);
    try {
      const formData = new FormData();
      formData.append('test_draws', testDraws);
      formData.append('bets_per_draw', betsPerDraw);

      const res = await fetch(`${API_URL}/api/backtest`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setBacktestResult(data.resumo);
    } catch (err) {
      alert('Erro ao executar o Backtest.');
    } finally {
      setBacktesting(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        alert('Planilha enviada com sucesso!');
        fetchStatus();
      } else {
        alert('Erro ao processar planilha.');
      }
    } catch (err) {
      alert('Erro ao enviar o arquivo.');
    } finally {
      setUploading(false);
    }
  };

  const copyTicketToClipboard = (ticket, index) => {
    const text = ticket.map(n => String(n).padStart(2, '0')).join(', ');
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const isPrime = (num) => [2, 3, 5, 7, 11, 13, 17, 19, 23].includes(num);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* HEADER / BANNER */}
        <header className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-3xl">🤖</span>
              <h1 className="text-2xl md:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                Robô Lotofácil IA
              </h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Análise Preditiva com Random Forest & Filtros de Alta Probabilidade
            </p>
          </div>

          <div className="flex items-center gap-3">
            <label className="cursor-pointer bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-sm font-medium border border-slate-700 transition-all flex items-center gap-2">
              <span>{uploading ? '⏳ Enviando...' : '📁 Atualizar Planilha'}</span>
              <input type="file" accept=".xlsx,.csv" onChange={handleFileUpload} className="hidden" />
            </label>
            <button onClick={fetchStatus} className="bg-slate-800 hover:bg-slate-700 p-2 rounded-xl border border-slate-700 text-slate-300">
              🔄
            </button>
          </div>
        </header>

        {/* PAINEL DE STATUS DO ÚLTIMO CONCURSO */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <span>🎯</span> Último Sorteio Oficial
              {status?.stats?.ultimo_concurso && (
                <span className="bg-emerald-500/10 text-emerald-400 text-xs font-semibold px-2.5 py-1 rounded-full border border-emerald-500/20">
                  Concurso #{status.stats.ultimo_concurso}
                </span>
              )}
            </h2>
            <span className="text-xs text-slate-400">
              Total na Base: <strong>{status?.stats?.total_concursos || 0}</strong> jogos
            </span>
          </div>

          {loadingStatus ? (
            <div className="text-center py-4 text-slate-400 animate-pulse">Sincronizando com a Caixa...</div>
          ) : status?.last_draw?.length > 0 ? (
            <div className="flex flex-wrap gap-2 justify-center md:justify-start">
              {status.last_draw.map((num) => (
                <span
                  key={num}
                  className="w-10 h-10 flex items-center justify-center font-bold text-lg rounded-full bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                >
                  {String(num).padStart(2, '0')}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-slate-400 text-sm">Nenhum concurso carregado na base ainda.</div>
          )}
        </div>

        {/* NAVEGAÇÃO DE ABAS */}
        <div className="flex bg-slate-900 p-1.5 rounded-xl border border-slate-800 max-w-md mx-auto">
          <button
            onClick={() => setActiveTab('generator')}
            className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'generator' ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🤖 Gerar Palpites
          </button>
          <button
            onClick={() => setActiveTab('ranking')}
            className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'ranking' ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🔥 Ranking IA
          </button>
          <button
            onClick={() => setActiveTab('backtest')}
            className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'backtest' ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            📊 Simulação
          </button>
        </div>

        {/* CONTEÚDO DA ABA 1: GERADOR DE PALPITES */}
        {activeTab === 'generator' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4 w-full md:w-auto">
                <label className="text-sm font-medium text-slate-300 whitespace-nowrap">Qtd. de Jogos:</label>
                <select
                  value={count}
                  onChange={(e) => setCount(e.target.value)}
                  className="bg-slate-800 border border-slate-700 text-slate-100 px-4 py-2 rounded-xl focus:outline-none focus:border-emerald-500 w-full md:w-auto"
                >
                  <option value={1}>1 Bilhete</option>
                  <option value={5}>5 Bilhetes</option>
                  <option value={10}>10 Bilhetes</option>
                  <option value={20}>20 Bilhetes</option>
                </select>
              </div>

              <button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full md:w-auto bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-bold px-8 py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50"
              >
                {generating ? '🧠 Calculando no Random Forest...' : '✨ Gerar Jogos Inteligentes'}
              </button>
            </div>

            {/* LISTA DE JOGOS GERADOS */}
            {tickets.length > 0 && (
              <div className="grid grid-cols-1 gap-4">
                {tickets.map((ticket, idx) => {
                  const soma = ticket.reduce((a, b) => a + b, 0);
                  const pares = ticket.filter((n) => n % 2 === 0).length;
                  const primos = ticket.filter(isPrime).length;

                  return (
                    <div key={idx} className="bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all rounded-2xl p-5 space-y-4">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                        <span className="font-bold text-emerald-400 text-sm">Bilhete #{idx + 1}</span>
                        
                        <div className="flex gap-3 text-xs text-slate-400">
                          <span>Soma: <strong className="text-slate-200">{soma}</strong></span>
                          <span>Pares: <strong className="text-slate-200">{pares}</strong></span>
                          <span>Primos: <strong className="text-slate-200">{primos}</strong></span>
                        </div>

                        <button
                          onClick={() => copyTicketToClipboard(ticket, idx)}
                          className="bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition-all"
                        >
                          {copiedIndex === idx ? '✅ Copiado!' : '📋 Copiar'}
                        </button>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {ticket.map((num) => (
                          <span
                            key={num}
                            className="w-9 h-9 flex items-center justify-center font-bold text-sm rounded-xl bg-slate-800 text-cyan-300 border border-slate-700"
                          >
                            {String(num).padStart(2, '0')}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* CONTEÚDO DA ABA 2: RANKING IA DE PROBABILIDADES */}
        {activeTab === 'ranking' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-200 mb-2">🔥 Ranking de Probabilidades (Random Forest)</h3>
            <p className="text-sm text-slate-400 mb-6">
              Esta é a chance estimada pelo modelo para a saída de cada dezena no próximo concurso com base em janelas de frequência e atrito de atraso.
            </p>

            {ranking.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                Clique em <strong>"Gerar Palpites"</strong> para calcular o ranking mais recente.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {ranking.map((item) => (
                  <div key={item.dezena} className="bg-slate-800/50 p-3 rounded-xl border border-slate-800 flex items-center gap-4">
                    <span className="w-9 h-9 flex items-center justify-center font-extrabold text-slate-950 rounded-xl bg-cyan-400">
                      {String(item.dezena).padStart(2, '0')}
                    </span>
                    
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-300">Dezena {item.dezena}</span>
                        <span className="text-emerald-400">{item.probabilidade}%</span>
                      </div>
                      
                      <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full transition-all duration-500"
                          style={{ width: `${item.probabilidade}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* CONTEÚDO DA ABA 3: SIMULAÇÃO E BACKTEST */}
        {activeTab === 'backtest' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <h3 className="text-lg font-bold text-slate-200">📊 Teste Histórico Cruzado (Backtest Real)</h3>
              <p className="text-sm text-slate-400">
                Simule como o algoritmo teria se comportado nos concursos passados sem vazar informações do futuro.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Qtd. de Concursos Passados para Testar:</label>
                  <input
                    type="number"
                    value={testDraws}
                    onChange={(e) => setTestDraws(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 px-4 py-2 rounded-xl focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1">Apostas por Concurso:</label>
                  <input
                    type="number"
                    value={betsPerDraw}
                    onChange={(e) => setBetsPerDraw(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 px-4 py-2 rounded-xl focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <button
                onClick={handleBacktest}
                disabled={backtesting}
                className="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-400 font-bold py-3 rounded-xl transition-all disabled:opacity-50"
              >
                {backtesting ? '⏳ Rodando Cruzamento Real...' : '🚀 Executar Simulação'}
              </button>
            </div>

            {/* RESULTADO DO BACKTEST */}
            {backtestResult && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <h4 className="font-bold text-slate-200">Resultado do Teste</h4>
                  <span className="text-xs text-slate-400">
                    Total de Bilhetes Conferidos: <strong>{backtestResult.total_apostas}</strong>
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {[11, 12, 13, 14, 15].map((pts) => (
                    <div key={pts} className="bg-slate-800/40 border border-slate-800 p-4 rounded-xl text-center space-y-1">
                      <span className="text-xs text-slate-400 block">{pts} Pontos</span>
                      <span className="text-2xl font-black text-emerald-400">
                        {backtestResult[String(pts)] || 0}
                      </span>
                      <span className="text-[10px] text-slate-500 block">bilhetes premiados</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}