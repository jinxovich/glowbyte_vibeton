"""Сервис сохранения загружаемых CSV."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from ..config import get_config


def store_upload(dataset: str, file: UploadFile) -> Path:
    """Сохраняет загруженный CSV в data/uploads/<dataset>/."""
    cfg = get_config()
    dataset_dir = cfg.uploads_dir / dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{dataset}_{timestamp}_{file.filename}"
    target_path = dataset_dir / safe_name

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return target_path


__all__ = ["store_upload"]

