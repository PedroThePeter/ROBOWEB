import React, { useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  Play, Target, Award, BrainCircuit, Activity, Upload, Sparkles, CheckCircle2, ShieldAlert, Scale 
} from 'lucide-react';

export default function App() {
  const [isSimulating, setIsSimulating] = useState(false);
  const [isGerando, setIsGerando] = useState(false);
  const [resultados, setResultados] = useState(null);
  const [palpites, setPalpites] = useState(null);
  const [arquivoNome, setArquivoNome] = useState(null);

  // URL Oficial do teu Backend no Render (AGORA ONLINE!)
  const API_URL = 'https://roboweb-cvha.onrender.com';

  // Executa o backtest conectando ao Render
  const executarBacktest = async () => {
    setIsSimulating(true);
    try {
      const response = await fetch(`${API_URL}/api/backtest`);
      if (!response.ok) throw new Error('Falha na resposta do servidor.');
      const data = await response.json();
      setResultados(data);
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao conectar com o servidor no Render. Verifica se o backend está a rodar e não adormeceu.');
    } finally {
      setIsSimulating(false);
    }
  };

  // Faz o upload da base de dados Excel para o Render
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

  // Simula a geração dos 3 bilhetes através dos Curadores
  const gerarPalpiteDoDia = () => {
    setIsGerando(true);
    setTimeout(() => {
      setPalpites({
        curador1: [1, 2, 4, 5, 8, 9, 11, 13, 14, 18, 20, 21, 22, 24, 25],
        curador2: [2, 3, 4, 6, 8, 9, 10, 13, 15, 17, 19, 20, 23, 24, 25],
        curador3: [1, 3, 4, 7, 8, 10, 11, 13, 14, 17, 18, 20, 22, 24, 25] // O recomendado
      });
      setIsGerando(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      
      {/* HEADER PRINCIPAL */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-center border-b border-slate-800 pb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-emerald-400 flex items-center gap-3">
            <BrainCircuit size={36} /> Lotofácil Master AI
          </h1>
          <p className="text-slate-400 mt-1">Ensemble de 5 Juízes & 3 Curadores Simultâneos</p>
        </div>
        <button 
          onClick={executarBacktest} 
          disabled={isSimulating} 
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all disabled:opacity-50"
        >
          {isSimulating ? <Activity className="animate-spin text-emerald-400" size={18} /> : <Play size={18} />}
          Executar Backtest Global
        </button>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* PAINEL DE CONTROLO SUPERIOR */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Caixa de Upload */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
                <Upload className="text-emerald-400" size={22} /> Base de Dados Oficial
              </h2>
              <p className="text-slate-400 text-sm mb-6">Carregue o ficheiro `.xlsx` atualizado para treinar os 5 Juízes.</p>
            </div>
            <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500 bg-slate-950/50 p-6 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-colors">
              <input type="file" accept=".xlsx, .xls" onChange={handleFileUpload} className="hidden" />
              {arquivoNome ? (
                <div className="text-emerald-400 flex items-center gap-2 font-medium">
                  <CheckCircle2 size={20} /> {arquivoNome} sincronizado!
                </div>
              ) : (
                <>
                  <Upload size={32} className="text-slate-500 mb-2" />
                  <span className="text-slate-300 font-medium text-sm">Clique para enviar Excel</span>
                </>
              )}
            </label>
          </div>

          {/* Botão Gerador */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
                <Sparkles className="text-emerald-400" size={22} /> Gerador de Consenso
              </h2>
              <p className="text-slate-400 text-sm mb-6">Inicia a câmara de avaliação. Os 3 Curadores vão processar os dados dos 5 Juízes e emitir os bilhetes finais.</p>
            </div>
            <button 
              onClick={gerarPalpiteDoDia} 
              disabled={isGerando} 
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {isGerando ? <><Activity className="animate-spin" size={20} /> Processando 5 modelos...</> : <><Target size={20} /> Gerar Bilhetes dos Curadores</>}
            </button>
          </div>
        </div>

        {/* ÁREA DE EXIBIÇÃO DOS BILHETES GERADOS */}
        {palpites && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in">
            {/* Curador 1 */}
            <div className="bg-slate-900 border border-slate-700 p-5 rounded-2xl">
              <h3 className="text-lg font-bold text-slate-300 flex items-center gap-2 mb-4">
                <Scale size={18}/> 1º Curador (Voto Simples)
              </h3>
              <div className="flex flex-wrap gap-2 justify-center">
                {palpites.curador1.map(d => (
                  <div key={d} className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-sm font-bold text-slate-300 border border-slate-700">
                    {String(d).padStart(2,'0')}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Curador 2 */}
            <div className="bg-slate-900 border border-blue-500/30 p-5 rounded-2xl shadow-[0_0_15px_rgba(59,130,246,0.1)]">
              <h3 className="text-lg font-bold text-blue-400 flex items-center gap-2 mb-4">
                <ShieldAlert size={18}/> 2º Curador (Pesos Históricos)
              </h3>
              <div className="flex flex-wrap gap-2 justify-center">
                {palpites.curador2.map(d => (
                  <div key={d} className="w-10 h-10 rounded-lg bg-blue-950/50 border border-blue-800/50 flex items-center justify-center text-sm font-bold text-blue-300">
                    {String(d).padStart(2,'0')}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Curador 3 */}
            <div className="bg-gradient-to-br from-slate-900 to-emerald-950 border border-emerald-500/50 p-5 rounded-2xl shadow-[0_0_20px_rgba(16,185,129,0.15)] relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-emerald-500 text-xs text-white px-3 py-1 rounded-bl-lg font-bold">RECOMENDADO</div>
              <h3 className="text-lg font-bold text-emerald-400 flex items-center gap-2 mb-4">
                <Award size={18}/> 3º Curador (Assimétrico)
              </h3>
              <div className="flex flex-wrap gap-2 justify-center">
                {palpites.curador3.map(d => (
                  <div key={d} className="w-10 h-10 rounded-lg bg-emerald-900/80 border border-emerald-500/50 flex items-center justify-center text-sm font-bold text-white shadow-md shadow-emerald-900/50">
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
               <div className="bg-slate-900 border border-slate-700 p-6 rounded-2xl text-center">
                  <p className="text-slate-400 font-semibold mb-1">Média 1º Curador</p>
                  <p className="text-3xl font-bold text-white">{resultados.medias.curador1.toFixed(2)}</p>
                  <p className="text-xs text-slate-500 mt-2">Voto igualitário</p>
               </div>
               <div className="bg-slate-900 border border-blue-500/30 p-6 rounded-2xl text-center">
                  <p className="text-blue-400 font-semibold mb-1">Média 2º Curador</p>
                  <p className="text-4xl font-bold text-blue-300">{resultados.medias.curador2.toFixed(2)}</p>
                  <p className="text-xs text-blue-500/70 mt-2">Ponderado histórico</p>
               </div>
               <div className="bg-slate-900 border border-emerald-500/50 p-6 rounded-2xl text-center shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                  <p className="text-emerald-400 font-bold mb-1">Média 3º Curador (Líder)</p>
                  <p className="text-5xl font-extrabold text-emerald-400">{resultados.medias.curador3.toFixed(2)}</p>
                  <p className="text-xs text-emerald-500/70 mt-2">Calibração Assimétrica</p>
               </div>
            </div>

            {/* Desempenho dos 5 Juízes */}
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
              <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2">
                <BrainCircuit size={16}/> Desempenho Individual dos 5 Juízes
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[
                  { nome: 'Padrões', val: resultados.medias.padroes, color: 'text-emerald-400' },
                  { nome: 'Frequência', val: resultados.medias.frequencia, color: 'text-blue-400' },
                  { nome: 'Atrasos', val: resultados.medias.atrasos, color: 'text-pink-400' },
                  { nome: 'Repetição (Ant)', val: resultados.medias.repeticao, color: 'text-amber-400' },
                  { nome: 'Moldura/Miolo', val: resultados.medias.moldura, color: 'text-purple-400' }
                ].map(juiz => (
                  <div key={juiz.nome} className="bg-slate-950 border border-slate-800 p-4 rounded-xl text-center flex flex-col justify-center items-center">
                    <p className="text-xs text-slate-400 mb-1">{juiz.nome}</p>
                    <p className={`text-xl font-bold ${juiz.color}`}>{juiz.val.toFixed(2)}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* GRÁFICO DA EVOLUÇÃO DOS 5 JUÍZES */}
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl mt-6">
              <h2 className="text-xl font-bold text-white mb-6">Batalha de Pesos (Ajuste Dinâmico do 3º Curador)</h2>
              <div className="h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={resultados.historicoPesos}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="concurso" stroke="#64748b" />
                    <YAxis stroke="#64748b" domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }} />
                    <Legend />
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