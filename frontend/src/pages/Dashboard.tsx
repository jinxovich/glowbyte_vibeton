import { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import { getDashboard } from '../lib/api';
import type { DashboardData } from '../types';
import { getRiskColor, formatDate } from '../lib/utils';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import PredictionForm from '../components/PredictionForm';

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const dashboardData = await getDashboard();
      setData(dashboardData);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card text-center">
        <p className="text-gray-500">Не удалось загрузить данные</p>
      </div>
    );
  }

  const kpiCards = [
    {
      title: 'Accuracy (±2 дня)',
      value: `${(data.metrics.accuracy_2days * 100).toFixed(1)}%`,
      subtitle: 'KPI: ≥70%',
      icon: CheckCircle2,
      color: data.metrics.kpi_achieved ? 'text-green-600 bg-green-100' : 'text-orange-500 bg-orange-100',
    },
    {
      title: 'MAE (дней)',
      value: data.metrics.mae.toFixed(2),
      subtitle: 'Средняя ошибка',
      icon: Clock,
      color: 'text-blue-600 bg-blue-100',
    },
    {
      title: 'Всего прогнозов',
      value: data.statistics.total_predictions.toString(),
      subtitle: 'Штабелей',
      icon: TrendingUp,
      color: 'text-purple-600 bg-purple-100',
    },
    {
      title: 'В зоне риска',
      value: data.statistics.at_risk_count.toString(),
      subtitle: 'Критично',
      icon: AlertTriangle,
      color: 'text-red-600 bg-red-100',
    },
  ];

  const chartData = Object.entries(data.statistics.risk_distribution).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = {
    'критический': '#dc2626',
    'высокий': '#f97316',
    'средний': '#facc15',
    'низкий': '#10b981',
    'минимальный': '#9ca3af',
  };

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div key={index} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${card.color}`}>
                  <Icon className="h-6 w-6" />
                </div>
              </div>
              <h3 className="text-sm font-medium text-gray-600">{card.title}</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{card.value}</p>
              <p className="text-xs text-gray-500 mt-1">{card.subtitle}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Prediction Form */}
        <div className="lg:col-span-2">
          <PredictionForm />
        </div>

        {/* Risk Distribution Chart */}
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Распределение рисков</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Upcoming Fires */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          <h3 className="text-lg font-bold text-gray-900">Ближайшие возгорания (7 дней)</h3>
        </div>

        {data.upcoming_fires.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Нет прогнозов на ближайшие 7 дней</p>
        ) : (
          <div className="space-y-3">
            {data.upcoming_fires.slice(0, 10).map((fire, index) => (
              <div
                key={index}
                className={`flex items-center justify-between p-4 rounded-lg border-l-4 ${
                  fire.risk_level === 'критический' ? 'border-red-600 bg-red-50' :
                  fire.risk_level === 'высокий' ? 'border-orange-500 bg-orange-50' :
                  'border-yellow-400 bg-yellow-50'
                } hover:shadow-md transition-shadow`}
              >
                <div>
                  <p className="font-semibold text-gray-900">
                    Склад {fire.storage_id}, Штабель {fire.stack_id}
                  </p>
                  <p className="text-sm text-gray-600">{formatDate(fire.date)}</p>
                </div>
                <div className="text-right">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskColor(fire.risk_level)}`}>
                    {fire.risk_level}
                  </span>
                  <p className="text-sm text-gray-600 mt-1">{fire.days_until} дн.</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

