import { useState } from 'react';
import { Settings, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { trainModel } from '../lib/api';

export default function Train() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrain = async () => {
    if (!confirm('Запустить обучение модели? Это может занять несколько минут.')) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await trainModel(false);
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при обучении модели');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-red-100 rounded-lg">
            <Settings className="h-6 w-6 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            Обучение модели
          </h2>
        </div>

        <div className="space-y-6">
          <div className="p-4 bg-blue-50 border-l-4 border-blue-500">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
              <div>
                <h3 className="text-sm font-semibold text-blue-900 mb-1">Информация</h3>
                <p className="text-sm text-blue-800">
                  Обучение модели может занять несколько минут. 
                  Модель будет обучена на всех доступных данных с использованием 
                  кросс-валидации (TimeSeriesSplit, 5 фолдов).
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-semibold text-gray-900">Что будет сделано:</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Загрузка данных из CSV файлов</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Объединение и предобработка данных</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Создание 50+ признаков (feature engineering)</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Обучение XGBoost модели</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Кросс-валидация (5 фолдов)</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Сохранение модели и метрик</span>
              </li>
            </ul>
          </div>

          <button
            onClick={handleTrain}
            disabled={loading}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Обучение модели...</span>
              </>
            ) : (
              <>
                <Play className="h-5 w-5" />
                <span>Начать обучение</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress */}
      {loading && (
        <div className="card bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-600">
          <div className="flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
            <div>
              <h3 className="font-semibold text-gray-900">Обучение в процессе...</h3>
              <p className="text-sm text-gray-600">Пожалуйста, подождите. Это может занять 2-5 минут.</p>
            </div>
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="card bg-green-50 border-l-4 border-green-600">
          <div className="flex items-start space-x-3">
            <CheckCircle2 className="h-6 w-6 text-green-600 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-bold text-green-900 mb-4">
                ✅ Обучение завершено успешно!
              </h3>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-green-700">Accuracy (±2 дня):</span>
                  <span className="font-bold text-green-900">
                    {(result.metrics.accuracy_2days * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">MAE:</span>
                  <span className="font-bold text-green-900">
                    {result.metrics.mae.toFixed(2)} дней
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">RMSE:</span>
                  <span className="font-bold text-green-900">
                    {result.metrics.rmse.toFixed(2)} дней
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">KPI достигнут:</span>
                  <span className="font-bold text-green-900">
                    {result.metrics.kpi_achieved ? '✓ Да' : '✗ Нет'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card bg-red-50 border-l-4 border-red-600">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-6 w-6 text-red-600 mt-1" />
            <div>
              <h3 className="text-lg font-bold text-red-900 mb-2">
                Ошибка при обучении
              </h3>
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

