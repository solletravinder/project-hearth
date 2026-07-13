"""Ollama provider — calls Ollama's native HTTP API.

Supports:
- POST /api/chat (streaming)
- POST /api/embed (embeddings)
"""

import json
import logging
from collections.abc import AsyncIterator

import httpx2

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Provider that calls a local Ollama instance."""

    def __init__(self) -> None:
        self._client: httpx2.AsyncClient | None = None
        self._available: bool | None = None

    @property
    def client(self) -> httpx2.AsyncClient:
        if self._client is None:
            self._client = httpx2.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=httpx2.Timeout(120.0, connect=5.0),
            )
        return self._client

    async def check_available(self) -> bool:
        """Check if Ollama is reachable (caches success, always retries on failure)."""
        if self._available:
            return True
        try:
            resp = await self.client.get("/api/tags", timeout=5.0)
            self._available = resp.is_success
        except Exception:
            self._available = False
        return self._available

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts via Ollama /api/embed."""
        if not texts:
            return []
        try:
            resp = await self.client.post(
                "/api/embed",
                json={"model": settings.embedding_model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("embeddings", [])
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            return [[0.0] * 384 for _ in texts]

    async def chat(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Chat via Ollama /api/chat (non-streaming)."""
        model_name = model or settings.default_model or "llama3.2"
        try:
            resp = await self.client.post(
                "/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return f"[Ollama unavailable: {e}]"

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream chat via Ollama /api/chat (SSE streaming)."""
        model_name = model or settings.default_model or "llama3.2"
        try:
            async with self.client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield f"[Ollama unavailable: {e}]"
