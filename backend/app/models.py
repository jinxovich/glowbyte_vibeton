from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class UserStatus(str, enum.Enum):
    PENDING = "pending"   # Ждет одобрения
    APPROVED = "approved" # Может пользоваться
    REJECTED = "rejected" # Забанен

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.USER)
    status = Column(String, default=UserStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="owner")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Входные данные
    storage_id = Column(String)
    stack_id = Column(String)
    input_data = Column(JSON)  # Полный JSON входных данных
    
    # Результат ML
    predicted_days = Column(Integer)
    confidence = Column(Integer) # % уверенности
    risk_level = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="predictions")