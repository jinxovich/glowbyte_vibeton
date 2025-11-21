import { useEffect, useMemo, useState } from "react";
import AnalyticsChart from "./AnalyticsChart";
import CalendarView from "./CalendarView";
import FileUpload from "./FileUpload";
import {
  fetchHistory,
  predictStacks,
  trainModel,
  uploadDataset,
} from "../lib/api";
import type {
  HistoryResponse,
  PredictionPayload,
  PredictionResponse,
  UploadDataset,
} from "../types";

const initialPrediction: PredictionPayload = {
  storage_id: "4",
  stack_id: "15",
  measurement_date: new Date().toISOString().slice(0, 16),
  max_temperature: 65,
  pile_age_days: 30,
  stack_mass_tons: 12000,
  weather_temp: -5,
  weather_humidity: 70,
  weather_pressure: 1010,
  weather_precipitation: 0,
  weather_wind_avg: 6,
  weather_cloudcover: 80,
};

export default function Dashboard() {
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [isLoading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [predictionForm, setPredictionForm] =
    useState<PredictionPayload>(initialPrediction);
  const [isTraining, setTraining] = useState(false);
  const [isPredicting, setPredicting] = useState(false);

  const ingestionUploads: Array<{
    title: string;
    description: string;
    dataset: UploadDataset;
  }> = [
    {
      title: "Supplies.csv",
      description: "История поставок и массы штабелей.",
      dataset: "supplies",
    },
    {
      title: "Temperature.csv",
      description: "Внутренние температуры и акты замеров.",
      dataset: "temperature",
    },
    {
      title: "Weather_data*.csv",
      description: "Погодные условия по часам.",
      dataset: "weather",
    },
  ];

  const calibrationUploads: typeof ingestionUploads = [
    {
      title: "current.csv",
      description: "Актуальные измерения для быстрого прогноза.",
      dataset: "current",
    },
    {
      title: "fires.csv",
      description: "Фактические возгорания для калибровки.",
      dataset: "fires",
    },
  ];

  useEffect(() => {
    void loadHistory();
  }, []);

  const latestPredictions = useMemo<PredictionResponse[]>(() => {
    if (!history) return [];
    return [...history.predictions].reverse().slice(0, 8);
  }, [history]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchHistory();
      setHistory(data);
    } catch (error) {
      console.error(error);
      setMessage("Не удалось загрузить историю.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File, dataset: UploadDataset) => {
    try {
      await uploadDataset(dataset, file);
      setMessage(`Файл загружен: ${dataset}`);
    } catch (error) {
      console.error(error);
      setMessage("Ошибка загрузки файла.");
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      const response = await trainModel();
      setMessage("Модель переобучена.");
      setHistory((prev) =>
        prev
          ? { ...prev, metrics: response.metrics }
          : { metrics: response.metrics, predictions: [] },
      );
    } catch (error) {
      console.error(error);
      setMessage("Ошибка обучения модели.");
    } finally {
      setTraining(false);
    }
  };

  const handlePredict = async () => {
    setPredicting(true);
    try {
      const payload = {
        ...predictionForm,
        measurement_date: new Date(predictionForm.measurement_date).toISOString(),
      };
      const result = await predictStacks(payload);
      setMessage("Прогноз рассчитан.");
      setHistory((prev) =>
        prev
          ? { ...prev, predictions: [...prev.predictions, ...result] }
          : { metrics: {}, predictions: result },
      );
    } catch (error) {
      console.error(error);
      setMessage("Ошибка прогноза.");
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="space-y-6">
      {message && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-3 text-sm text-slate-100">
          {message}
        </div>
      )}

      <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {ingestionUploads.map((item) => (
          <FileUpload key={item.dataset} {...item} onUpload={handleUpload} />
        ))}
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        {calibrationUploads.map((item) => (
          <FileUpload key={item.dataset} {...item} onUpload={handleUpload} />
        ))}
      </section>

      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">
              Онлайн-прогноз
            </p>
            <h2 className="text-xl font-semibold text-white">
              Рассчитать окно возгорания
            </h2>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:border-slate-500"
              onClick={handleTrain}
              disabled={isTraining}
            >
              {isTraining ? "Обучение..." : "Переобучить модель"}
            </button>
            <button
              type="button"
              className="rounded-full bg-accent px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-accent/90"
              onClick={handlePredict}
              disabled={isPredicting}
            >
              {isPredicting ? "Прогноз..." : "Предсказать"}
            </button>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-300">
            Склад и штабель
            <div className="mt-2 flex gap-3">
              <input
                className="flex-1 rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-2 text-white"
                value={predictionForm.storage_id}
                onChange={(event) =>
                  setPredictionForm((prev) => ({
                    ...prev,
                    storage_id: event.target.value,
                  }))
                }
                placeholder="storage_id"
              />
              <input
                className="flex-1 rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-2 text-white"
                value={predictionForm.stack_id}
                onChange={(event) =>
                  setPredictionForm((prev) => ({
                    ...prev,
                    stack_id: event.target.value,
                  }))
                }
                placeholder="stack_id"
              />
            </div>
          </label>
          <label className="text-sm text-slate-300">
            Дата измерения
            <input
              type="datetime-local"
              className="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-2 text-white"
              value={predictionForm.measurement_date}
              onChange={(event) =>
                setPredictionForm((prev) => ({
                  ...prev,
                  measurement_date: event.target.value,
                }))
              }
            />
          </label>
          <label className="text-sm text-slate-300">
            Температура внутри штабеля, °C
            <input
              type="number"
              className="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-2 text-white"
              value={predictionForm.max_temperature}
              onChange={(event) =>
                setPredictionForm((prev) => ({
                  ...prev,
                  max_temperature: Number(event.target.value),
                }))
              }
            />
          </label>
          <label className="text-sm text-slate-300">
            Возраст штабеля, дней
            <input
              type="number"
              className="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-2 text-white"
              value={predictionForm.pile_age_days ?? 0}
              onChange={(event) =>
                setPredictionForm((prev) => ({
                  ...prev,
                  pile_age_days: Number(event.target.value),
                }))
              }
            />
          </label>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <CalendarView predictions={history?.predictions ?? []} />
        <AnalyticsChart metrics={history?.metrics} />
      </section>

      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">
              Последние прогнозы
            </p>
            <h2 className="text-xl font-semibold text-white">
              Журнал событий
            </h2>
          </div>
          <button
            type="button"
            className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:border-slate-500"
            onClick={loadHistory}
            disabled={isLoading}
          >
            {isLoading ? "Обновление..." : "Обновить"}
          </button>
        </div>

        <div className="mt-4 overflow-hidden rounded-2xl border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-900/80 text-slate-300">
              <tr>
                <th className="px-4 py-3 text-left">Склад</th>
                <th className="px-4 py-3 text-left">Штабель</th>
                <th className="px-4 py-3 text-left">Замер</th>
                <th className="px-4 py-3 text-left">TTF, дн.</th>
                <th className="px-4 py-3 text-left">Дата риска</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {latestPredictions.map((item) => (
                <tr key={`${item.storage_id}-${item.stack_id}-${item.measurement_date}`}>
                  <td className="px-4 py-3">{item.storage_id}</td>
                  <td className="px-4 py-3">{item.stack_id}</td>
                  <td className="px-4 py-3">{item.measurement_date}</td>
                  <td className="px-4 py-3 font-semibold text-accent">
                    {item.predicted_ttf_days}
                  </td>
                  <td className="px-4 py-3 text-white">
                    {item.predicted_combustion_date}
                  </td>
                </tr>
              ))}
              {latestPredictions.length === 0 && (
                <tr>
                  <td
                    className="px-4 py-6 text-center text-slate-400"
                    colSpan={5}
                  >
                    Пока нет прогнозов. Загрузите данные и нажмите «Предсказать».
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

