import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import api from '../lib/api';
import { AlertTriangle, CheckCircle, Thermometer } from 'lucide-react';

export default function Dashboard() {
  const [history, setHistory] = useState<any[]>([]);
  const [stats, setStats] = useState({ total: 0, critical: 0, safe: 0 });

  useEffect(() => {
    api.get('/predict/history').then((res) => {
      const data = res.data;
      const chartData = [...data].reverse().slice(0, 30); 
      setHistory(chartData);
      const crit = data.filter((i: any) => ['критический', 'высокий'].includes(i.risk_level)).length;
      setStats({ total: data.length, critical: crit, safe: data.length - crit });
    });
  }, []);

  return (
    <div className="space-y-8 animate-in">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Обзор ситуации</h1>
          <p className="text-slate-500 mt-1">Мониторинг угольных штабелей в реальном времени</p>
        </div>
        <div className="text-sm text-slate-400 bg-white px-4 py-2 rounded-lg shadow-sm hidden sm:block">
          Обновлено: {new Date().toLocaleTimeString()}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-xl text-blue-600"><Thermometer size={32} /></div>
          <div><p className="text-slate-500 text-sm font-medium">Прогнозов</p><p className="text-3xl font-bold text-slate-900">{stats.total}</p></div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-red-100 rounded-xl text-red-600"><AlertTriangle size={32} /></div>
          <div><p className="text-slate-500 text-sm font-medium">Риск возгорания</p><p className="text-3xl font-bold text-red-600">{stats.critical}</p></div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-xl text-green-600"><CheckCircle size={32} /></div>
          <div><p className="text-slate-500 text-sm font-medium">Безопасно</p><p className="text-3xl font-bold text-green-600">{stats.safe}</p></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[400px]">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Динамика прогнозов (дни до пожара)</h3>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="storage_id" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              <Line type="monotone" dataKey="predicted_ttf_days" stroke="#ea580c" strokeWidth={3} dot={{ r: 4, fill: '#ea580c', stroke: '#fff' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[400px]">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Уверенность модели (%)</h3>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={history}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="storage_id" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
              <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              <Bar dataKey="confidence" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}