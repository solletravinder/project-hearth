"""ProviderRegistry — selects the active provider based on settings."""

import logging
from typing import TYPE_CHECKING

from app.config import settings
from app.models.embedding_model import EmbeddingService
from app.models.trocr_model import trocr_service
from app.models.whisper_model import whisper_service

if TYPE_CHECKING:
    from app.providers.base import EmbeddingProvider
    from app.providers.ollama import OllamaProvider
    from app.providers.openai_compat import OpenAICompatProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry that provides the correct model provider based on settings.

    Provider flow:
        1. User sets embedding_provider or chat_provider in settings
        2. ProviderRegistry returns the correct provider instance
        3. If a remote provider is selected but unavailable, falls back to local
        4. If local models aren't installed, falls back to mock (same as before)
    """

    def __init__(self) -> None:
        self._embedding_service = EmbeddingService()
        self._ollama: OllamaProvider | None = None
        self._openai: OpenAICompatProvider | None = None

    # ── Lazy init helpers ──────────────────────────────────────────────

    def _get_ollama(self):
        if self._ollama is None:
            try:
                from app.providers.ollama import OllamaProvider

                self._ollama = OllamaProvider()
            except Exception as e:
                logger.warning(f"Failed to init Ollama provider: {e}")
        return self._ollama

    def _get_openai(self):
        if self._openai is None:
            try:
                from app.providers.openai_compat import OpenAICompatProvider

                self._openai = OpenAICompatProvider()
            except Exception as e:
                logger.warning(f"Failed to init OpenAI-compat provider: {e}")
        return self._openai

    # ── Embedding selection ────────────────────────────────────────────

    def get_embedding(self, preferred: str = "") -> "EmbeddingProvider":
        """Return the embedding provider selected by settings.

        Falls back: ollama/openai → local → mock
        """
        provider_name = preferred or settings.embedding_provider

        if provider_name == "ollama":
            provider = self._get_ollama()
            if provider is not None:
                return provider
        elif provider_name == "openai":
            provider = self._get_openai()
            if provider is not None:
                return provider

        # Fallback to local
        return self._embedding_service

    # ── Chat selection ─────────────────────────────────────────────────

    def get_chat(self, preferred: str = ""):
        """Return the chat provider selected by settings.

        Falls back: ollama/openai → mock only (no local chat yet)
        """
        provider_name = preferred or settings.chat_provider

        if provider_name == "ollama":
            provider = self._get_ollama()
            if provider is not None:
                return provider
        elif provider_name == "openai":
            provider = self._get_openai()
            if provider is not None:
                return provider

        # No local chat model yet — return None so caller uses mock
        return None

    # ── Transcription / OCR ────────────────────────────────────────────

    def get_transcriber(self):
        """Return the transcription service (local only for now)."""
        return whisper_service

    def get_ocr(self):
        """Return the OCR service (local only for now)."""
        return trocr_service

    # ── Status ─────────────────────────────────────────────────────────

    async def get_status(self) -> dict:
        """Return availability status of all providers."""
        ollama = self._get_ollama()
        openai = self._get_openai()

        return {
            "providers": {
                "local": {"available": True, "type": "local"},
                "ollama": {
                    "available": ollama is not None and await ollama.check_available(),
                    "type": "ollama",
                    "base_url": settings.ollama_base_url,
                },
                "openai": {
                    "available": openai is not None and await openai.check_available(),
                    "type": "openai",
                    "base_url": settings.openai_base_url,
                },
            },
            "active": {
                "embedding": settings.embedding_provider,
                "chat": settings.chat_provider,
            },
        }


provider_registry = ProviderRegistry()
