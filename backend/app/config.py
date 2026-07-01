from __future__ import annotations

from pathlib import Path
from typing import Dict

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8765
    data_dir: Path = Path("data")
    models_dir: Path = Path("models")
    cors_origins: list[str] = ["http://localhost:5173"]

    profiles: Dict[str, Dict[str, int | float]] = {
        "fast": {"chunk_size": 1000, "chunk_overlap": 100},
        "balanced": {"chunk_size": 2000, "chunk_overlap": 200},
        "accurate": {"chunk_size": 500, "chunk_overlap": 50},
    }

    @property
    def resolved_db_path(self) -> Path:
        return self.data_dir / "hearth.db"

    model_config = {"env_prefix": "HEARTH_"}


settings = Settings()
