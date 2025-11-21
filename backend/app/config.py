"""Конфигурация проекта и пути к данным."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class ProjectConfig:
    """Настройки путей и CORS."""

    project_root: Path
    data_dir: Path
    artifacts_dir: Path
    uploads_dir: Path
    allowed_origins: Tuple[str, ...] = ("*",)

    @property
    def history_path(self) -> Path:
        return self.artifacts_dir / "prediction_history.json"


@lru_cache(maxsize=1)
def get_config() -> ProjectConfig:
    """Возвращает singleton конфигурации проекта."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts_dir = project_root / "ML" / "artifacts"
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return ProjectConfig(
        project_root=project_root,
        data_dir=data_dir,
        artifacts_dir=artifacts_dir,
        uploads_dir=uploads_dir,
    )


__all__ = ["ProjectConfig", "get_config"]

