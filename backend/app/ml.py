"""Интеграция FastAPI c ML-моделью."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from functools import lru_cache
from typing import Any

import pandas as pd

# Add ML module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ML.predictor import CoalCombustionPredictor

from .config import get_config


@lru_cache(maxsize=1)
def _create_predictor() -> CoalCombustionPredictor:
    """Создаёт и кеширует экземпляр ML-модели."""
    cfg = get_config()
    return CoalCombustionPredictor(
        data_dir=cfg.data_dir,
        artifacts_dir=cfg.artifacts_dir,
    )


def get_predictor() -> CoalCombustionPredictor:
    """Dependency для FastAPI."""
    return _create_predictor()


def read_prediction_history(limit: int = 100) -> list[dict[str, Any]]:
    """Возвращает хвост истории прогнозов из артефактов."""
    cfg = get_config()
    history_path = cfg.history_path
    if not history_path.exists():
        return []
    data: list[dict[str, Any]] = json.loads(history_path.read_text(encoding="utf-8"))
    return data[-limit:]


def predictor_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Преобразует запрос модели в DataFrame."""
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


__all__ = ["get_predictor", "read_prediction_history", "predictor_to_dataframe"]