import { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../lib/api';
import { AlertTriangle, Calendar, Database, Thermometer, Wind, Loader2, ArrowRight } from 'lucide-react';

export default function Predict() {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm();
  const [result, setResult] = useState<any>(null);

  const onSubmit = async (data: any) => {
    try {
      const res = await api.post('/predict/', {
        ...data,
        max_temperature: parseFloat(data.max_temperature),
        weather_temp: parseFloat(data.weather_temp || 0),
        weather_humidity: parseFloat(data.weather_humidity || 0),
        wind_speed_avg: parseFloat(data.wind_speed_avg || 0),
      });
      setResult(res.data);
    } catch (err) {
      alert('Ошибка при прогнозе. Проверьте корректность данных.');
    }
  };

  const getRiskColor = (level: string) => {
    if (['критический', 'высокий'].includes(level)) return 'bg-red-50 text-red-700 border-red-200';
    if (level === 'средний') return 'bg-yellow-50 text-yellow-700 border-yellow-200';
    return 'bg-green-50 text-green-700 border-green-200';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in">
      <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-xl font-bold text-slate-900">Новый прогноз</h2>
          <p className="text-slate-500 text-sm">Введите данные датчиков</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase flex gap-2"><Database size={14}/> Склад / Штабель</label>
              <div className="flex gap-2">
                <input {...register('storage_id')} placeholder="ID Склада" className="w-full p-3 bg-slate-50 rounded-xl focus:bg-white focus:ring-2 focus:ring-orange-500 transition-all" required />
                <input {...register('stack_id')} placeholder="ID Штабеля" className="w-full p-3 bg-slate-50 rounded-xl focus:bg-white focus:ring-2 focus:ring-orange-500 transition-all" required />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase flex gap-2"><Calendar size={14}/> Дата замера</label>
              <input type="date" {...register('measurement_date')} className="w-full p-3 bg-slate-50 rounded-xl focus:bg-white focus:ring-2 focus:ring-orange-500 transition-all" required />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase flex gap-2"><Thermometer size={14}/> Температура (°C)</label>
              <input type="number" step="0.1" {...register('max_temperature')} className="w-full p-3 bg-slate-50 rounded-xl focus:bg-white focus:ring-2 focus:ring-orange-500 font-mono text-lg" placeholder="45.5" required />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase flex gap-2"><Wind size={14}/> Погода (опц.)</label>
              <div className="grid grid-cols-3 gap-2">
                <input type="number" step="0.1" {...register('weather_temp')} placeholder="T°C" className="w-full p-3 bg-slate-50 rounded-xl text-sm" />
                <input type="number" step="0.1" {...register('weather_humidity')} placeholder="Влаж" className="w-full p-3 bg-slate-50 rounded-xl text-sm" />
                <input type="number" step="0.1" {...register('wind_speed_avg')} placeholder="Ветер" className="w-full p-3 bg-slate-50 rounded-xl text-sm" />
              </div>
            </div>
          </div>
          <button disabled={isSubmitting} className="w-full bg-slate-900 text-white font-bold py-4 rounded-xl hover:bg-orange-600 transition-all flex items-center justify-center gap-3 shadow-xl">
            {isSubmitting ? <Loader2 className="animate-spin" /> : <ArrowRight />} РАССЧИТАТЬ РИСК
          </button>
        </form>
      </div>

      <div className="lg:col-span-1">
        {result ? (
          <div className={`h-full rounded-2xl p-8 border-2 flex flex-col justify-between animate-in ${getRiskColor(result.risk_level)}`}>
            <div>
              <div className="flex items-center gap-3 mb-2 opacity-80"><AlertTriangle size={24} /><span className="font-bold uppercase text-sm">Результат</span></div>
              <h3 className="text-4xl font-black mb-1">{result.predicted_ttf_days.toFixed(1)} Дней</h3>
              <p className="text-sm opacity-75">До самовозгорания</p>
            </div>
            <div className="my-8">
              <div className="flex justify-between text-sm mb-2 font-bold opacity-80"><span>РИСК</span><span className="uppercase">{result.risk_level}</span></div>
              <div className="w-full bg-black/10 h-4 rounded-full overflow-hidden">
                <div className="h-full bg-current transition-all duration-1000" style={{ width: result.risk_level === 'критический' ? '100%' : result.risk_level === 'высокий' ? '75%' : '40%' }} />
              </div>
            </div>
            <div className="bg-white/40 backdrop-blur-sm rounded-xl p-4 flex justify-between items-center">
              <span className="text-sm font-bold">Уверенность</span><span className="text-xl font-mono font-bold">{(result.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        ) : (
          <div className="h-full bg-slate-100 rounded-2xl border-2 border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-400 p-8 text-center">
            <Database size={48} className="mb-4 opacity-50" />
            <h3 className="font-bold text-slate-500">Ожидание данных</h3>
          </div>
        )}
      </div>
    </div>
  );
}