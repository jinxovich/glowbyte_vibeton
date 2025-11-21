"""Маршруты здоровья сервиса."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["service"])


@router.get("/health", summary="Проверка доступности API")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

