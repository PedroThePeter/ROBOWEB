import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export default function App() {
  // Estados principais
  const [file, setFile] = useState(null);
  const [session, setSession] = useState(null);
  const [stats, setStats] = useState(null);
  const [lastDraw, setLastDraw] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState(5);

  // Estados do Backtest & Machine Learning
  const [backtestFile, setBacktestFile] = useState(null);
  const [testDraws, setTestDraws] = useState(10);
  const [ticketsPerDraw, setTicketsPerDraw] = useState(12);
  const [backtestResults, setBacktestResults] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [mlMessage, setMlMessage] = useState('');

  // Controle de Abas
  const [activeTab, setActiveTab] = useState('generator');

  // Upload da planilha na aba gerador
  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;
    setFile(uploadedFile);
    setBacktestFile(uploadedFile); // Compartilha o arquivo para facilitar

    const formData = new FormData();
    formData.append('file', uploadedFile);

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      setSession(res.data.session_id);
      setStats(res.data.stats);
      setLastDraw(res.data.last_draw || []);
      alert('Planilha carregada e processada com sucesso!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao enviar o arquivo.');
    } finally {
      setLoading(false);
    }
  };

  // Geração de palpites inteligentes guiados pelo modelo de IA
  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!session) {
      alert('Por favor, faça o upload de uma planilha primeiro.');
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

  // Execução do Backtest e salvamento do modelo na sessão
  const handleRunBacktest = async (e) => {
    e.preventDefault();
    const activeFile = backtestFile || file;
    if (!activeFile) {
      alert('Faça o upload da planilha para executar o Backtest.');
      return;
    }

    setBacktestLoading(true);
    const formData = new FormData();
    formData.append('file', activeFile);
    formData.append('test_draws', testDraws);
    formData.append('bets_per_draw', ticketsPerDraw);
    if (session) {
      formData.append('session_id', session); // Envia o ID da sessão para o backend atrelar o Random Forest
    }

    try {
      const res = await axios.post(`${API_URL}/backtest`, formData);
      setBacktestResults(res.data);
      setMlMessage('🤖 Backtest concluído! O Random Forest foi atualizado e já está filtrando os novos palpites.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao executar o Backtest.');
    } finally {
      setBacktestLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4 shadow-md flex justify-between items-center">
        <h1 className="text-xl font-bold text-emerald-400">🎯 Robô Inteligente - Lotofácil (com IA)</h1>
        <div className="flex space-x-2">
          <button 
            onClick={() => setActiveTab('generator')} 
            className={`px-4 py-2 rounded font-medium transition ${activeTab === 'generator' ? 'bg-emerald-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
          >
            Gerador & Estatísticas
          </button>
          <button 
            onClick={() => setActiveTab('backtest')} 
            className={`px-4 py-2 rounded font-medium transition ${activeTab === 'backtest' ? 'bg-emerald-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
          >
            Backtest & Treino de IA
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 max-w-6xl mx-auto w-full">
        {activeTab === 'generator' ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Painel Esquerdo: Controles e Upload */}
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg space-y-6">
              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-300">Carregar Histórico (Excel/CSV)</label>
                <input 
                  type="file" 
                  accept=".csv, .xlsx, .xls" 
                  onChange={handleFileUpload} 
                  className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-700 cursor-pointer"
                />
                {session && <p className="text-xs text-emerald-400 mt-2">✓ Sessão ativa ID: {session}</p>}
              </div>

              {mlMessage && (
                <div className="p-3 bg-emerald-900/40 border border-emerald-600/50 rounded-lg text-emerald-300 text-xs leading-relaxed">
                  {mlMessage}
                </div>
              )}

              <hr className="border-gray-700" />

              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2 text-gray-300">Quantidade de Jogos</label>
                  <input 
                    type="number" 
                    min="1" 
                    max="50" 
                    value={count} 
                    onChange={(e) => setCount(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <button 
                  type="submit" 
                  disabled={loading || !session}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-lg transition shadow-md"
                >
                  {loading ? 'Gerando Palpites...' : 'Gerar Palpites Inteligentes 🤖'}
                </button>
              </form>
            </div>

            {/* Painel Direito: Último Sorteio e Resultados */}
            <div className="md:col-span-2 space-y-6">
              {lastDraw.length > 0 && (
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
                  <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Último Sorteio Analisado</h3>
                  <div className="flex flex-wrap gap-2">
                    {lastDraw.map((num, idx) => (
                      <span key={idx} className="w-10 h-10 rounded-full bg-emerald-600/20 border border-emerald-500 text-emerald-400 font-bold flex items-center justify-center text-sm shadow">
                        {String(num).padStart(2, '0')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
                <h3 className="text-lg font-bold text-white mb-4">Bilhetes Recomendados</h3>
                {tickets.length === 0 ? (
                  <p className="text-gray-500 text-sm">Nenhum bilhete gerado ainda. Faça o upload da planilha e clique em gerar.</p>
                ) : (
                  <div className="space-y-3">
                    {tickets.map((ticket, i) => (
                      <div key={i} className="flex items-center justify-between bg-gray-900/60 p-3 rounded-lg border border-gray-700/50">
                        <span className="text-xs font-semibold text-gray-400">Jogo #{i + 1}</span>
                        <div className="flex flex-wrap gap-1.5 justify-end">
                          {ticket.map((n, idx) => (
                            <span key={idx} className="w-7 h-7 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">
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
          </div>
        ) : (
          /* Aba de Backtest & Treinamento de IA */
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg max-w-2xl mx-auto space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-1">Simulação de Backtest & Treinamento ML</h2>
              <p className="text-sm text-gray-400">Simule os palpites do robô nos concursos passados para treinar o Random Forest e refinar a geração de bilhetes.</p>
            </div>

            <form onSubmit={handleRunBacktest} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-300">Arquivo de Histórico</label>
                <input 
                  type="file" 
                  accept=".csv, .xlsx, .xls" 
                  onChange={(e) => setBacktestFile(e.target.files[0])} 
                  className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-700 cursor-pointer"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold mb-2 text-gray-300">Concursos de Teste</label>
                  <input 
                    type="number" 
                    value={testDraws} 
                    onChange={(e) => setTestDraws(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-2 text-gray-300">Apostas por Concurso</label>
                  <input 
                    type="number" 
                    value={ticketsPerDraw} 
                    onChange={(e) => setTicketsPerDraw(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <button 
                type="submit" 
                disabled={backtestLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 text-white font-semibold py-3 rounded-lg transition shadow-md"
              >
                {backtestLoading ? 'Rodando Backtest e Treinando IA...' : 'Iniciar Backtest & Treinar IA 🚀'}
              </button>
            </form>

            {backtestResults && (
              <div className="bg-gray-900 p-4 rounded-xl border border-gray-700 space-y-3">
                <h3 className="font-bold text-emerald-400 text-sm uppercase tracking-wider">Resultados da Simulação</h3>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                    <span className="block text-xs text-gray-400">Total de Apostas</span>
                    <span className="text-lg font-bold text-white">{backtestResults.resumo.total_apostas}</span>
                  </div>
                  <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                    <span className="block text-xs text-gray-400">14 Pontos</span>
                    <span className="text-lg font-bold text-emerald-400">{backtestResults.resumo["14"]}</span>
                  </div>
                  <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                    <span className="block text-xs text-gray-400">15 Pontos</span>
                    <span className="text-lg font-bold text-yellow-400">{backtestResults.resumo["15"]}</span>
                  </div>
                </div>
                <div className="text-xs text-gray-400 flex justify-around pt-2 border-t border-gray-800">
                  <span>11 Pts: <strong>{backtestResults.resumo["11"]}</strong></span>
                  <span>12 Pts: <strong>{backtestResults.resumo["12"]}</strong></span>
                  <span>13 Pts: <strong>{backtestResults.resumo["13"]}</strong></span>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}