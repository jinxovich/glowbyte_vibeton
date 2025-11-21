# ⚡ Quick Start - Coal Fire Prediction System

## 🚀 Get Running in 3 Minutes

### Step 1: Install Dependencies (1 minute)

```bash
cd /media/data/Projects/Web/glowbyte_vibeton

# Activate virtual environment
source .venv/bin/activate  # If already exists
# OR create new one
python3 -m venv .venv
source .venv/bin/activate

# Install packages
pip install pandas numpy scikit-learn xgboost joblib fastapi uvicorn python-multipart pydantic pydantic-settings pyarrow
```

### Step 2: Train Model (1 minute)

```bash
python ML/train_model.py
```

**You'll see:**
```
🔥 ОБУЧЕНИЕ МОДЕЛИ ПРОГНОЗИРОВАНИЯ САМОВОЗГОРАНИЯ УГЛЯ
============================================================
📊 Загрузка данных...
  ✓ fires: 486 записей
  ✓ supplies: 6323 записей
  ✓ temperature: 4106 записей
  ✓ weather: 2555 дней

✅ Обучение завершено!
  ✓ Средняя Accuracy (±2 дня): 47.22%
  ✓ Средний MAE: 3.70 дней

💾 Модель сохранена в: ML/artifacts/models/coal_fire_model.pkl
🎉 Готово к использованию!
```

### Step 3: Start Backend (30 seconds)

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Backend running at**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

### Step 4: Open Frontend (30 seconds)

**Option A**: Double-click `frontend/index.html`

**Option B**: Use a local server:
```bash
cd frontend
python3 -m http.server 3000
```

**Frontend running at**: http://localhost:3000

---

## 🎯 You're Done! Now Try:

### 1. Check Health
```bash
curl http://localhost:8000/health
```

### 2. Make a Prediction via UI
1. Go to http://localhost:3000
2. Fill in the form:
   - Склад: `3`
   - Штабель: `21`
   - Макс. температура: `45.5`
   - Дата: (select current date)
3. Click "Рассчитать"
4. See the prediction!

### 3. Make a Prediction via API
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "records": [{
      "storage_id": "3",
      "stack_id": "21",
      "measurement_date": "2024-11-21T10:00:00",
      "max_temperature": 45.5
    }]
  }'
```

**Response:**
```json
[{
  "storage_id": "3",
  "stack_id": "21",
  "predicted_ttf_days": 5.2,
  "predicted_combustion_date": "2024-11-26",
  "risk_level": "высокий",
  "confidence": 0.85
}]
```

---

## 📊 Explore the UI

### Dashboard Tab
- See KPI cards (Accuracy, MAE, Total, At Risk)
- View risk distribution chart
- Check upcoming fires (next 7 days)

### Calendar Tab
- See all predicted fire dates
- Color-coded by risk level:
  - 🔴 Red = Critical (< 3 days)
  - 🟠 Orange = High (3-7 days)
  - 🟡 Yellow = Medium (7-14 days)
  - 🟢 Green = Low (14-30 days)

### History Tab
- View all predictions ever made
- Search and filter

### Metrics Tab
- Detailed model performance
- Accuracy breakdown
- Feature importance

---

## 🔥 Make Predictions

### Via UI Form:
1. Enter storage and stack IDs
2. Enter current max temperature
3. Select measurement date
4. (Optional) Add advanced parameters
5. Click "Рассчитать"

### Via API:
```python
import requests

response = requests.post('http://localhost:8000/predict', json={
    "records": [{
        "storage_id": "3",
        "stack_id": "21",
        "measurement_date": "2024-11-21T10:00:00",
        "max_temperature": 45.5,
        "pile_age_days": 30,
        "stack_mass_tons": 5000
    }]
})

prediction = response.json()[0]
print(f"Fire in {prediction['predicted_ttf_days']:.1f} days")
print(f"Date: {prediction['predicted_combustion_date']}")
print(f"Risk: {prediction['risk_level']}")
```

---

## 🎓 Understanding Results

### Risk Levels
- **Критический**: Fire within 3 days - IMMEDIATE ACTION
- **Высокий**: Fire within 3-7 days - High priority
- **Средний**: Fire within 7-14 days - Monitor closely
- **Низкий**: Fire within 14-30 days - Normal monitoring
- **Минимальный**: Fire > 30 days away - Low concern

### Confidence Score
- **> 0.8**: High confidence, rely on prediction
- **0.5-0.8**: Moderate confidence, verify with additional checks
- **< 0.5**: Low confidence, more data needed

### Predicted Days
- The number of days until spontaneous combustion is predicted to occur
- Based on current temperature, weather, and historical patterns

---

## 🔧 Troubleshooting

### "Model not found"
**Solution**: Run `python ML/train_model.py` first

### "Port already in use"
**Solution**: 
```bash
pkill -f uvicorn
# Then start again
uvicorn backend.main:app --port 8000
```

### "Module not found"
**Solution**: 
```bash
pip install -r requirements.txt
```

### Low accuracy (< 70%)
**This is expected** with current limited data (649 examples, 11 stackpiles).
**To improve**: See `DEPLOYMENT.md` for recommendations

---

## 📚 More Information

- **Full Documentation**: See `README.md`
- **Deployment Guide**: See `DEPLOYMENT.md`
- **Implementation Details**: See `SUMMARY.md`
- **API Docs**: http://localhost:8000/docs (when running)

---

## ✅ Verification Checklist

After following this guide, you should have:

- [x] Model trained and saved in `ML/artifacts/models/`
- [x] Backend running on port 8000
- [x] Frontend accessible in browser
- [x] Health check returns `{"status": "ok", "model_loaded": true}`
- [x] Can make predictions via UI
- [x] Can see dashboard with KPIs
- [x] Can view calendar with fire dates

---

## 🎯 What's Next?

1. **Explore the UI** - Try all tabs
2. **Make predictions** - Test with different temperatures
3. **View calendar** - See predicted fire dates
4. **Check metrics** - Understand model performance
5. **Read docs** - Learn advanced features

---

**You're all set! 🎉**

The system is now fully operational and ready to predict coal fires.

**Support**: Check `README.md` for detailed documentation
**Issues**: See `DEPLOYMENT.md` troubleshooting section

