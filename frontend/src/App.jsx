import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, BarChart2, Hash, Settings, Download } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const API_URL = 'http://localhost:8000/api';

const PRESETS = {
  megasena: { name: 'Mega-Sena', total: 6, range: 60 },
  lotofacil: { name: 'Lotofácil', total: 15, range: 25 },
  quina: { name: 'Quina', total: 5, range: 80 },
  lotomania: { name: 'Lotomania', total: 20, range: 100 }
};

export default function App() {
  const [session, setSession] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('stats');
  
  const [config, setConfig] = useState(PRESETS.megasena);
  const [ticketCount, setTicketCount] = useState(5);
  const [tickets, setTickets] = useState([]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      setSession(res.data.session_id);
      fetchStats(res.data.session_id);
    } catch (err) {
      alert("Erro no upload do arquivo");
      setLoading(false);
    }
  };

  const fetchStats = async (sessionId) => {
    try {
      const res = await axios.get(`${API_URL}/stats/${sessionId}`);
      setStats(res.data);
    } catch (err) {
      alert("Erro ao buscar estatísticas");
    }
    setLoading(false);
  };

  const generateTickets = async () => {
    if (!session) return alert("Faça upload de uma planilha primeiro!");
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/generate-tickets`, {
        session_id: session,
        total_numbers: Number(config.total),
        number_range: Number(config.range),
        ticket_count: Number(ticketCount),
        fixed_numbers: [],
        excluded_numbers: []
      });
      setTickets(res.data.tickets);
      setActiveTab('generator');
    } catch (err) {
      alert("Erro ao gerar palpites");
    }
    setLoading(false);
  };

  const exportTxt = () => {
    const text = tickets.map(t => t.numeros.join(' - ')).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'palpites_otimizados.txt';
    a.click();
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 font-sans">
      {/* SIDEBAR */}
      <aside className="w-80 bg-gray-800 p-6 flex flex-col gap-6 border-r border-gray-700 overflow-y-auto">
        <h1 className="text-2xl font-bold flex items-center gap-2 text-indigo-400">
          <Hash /> LottoAI Analytics
        </h1>

        <div className="space-y-2">
          <label className="text-sm text-gray-400 font-semibold uppercase">Dados Base (Excel)</label>
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-600 border-dashed rounded-lg cursor-pointer hover:bg-gray-700 transition">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <UploadCloud className="w-8 h-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-400">Arraste ou clique .xlsx</p>
            </div>
            <input type="file" className="hidden" accept=".xlsx" onChange={handleUpload} />
          </label>
          {session && <p className="text-xs text-green-400">Sessão ativa: Planilha carregada</p>}
        </div>

        <div className="space-y-4">
          <label className="text-sm text-gray-400 font-semibold uppercase flex items-center gap-2">
            <Settings size={16}/> Configurações
          </label>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(PRESETS).map(([key, pre]) => (
              <button 
                key={key}
                onClick={() => setConfig(pre)}
                className={`p-2 text-sm rounded ${config.name === pre.name ? 'bg-indigo-600' : 'bg-gray-700 hover:bg-gray-600'}`}
              >
                {pre.name}
              </button>
            ))}
          </div>
          
          <div className="space-y-2">
            <label className="text-xs text-gray-400">Dezenas por Cartão</label>
            <input type="number" value={config.total} onChange={e => setConfig({...config, total: e.target.value})} className="w-full bg-gray-700 p-2 rounded text-white border border-gray-600" />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-gray-400">Universo (Ex: 1 a 60)</label>
            <input type="number" value={config.range} onChange={e => setConfig({...config, range: e.target.value})} className="w-full bg-gray-700 p-2 rounded text-white border border-gray-600" />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-gray-400">Qtd de Cartões a Gerar</label>
            <input type="number" value={ticketCount} onChange={e => setTicketCount(e.target.value)} className="w-full bg-gray-700 p-2 rounded text-white border border-gray-600" />
          </div>
        </div>

        <button onClick={generateTickets} disabled={!session || loading} className="w-full bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-3 px-4 rounded transition disabled:opacity-50">
          {loading ? 'Processando...' : 'Gerar Palpites'}
        </button>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <header className="flex border-b border-gray-700 bg-gray-800">
          <button onClick={() => setActiveTab('stats')} className={`px-6 py-4 flex items-center gap-2 ${activeTab === 'stats' ? 'border-b-2 border-indigo-400 text-indigo-400' : 'text-gray-400'}`}>
            <BarChart2 size={18}/> Visão Geral e Gráficos
          </button>
          <button onClick={() => setActiveTab('generator')} className={`px-6 py-4 flex items-center gap-2 ${activeTab === 'generator' ? 'border-b-2 border-indigo-400 text-indigo-400' : 'text-gray-400'}`}>
            <Hash size={18}/> Palpites Gerados
          </button>
        </header>

        <div className="p-8 overflow-y-auto flex-1">
          {!stats && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <UploadCloud size={64} className="mb-4 opacity-50"/>
              <p>Faça o upload do histórico de sorteios para começar.</p>
            </div>
          )}

          {stats && activeTab === 'stats' && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-6">
                 <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                   <p className="text-gray-400 text-sm">Média de Pares / Ímpares</p>
                   <p className="text-2xl font-bold mt-2">{stats.par_impar.media_pares.toFixed(1)} / {stats.par_impar.media_impares.toFixed(1)}</p>
                 </div>
                 <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                   <p className="text-gray-400 text-sm">Soma Histórica (Média)</p>
                   <p className="text-2xl font-bold mt-2">{stats.soma.media.toFixed(0)} <span className="text-sm text-gray-500">±{stats.soma.desvio_padrao.toFixed(0)}</span></p>
                 </div>
                 <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                   <p className="text-gray-400 text-sm">Par Mais Frequente</p>
                   <p className="text-2xl font-bold mt-2">{stats.top_pares[0]?.par}</p>
                 </div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 h-96">
                <h3 className="text-lg font-bold mb-4 text-indigo-400">Dezenas Mais Frequentes</h3>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={Object.entries(stats.frequencias).slice(0, 15).map(([k,v]) => ({name: k, total: v}))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip cursor={{fill: '#374151'}} contentStyle={{backgroundColor: '#1F2937', border: 'none', borderRadius: '8px'}} />
                    <Bar dataKey="total" fill="#6366F1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {activeTab === 'generator' && tickets.length > 0 && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Otimização Concluída</h2>
                <button onClick={exportTxt} className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded flex items-center gap-2 transition">
                  <Download size={18}/> Exportar TXT
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tickets.map((t, idx) => (
                  <div key={idx} className="bg-gray-800 p-6 rounded-lg border border-gray-700 relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-indigo-500/20 text-indigo-300 text-xs px-3 py-1 rounded-bl-lg">
                      Score: {t.score_confianca}%
                    </div>
                    <div className="flex flex-wrap gap-2 mt-4">
                      {t.numeros.map(n => (
                        <span key={n} className="w-10 h-10 flex items-center justify-center bg-gray-700 border-2 border-gray-600 rounded-full font-bold text-lg text-white">
                          {n.toString().padStart(2, '0')}
                        </span>
                      ))}
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between text-xs text-gray-400">
                      <span>Soma: {t.soma}</span>
                      <span>Par/Ímpar: {t.pares}/{t.impares}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}