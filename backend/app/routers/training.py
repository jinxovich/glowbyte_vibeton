"""Маршруты обучения модели и просмотра истории."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from ..ml import get_predictor, read_prediction_history
from ..schemas import HistoryResponse, PredictionResponse, TrainResponse

router = APIRouter(tags=["training"])


@router.post("/train", response_model=TrainResponse, summary="Запустить обучение модели")
def train_endpoint(
    force: bool = Body(default=False, description="Флаг принудительного переобучения."),
    predictor=Depends(get_predictor),
) -> TrainResponse:
    try:
        metrics = predictor.train()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TrainResponse(status="ok", metrics=metrics)


@router.get("/history", response_model=HistoryResponse, summary="История прогнозов и метрик")
def history_endpoint(predictor=Depends(get_predictor)) -> HistoryResponse:
    metrics = predictor.load_metrics()
    raw_history = read_prediction_history()
    predictions = [PredictionResponse(**item) for item in raw_history]
    return HistoryResponse(metrics=metrics, predictions=predictions)

