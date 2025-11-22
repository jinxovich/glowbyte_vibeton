import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import api from '../lib/api';
import { AlertTriangle, CheckCircle, Thermometer, Clock } from 'lucide-react';

interface Prediction {
  id: number;
  storage_id: string;
  stack_id: string;
  predicted_days: number;
  risk_level: string;
  confidence: number;
  created_at: string;
  input_data?: any;
}

export default function Dashboard() {
  const [allPredictions, setAllPredictions] = useState<Prediction[]>([]);
  const [stats, setStats] = useState({ 
    total: 0, 
    critical: 0, 
    safe: 0,
    avg_confidence: 0
  });
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadDashboard();
    
    // Автообновление каждые 5 секунд
    const interval = setInterval(() => {
      loadDashboard();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboard = async () => {
    try {
      console.log('🔄 Загрузка дашборда...');
      const res = await api.get('/predict/dashboard');
      const data = res.data;
      
      console.log('📊 Получены данные:', {
        total: data.total_predictions,
        critical: data.critical_count,
        predictions_count: data.all_predictions?.length
      });
      
      setAllPredictions(data.all_predictions || []);
      setStats({
        total: data.total_predictions || 0,
        critical: data.critical_count || 0,
        safe: (data.total_predictions || 0) - (data.critical_count || 0),
        avg_confidence: data.avg_confidence || 0
      });
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('❌ Ошибка загрузки дашборда:', error);
      setLoading(false);
    }
  };

  const getRiskColor = (risk: string) => {
    const colors: Record<string, string> = {
      'критический': 'bg-red-100 text-red-700 border-red-200',
      'высокий': 'bg-orange-100 text-orange-700 border-orange-200',
      'средний': 'bg-yellow-100 text-yellow-700 border-yellow-200',
      'низкий': 'bg-green-100 text-green-700 border-green-200',
      'минимальный': 'bg-gray-100 text-gray-700 border-gray-200',
    };
    return colors[risk] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return <div className="flex items-center justify-center h-96">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
    </div>;
  }

  return (
    <div className="space-y-8 animate-in">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">📊 Дашборд прогнозов</h1>
          <p className="text-slate-500 mt-1">Мониторинг всех замеров и предсказаний (автообновление каждые 5 сек)</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <button 
            onClick={loadDashboard}
            className="text-sm text-orange-600 bg-white px-4 py-2 rounded-lg shadow-sm hover:bg-orange-50 transition flex items-center gap-2"
          >
            <Clock size={16} /> Обновить
          </button>
          <span className="text-xs text-slate-400">
            Обновлено: {lastUpdate.toLocaleTimeString('ru-RU')}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-xl text-blue-600"><Thermometer size={32} /></div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Всего замеров</p>
            <p className="text-3xl font-bold text-slate-900">{stats.total}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-red-100 rounded-xl text-red-600"><AlertTriangle size={32} /></div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Критических</p>
            <p className="text-3xl font-bold text-red-600">{stats.critical}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-xl text-green-600"><CheckCircle size={32} /></div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Безопасных</p>
            <p className="text-3xl font-bold text-green-600">{stats.safe}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-purple-100 rounded-xl text-purple-600"><CheckCircle size={32} /></div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Сред. уверенность</p>
            <p className="text-3xl font-bold text-purple-600">{stats.avg_confidence}%</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[400px]">
          <h3 className="text-lg font-bold text-slate-800 mb-6">📈 Динамика прогнозов</h3>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={allPredictions.slice(0, 30).reverse()}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="id" tick={{fill: '#94a3b8', fontSize: 12}} axisLine={false} tickLine={false} />
              <YAxis tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} label={{ value: 'Дни', angle: -90, position: 'insideLeft' }} />
              <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              <Line type="monotone" dataKey="predicted_days" stroke="#ea580c" strokeWidth={3} dot={{ r: 4, fill: '#ea580c', stroke: '#fff' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[400px]">
          <h3 className="text-lg font-bold text-slate-800 mb-6">🎯 Уверенность модели</h3>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={allPredictions.slice(0, 30).reverse()}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="id" tick={{fill: '#94a3b8', fontSize: 12}} axisLine={false} tickLine={false} />
              <YAxis tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} label={{ value: '%', angle: -90, position: 'insideLeft' }} />
              <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              <Bar dataKey="confidence" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Таблица всех замеров */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h3 className="text-lg font-bold text-slate-800">📋 Все замеры ({allPredictions.length})</h3>
          <p className="text-sm text-slate-500 mt-1">История всех предсказаний</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Склад</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Штабель</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Прогноз</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Риск</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Уверенность</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Дата</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {allPredictions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    Нет замеров. Сделайте первый прогноз!
                  </td>
                </tr>
              ) : (
                allPredictions.map((pred) => (
                  <tr key={pred.id} className="hover:bg-slate-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">#{pred.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{pred.storage_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{pred.stack_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-orange-600">{pred.predicted_days} дней</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getRiskColor(pred.risk_level)}`}>
                        {pred.risk_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-slate-700">{pred.confidence}%</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                      {new Date(pred.created_at).toLocaleString('ru-RU', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}