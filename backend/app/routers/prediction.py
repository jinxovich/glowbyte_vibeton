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
    from ML.predictor import CoalCombustionPredictor
except ImportError:
    print("⚠️ Не удалось импортировать ML модуль. Убедитесь, что запускаете из корня.")

# Инициализация ML модели (Синглтон)
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        data_dir = PROJECT_ROOT / "data"
        artifacts_dir = PROJECT_ROOT / "ML" / "artifacts"
        predictor = CoalCombustionPredictor(data_dir, artifacts_dir)
    return predictor

router = APIRouter(prefix="/predict", tags=["ML Prediction"])

@router.post("/", response_model=schemas.PredictionResponse)
def predict_coal_fire(
    input_data: schemas.PredictionInput,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    ml_model = get_predictor()
    
    # Конвертация в DataFrame
    df = pd.DataFrame([input_data.model_dump()])
    
    try:
        # Предсказание
        results = ml_model.predict(df)
        result = results[0] # Берем первый результат
        
        # Сохранение в БД (История)
        db_prediction = models.Prediction(
            user_id=current_user.id,
            storage_id=result['storage_id'],
            stack_id=result['stack_id'],
            input_data=input_data.model_dump(),
            predicted_days=int(result['predicted_ttf_days']),
            confidence=int(result['confidence'] * 100),
            risk_level=result['risk_level']
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        # Формируем ответ
        return {
            "id": db_prediction.id,
            "storage_id": db_prediction.storage_id,
            "stack_id": db_prediction.stack_id,
            "predicted_ttf_days": result['predicted_ttf_days'],
            "risk_level": result['risk_level'],
            "confidence": result['confidence'],
            "created_at": db_prediction.created_at
        }
        
    except Exception as e:
        print(f"ML Error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка ML модели: {str(e)}")

@router.get("/history", response_model=list[schemas.PredictionResponse])
def get_history(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    return db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).order_by(models.Prediction.created_at.desc()).all()