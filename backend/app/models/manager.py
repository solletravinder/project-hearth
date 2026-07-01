from __future__ import annotations

from typing import Any, Dict, Optional


class ModelManager:
    """Singleton-like manager for ML model lifecycle."""

    _instance: Optional["ModelManager"] = None
    _loaded_models: Dict[str, Any] = {}

    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_status(self) -> Dict[str, Any]:
        """Return status of all managed models."""
        return {
            "loaded_models": list(self._loaded_models.keys()),
            "count": len(self._loaded_models),
        }

    def get_model(self, name: str) -> Optional[Any]:
        """Get a loaded model by name."""
        return self._loaded_models.get(name)

    def unload(self, name: str) -> bool:
        """Unload a model by name."""
        if name in self._loaded_models:
            del self._loaded_models[name]
            return True
        return False

    def load_model(self, name: str, model: Any) -> None:
        """Stub: store a model instance."""
        self._loaded_models[name] = model


model_manager = ModelManager()
