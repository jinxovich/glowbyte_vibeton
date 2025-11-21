"""Configuration for the application."""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    artifacts_dir: Path = project_root / "ML" / "artifacts"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    reload: bool = True
    
    # Model settings
    model_name: str = "coal_fire_model.pkl"
    
    @property
    def model_path(self) -> Path:
        """Get model path."""
        return self.artifacts_dir / "models" / self.model_name
    
    @property
    def metrics_path(self) -> Path:
        """Get metrics path."""
        return self.artifacts_dir / "training_metrics.json"
    
    @property
    def history_path(self) -> Path:
        """Get prediction history path."""
        return self.artifacts_dir / "prediction_history.json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_config() -> Settings:
    """Get cached settings instance."""
    return Settings()


__all__ = ["Settings", "get_config"]

