import { useMemo } from "react";
import Calendar from "react-calendar";
import type { PredictionResponse } from "../types";
import "react-calendar/dist/Calendar.css";

type CalendarViewProps = {
  predictions: PredictionResponse[];
};

export default function CalendarView({ predictions }: CalendarViewProps) {
  const markers = useMemo(() => {
    const map = new Map<string, PredictionResponse[]>();
    predictions.forEach((item) => {
      if (!item.predicted_combustion_date) return;
      const key = item.predicted_combustion_date;
      const list = map.get(key) ?? [];
      list.push(item);
      map.set(key, list);
    });
    return map;
  }, [predictions]);

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">
            Календарь
          </p>
          <h2 className="text-xl font-semibold text-white">
            Окно самовозгорания
          </h2>
        </div>
        <span className="rounded-full bg-accent/20 px-3 py-1 text-xs text-accent">
          {predictions.length} прогнозов
        </span>
      </div>

      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
        <Calendar
          className="react-calendar w-full bg-transparent text-white"
          tileClassName={({ date }) => {
            const iso = date.toISOString().slice(0, 10);
            return markers.has(iso) ? "has-warning" : undefined;
          }}
          locale="ru-RU"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-300">
        {Array.from(markers.entries())
          .slice(-6)
          .map(([date, items]) => (
            <div
              key={date}
              className="rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-2"
            >
              <p className="text-xs uppercase tracking-[0.3em] text-accent">
                {date}
              </p>
              <p className="text-sm text-white">
                {items.length} штаб. ({items.map((i) => i.stack_id).join(", ")})
              </p>
            </div>
          ))}
      </div>
    </div>
  );
}

