# Coal Fire Prediction Frontend

Современный React + TypeScript + Vite фронтенд для системы прогнозирования самовозгорания угля.

## Технологии

- **React 18** - UI библиотека
- **TypeScript** - Типизация
- **Vite** - Быстрая сборка
- **Tailwind CSS** - Утилитарный CSS
- **React Router** - Роутинг
- **Recharts** - Графики
- **Axios** - HTTP клиент
- **Lucide React** - Иконки

## Быстрый старт

```bash
# Установка зависимостей
npm install

# Запуск dev сервера
npm run dev

# Билд для продакшена
npm run build

# Предпросмотр билда
npm run preview
```

## Конфигурация

Создайте файл `.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Структура проекта

```
frontend/
├── src/
│   ├── components/         # React компоненты
│   │   ├── Layout.tsx     # Главный layout
│   │   └── PredictionForm.tsx
│   ├── pages/             # Страницы
│   │   ├── Dashboard.tsx
│   │   ├── Calendar.tsx
│   │   ├── History.tsx
│   │   ├── Metrics.tsx
│   │   └── Train.tsx
│   ├── lib/               # Библиотеки
│   │   ├── api.ts         # API клиент
│   │   └── utils.ts       # Утилиты
│   ├── types/             # TypeScript типы
│   │   └── index.ts
│   ├── App.tsx            # Главный компонент
│   ├── main.tsx           # Точка входа
│   └── index.css          # Стили
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

## Доступные скрипты

- `npm run dev` - Запуск dev сервера (http://localhost:3000)
- `npm run build` - Сборка для продакшена
- `npm run preview` - Предпросмотр собранной версии
- `npm run lint` - Проверка кода

## Особенности

- ✨ Современный UI с Tailwind CSS
- 🚀 Быстрая загрузка с Vite
- 📱 Полностью responsive дизайн
- 🎨 Красивые анимации и переходы
- 📊 Интерактивные графики
- 🗓️ Календарь с цветовой кодировкой
- 🔄 Автообновление данных
- 💪 Полная типизация TypeScript
- 🎯 Оптимизированный bundle

## API Integration

Фронтенд общается с FastAPI бэкендом через прокси (настроен в `vite.config.ts`).

Все запросы автоматически проксируются на `http://localhost:8000`.
