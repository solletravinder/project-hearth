"""Embedding model using sentence-transformers with gte-small."""

import logging
import random

import numpy as np
from typing import Optional

from app.models.manager import model_manager

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


class EmbeddingService:
    """Text embedding service. Falls back to mock embeddings if model unavailable."""

    def __init__(self):
        self._model = None

    async def load(self):
        """Load the embedding model (gte-small via sentence-transformers)."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer("gte-small", trust_remote_code=True)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed; using mock embeddings")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}; using mock embeddings")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into 384-dim vectors."""
        if self._model is None:
            await self.load()
        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, normalize_embeddings=True)
                return embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
            except Exception as e:
                logger.error(f"Embedding failed: {e}; falling back to mock")
        # Fallback: random unit vectors
        return [[random.gauss(0, 0.1) for _ in range(EMBEDDING_DIM)] for _ in texts]


embedding_service = EmbeddingService()
