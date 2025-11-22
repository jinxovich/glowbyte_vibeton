from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime
from .models import UserRole, UserStatus

# --- USER ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- PREDICTION ---
class PredictionInput(BaseModel):
    storage_id: str
    stack_id: str
    max_temperature: float
    measurement_date: str
    # Опциональные
    weather_temp: Optional[float] = 0
    weather_humidity: Optional[float] = 0
    wind_speed_avg: Optional[float] = 0
    
class PredictionResponse(BaseModel):
    id: int
    storage_id: str
    stack_id: str
    predicted_ttf_days: float
    risk_level: str
    confidence: float
    created_at: datetime
    class Config:
        from_attributes = True