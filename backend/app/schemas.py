"""Pydantic-схемы запросов и ответов API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class PredictionItem(BaseModel):
    """Запрос на прогноз для одного штабеля."""

    storage_id: str = Field(..., description="Идентификатор склада, например '3'.")
    stack_id: str = Field(..., description="Номер штабеля или бурта.")
    measurement_date: datetime = Field(..., description="Дата и время замера температуры.")
    max_temperature: float = Field(..., description="Максимальная температура внутри штабеля.")
    pile_age_days: float | None = Field(
        default=None,
        ge=0,
        description="Возраст штабеля в сутках, если известен.",
    )
    stack_mass_tons: float | None = Field(
        default=None,
        description="Фактическая масса штабеля, т.",
    )
    weather_temp: float | None = Field(default=None, description="Температура воздуха, °C.")
    weather_humidity: float | None = Field(default=None, description="Влажность воздуха, %.")  # noqa: RUF001
    weather_pressure: float | None = Field(default=None, description="Давление, гПа.")
    weather_precipitation: float | None = Field(default=None, description="Осадки, мм.")
    weather_wind_avg: float | None = Field(default=None, description="Средняя скорость ветра, м/с.")
    weather_cloudcover: float | None = Field(default=None, description="Облачность, %.")  # noqa: RUF001

    @validator("storage_id", "stack_id", pre=True)
    def cast_to_str(cls, value: object) -> str:
        return str(value)


class PredictionRequest(BaseModel):
    records: list[PredictionItem]


class PredictionResponse(BaseModel):
    storage_id: str
    stack_id: str
    measurement_date: str
    predicted_ttf_days: float
    predicted_combustion_date: str


class TrainResponse(BaseModel):
    status: Literal["ok"]
    metrics: dict[str, Any]


class HistoryResponse(BaseModel):
    metrics: dict[str, Any]
    predictions: list[PredictionResponse]


__all__ = [
    "PredictionItem",
    "PredictionRequest",
    "PredictionResponse",
    "TrainResponse",
    "HistoryResponse",
]