## Coal Spontaneous Combustion Prediction System

Хакатон-проект для прогноза даты самовозгорания угольных штабелей. Решение состоит из трёх независимых частей:

- `ML/` — обучение и инференс модели `CoalCombustionPredictor` (RandomForest).
- `backend/` — FastAPI REST API со всех необходимых эндпоинтов (загрузка CSV, обучение, прогноз, история).
- `frontend/` — React + Vite + Tailwind для загрузки данных, визуализации календаря и метрик, запуска прогноза.

> Вся документация и интерфейсы локализованы на русском.

---

### Требования к окружению

| Компонент       | Версия (мин.) | Комментарий                        |
|-----------------|---------------|------------------------------------|
| Python          | 3.11          | `venv`/`pyenv` рекомендуется       |
| Node.js + npm   | 18 / 9        | Нужен для Vite/Tailwind            |
| pip             | 23            | Для установки Python-зависимостей |

### Датасеты

Файлы располагаются в `./data`:

1. `supplies.csv` — обязательные столбцы: `ВыгрузкаНаСклад`, `ПогрузкаНаСудно`, `Штабель`, `Склад`, `На склад, тн`. Используются для расчёта массы и возраста штабеля.
2. `temperature.csv` — `Склад`, `Штабель`, `Марка`, `Максимальная температура`, `Дата акта`. Источник внутренних температур.
3. `weather_data_YYYY.csv` — `date`, `t`, `p`, `humidity`, `precipitation`, `v_avg`, `cloudcover`. Агрегируются по дням.
4. `fires.csv` — `Склад`, `Штабель`, `Дата начала`. Точки фактических возгораний (таргет).

Дополнительные CSV (например, `current.csv`) можно грузить через `/upload` — они сохраняются в `data/uploads/<dataset>/`.

---

## Установка и запуск

### 1. Python-окружение и ML

```bash
cd /media/data/Projects/Web/glowbyte_vibeton
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install pandas scikit-learn joblib pyarrow fastapi uvicorn[standard] python-multipart

# обучение базовой модели, формирование артефактов в ML/artifacts/
python ML/eda_prep.py
```

После выполнения появятся:
- `ML/artifacts/models/coal_rf_model.pkl`
- `ML/artifacts/datasets/training_dataset.parquet`
- `ML/artifacts/training_metrics.json`
- `ML/artifacts/prediction_history.json` (после первых запросов `/predict`)

### 2. Backend (FastAPI)

```bash
cd /media/data/Projects/Web/glowbyte_vibeton
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Эндпоинты:

| Метод | Путь        | Назначение                                 |
|-------|-------------|---------------------------------------------|
| GET   | `/health`   | Проверка состояния                          |
| POST  | `/upload`   | Загрузка CSV (`dataset` = supplies/... )    |
| POST  | `/train`    | Переобучение модели                         |
| POST  | `/predict`  | Прогноз даты возгорания                     |
| GET   | `/history`  | Сводка метрик и последних прогнозов         |

### 3. Frontend (React + Vite + Tailwind)

```bash
cd /media/data/Projects/Web/glowbyte_vibeton/frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev    # запуск dev-сервера
npm run build                                     # прод-сборка (dist/)
```

- `VITE_API_URL` указывает на адрес backend (по умолчанию `http://localhost:8000`).
- Dev-сервер поднимается на `http://localhost:5173`, прокси `/api` настроен автоматически.

---

## Пайплайн работы

1. **Загрузка исторических CSV** через UI или напрямую в `data/`.
2. **Обучение** (`python ML/eda_prep.py` или POST `/train`) — генерируются артефакты и метрики (`MAE`, точность `±2 дня`).
3. **Инференс**:
   - загрузить актуальный `current.csv` через `/upload` или заполнить форму в UI;
   - вызвать `POST /predict` (UI делает это автоматически) — API возвращает дату риска (не менее 3 дней вперёд).
4. **Визуализация**:
   - `CalendarView` подсвечивает дни с риском возгорания;
   - `AnalyticsChart` сравнивает целевой KPI (70% в ±2 дня) с текущими метриками;
   - таблица «Журнал событий» хранит историю запросов.

---

## Переменные окружения

| Переменная      | Где используется     | Назначение                             |
|-----------------|----------------------|----------------------------------------|
| `VITE_API_URL`  | `frontend`           | URL backend при запуске Vite/сборки    |

При необходимости можно добавить `.env` и использовать `dotenv` (не включено по умолчанию).

---

## Полезные команды

| Команда                                         | Описание                                 |
|-------------------------------------------------|-------------------------------------------|
| `python ML/eda_prep.py`                         | Подготовка датасета и обучение модели    |
| `uvicorn backend.main:app --reload`             | Запуск API локально                      |
| `npm run dev` (в `frontend/`)                   | UI в режиме разработки                   |
| `npm run build` (в `frontend/`)                 | Прод-сборка фронтенда                    |
| `npm run preview`                               | Проверка собранного бандла               |

---

## План развития

- Добавить альтернативные модели (XGBoost/LightGBM) и расширенные признаки (лаговые погодные показатели, влажность угля).
- Автоматизировать загрузку новых CSV в основной датасет и хранить версии.
- Добавить расчёт фактической точности на основе загруженных `fires.csv` непосредственно в `/history`.
- Написать end-to-end тесты (pytest + Playwright) и CI-пайплайн.

---

### Контакты

Команда Glowbyte Vibeton — Slack #coal-ai или электронная почта, указанная в заявке на хакатон. Оставляйте тикеты/вопросы в репозитории.

