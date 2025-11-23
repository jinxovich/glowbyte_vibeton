import sys
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models, security, database

# --- НАСТРОЙКА ПУТЕЙ ---
# Текущий файл: backend/app/routers/prediction.py
# Нам нужно попасть в корень проекта (где папки ML и backend лежат рядом)
# .parents[0] = routers
# .parents[1] = app
# .parents[2] = backend
# .parents[3] = КОРЕНЬ PROJEKTA
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Добавляем корень в sys.path, чтобы питон видел модуль ML
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# --- ИМПОРТ НОВОГО ПРЕДИКТОРА ---
try:
    from ML.predictor import CoalCombustionPredictor
except ImportError as e:
    print(f"❌ ОШИБКА ИМПОРТА ML: {e}")
    print(f"   Ожидаемый путь к ML: {PROJECT_ROOT / 'ML'}")
    # Не падаем сразу, чтобы хоть сваггер открылся, но модель работать не будет
    CoalCombustionPredictor = None

# Инициализация ML модели (Синглтон)
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        if CoalCombustionPredictor is None:
             raise HTTPException(500, "ML модуль не загружен. Проверьте пути.")
             
        data_dir = PROJECT_ROOT / "data"
        artifacts_dir = PROJECT_ROOT / "ML" / "artifacts"
        
        print(f"🔄 Инициализация модели из {artifacts_dir}...")
        predictor = CoalCombustionPredictor(data_dir, artifacts_dir)
        
    return predictor

router = APIRouter(prefix="/predict", tags=["ML Prediction"])

# Вспомогательная функция для анализа химических рисков
def analyze_chemical_risks(data: schemas.PredictionInput) -> List[str]:
    warnings = []
    if data.co_level_ppm and data.co_level_ppm > 50:
        warnings.append("⚠️ Высокий уровень CO! Идет активное окисление.")
    if data.ash_content and data.ash_content > 15:
        warnings.append("ℹ️ Высокая зольность может влиять на теплообмен.")
    if data.moisture_content and data.moisture_content < 5:
        warnings.append("⚠️ Уголь слишком сухой, риск возгорания повышен.")
    return warnings

@router.post("/", response_model=schemas.PredictionResponse)
def predict_coal_fire(
    input_data: schemas.PredictionInput,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    ml_model = get_predictor()
    
    try:
        data_dict = input_data.model_dump()
        
        # МАППИНГ ВСЕХ ПОЛЕЙ (API -> ML DataFrame columns)
        mapped_data = {
            'storage_id': data_dict.get('storage_id'),
            'stack_id': data_dict.get('stack_id'),
            'max_temp': data_dict.get('max_temperature'),
            'coal_grade': data_dict.get('coal_grade'),
            'days_since_formation': data_dict.get('pile_age_days'),
            'coal_weight_storage': data_dict.get('stack_mass_tons'),
            
            # Новые поля (локация)
            'picket': data_dict.get('picket'),
            'shift': data_dict.get('shift'),
            
            # Новые поля (погода full)
            'weather_temp': data_dict.get('weather_temp'),
            'weather_humidity': data_dict.get('weather_humidity'),
            'pressure': data_dict.get('pressure'),
            'weather_precipitation': data_dict.get('precipitation'),
            'cloud_cover': data_dict.get('cloud_cover'),
            'visibility': data_dict.get('visibility'),
            'wind_speed_avg': data_dict.get('wind_speed'),
            'wind_speed_max': data_dict.get('wind_speed_max'),
            'wind_dir': data_dict.get('wind_direction'),
            'weather_code': data_dict.get('weather_code'),
            
            'measurement_date': data_dict.get('measurement_date')
        }
        
        input_df = pd.DataFrame([mapped_data])
        
        # Предикт
        results = ml_model.predict(input_df)
        result = results[0]
        
        # Логика варнингов и сохранения (остается прежней)
        warnings = analyze_chemical_risks(input_data)
        if input_data.co_level_ppm and input_data.co_level_ppm > 100:
             result['predicted_ttf_days'] = min(result['predicted_ttf_days'], 3.0)
             result['risk_level'] = "критический"
             warnings.append("🔴 SAFETY: Критический уровень газа.")

        db_prediction = models.Prediction(
            user_id=current_user.id,
            storage_id=str(result['storage_id']),
            stack_id=str(result['stack_id']),
            input_data=data_dict,
            predicted_days=int(result['predicted_ttf_days']),
            confidence=int(result['confidence'] * 100),
            risk_level=result['risk_level']
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        return {
            "id": db_prediction.id,
            "storage_id": db_prediction.storage_id,
            "stack_id": db_prediction.stack_id,
            "predicted_ttf_days": result['predicted_ttf_days'],
            "risk_level": result['risk_level'],
            "confidence": result['confidence'],
            "created_at": db_prediction.created_at,
            "warnings": warnings
        }
        
    except Exception as e:
        print(f"❌ ML Runtime Error: {e}")
        raise HTTPException(status_code=500, detail=f"ML Error: {str(e)}")


@router.post("/", response_model=schemas.PredictionResponse)
def predict_coal_fire(
    input_data: schemas.PredictionInput,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    ml_model = get_predictor()
    
    try:
        # 1. Подготовка данных для модели
        # Модель v3.0 принимает DataFrame
        data_dict = input_data.model_dump()
        
        # Маппинг полей Pydantic -> поля, которые ждет модель (если они отличаются)
        # Но predictor.py сам делает rename, поэтому передаем как есть, главное имена ключей
        input_df = pd.DataFrame([data_dict])
        
        # 2. Предсказание
        # Возвращает список словарей, берем первый
        results = ml_model.predict(input_df)
        result = results[0]
        
        # 3. Анализ хим. рисков
        warnings = analyze_chemical_risks(input_data)
        
        # Safety Layer: Если CO зашкаливает, ставим критический риск вручную
        if input_data.co_level_ppm and input_data.co_level_ppm > 100:
             result['predicted_ttf_days'] = min(result['predicted_ttf_days'], 3.0)
             result['risk_level'] = "критический"
             warnings.append("🔴 SAFETY: Критический уровень газа перекрывает ML-прогноз.")

        # 4. Сохранение в БД
        db_prediction = models.Prediction(
            user_id=current_user.id,
            storage_id=str(result['storage_id']),
            stack_id=str(result['stack_id']),
            input_data=data_dict,
            predicted_days=int(result['predicted_ttf_days']),
            confidence=int(result['confidence'] * 100),
            risk_level=result['risk_level']
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        return {
            "id": db_prediction.id,
            "storage_id": db_prediction.storage_id,
            "stack_id": db_prediction.stack_id,
            "predicted_ttf_days": result['predicted_ttf_days'],
            "risk_level": result['risk_level'],
            "confidence": result['confidence'],
            "created_at": db_prediction.created_at,
            "warnings": warnings
        }
        
    except Exception as e:
        print(f"❌ ML Runtime Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка ML модели: {str(e)}")

@router.post("/forecast", response_model=schemas.ForecastResponse)
def simulate_future_risk(
    input_data: schemas.PredictionInput,
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Симуляция будущего состояния.
    """
    ml_model = get_predictor()
    
    forecast_points = []
    offsets = [0, 7, 14, 30]
    current_temp = input_data.max_temperature
    
    # Простая модель нагрева для симуляции
    heating_rate = 0.1 if current_temp < 30 else (0.5 if current_temp < 50 else 2.0)
    
    base_data = input_data.model_dump()
    
    for days in offsets:
        # Модифицируем данные для сценария
        scenario_data = base_data.copy()
        scenario_data['pile_age_days'] = (scenario_data.get('pile_age_days') or 0) + days
        scenario_data['max_temperature'] = current_temp + (heating_rate * days)
        
        # Создаем DF для предиктора
        scenario_df = pd.DataFrame([scenario_data])
        
        # Предикт
        res_list = ml_model.predict(scenario_df)
        res = res_list[0]
        
        forecast_points.append({
            "days_offset": days,
            "predicted_days_left": res['predicted_ttf_days'],
            "risk_level": res['risk_level'],
            "estimated_temp": round(scenario_data['max_temperature'], 1)
        })
        
    return {
        "storage_id": input_data.storage_id,
        "stack_id": input_data.stack_id,
        "current_risk": forecast_points[0]['risk_level'],
        "forecast": forecast_points
    }

@router.post("/batch", response_model=List[schemas.PredictionResponse])
def predict_batch(
    inputs: List[schemas.PredictionInput],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Массовая обработка (неоптимально, но работает)."""
    results = []
    for item in inputs:
        res = predict_coal_fire(item, db, current_user)
        results.append(res)
    return results

@router.get("/history", response_model=list[schemas.PredictionResponse])
def get_history(
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    return db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).order_by(models.Prediction.created_at.desc()).limit(limit).all()

@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).order_by(models.Prediction.created_at.desc()).all()
    
    total = len(predictions)
    risk_counts = {}
    for p in predictions:
        risk = p.risk_level
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    
    critical_count = sum(1 for p in predictions if p.predicted_days < 7)
    avg_confidence = sum(p.confidence for p in predictions) / total if total > 0 else 0
    
    recent_predictions = []
    for p in predictions[:10]:
        recent_predictions.append({
            "id": p.id,
            "storage_id": p.storage_id,
            "stack_id": p.stack_id,
            "predicted_days": p.predicted_days,
            "risk_level": p.risk_level,
            "confidence": p.confidence,
            "created_at": p.created_at.isoformat()
        })
    
    return {
        "total_predictions": total,
        "critical_count": critical_count,
        "avg_confidence": int(avg_confidence),
        "risk_distribution": risk_counts,
        "recent_predictions": recent_predictions,
        "all_predictions": [
            {
                "id": p.id,
                "storage_id": p.storage_id,
                "stack_id": p.stack_id,
                "predicted_days": p.predicted_days,
                "risk_level": p.risk_level,
                "confidence": p.confidence,
                "created_at": p.created_at.isoformat(),
                "input_data": p.input_data
            }
            for p in predictions
        ]
    }