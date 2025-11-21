# 🚀 Deployment Guide - Coal Fire Prediction System

## ✅ System Components Status

### ML Module ✅
- **Data Preprocessor**: ✅ Working - Successfully loads and merges all 4 CSV files
- **Feature Engineering**: ✅ Working - Creates 50+ features
- **XGBoost Model**: ✅ Working - Trains successfully
- **Metrics**: ✅ Working - Comprehensive evaluation
- **Predictor**: ✅ Working - Full training and prediction pipeline

### Backend API ✅
- **FastAPI Application**: ✅ Working - Starts successfully
- **Health Endpoint**: ✅ Working - Returns model status
- **Prediction Endpoint**: ✅ Working - Makes predictions
- **Training Endpoint**: ✅ Working - Triggers model training
- **Analytics Endpoints**: ✅ Working - Dashboard, calendar, metrics

### Frontend ✅
- **HTML/CSS/JS**: ✅ Complete - Beautiful responsive UI
- **Bootstrap 5.3**: ✅ Integrated - Modern design
- **Chart.js**: ✅ Integrated - Interactive visualizations
- **Calendar View**: ✅ Implemented - Color-coded risk levels
- **Dashboard**: ✅ Implemented - KPIs and statistics

---

## 📊 Model Performance

### Current Metrics
- **CV Accuracy (±2 days)**: 47.22%
- **Training Accuracy**: 100% (indicates overfitting)
- **MAE**: 3.70 days (cross-validation)
- **RMSE**: 5.19 days (cross-validation)

### Target KPI
- **Required**: Accuracy ±2 days >= 70%
- **Status**: ⚠️ Not yet achieved (47.22%)

### Recommendations to Reach 70% KPI

1. **More Training Data**
   - Current: 649 training examples from 11 stackpiles
   - Recommended: 2000+ examples from 50+ stackpiles
   - Action: Collect more historical fire events

2. **Feature Engineering Improvements**
   ```python
   # Add these features in ML/feature_engineering.py:
   
   # 1. Coal chemistry features (if available)
   - Sulfur content
   - Moisture content
   - Volatile matter
   
   # 2. Штабель geometry features
   - Stack height
   - Stack volume
   - Surface area
   
   # 3. More sophisticated lags
   - Exponentially weighted moving averages
   - Change rates over multiple windows
   ```

3. **Hyperparameter Tuning**
   ```python
   # Use GridSearchCV or Optuna for tuning
   from sklearn.model_selection import GridSearchCV
   
   param_grid = {
       'n_estimators': [300, 500, 700],
       'max_depth': [8, 10, 12],
       'learning_rate': [0.01, 0.03, 0.05],
       'subsample': [0.7, 0.8, 0.9],
       'colsample_bytree': [0.7, 0.8, 0.9]
   }
   ```

4. **Ensemble Methods**
   - Combine XGBoost with LightGBM and CatBoost
   - Use stacking or voting ensemble
   - Weight predictions by confidence

5. **Address Class Imbalance**
   - Current data might have uneven distribution of days_until_fire
   - Use SMOTE or other sampling techniques
   - Adjust sample weights in XGBoost

---

## 🎯 Quick Start

### 1. Install Dependencies
```bash
cd /media/data/Projects/Web/glowbyte_vibeton
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Train Model
```bash
python ML/train_model.py
```

Expected output:
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
  ✓ Средний RMSE: 5.19 дней

💾 Модель сохранена в: ML/artifacts/models/coal_fire_model.pkl
```

### 3. Start Backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 4. Open Frontend
Simply open `frontend/index.html` in your browser or use:
```bash
cd frontend
python3 -m http.server 3000
# or
live-server --port=3000
```

Frontend will be available at: http://localhost:3000

---

## 🔌 API Examples

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_path": "/path/to/model.pkl",
  "data_dir": "/path/to/data"
}
```

### Make Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "records": [{
      "storage_id": "3",
      "stack_id": "21",
      "measurement_date": "2024-11-21T10:00:00",
      "max_temperature": 45.5,
      "pile_age_days": 30,
      "stack_mass_tons": 5000
    }]
  }'
```

Response:
```json
[{
  "storage_id": "3",
  "stack_id": "21",
  "measurement_date": "2024-11-21 10:00:00",
  "predicted_ttf_days": 5.2,
  "predicted_combustion_date": "2024-11-26",
  "confidence": 0.85,
  "risk_level": "высокий",
  "max_temperature": 45.5
}]
```

### Get Dashboard Data
```bash
curl http://localhost:8000/api/dashboard
```

### Train Model via API
```bash
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

---

## 📁 Project Structure

```
glowbyte_vibeton/
├── ML/                              ✅ Complete
│   ├── __init__.py
│   ├── data_preprocessor.py        # Loads & merges CSV
│   ├── feature_engineering.py      # 50+ features
│   ├── model.py                    # XGBoost model
│   ├── metrics.py                  # Evaluation
│   ├── predictor.py                # Main predictor class
│   ├── train_model.py              # Training script
│   └── artifacts/                  # Saved models & metrics
│
├── backend/                         ✅ Complete
│   ├── main.py
│   └── app/
│       ├── __init__.py             # FastAPI app factory
│       ├── config.py               # Configuration
│       ├── ml.py                   # ML integration
│       ├── schemas.py              # Pydantic models
│       └── routers/
│           ├── health.py           # Health check
│           ├── prediction.py       # Predictions
│           ├── training.py         # Training
│           └── analytics.py        # Dashboard/analytics
│
├── frontend/                        ✅ Complete
│   ├── index.html                  # Main page
│   ├── style.css                   # Styles
│   └── app.js                      # JavaScript logic
│
├── data/                            ✅ Present
│   ├── fires.csv
│   ├── supplies.csv
│   ├── temperature.csv
│   └── weather_data_*.csv
│
├── requirements.txt                 ✅ Complete
├── README.md                        ✅ Complete
├── DEPLOYMENT.md                    ✅ This file
└── .gitignore                       ✅ Complete
```

---

## ✅ Completed Checklist

### Architecture ✅
- [x] Modular structure (ML / Backend / Frontend)
- [x] RESTful API with FastAPI
- [x] Proper folder organization
- [x] Configuration with environment variables
- [x] Logging and error handling
- [x] CORS middleware

### Data Processing ✅
- [x] Load all 4 CSV files (fires, supplies, temperature, weather)
- [x] Handle Cyrillic column names correctly
- [x] Merge data properly with time alignment
- [x] Create comprehensive feature set (50+ features)
- [x] Handle missing values
- [x] Time-based train/test splitting

### ML Model ✅
- [x] XGBoost implementation
- [x] Cross-validation (TimeSeriesSplit)
- [x] Feature engineering
- [x] Model saving/loading
- [x] Metrics calculation
- [x] Confidence scores
- [x] Risk level classification

### Backend API ✅
- [x] Health check endpoint
- [x] Prediction endpoint
- [x] Training endpoint
- [x] History endpoint
- [x] Dashboard endpoint
- [x] Calendar endpoint
- [x] Metrics endpoint
- [x] Swagger documentation

### Frontend ✅
- [x] Responsive design (Bootstrap 5)
- [x] KPI cards display
- [x] Interactive charts (Chart.js)
- [x] Calendar view with color coding
- [x] Prediction form
- [x] History table
- [x] Metrics display
- [x] Real-time updates
- [x] Error handling
- [x] Beautiful UI/UX

### Documentation ✅
- [x] Comprehensive README
- [x] API documentation
- [x] Code comments
- [x] Deployment guide
- [x] Setup instructions
- [x] Troubleshooting

---

## 🔧 Troubleshooting

### Model Doesn't Load
**Error**: `FileNotFoundError: Model not found`

**Solution**:
```bash
python ML/train_model.py
```

### API Won't Start
**Error**: `Address already in use`

**Solution**:
```bash
pkill -f uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Import Errors
**Error**: `ModuleNotFoundError: No module named 'xgboost'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Low Accuracy
**Current**: 47.22% (CV)

**Solutions**:
1. Collect more training data (especially fire events)
2. Add domain-specific features (coal chemistry, stack geometry)
3. Tune hyperparameters with GridSearchCV
4. Try ensemble methods
5. Address data quality issues

---

## 🎉 Success Criteria

### Achieved ✅
- [x] Application starts without errors
- [x] CSV files load and parse correctly (including Cyrillic)
- [x] Predictions calculated for each stackpile
- [x] Metrics computed and compared with real data
- [x] Modular architecture implemented
- [x] RESTful API working
- [x] Intuitive UI created
- [x] README with step-by-step instructions
- [x] Input validation with user-friendly errors
- [x] EDA with visualizations
- [x] Justified model choice
- [x] Feature engineering (50+ features)
- [x] Cross-validation (TimeSeriesSplit)

### Partially Achieved ⚠️
- [⚠️] Accuracy ±2 days >= 70% (currently 47.22% CV)
  - Training set accuracy: 100% (overfitting)
  - Cross-validation accuracy: 47.22% (more realistic)
  - **Recommendation**: Need more diverse training data

---

## 📧 Support

For questions or issues:
- Check README.md for detailed documentation
- Review API docs at http://localhost:8000/docs
- Check logs in `/tmp/uvicorn.log`

---

**System Status**: ✅ **FULLY FUNCTIONAL** with room for accuracy improvement
**Last Updated**: 2024-11-21
**Version**: 1.0.0

