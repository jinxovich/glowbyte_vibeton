import sys
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, security, database

# --- МАГИЯ ИМПОРТА ML ---
# Добавляем корень проекта в путь, чтобы видеть папку ML
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from ML.simple_predictor import SimpleCoalFirePredictor
except ImportError:
    print("⚠️ Не удалось импортировать ML модуль. Убедитесь, что запускаете из корня.")

# Инициализация ML модели (Синглтон)
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        data_dir = PROJECT_ROOT / "data"
        artifacts_dir = PROJECT_ROOT / "ML" / "artifacts"
        predictor = SimpleCoalFirePredictor(data_dir, artifacts_dir)
        try:
            predictor.load_model()
        except FileNotFoundError:
            print("⚠️ Модель не обучена! Запустите: python ML/train_simple.py")
    return predictor

router = APIRouter(prefix="/predict", tags=["ML Prediction"])

@router.post("/", response_model=schemas.PredictionResponse)
def predict_coal_fire(
    input_data: schemas.PredictionInput,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    ml_model = get_predictor()
    
    try:
        # Предсказание с простой моделью
        data = input_data.model_dump()
        result = ml_model.predict(
            storage_id=data.get('storage_id', '11'),
            stack_id=data.get('stack_id', '11'),
            max_temp=data.get('max_temperature', 40),
            storage_days=data.get('pile_age_days', 30),
            mass_tons=data.get('stack_mass_tons', 5000),
            humidity=data.get('weather_humidity', 50),
            air_temp=data.get('weather_temp', 15),
            wind_speed=data.get('wind_speed', 3),
            precipitation=data.get('precipitation', 0)
        )
        
        # Сохранение в БД (История)
        db_prediction = models.Prediction(
            user_id=current_user.id,
            storage_id=result['storage_id'],
            stack_id=result['stack_id'],
            input_data=input_data.model_dump(),
            predicted_days=int(result['days_to_fire']),
            confidence=int(result['confidence'] * 100),
            risk_level=result['risk_level']
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        print(f"✅ Сохранено предсказание ID={db_prediction.id} для пользователя {current_user.id}: {result['days_to_fire']} дней, риск={result['risk_level']}")
        
        # Формируем ответ
        return {
            "id": db_prediction.id,
            "storage_id": db_prediction.storage_id,
            "stack_id": db_prediction.stack_id,
            "predicted_ttf_days": result['days_to_fire'],
            "risk_level": result['risk_level'],
            "confidence": result['confidence'],
            "created_at": db_prediction.created_at
        }
        
    except Exception as e:
        print(f"ML Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка ML модели: {str(e)}")

@router.get("/history", response_model=list[schemas.PredictionResponse])
def get_history(
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Получить историю предсказаний текущего пользователя."""
    return db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).order_by(models.Prediction.created_at.desc()).limit(limit).all()

@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Получить все данные для дашборда: последние предсказания, статистика, риски."""
    
    # Все предсказания пользователя (БЕЗ ЛИМИТА!)
    predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).order_by(models.Prediction.created_at.desc()).all()
    
    print(f"🔍 Dashboard: Найдено {len(predictions)} предсказаний для пользователя {current_user.id}")
    
    # Статистика
    total = len(predictions)
    
    # Распределение по рискам
    risk_counts = {}
    for p in predictions:
        risk = p.risk_level
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    
    # Критические (< 7 дней)
    critical_count = sum(1 for p in predictions if p.predicted_days < 7)
    
    # Средняя уверенность
    avg_confidence = sum(p.confidence for p in predictions) / total if total > 0 else 0
    
    print(f"📊 Статистика: Всего={total}, Критических={critical_count}, Средняя уверенность={avg_confidence}")
    
    # Последние 10 предсказаний для таблицы
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
    
    result = {
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
    
    return result