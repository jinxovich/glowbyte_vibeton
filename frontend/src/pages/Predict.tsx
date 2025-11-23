import { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../lib/api';
import { 
  AlertTriangle, Calendar, Database, Thermometer, Wind, Loader2, 
  ArrowRight, Droplets, Gauge, Cloud, Eye, Navigation, Package,
  Clock, Flame
} from 'lucide-react';

export default function Predict() {
  const { register, handleSubmit, formState: { isSubmitting }, watch } = useForm({
    defaultValues: {
      storage_id: '11',
      stack_id: '11',
      pile_age_days: 30,
      stack_mass_tons: 5000,
      weather_temp: 15,
      weather_humidity: 50,
      wind_speed: 3,
      precipitation: 0,
      pressure: 1013,
      cloud_cover: 50,
      visibility: 10000,
      wind_speed_max: 5,
      wind_direction: 0
    }
  });
  const [result, setResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'basic' | 'weather' | 'advanced'>('basic');

  const onSubmit = async (data: any) => {
    try {
      const payload = {
        storage_id: data.storage_id,
        stack_id: data.stack_id,
        max_temperature: parseFloat(data.max_temperature),
        pile_age_days: parseInt(data.pile_age_days) || 30,
        stack_mass_tons: parseFloat(data.stack_mass_tons) || 5000,
        coal_grade: data.coal_grade || 'unknown',
        weather_temp: parseFloat(data.weather_temp) || 15,
        weather_humidity: parseFloat(data.weather_humidity) || 50,
        wind_speed: parseFloat(data.wind_speed) || 3,
        precipitation: parseFloat(data.precipitation) || 0,
        pressure: parseFloat(data.pressure) || 1013,
        cloud_cover: parseFloat(data.cloud_cover) || 50,
        visibility: parseFloat(data.visibility) || 10000,
        wind_speed_max: parseFloat(data.wind_speed_max) || 5,
        wind_direction: parseFloat(data.wind_direction) || 0,
        measurement_date: data.measurement_date,
        picket: data.picket || null,
        shift: data.shift || null,
        co_level_ppm: parseFloat(data.co_level_ppm) || 0,
        ash_content: parseFloat(data.ash_content) || 10,
        moisture_content: parseFloat(data.moisture_content) || 12
      };
      
      console.log('📤 Отправка данных:', payload);
      const res = await api.post('/predict/', payload);
      console.log('📥 Получен ответ:', res.data);
      setResult(res.data);
    } catch (err: any) {
      console.error('❌ Ошибка:', err);
      alert(`Ошибка: ${err.response?.data?.detail || err.message}`);
    }
  };

  const getRiskColor = (level: string) => {
    const colors: Record<string, string> = {
      'критический': 'bg-red-50 text-red-700 border-red-300',
      'высокий': 'bg-orange-50 text-orange-700 border-orange-300',
      'средний': 'bg-yellow-50 text-yellow-700 border-yellow-300',
      'низкий': 'bg-green-50 text-green-700 border-green-300',
      'минимальный': 'bg-slate-50 text-slate-700 border-slate-300',
    };
    return colors[level] || 'bg-green-50 text-green-700 border-green-200';
  };

  const getRiskPercentage = (level: string) => {
    const percentages: Record<string, number> = {
      'критический': 100,
      'высокий': 75,
      'средний': 50,
      'низкий': 30,
      'минимальный': 15
    };
    return percentages[level] || 30;
  };

  const currentTemp = watch('max_temperature');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in">
      <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-2xl font-bold text-slate-900">🔥 Новый прогноз возгорания</h2>
          <p className="text-slate-500 text-sm mt-1">Заполните данные для расчета риска самовозгорания угля</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-slate-100 bg-slate-50">
          <div className="flex">
            <button
              type="button"
              onClick={() => setActiveTab('basic')}
              className={`flex-1 px-6 py-3 font-medium text-sm transition ${
                activeTab === 'basic'
                  ? 'bg-white text-orange-600 border-b-2 border-orange-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              📊 Основные
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('weather')}
              className={`flex-1 px-6 py-3 font-medium text-sm transition ${
                activeTab === 'weather'
                  ? 'bg-white text-orange-600 border-b-2 border-orange-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              🌦️ Погода
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('advanced')}
              className={`flex-1 px-6 py-3 font-medium text-sm transition ${
                activeTab === 'advanced'
                  ? 'bg-white text-orange-600 border-b-2 border-orange-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              🔬 Доп. данные
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-8">
          {/* Основные поля */}
          {activeTab === 'basic' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Склад и штабель */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Database size={14}/> Склад
                  </label>
                  <input 
                    {...register('storage_id')} 
                    placeholder="11" 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all" 
                    required 
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Package size={14}/> Штабель
                  </label>
                  <input 
                    {...register('stack_id')} 
                    placeholder="11" 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all" 
                    required 
                  />
                </div>

                {/* Температура - самое важное поле */}
                <div className="md:col-span-2 space-y-2">
                  <label className="text-xs font-bold text-orange-600 uppercase flex gap-2 items-center">
                    <Thermometer size={16}/> Максимальная температура (°C) *
                  </label>
                  <div className="relative">
                    <input 
                      type="number" 
                      step="0.1" 
                      {...register('max_temperature')} 
                      className="w-full p-4 bg-orange-50 rounded-xl border-2 border-orange-200 focus:bg-white focus:ring-2 focus:ring-orange-500 focus:border-transparent font-mono text-2xl font-bold text-orange-700 transition-all" 
                      placeholder="45.5" 
                      required 
                    />
                    {currentTemp && parseFloat(currentTemp) > 50 && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        <Flame className="text-red-500 animate-pulse" size={24} />
                      </div>
                    )}
                  </div>
                  {currentTemp && parseFloat(currentTemp) > 60 && (
                    <p className="text-xs text-red-600 font-medium">⚠️ Критическая температура! Высокий риск возгорания</p>
                  )}
                </div>

                {/* Дата замера */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Calendar size={14}/> Дата замера
                  </label>
                  <input 
                    type="date" 
                    {...register('measurement_date')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                  />
                </div>

                {/* Возраст штабеля */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Clock size={14}/> Возраст штабеля (дней)
                  </label>
                  <input 
                    type="number" 
                    {...register('pile_age_days')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all" 
                    placeholder="30"
                  />
                </div>

                {/* Масса */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Package size={14}/> Масса (тонн)
                  </label>
                  <input 
                    type="number" 
                    {...register('stack_mass_tons')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all" 
                    placeholder="5000"
                  />
                </div>

                {/* Марка угля */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Database size={14}/> Марка угля
                  </label>
                  <input 
                    {...register('coal_grade')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all" 
                    placeholder="Не указана"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Погода */}
          {activeTab === 'weather' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Thermometer size={14}/> Температура воздуха (°C)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('weather_temp')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="15"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Droplets size={14}/> Влажность (%)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('weather_humidity')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="50"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Wind size={14}/> Ветер средний (м/с)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('wind_speed')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="3"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Wind size={14}/> Ветер макс. (м/с)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('wind_speed_max')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="5"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Navigation size={14}/> Направление ветра (°)
                  </label>
                  <input 
                    type="number" 
                    {...register('wind_direction')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="0-360"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Droplets size={14}/> Осадки (мм)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('precipitation')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="0"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Gauge size={14}/> Давление (гПа)
                  </label>
                  <input 
                    type="number" 
                    {...register('pressure')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="1013"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Cloud size={14}/> Облачность (%)
                  </label>
                  <input 
                    type="number" 
                    {...register('cloud_cover')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="50"
                  />
                </div>

                <div className="md:col-span-2 space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase flex gap-2 items-center">
                    <Eye size={14}/> Видимость (м)
                  </label>
                  <input 
                    type="number" 
                    {...register('visibility')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" 
                    placeholder="10000"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Дополнительные данные */}
          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase">
                    🎯 Пикет (место замера)
                  </label>
                  <input 
                    {...register('picket')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all" 
                    placeholder="Не указан"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase">
                    🕐 Смена
                  </label>
                  <input 
                    {...register('shift')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all" 
                    placeholder="Не указана"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase">
                    🧪 CO (ppm)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('co_level_ppm')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all" 
                    placeholder="0.0"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase">
                    🪨 Зольность (%)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('ash_content')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all" 
                    placeholder="10.0"
                  />
                </div>

                <div className="md:col-span-2 space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase">
                    💧 Влажность угля (%)
                  </label>
                  <input 
                    type="number" 
                    step="0.1" 
                    {...register('moisture_content')} 
                    className="w-full p-3 bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all" 
                    placeholder="12.0"
                  />
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <p className="text-sm text-blue-700">
                  ℹ️ <strong>Совет:</strong> Эти поля опциональны. Заполняйте их только если есть точные данные из лаборатории.
                </p>
              </div>
            </div>
          )}

          {/* Кнопка отправки */}
          <div className="mt-8">
            <button 
              type="submit"
              disabled={isSubmitting} 
              className="w-full bg-gradient-to-r from-orange-600 to-red-600 text-white font-bold py-4 rounded-xl hover:from-orange-700 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-3 shadow-lg hover:shadow-xl"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Анализ данных...
                </>
              ) : (
                <>
                  <Flame size={20} />
                  РАССЧИТАТЬ РИСК ВОЗГОРАНИЯ
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Результат */}
      <div className="lg:col-span-1">
        {result ? (
          <div className={`h-full rounded-2xl p-8 border-2 flex flex-col justify-between animate-in shadow-lg ${getRiskColor(result.risk_level)}`}>
            <div>
              <div className="flex items-center gap-3 mb-4 opacity-80">
                <AlertTriangle size={28} />
                <span className="font-bold uppercase text-sm tracking-wider">Прогноз</span>
              </div>
              <h3 className="text-5xl font-black mb-2">
                {result.predicted_ttf_days.toFixed(1)}
              </h3>
              <p className="text-lg font-medium opacity-90">дней до возгорания</p>
            </div>

            <div className="my-8 space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2 font-bold opacity-80">
                  <span>УРОВЕНЬ РИСКА</span>
                  <span className="uppercase">{result.risk_level}</span>
                </div>
                <div className="w-full bg-black/10 h-4 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-current transition-all duration-1000 ease-out" 
                    style={{ width: `${getRiskPercentage(result.risk_level)}%` }} 
                  />
                </div>
              </div>

              {result.warnings && result.warnings.length > 0 && (
                <div className="bg-white/60 backdrop-blur-sm rounded-lg p-3">
                  <p className="text-xs font-bold mb-2">⚠️ ПРЕДУПРЕЖДЕНИЯ:</p>
                  <ul className="text-xs space-y-1">
                    {result.warnings.map((warning: string, idx: number) => (
                      <li key={idx} className="opacity-90">• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div className="bg-white/40 backdrop-blur-sm rounded-xl p-4 flex justify-between items-center">
                <span className="text-sm font-bold">Уверенность модели</span>
                <span className="text-2xl font-mono font-bold">
                  {(result.confidence * 100).toFixed(0)}%
                </span>
              </div>
              
              <div className="bg-white/40 backdrop-blur-sm rounded-xl p-4">
                <div className="text-xs opacity-80 space-y-1">
                  <p><strong>ID:</strong> #{result.id}</p>
                  <p><strong>Склад/Штабель:</strong> {result.storage_id}/{result.stack_id}</p>
                  <p><strong>Дата:</strong> {new Date(result.created_at).toLocaleString('ru-RU')}</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl border-2 border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-400 p-8 text-center">
            <Flame size={64} className="mb-4 opacity-30" />
            <h3 className="font-bold text-slate-500 text-lg mb-2">Ожидание расчета</h3>
            <p className="text-sm">Заполните форму и нажмите кнопку</p>
          </div>
        )}
      </div>
    </div>
  );
}
