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
    # Опциональные
    pile_age_days: Optional[int] = 30
    stack_mass_tons: Optional[float] = 5000
    weather_temp: Optional[float] = 15
    weather_humidity: Optional[float] = 50
    wind_speed: Optional[float] = 3
    precipitation: Optional[float] = 0
    measurement_date: Optional[str] = None
    
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