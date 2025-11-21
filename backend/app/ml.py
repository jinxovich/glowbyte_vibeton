"""Интеграция с ML-моделью и утилиты работы с артефактами."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import pandas as pd

from ML.eda_prep import CoalCombustionPredictor

from .config import get_config


@lru_cache(maxsize=1)
def _create_predictor() -> CoalCombustionPredictor:
    cfg = get_config()
    return CoalCombustionPredictor(
        data_dir=cfg.data_dir,
        artifacts_dir=cfg.artifacts_dir,
    )


def get_predictor() -> CoalCombustionPredictor:
    """Dependency-фабрика для FastAPI."""
    return _create_predictor()


def read_prediction_history(limit: int = 100) -> list[dict[str, Any]]:
    """Возвращает последние прогнозы из артефактов."""
    cfg = get_config()
    path = cfg.history_path
    if not path.exists():
        return []
    data: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return data[-limit:]


def predictor_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Преобразует список словарей в DataFrame для модели."""
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


__all__ = ["get_predictor", "read_prediction_history", "predictor_to_dataframe"]

