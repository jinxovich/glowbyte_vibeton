"""FastAPI application for coal fire prediction."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="🔥 Coal Fire Prediction API",
        description="REST API для прогнозирования самовозгорания угля при открытом хранении",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене ограничить конкретными доменами
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    from .routers import prediction, training, health, analytics
    
    app.include_router(health.router)
    app.include_router(prediction.router)
    app.include_router(training.router)
    app.include_router(analytics.router)
    
    return app


__all__ = ["create_app"]

