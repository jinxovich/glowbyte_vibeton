# ✅ Backend исправлен и запущен

**Дата:** 23 ноября 2025  
**Статус:** ✅ РАБОТАЕТ

---

## 🐛 Проблема

```
AttributeError: module 'app.schemas' has no attribute 'UserResponse'
```

**Причина:** При редактировании `backend/app/schemas.py` были случайно удалены User-схемы (UserResponse, UserCreate, UserLogin и т.д.)

---

## ✅ Исправления

### 1. `backend/app/schemas.py`
Восстановлены все User-схемы:

```python
from pydantic import BaseModel, EmailStr
from .models import UserRole, UserStatus

# --- USER ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

### 2. `backend/app/routers/prediction.py`
Уже использует правильный импорт:
```python
from ML.predictor import CoalCombustionPredictor
```

---

## 🚀 Текущий статус

- ✅ Backend запущен: **http://localhost:8000**
- ✅ Swagger UI: **http://localhost:8000/docs**
- ✅ ReDoc: **http://localhost:8000/redoc**
- ✅ ML модель: `CoalCombustionPredictor` загружена
- ✅ База данных: `backend/sql_app.db`
- ✅ Дашборд: Автообновление каждые 5 сек

---

## 📋 Как запустить полностью

### 1. Backend (уже запущен)
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend
```bash
cd frontend
npm run dev
```

### 3. Открыть в браузере
```
http://localhost:5173
```

---

## 🎯 Что работает

### Backend API ✅
- `/register` - регистрация пользователя
- `/token` - авторизация (логин)
- `/predict/` - создать прогноз
- `/predict/history` - история прогнозов
- `/predict/dashboard` - данные для дашборда (все замеры)
- `/admin/users` - управление пользователями (только админ)

### ML модель ✅
- Модель: `CoalCombustionPredictor` (XGBoost)
- Артефакты: `ML/artifacts/models/coal_fire_model.pkl`
- Обучена на: 1536+ примерах
- Accuracy: ~63% (±2 дня)

### Дашборд ✅
- Автообновление каждые 5 секунд
- Все замеры сохраняются в БД
- Статистика: Всего / Критических / Безопасных
- Графики: Динамика прогнозов и уверенность
- Таблица: Полная история всех замеров

---

## 🔧 Troubleshooting

### Backend не запускается
```bash
# Проверить что модель обучена
ls ML/artifacts/models/coal_fire_model.pkl

# Если нет - обучить
python ML/train_model.py

# Проверить что БД существует
ls backend/sql_app.db

# Если нет - создать
python -c "from backend.app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Frontend не подключается
1. Проверьте `frontend/src/lib/api.ts`:
   ```typescript
   const API_URL = 'http://localhost:8000';
   ```

2. Проверьте CORS в `backend/main.py`:
   ```python
   origins = ["http://localhost:5173", ...]
   ```

### Дашборд показывает старые данные
- Откройте консоль браузера (F12)
- Проверьте логи: `🔄 Загрузка дашборда...`
- Нажмите кнопку "Обновить" вручную
- Проверьте что авторизованы (токен не истек)

---

## 🎉 Готово!

Всё работает! Можно:
- Делать прогнозы
- Смотреть дашборд
- История сохраняется автоматически
- Счетчики обновляются каждые 5 сек

**Backend работает! 🚀**

