"""Semantic retrieval module with score thresholding and metadata preservation."""

import logging
from typing import List, Optional

from archimind.api.schemas import DocumentChunkModel
from archimind.config import settings
from archimind.embeddings.service import EmbeddingService
from archimind.storage.base import VectorStore
from archimind.storage.factory import get_vector_store

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Retrieves top-k relevant document chunks for system design queries."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        default_top_k: int = settings.DEFAULT_TOP_K,
        similarity_threshold: float = settings.SIMILARITY_THRESHOLD,
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or EmbeddingService.get_instance()
        self.default_top_k = default_top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> List[DocumentChunkModel]:
        """Performs dense vector retrieval and filters by minimum similarity score."""
        k = top_k if top_k is not None else self.default_top_k
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.similarity_threshold
        )

        query = query.strip()
        if not query:
            return []

        # Generate query vector
        query_embedding = self.embedding_service.embed_query(query)

        # Vector similarity search
        chunks = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=k,
            min_score=threshold,
        )

        logger.info(
            "Retrieved %d candidate chunks for query '%s' (threshold=%.2f)",
            len(chunks),
            query[:60],
            threshold,
        )
        return chunks
