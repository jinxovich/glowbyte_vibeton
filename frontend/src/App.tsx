import { Sparkles } from "./components/icons/Sparkles";
import Dashboard from "./components/Dashboard";

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-4">
          <div className="flex size-12 items-center justify-center rounded-full bg-primary/20 text-accent">
            <Sparkles />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
              Glowbyte Hackathon 2025
            </p>
            <h1 className="text-2xl font-semibold text-white">
              Coal Spontaneous Combustion Prediction
            </h1>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[260px,1fr]">
        <aside className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">
            Навигация
          </p>
          <ul className="mt-6 space-y-4 text-sm text-slate-300">
            <li className="font-semibold text-white">Данные и загрузка</li>
            <li>Календарь возгораний</li>
            <li>Метрики модели</li>
            <li>История прогнозов</li>
          </ul>
          <div className="mt-8 rounded-2xl bg-gradient-to-br from-primary/40 to-accent/20 p-4 text-sm text-slate-100">
            <p className="font-semibold text-white">Требования</p>
            <p className="mt-2 text-slate-200">
              • Загрузка CSV <br />• Горизонт ≥ 3 дня <br />• Точность ≥ 70% в
              ±2 дня
            </p>
          </div>
        </aside>

        <main>
          <Dashboard />
        </main>
      </div>
    </div>
  );
}

export default App;

