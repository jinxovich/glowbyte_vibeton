from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- PREDICTION ---

class PredictionInput(BaseModel):
    # Обязательные поля
    storage_id: str
    stack_id: str
    max_temperature: float
    
    # Основные параметры штабеля
    coal_grade: Optional[str] = Field("unknown", description="Марка угля (Груз/Наим. ЕТСНГ)")
    pile_age_days: Optional[int] = Field(30, description="Дней с начала формирования")
    stack_mass_tons: Optional[float] = Field(5000, description="Текущая масса на складе")
    
    # Локация внутри штабеля (из temperature.csv)
    picket: Optional[str] = Field(None, description="Номер пикета (место замера)")
    shift: Optional[str] = Field(None, description="Номер смены")
    
    # Полная погода (из weather_data.csv)
    weather_temp: Optional[float] = 15
    weather_humidity: Optional[float] = 50
    pressure: Optional[float] = Field(1013, description="Давление (p), гПа")
    precipitation: Optional[float] = 0
    cloud_cover: Optional[float] = Field(50, description="Облачность (cloudcover), %")
    visibility: Optional[float] = Field(10000, description="Видимость, м")
    wind_speed: Optional[float] = Field(3, description="Средняя скорость ветра (v_avg)")
    wind_speed_max: Optional[float] = Field(5, description="Макс. скорость ветра (v_max)")
    wind_direction: Optional[float] = Field(0, description="Направление ветра (wind_dir), градусы 0-360")
    weather_code: Optional[int] = Field(0, description="Код погоды (weather_code)")

    # Дата замера (опционально)
    measurement_date: Optional[str] = None

    # Химия (Deep Tech, если есть)
    co_level_ppm: Optional[float] = 0.0
    ash_content: Optional[float] = 10.0
    moisture_content: Optional[float] = 12.0

class PredictionResponse(BaseModel):
    id: int
    storage_id: str
    stack_id: str
    predicted_ttf_days: float
    risk_level: str
    confidence: float
    created_at: datetime
    warnings: Optional[List[str]] = [] 
    class Config:
        from_attributes = True

# Для симуляции (оставляем как было)
class ForecastPoint(BaseModel):
    days_offset: int
    predicted_days_left: float
    risk_level: str
    estimated_temp: float

class ForecastResponse(BaseModel):
    storage_id: str
    stack_id: str
    current_risk: str
    forecast: List[ForecastPoint]