"""Base protocols for model providers."""

from collections.abc import AsyncIterator
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for text embedding providers."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into float vectors."""
        ...


class ChatProvider(Protocol):
    """Protocol for chat completion providers."""

    async def chat(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request and return the response text."""
        ...

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Send a streaming chat completion request.

        Yields tokens as they arrive.
        """
        ...
        yield ""  # pragma: no cover


class TranscriptionProvider(Protocol):
    """Protocol for speech-to-text providers."""

    async def transcribe(self, audio_path: str) -> str:
        """Transcribe an audio file to text."""
        ...


class OCRProvider(Protocol):
    """Protocol for image OCR providers."""

    async def ocr(self, image_path: str) -> str:
        """Extract text from an image."""
        ...
