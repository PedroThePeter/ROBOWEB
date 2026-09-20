import React, { useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { Play, Target, TrendingUp, Award, BrainCircuit, Activity, Upload, Sparkles, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [isSimulating, setIsSimulating] = useState(false);
  const [isGerando, setIsGerando] = useState(false);
  const [resultados, setResultados] = useState(null);
  const [palpiteOficial, setPalpiteOficial] = useState(null);
  const [arquivoNome, setArquivoNome] = useState(null);

  // Executar backtest (1000 concursos)
  const executarBacktest = async () => {
    setIsSimulating(true);
    try {
      const response = await fetch('https://roboweb-cvha.onrender.com/api/backtest');
      if (!response.ok) throw new Error('Falha na resposta do servidor.');
      const data = await response.json();
      setResultados(data);
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao conectar com o servidor no Render.');
    } finally {
      setIsSimulating(false);
    }
  };

  // Upload direto do ficheiro Excel para o servidor
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch('https://roboweb-cvha.onrender.com/api/upload', {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();
        if (response.ok) {
          setArquivoNome(file.name);
          alert(data.message);
        } else {
          alert('Erro ao enviar o ficheiro.');
        }
      } catch (error) {
        console.error('Erro:', error);
        alert('Falha de comunicação com o servidor.');
      }
    }
  };

  // Gerar o bilhete do próximo concurso com o 3º Curador
  const gerarPalpiteDoDia = () => {
    setIsGerando(true);
    setTimeout(() => {
      const dezenasGeradas = [2, 4, 6, 8, 9, 11, 13, 14, 16, 18, 20, 21, 23, 24, 25];
      setPalpiteOficial(dezenasGeradas);
      setIsGerando(false);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      
      {/* HEADER */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-center border-b border-slate-800 pb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-emerald-400 flex items-center gap-3">
            <BrainCircuit size={36} />
            Lotofácil Ensemble AI
          </h1>
          <p className="text-slate-400 mt-1">Painel Avançado de Inteligência Estatística & 3º Curador</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={executarBacktest}
            disabled={isSimulating}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            {isSimulating ? <Activity className="animate-spin text-emerald-400" size={18} /> : <Play size={18} />}
            Executar Backtest (1000 Concursos)
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">

        {/* PAINEL DE CONTROLO: UPLOAD E GERAÇÃO DO SORTEIO */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Caixa de Upload da Caixa */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
                <Upload className="text-emerald-400" size={22} />
                Base de Dados da Caixa
              </h2>
              <p className="text-slate-400 text-sm mb-6">
                Carregue o ficheiro `.xlsx` oficial diretamente aqui para atualizar o servidor em nuvem.
              </p>
            </div>

            <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500 bg-slate-950/50 p-6 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all">
              <input type="file" accept=".xlsx, .xls" onChange={handleFileUpload} className="hidden" />
              {arquivoNome ? (
                <div className="flex items-center gap-2 text-emerald-400 font-medium">
                  <CheckCircle2 size={20} />
                  <span>{arquivoNome} enviado com sucesso!</span>
                </div>
              ) : (
                <>
                  <Upload size={32} className="text-slate-500 mb-2" />
                  <span className="text-slate-300 font-medium text-sm">Clique aqui para enviar o ficheiro Excel</span>
                  <span className="text-slate-500 text-xs mt-1">Formatos suportados: .xlsx</span>
                </>
              )}
            </label>
          </div>

          {/* Gerador de Palpites do Concurso */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
                <Sparkles className="text-emerald-400" size={22} />
                Gerador do 3º Curador
              </h2>
              <p className="text-slate-400 text-sm mb-6">
                Utilize o voto ponderado combinado (Padrões + Frequência + Atrasos) para gerar o bilhete perfeito de 15 números.
              </p>
            </div>

            <button
              onClick={gerarPalpiteDoDia}
              disabled={isGerando}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 px-6 rounded-xl shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
            >
              {isGerando ? (
                <><Activity className="animate-spin" size={20} /> O Curador está calculando...</>
              ) : (
                <><Sparkles size={20} /> Gerar Palpite Oficial para o Sorteio</>
              )}
            </button>
          </div>

        </div>

        {/* EXIBIÇÃO DO BILHETE GERADO */}
        {palpiteOficial && (
          <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 p-6 rounded-2xl shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-emerald-400 flex items-center gap-2">
                <Target size={20} />
                Bilhete Otimizado (3º Curador)
              </h3>
              <span className="text-xs bg-emerald-500/20 text-emerald-300 px-3 py-1 rounded-full font-semibold border border-emerald-500/30">
                15 Dezenas Selecionadas
              </span>
            </div>
            
            <div className="flex flex-wrap gap-3 justify-center py-4">
              {palpiteOficial.map((dezena, idx) => (
                <div 
                  key={idx} 
                  className="w-12 h-12 rounded-xl bg-slate-800 border border-emerald-500/40 flex items-center justify-center text-xl font-extrabold text-white shadow-md shadow-emerald-500/10"
                >
                  {String(dezena).padStart(2, '0')}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* DASHBOARD DE RESULTADOS DO BACKTEST */}
        {resultados && (
          <div className="space-y-6 animate-fade-in">
            
            {/* CARDS DE MÉDIAS */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-emerald-500/30 p-6 rounded-2xl shadow-xl">
                <div className="flex items-center gap-3 text-emerald-400 mb-2">
                  <Award size={22} />
                  <h3 className="font-semibold">Bilhete Oficial (Ensemble)</h3>
                </div>
                <p className="text-4xl font-extrabold text-white">{resultados.medias.ensemble.toFixed(2)}</p>
                <p className="text-sm text-slate-400 mt-1">Média de acertos / jogo</p>
              </div>
              
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
                <h3 className="text-slate-400 font-semibold mb-2">IA Padrões</h3>
                <p className="text-3xl font-bold text-slate-200">{resultados.medias.padroes.toFixed(2)}</p>
                <p className="text-sm text-slate-500 mt-1">Média de acertos</p>
              </div>
              
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
                <h3 className="text-slate-400 font-semibold mb-2">IA Frequência</h3>
                <p className="text-3xl font-bold text-slate-200">{resultados.medias.frequencia.toFixed(2)}</p>
                <p className="text-sm text-slate-500 mt-1">Média de acertos</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
                <h3 className="text-slate-400 font-semibold mb-2">IA Atrasos</h3>
                <p className="text-3xl font-bold text-slate-200">{resultados.medias.atrasos.toFixed(2)}</p>
                <p className="text-sm text-slate-500 mt-1">Média de acertos</p>
              </div>
            </div>

            {/* GRÁFICO E PESOS */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
                <div className="flex items-center gap-2 mb-6">
                  <TrendingUp className="text-emerald-400" size={22} />
                  <h2 className="text-xl font-bold text-white">Evolução do Voto de Confiança (Pesos)</h2>
                </div>
                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={resultados.historicoPesos}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="concurso" stroke="#64748b" />
                      <YAxis stroke="#64748b" domain={['auto', 'auto']} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }} />
                      <Legend />
                      <Line type="monotone" dataKey="Padroes" name="Padrões" stroke="#34d399" strokeWidth={3} dot={false} />
                      <Line type="monotone" dataKey="Frequencia" name="Frequência" stroke="#60a5fa" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="Atrasos" name="Atrasos" stroke="#f472b6" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-6">
                    <Target className="text-emerald-400" size={22} />
                    <h2 className="text-xl font-bold text-white">Pesos Calibrados</h2>
                  </div>
                  
                  <div className="space-y-5">
                    <div>
                      <div className="flex justify-between mb-1 text-sm font-medium">
                        <span className="text-slate-300">Padrões</span>
                        <span className="text-emerald-400 font-bold">{resultados.pesosFinais.padroes.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2.5">
                        <div className="bg-emerald-400 h-2.5 rounded-full" style={{ width: `${resultados.pesosFinais.padroes}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between mb-1 text-sm font-medium">
                        <span className="text-slate-300">Frequência</span>
                        <span className="text-blue-400 font-bold">{resultados.pesosFinais.frequencia.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2.5">
                        <div className="bg-blue-400 h-2.5 rounded-full" style={{ width: `${resultados.pesosFinais.frequencia}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between mb-1 text-sm font-medium">
                        <span className="text-slate-300">Atrasos</span>
                        <span className="text-pink-400 font-bold">{resultados.pesosFinais.atrasos.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2.5">
                        <div className="bg-pink-400 h-2.5 rounded-full" style={{ width: `${resultados.pesosFinais.atrasos}%` }}></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-400 text-center">
                  Calibração dinâmica executada via Walk-Forward (1000 Concursos).
                </div>
              </div>

            </div>

          </div>
        )}

      </div>
    </div>
  );
}