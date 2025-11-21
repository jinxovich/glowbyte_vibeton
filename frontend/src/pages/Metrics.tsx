import { useState, useEffect } from 'react';
import { BarChart3, CheckCircle2, XCircle } from 'lucide-react';
import { getMetrics } from '../lib/api';
import type { Metrics as MetricsType } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function Metrics() {
  const [data, setData] = useState<MetricsType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const metricsData = await getMetrics();
      setData(metricsData);
    } catch (error) {
      console.error('Failed to load metrics:', error);
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
        <p className="text-gray-500">Нет данных о метриках. Обучите модель.</p>
      </div>
    );
  }

  const chartData = [
    { name: 'Accuracy ±2d', value: data.accuracy_2days * 100 },
    { name: 'MAE', value: data.mae },
    { name: 'RMSE', value: data.rmse },
  ];

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-red-100 rounded-lg">
            <BarChart3 className="h-6 w-6 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            Детальные метрики модели
          </h2>
        </div>

        {/* KPI Status */}
        <div className={`p-6 rounded-lg mb-6 ${
          data.kpi_achieved ? 'bg-green-50 border-2 border-green-500' : 'bg-yellow-50 border-2 border-yellow-500'
        }`}>
          <div className="flex items-center space-x-3">
            {data.kpi_achieved ? (
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            ) : (
              <XCircle className="h-8 w-8 text-yellow-600" />
            )}
            <div>
              <p className={`text-lg font-bold ${data.kpi_achieved ? 'text-green-900' : 'text-yellow-900'}`}>
                Статус KPI: {data.kpi_achieved ? 'Достигнут ✓' : 'Не достигнут'}
              </p>
              <p className={`text-sm ${data.kpi_achieved ? 'text-green-700' : 'text-yellow-700'}`}>
                Требуется точность {'>='} 70%, текущая: {(data.accuracy_2days * 100).toFixed(2)}%
              </p>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card bg-gradient-to-br from-green-50 to-green-100">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Accuracy (±2 дня)</h3>
            <p className="text-4xl font-bold text-green-700">
              {(data.accuracy_2days * 100).toFixed(2)}%
            </p>
            <p className="text-xs text-gray-600 mt-2">KPI: ≥70%</p>
          </div>

          <div className="card bg-gradient-to-br from-blue-50 to-blue-100">
            <h3 className="text-sm font-medium text-gray-600 mb-2">MAE (Mean Absolute Error)</h3>
            <p className="text-4xl font-bold text-blue-700">
              {data.mae.toFixed(2)}
            </p>
            <p className="text-xs text-gray-600 mt-2">дней</p>
          </div>

          <div className="card bg-gradient-to-br from-purple-50 to-purple-100">
            <h3 className="text-sm font-medium text-gray-600 mb-2">RMSE</h3>
            <p className="text-4xl font-bold text-purple-700">
              {data.rmse.toFixed(2)}
            </p>
            <p className="text-xs text-gray-600 mt-2">Root Mean Square Error</p>
          </div>
        </div>

        {/* Chart */}
        <div className="card bg-gray-50">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Визуализация метрик</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#dc2626" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Additional Info */}
        {data.trained_at && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              Модель обучена: {new Date(data.trained_at).toLocaleString('ru-RU')}
            </p>
          </div>
        )}

        {data.total_predictions && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              Всего предсказаний: {data.total_predictions}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

