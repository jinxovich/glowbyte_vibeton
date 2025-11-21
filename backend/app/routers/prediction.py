"""Маршрут прогнозирования даты возгорания."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..ml import get_predictor, predictor_to_dataframe
from ..schemas import PredictionRequest, PredictionResponse

router = APIRouter(tags=["prediction"])


@router.post(
    "/predict",
    response_model=list[PredictionResponse],
    summary="Получить прогноз самовозгорания",
)
def predict_endpoint(
    payload: PredictionRequest,
    predictor=Depends(get_predictor),
) -> list[PredictionResponse]:
    if not payload.records:
        raise HTTPException(status_code=400, detail="Передайте хотя бы одну запись для прогноза.")

    frame = predictor_to_dataframe([record.dict() for record in payload.records])
    try:
        predictions = predictor.predict(frame)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return [PredictionResponse(**item) for item in predictions]