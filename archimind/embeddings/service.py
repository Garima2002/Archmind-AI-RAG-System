"""Dense vector embedding service using Sentence Transformers."""

import logging
import os
from typing import List, Optional

import numpy as np

# Prevent OpenMP runtime conflict on Windows/conda
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from archimind.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Manages text embedding generation via Sentence Transformers."""

    _instance: Optional["EmbeddingService"] = None

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        device: str = settings.EMBEDDING_DEVICE,
        dimension: int = settings.EMBEDDING_DIMENSION,
    ):
        self.model_name = model_name
        self.device = device
        self.dimension = dimension
        self._model = None

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Singleton accessor for the embedding service."""
        if cls._instance is None:
            cls._instance = EmbeddingService()
        return cls._instance

    @property
    def model(self):
        """Lazy loader for SentenceTransformer model."""
        if self._model is None:
            logger.info("Loading embedding model '%s' on %s...", self.model_name, self.device)
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def embed_query(self, query: str) -> List[float]:
        """Embeds a single query string into a normalized dense vector."""
        if not query or not query.strip():
            return [0.0] * self.dimension
        embedding = self.model.encode(
            query.strip(),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embeds a batch of texts into normalized dense vectors."""
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()
