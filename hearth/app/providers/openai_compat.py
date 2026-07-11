"""OpenAI-compatible provider — for llama.cpp, LocalAI, vLLM, etc.

Uses the standard OpenAI API format:
- POST /v1/chat/completions
- POST /v1/embeddings
"""

import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAICompatProvider:
    """Provider that calls any OpenAI-compatible API endpoint."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._available: bool | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.openai_base_url,
                timeout=httpx.Timeout(120.0, connect=5.0),
            )
        return self._client

    async def check_available(self) -> bool:
        """Check if the API is reachable (caches success, always retries on failure)."""
        if self._available:
            return True
        try:
            resp = await self.client.get("/v1/models", timeout=5.0)
            self._available = resp.is_success
        except Exception:
            self._available = False
        return self._available

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts via /v1/embeddings."""
        if not texts:
            return []
        try:
            resp = await self.client.post(
                "/v1/embeddings",
                json={"model": settings.embedding_model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]
        except Exception as e:
            logger.error(f"OpenAI-compat embedding failed: {e}")
            return [[0.0] * 384 for _ in texts]

    async def chat(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Chat via /v1/chat/completions (non-streaming)."""
        model_name = model or settings.default_model or "llama3.2"
        try:
            resp = await self.client.post(
                "/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"OpenAI-compat chat failed: {e}")
            return f"[API unavailable: {e}]"

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream chat via /v1/chat/completions (SSE streaming)."""
        model_name = model or settings.default_model or "llama3.2"
        try:
            async with self.client.stream(
                "POST",
                "/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    if line.startswith("data: "):
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"OpenAI-compat streaming failed: {e}")
            yield f"[API unavailable: {e}]"
