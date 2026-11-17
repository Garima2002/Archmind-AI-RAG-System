"""Vector store factory providing unified access to pgvector or in-memory fallback."""

import logging
from typing import Optional

from archimind.config import settings
from archimind.storage.base import VectorStore
from archimind.storage.memory import InMemoryVectorStore

logger = logging.getLogger(__name__)

_vector_store_instance: Optional[VectorStore] = None


def get_vector_store(force_new: bool = False) -> VectorStore:
    """Returns the configured vector store singleton, with graceful fallback."""
    global _vector_store_instance
    if _vector_store_instance is not None and not force_new:
        return _vector_store_instance

    if settings.VECTOR_STORE_TYPE == "pgvector":
        try:
            from archimind.storage.pgvector import PgVectorStore

            store = PgVectorStore(settings.POSTGRES_URL)
            if store.is_healthy():
                logger.info("Using PostgreSQL with pgvector as active vector store.")
                _vector_store_instance = store
                return _vector_store_instance
            else:
                logger.warning(
                    "PostgreSQL at %s is not healthy or unreachable. Falling back to InMemoryVectorStore.",
                    settings.POSTGRES_URL,
                )
        except Exception as e:
            logger.warning(
                "Failed to initialize PgVectorStore (%s). Falling back to InMemoryVectorStore.", e
            )

    logger.info("Using InMemoryVectorStore as active vector store.")
    _vector_store_instance = InMemoryVectorStore()
    return _vector_store_instance
