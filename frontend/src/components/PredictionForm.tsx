import { useState } from 'react';
import type { FormEvent } from 'react';
import { Calculator, ChevronDown, ChevronUp } from 'lucide-react';
import { predict } from '../lib/api';
import type { PredictionRequest, PredictionResponse } from '../types';
import { getRiskColor, formatDate } from '../lib/utils';

export default function PredictionForm() {
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<PredictionRequest>({
    storage_id: '3',
    stack_id: '21',
    measurement_date: new Date().toISOString().slice(0, 16),
    max_temperature: 45.5,
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const results = await predict([formData]);
      setResult(results[0]);
    } catch (err) {
      setError('Ошибка при выполнении прогноза. Убедитесь что модель обучена.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-red-100 rounded-lg">
            <Calculator className="h-6 w-6 text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Сделать прогноз</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Склад
              </label>
              <input
                type="text"
                className="input"
                value={formData.storage_id}
                onChange={(e) => setFormData({ ...formData, storage_id: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Штабель
              </label>
              <input
                type="text"
                className="input"
                value={formData.stack_id}
                onChange={(e) => setFormData({ ...formData, stack_id: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Максимальная температура (°C)
              </label>
              <input
                type="number"
                step="0.1"
                className="input"
                value={formData.max_temperature}
                onChange={(e) => setFormData({ ...formData, max_temperature: parseFloat(e.target.value) })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Дата измерения
              </label>
              <input
                type="datetime-local"
                className="input"
                value={formData.measurement_date}
                onChange={(e) => setFormData({ ...formData, measurement_date: e.target.value })}
                required
              />
            </div>
          </div>

          {/* Advanced Options */}
          <div className="border-t border-gray-200 pt-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900"
            >
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              <span>Дополнительные параметры</span>
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Возраст штабеля (дни)
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={formData.pile_age_days || ''}
                    onChange={(e) => setFormData({ ...formData, pile_age_days: e.target.value ? parseInt(e.target.value) : undefined })}
                    placeholder="30"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Масса (тонн)
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={formData.stack_mass_tons || ''}
                    onChange={(e) => setFormData({ ...formData, stack_mass_tons: e.target.value ? parseFloat(e.target.value) : undefined })}
                    placeholder="5000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Влажность (%)
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={formData.weather_humidity || ''}
                    onChange={(e) => setFormData({ ...formData, weather_humidity: e.target.value ? parseFloat(e.target.value) : undefined })}
                    placeholder="60"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Температура воздуха (°C)
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={formData.weather_temp || ''}
                    onChange={(e) => setFormData({ ...formData, weather_temp: e.target.value ? parseFloat(e.target.value) : undefined })}
                    placeholder="20"
                  />
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Расчет...' : 'Рассчитать прогноз'}
          </button>
        </form>
      </div>

      {/* Result */}
      {result && (
        <div className="card border-l-4 border-red-600 bg-gradient-to-r from-red-50 to-white">
          <h3 className="text-lg font-bold text-gray-900 mb-4">✅ Прогноз выполнен</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-200">
              <span className="text-sm text-gray-600">Склад / Штабель:</span>
              <span className="font-semibold text-gray-900">
                {result.storage_id} / {result.stack_id}
              </span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-gray-200">
              <span className="text-sm text-gray-600">Дней до возгорания:</span>
              <span className="font-bold text-2xl text-red-600">
                {result.predicted_ttf_days.toFixed(1)}
              </span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-gray-200">
              <span className="text-sm text-gray-600">Прогнозируемая дата:</span>
              <span className="font-semibold text-gray-900">
                {formatDate(result.predicted_combustion_date)}
              </span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-gray-200">
              <span className="text-sm text-gray-600">Уровень риска:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(result.risk_level)}`}>
                {result.risk_level}
              </span>
            </div>

            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-600">Уверенность:</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-600 h-2 rounded-full"
                    style={{ width: `${result.confidence * 100}%` }}
                  />
                </div>
                <span className="font-semibold text-gray-900">
                  {(result.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card bg-red-50 border-l-4 border-red-600">
          <p className="text-red-800">{error}</p>
        </div>
      )}
    </div>
  );
}

