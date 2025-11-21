"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..ml import get_predictor
from ..config import get_config

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_path: str
    data_dir: str


@router.get("/health", response_model=HealthResponse)
def health_check(
    predictor=Depends(get_predictor),
    config=Depends(get_config)
) -> HealthResponse:
    """
    Проверить статус API и модели.
    
    Returns:
        Статус сервиса
    """
    model_loaded = config.model_path.exists()
    
    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        model_path=str(config.model_path),
        data_dir=str(config.data_dir)
    )


__all__ = ["router"]

