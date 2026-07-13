"""Local LLM provider — loads GGUF models via llama-cpp-python.

Falls back to Ollama if llama-cpp-python is not installed.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_llm_instance = None


def _find_gguf(model_name: str) -> Path | None:
    """Search for a GGUF file matching the model name in models_dir."""
    models_dir = settings.models_dir
    if not models_dir.exists():
        return None

    # Direct filename match
    for f in models_dir.glob("*.gguf"):
        if model_name.lower() in f.stem.lower():
            return f

    # Fallback: first GGUF found
    ggufs = list(models_dir.glob("*.gguf"))
    return ggufs[0] if ggufs else None


def _get_llm():
    """Load or return cached llama-cpp-python LLM instance."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    try:
        from llama_cpp import Llama
    except ImportError:
        logger.warning("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        return None

    model_name = settings.default_model
    gguf_path = _find_gguf(model_name)
    if gguf_path is None:
        logger.warning("No GGUF model found in %s for model '%s'", settings.models_dir, model_name)
        return None

    logger.info("Loading GGUF model: %s", gguf_path)
    try:
        _llm_instance = Llama(
            model_path=str(gguf_path),
            n_ctx=2048,
            n_threads=2,
            verbose=False,
        )
        logger.info("GGUF model loaded successfully: %s", gguf_path.name)
        return _llm_instance
    except Exception as e:
        logger.error("Failed to load GGUF model: %s", e)
        return None


class LlamaCppProvider:
    """Chat provider that loads GGUF models in-process via llama-cpp-python."""

    async def check_available(self) -> bool:
        """Check if llama-cpp-python is installed and a GGUF model exists."""
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            return False
        return _find_gguf(settings.default_model) is not None

    async def chat(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        llm = _get_llm()
        if llm is None:
            return "[Local LLM unavailable: no GGUF model found]"

        loop = asyncio.get_running_loop()

        def _run():
            return llm.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        try:
            result = await loop.run_in_executor(None, _run)
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Local LLM chat failed: %s", e)
            return f"[Local LLM error: {e}]"

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        llm = _get_llm()
        if llm is None:
            yield "[Local LLM unavailable: no GGUF model found]"
            return

        loop = asyncio.get_running_loop()

        def _run_stream():
            return llm.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

        try:
            stream = await loop.run_in_executor(None, _run_stream)
            for chunk in stream:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
        except Exception as e:
            logger.error("Local LLM streaming failed: %s", e)
            yield f"[Local LLM error: {e}]"
