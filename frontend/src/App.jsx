import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, BarChart2, History, Cpu, CheckCircle, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'https://roboweb-cvha.onrender.com/api';

// Configuração fixa exclusiva para Lotofácil
const LOTOFACIL_CONFIG = { name: 'Lotofácil', total: 15, range: 25 };

export default function App() {
  const [session, setSession] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('stats');

  // Configurações e Palpites
  const [ticketCount, setTicketCount] = useState(5);
  const [history, setHistory] = useState([]);
  const [lastDrawnNumbers, setLastDrawnNumbers] = useState([]);
  const [mlMessage, setMlMessage] = useState('');

  // Carregar histórico do localStorage ao abrir a aplicação
  useEffect(() => {
    const savedHistory = localStorage.getItem('lottoai_history');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Erro ao carregar histórico:', e);
      }
    }
  }, []);

  // Salvar histórico no localStorage sempre que houver alterações
  const saveHistory = (newHistory) => {
    setHistory(newHistory);
    localStorage.setItem('lottoai_history', JSON.stringify(newHistory));
  };

  // Upload do Excel + Atualização do aprendizado
  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      setSession(res.data.session_id);
      
      if (res.data.stats) {
        setStats(res.data.stats);
      }

      // Se o backend retornar o último sorteio
      if (res.data.last_draw) {
        const drawn = res.data.last_draw; // Array de números [1, 2, 5, ...]
        setLastDrawnNumbers(drawn);
        confrontLastBet(drawn);
      } else {
        setMlMessage('Planilha analisada com sucesso! Dados prontos para novos palpites.');
      }
    } catch (err) {
      alert('Erro ao enviar planilha. Verifique a conexão ou o formato do arquivo.');
    } finally {
      setLoading(false);
    }
  };

  // Confronta o último sorteio com os palpites salvos no histórico
  const confrontLastBet = (drawnNumbers) => {
    if (history.length === 0) {
      setMlMessage('Último sorteio identificado! Gere palpites para habilitar o aprendizado do robô.');
      return;
    }

    // Pega a última rodada de palpites gerada
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
    setMlMessage(`🤖 Machine Learning: Confronto realizado! Melhor desempenho no último sorteio: ${bestHits} acertos.`);
  };

  // Gerar novos palpites para a Lotofácil
  const handleGenerate = async () => {
    if (!session) {
      alert('Por favor, faça o upload da planilha com o histórico primeiro.');
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
      setMlMessage('🤖 Palpites gerados com base na matriz estatística da Lotofácil!');
    } catch (err) {
      alert('Erro ao gerar palpites.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
      {/* PAINEL LATERAL ESQUERDO */}
      <div className="w-80 bg-slate-800 p-6 flex flex-col gap-6 border-r border-slate-700 overflow-y-auto">
        <div className="flex items-center gap-3">
          <Zap className="w-8 h-8 text-emerald-400" />
          <h1 className="text-xl font-bold text-emerald-400">LottoAI Lotofácil</h1>
        </div>

        {/* UPLOAD EXCEL */}
        <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-emerald-400 transition cursor-pointer relative bg-slate-800/50">
          <input type="file" onChange={handleUpload} accept=".xlsx, .xls, .csv" className="absolute inset-0 opacity-0 cursor-pointer" />
          <UploadCloud className="w-10 h-10 mx-auto text-slate-400 mb-2" />
          <p className="text-sm text-slate-300 font-medium">Atualizar Histórico (.xlsx)</p>
          <p className="text-xs text-slate-500 mt-1">Arraste ou clique para carregar</p>
        </div>

        {/* MENSAGEM DO MACHINE LEARNING */}
        {mlMessage && (
          <div className="bg-emerald-950/40 border border-emerald-500/30 p-3 rounded-lg text-xs text-emerald-300 flex items-start gap-2">
            <Cpu className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{mlMessage}</span>
          </div>
        )}

        {/* CONFIGURAÇÃO LOTOFÁCIL */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-slate-300 font-semibold border-b border-slate-700 pb-2">
            <BarChart2 className="w-4 h-4 text-emerald-400" />
            <span>Configuração Lotofácil</span>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Dezenas por Cartão</label>
            <input type="number" value={15} disabled className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-400 cursor-not-allowed" />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Universo de Números</label>
            <input type="text" value="1 ao 25" disabled className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-400 cursor-not-allowed" />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Quantidade de Palpites a Gerar</label>
            <input 
              type="number" 
              min="1" 
              max="20" 
              value={ticketCount} 
              onChange={(e) => setTicketCount(Number(e.target.value))} 
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm focus:border-emerald-400 outline-none" 
            />
          </div>

          <button 
            onClick={handleGenerate} 
            disabled={loading}
            className="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-2.5 rounded-lg transition disabled:opacity-50 mt-2 shadow-lg shadow-emerald-500/10"
          >
            {loading ? 'Processando IA...' : 'Gerar Palpites Inteligentes'}
          </button>
        </div>
      </div>

      {/* PAINEL PRINCIPAL */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* NAVEGAÇÃO ENTRE ABAS */}
        <div className="flex border-b border-slate-700 bg-slate-800/50">
          <button 
            onClick={() => setActiveTab('stats')} 
            className={`px-6 py-4 flex items-center gap-2 font-medium text-sm border-b-2 transition ${activeTab === 'stats' ? 'border-emerald-400 text-emerald-400 bg-slate-800' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <BarChart2 className="w-4 h-4" /> Visão Geral & Estatísticas
          </button>
          <button 
            onClick={() => setActiveTab('history')} 
            className={`px-6 py-4 flex items-center gap-2 font-medium text-sm border-b-2 transition ${activeTab === 'history' ? 'border-emerald-400 text-emerald-400 bg-slate-800' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <History className="w-4 h-4" /> Histórico de Palpites Gerados
          </button>
        </div>

        {/* CONTEÚDO DA ABA 1: ESTATÍSTICAS */}
        {activeTab === 'stats' && (
          <div className="flex-1 p-6 overflow-y-auto">
            {stats ? (
              <div className="space-y-6">
                <h2 className="text-lg font-bold text-slate-200">Frequência das Dezenas (Lotofácil)</h2>
                <div className="h-80 bg-slate-800 p-4 rounded-xl border border-slate-700">
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
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500">
                <UploadCloud className="w-16 h-16 mb-4 text-slate-600 animate-bounce" />
                <p className="text-lg">Envie o arquivo Excel do histórico da Lotofácil para começar.</p>
              </div>
            )}
          </div>
        )}

        {/* CONTEÚDO DA ABA 2: HISTÓRICO E CONFRONTO */}
        {activeTab === 'history' && (
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            <h2 className="text-xl font-bold text-slate-200 flex items-center gap-2">
              <History className="w-5 h-5 text-emerald-400" />
              Histórico de Palpites & Confrontos
            </h2>

            {history.length === 0 ? (
              <div className="text-slate-500 text-center py-12 bg-slate-800/40 rounded-xl border border-slate-700">
                <p>Nenhum palpite gerado ainda. Clique em "Gerar Palpites Inteligentes" no painel esquerdo.</p>
              </div>
            ) : (
              history.map((group) => (
                <div key={group.id} className="bg-slate-800 rounded-xl border border-slate-700 p-5 space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-700 pb-3">
                    <div>
                      <span className="text-xs text-slate-400 block">Gerado em:</span>
                      <span className="font-semibold text-slate-200">{group.date}</span>
                    </div>
                    {group.confronted ? (
                      <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs px-3 py-1 rounded-full flex items-center gap-1 font-medium">
                        <CheckCircle className="w-3.5 h-3.5" /> Confrontado com o último sorteio
                      </span>
                    ) : (
                      <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs px-3 py-1 rounded-full">
                        Aguardando novo sorteio no Excel
                      </span>
                    )}
                  </div>

                  {/* RESULTADO DO SORTEIO CONFRONTADO (SE HOUVER) */}
                  {group.drawnNumbers && (
                    <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
                      <span className="text-xs text-slate-400 block mb-2 font-medium">Dezenas sorteadas no concurso atual:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {group.drawnNumbers.map(n => (
                          <span key={n} className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-300 font-bold text-xs flex items-center justify-center border border-emerald-500/40">
                            {String(n).padStart(2, '0')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* CARTÕES GERADOS */}
                  <div className="space-y-2">
                    {group.tickets.map((ticket, idx) => (
                      <div key={idx} className="bg-slate-900/80 p-3 rounded-lg flex items-center justify-between border border-slate-700/40 hover:border-slate-600 transition">
                        <div className="flex flex-wrap gap-1.5">
                          {ticket.numbers.map((num) => {
                            const isHit = group.drawnNumbers && group.drawnNumbers.includes(num);
                            return (
                              <span
                                key={num}
                                className={`w-8 h-8 rounded-lg font-bold text-xs flex items-center justify-center transition ${
                                  isHit
                                    ? 'bg-emerald-500 text-slate-950 font-extrabold shadow-md shadow-emerald-500/20'
                                    : 'bg-slate-800 text-slate-300 border border-slate-700'
                                }`}
                              >
                                {String(num).padStart(2, '0')}
                              </span>
                            );
                          })}
                        </div>

                        {ticket.hits !== null && ticket.hits !== undefined && (
                          <div className={`px-3 py-1 rounded-lg text-xs font-bold shrink-0 ml-4 ${
                            ticket.hits >= 11 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {ticket.hits} Acertos
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}