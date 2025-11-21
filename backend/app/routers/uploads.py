"""Маршруты загрузки вспомогательных CSV."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.uploads import store_upload

router = APIRouter(tags=["ingestion"])

ALLOWED_DATASETS = {"supplies", "temperature", "weather", "fires", "current"}


@router.post("/upload", summary="Загрузка CSV-файла")
async def upload_dataset(
    dataset: str,
    file: UploadFile = File(...),
) -> dict[str, str]:
    if dataset not in ALLOWED_DATASETS:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя загрузить тип '{dataset}'. Поддерживаются: {', '.join(sorted(ALLOWED_DATASETS))}.",
        )
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Допускаются только CSV-файлы.")
    stored_path = store_upload(dataset, file)
    return {
        "dataset": dataset,
        "stored_as": str(stored_path),
    }

