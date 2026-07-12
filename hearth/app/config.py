from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8765
    data_dir: Path = Path("data")
    models_dir: Path = Path("models")
    cors_origins: list[str] = ["http://localhost:5173"]

    profiles: dict[str, dict[str, int | float]] = {
        "fast": {"chunk_size": 1000, "chunk_overlap": 100},
        "balanced": {"chunk_size": 2000, "chunk_overlap": 200},
        "accurate": {"chunk_size": 500, "chunk_overlap": 50},
    }

    # Active performance profile
    active_profile: str = "balanced"

    # Local model names
    embedding_model: str = "gte-small"
    whisper_model: str = "base"
    trocr_model: str = "microsoft/trocr-base-printed"
    ner_model: str = "en_core_web_sm"

    # Provider selection
    default_model: str = "smollm2:1.7b-instruct-q4_K_M"
    embedding_provider: Literal["local", "ollama", "openai"] = "local"
    chat_provider: Literal["local", "ollama", "openai"] = "ollama"

    # Remote provider URLs
    ollama_base_url: str = "http://localhost:11434"
    openai_base_url: str = "http://localhost:11434/v1"

    # Frontend static files (React build output)
    frontend_dist_dir: Path = Path("static/frontend/dist")

    # Device and compute
    device: str = "cpu"

    @property
    def resolved_db_path(self) -> Path:
        return self.data_dir / "hearth.db"

    @property
    def active_chunk_size(self) -> int:
        profile = self.profiles.get(self.active_profile)
        if profile:
            return int(profile.get("chunk_size", 2000))
        return 2000

    @property
    def active_chunk_overlap(self) -> int:
        profile = self.profiles.get(self.active_profile)
        if profile:
            return int(profile.get("chunk_overlap", 200))
        return 200

    model_config = {
        "env_prefix": "HEARTH_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
