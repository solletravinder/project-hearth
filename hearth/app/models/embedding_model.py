"""Embedding model using sentence-transformers."""

import logging
import random

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


class EmbeddingService:
    """Text embedding service. Falls back to mock embeddings if model unavailable."""

    def __init__(self):
        self._model = None

    async def load(self):
        """Load the embedding model from settings."""
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not installed; using mock embeddings")
            return
        try:
            model_name = settings.embedding_model
            self._model = SentenceTransformer(model_name, trust_remote_code=True)
            logger.info("Embedding model loaded successfully: %s", model_name)
        except Exception as e:
            logger.warning("Failed to load embedding model: %s; using mock embeddings", e)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vectors."""
        if self._model is None:
            await self.load()
        if self._model is not None and HAS_NUMPY:
            try:
                embeddings = self._model.encode(texts, normalize_embeddings=True)
                return embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
            except Exception as e:
                logger.error("Embedding failed: %s; falling back to mock", e)
        # Fallback: random unit vectors
        return [[random.gauss(0, 0.1) for _ in range(EMBEDDING_DIM)] for _ in texts]


embedding_service = EmbeddingService()
