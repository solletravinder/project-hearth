from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


@dataclass
class ModelEntry:
    name: str
    status: str = "unloaded"  # unloaded | loading | ready | error
    loaded_at: Optional[datetime] = None
    memory_mb: float = 0.0
    error: Optional[str] = None
    ttl_seconds: int = 900  # 15 min default


class ModelManager:
    _instance: Optional["ModelManager"] = None
    _models: dict[str, ModelEntry] = {}
    _instances: dict[str, Any] = {}  # actual loaded model objects
    _active_profile: Optional[str] = None

    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, name: str) -> Optional[Any]:
        return self._instances.get(name)

    def register_model(self, name: str, entry: ModelEntry) -> None:
        self._models[name] = entry

    async def load_model(self, name: str, loader: Callable) -> Any:
        """Lazy-load a model, caching the instance."""
        if name in self._instances:
            return self._instances[name]
        entry = self._models.get(name, ModelEntry(name=name))
        entry.status = "loading"
        try:
            instance = await loader()
            self._instances[name] = instance
            entry.status = "ready"
            entry.loaded_at = datetime.now(timezone.utc)
        except Exception as e:
            entry.status = "error"
            entry.error = str(e)
            raise
        self._models[name] = entry
        return self._instances[name]

    def unload(self, name: str) -> bool:
        if name in self._instances:
            del self._instances[name]
        if name in self._models:
            self._models[name].status = "unloaded"
            self._models[name].loaded_at = None
            return True
        return False

    def get_status(self) -> dict:
        models_status = {}
        for name, entry in self._models.items():
            models_status[name] = {
                "status": entry.status,
                "loaded_at": entry.loaded_at.isoformat() if entry.loaded_at else None,
                "memory_mb": entry.memory_mb,
                "error": entry.error,
            }
        return {
            "models": models_status,
            "active_profile": self._active_profile,
            "loaded_count": len(self._instances),
        }


model_manager = ModelManager()
