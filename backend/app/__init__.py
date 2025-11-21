"""Инициализация FastAPI-приложения и подключение роутеров."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_config
from .routers import health, prediction, training, uploads


def create_app() -> FastAPI:
    """Создаёт экземпляр FastAPI с необходимыми зависимостями."""
    cfg = get_config()

    app = FastAPI(
        title="Coal Spontaneous Combustion API",
        description="REST API для загрузки данных, обучения модели и прогнозов возгорания угольных штабелей.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(uploads.router)
    app.include_router(training.router)
    app.include_router(prediction.router)

    return app


__all__ = ["create_app"]

