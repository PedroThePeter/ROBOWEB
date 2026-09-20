import React, { useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { Play, Target, TrendingUp, Award, BrainCircuit, Activity } from 'lucide-react';

export default function App() {
  const [isSimulating, setIsSimulating] = useState(false);
  const [resultados, setResultados] = useState(null);

  // Função para executar o backtest consumindo a API no Render
  const executarBacktest = async () => {
    setIsSimulating(true);
    
    try {
      const response = await fetch('https://roboweb-cvha.onrender.com/api/backtest');
      
      if (!response.ok) {
        throw new Error('Falha na resposta do servidor.');
      }

      const data = await response.json();
      setResultados(data);
    } catch (error) {
      console.error('Erro ao executar o backtest:', error);
      alert('Erro ao conectar com o servidor no Render. Verifique o console para mais detalhes.');
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 font-sans">
      
      {/* HEADER */}
      <div className="max-w-7xl mx-auto mb-8 flex justify-between items-center border-b border-slate-700 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-emerald-400 flex items-center gap-3">
            <BrainCircuit size={32} />
            Lotofácil Ensemble AI
          </h1>
          <p className="text-slate-400 mt-1">Walk-Forward Backtesting & 3º Curador</p>
        </div>
        <button 
          onClick={executarBacktest}
          disabled={isSimulating}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-all cursor-pointer disabled:cursor-not-allowed"
        >
          {isSimulating ? (
            <><Activity className="animate-spin" size={20} /> Processando 500 jogos...</>
          ) : (
            <><Play size={20} /> Executar Backtest</>
          )}
        </button>
      </div>

      {/* DASHBOARD BODY */}
      {resultados && (
        <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
          
          {/* CARDS DE DESTAQUE (MÉDIAS DE ACERTO) */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-800 p-6 rounded-xl border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
              <div className="flex items-center gap-3 text-emerald-400 mb-2">
                <Award size={24} />
                <h3 className="font-semibold">Bilhete Oficial (Ensemble)</h3>
              </div>
              <p className="text-4xl font-bold text-white">{resultados.medias.ensemble.toFixed(2)}</p>
              <p className="text-sm text-slate-400 mt-1">Acertos / jogo</p>
            </div>
            
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <h3 className="text-slate-400 font-semibold mb-2">IA Padrões</h3>
              <p className="text-3xl font-bold text-slate-200">{resultados.medias.padroes.toFixed(2)}</p>
              <p className="text-sm text-slate-500 mt-1">Acertos / jogo</p>
            </div>
            
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <h3 className="text-slate-400 font-semibold mb-2">IA Frequência</h3>
              <p className="text-3xl font-bold text-slate-200">{resultados.medias.frequencia.toFixed(2)}</p>
              <p className="text-sm text-slate-500 mt-1">Acertos / jogo</p>
            </div>

            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <h3 className="text-slate-400 font-semibold mb-2">IA Atrasos</h3>
              <p className="text-3xl font-bold text-slate-200">{resultados.medias.atrasos.toFixed(2)}</p>
              <p className="text-sm text-slate-500 mt-1">Acertos / jogo</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* GRÁFICO DE EVOLUÇÃO (PESOS) */}
            <div className="lg:col-span-2 bg-slate-800 p-6 rounded-xl border border-slate-700">
              <div className="flex items-center gap-2 mb-6">
                <TrendingUp className="text-emerald-400" size={24} />
                <h2 className="text-xl font-bold text-slate-100">Evolução do Voto de Confiança (Pesos)</h2>
              </div>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={resultados.historicoPesos}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="concurso" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                      itemStyle={{ color: '#f8fafc' }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="Padroes" name="Padrões" stroke="#34d399" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="Frequencia" name="Frequência" stroke="#60a5fa" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Atrasos" name="Atrasos" stroke="#f472b6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* PLACAR FINAL (PESOS CALIBRADOS PARA HOJE) */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex flex-col">
              <div className="flex items-center gap-2 mb-6">
                <Target className="text-emerald-400" size={24} />
                <h2 className="text-xl font-bold text-slate-100">Pesos Calibrados para o Próximo Jogo</h2>
              </div>
              
              <div className="flex-1 flex flex-col justify-center space-y-6">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-300 font-medium">Modelo de Padrões</span>
                    <span className="text-emerald-400 font-bold">{resultados.pesosFinais.padroes.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3">
                    <div className="bg-emerald-400 h-3 rounded-full" style={{ width: `${resultados.pesosFinais.padroes}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-300 font-medium">Modelo de Frequência</span>
                    <span className="text-blue-400 font-bold">{resultados.pesosFinais.frequencia.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3">
                    <div className="bg-blue-400 h-3 rounded-full" style={{ width: `${resultados.pesosFinais.frequencia}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-300 font-medium">Modelo de Atrasos</span>
                    <span className="text-pink-400 font-bold">{resultados.pesosFinais.atrasos.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3">
                    <div className="bg-pink-400 h-3 rounded-full" style={{ width: `${resultados.pesosFinais.atrasos}%` }}></div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-slate-900 rounded-lg border border-slate-700 text-sm text-slate-400 text-center">
                O 3º Curador usará esses pesos exatos para aplicar a votação ponderada no sorteio de hoje.
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}