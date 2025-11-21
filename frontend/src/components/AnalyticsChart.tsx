import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MetricsSnapshot } from "../types";

type AnalyticsChartProps = {
  metrics?: MetricsSnapshot;
};

export default function AnalyticsChart({ metrics }: AnalyticsChartProps) {
  const accuracy = metrics?.accuracy_within_2_days ?? 0;
  const testMae = metrics?.test_mae ?? 0;
  const trainMae = metrics?.train_mae ?? 0;

  const data = [
    {
      name: "Train MAE",
      model: Number(trainMae.toFixed(2)),
      target: 2,
    },
    {
      name: "Test MAE",
      model: Number(testMae.toFixed(2)),
      target: 2,
    },
    {
      name: "Accuracy ±2д",
      model: Number((accuracy * 100).toFixed(1)),
      target: 70,
    },
  ];

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">
            Метрики
          </p>
          <h2 className="text-xl font-semibold text-white">
            Точность модели vs целевой KPI
          </h2>
        </div>
        <span className="rounded-full bg-primary/20 px-3 py-1 text-xs text-primary">
          Цель: 70% в ±2 дня
        </span>
      </div>

      <div className="mt-6 h-60">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "1rem",
              }}
            />
            <Bar dataKey="target" fill="#1d3557" radius={[8, 8, 0, 0]} />
            <Bar dataKey="model" fill="#ff6b35" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

