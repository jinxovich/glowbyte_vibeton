from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, admin, prediction

# Создаем таблицы при старте
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Coal Fire Prediction System",
    description="Backend API for Vibeton Hackathon 2025",
    version="1.0.0"
)

# CORS (чтобы фронтенд мог стучаться)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # В проде указать конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(prediction.router)

@app.get("/")
def root():
    return {"message": "Coal Fire Prediction API is running 🔥"}