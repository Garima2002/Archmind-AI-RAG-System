"""FastAPI dependency injection providers."""

from functools import lru_cache

from archimind.embeddings.service import EmbeddingService
from archimind.ingestion.pipeline import IngestionPipeline
from archimind.rag.engine import RAGEngine
from archimind.rag.providers.factory import get_llm_provider
from archimind.rag.retriever import SemanticRetriever
from archimind.storage.base import VectorStore
from archimind.storage.factory import get_vector_store


def get_vector_store_dep() -> VectorStore:
    """Dependency providing the active vector store."""
    return get_vector_store()


def get_embedding_service_dep() -> EmbeddingService:
    """Dependency providing the embedding service."""
    return EmbeddingService.get_instance()


def get_ingestion_pipeline_dep() -> IngestionPipeline:
    """Dependency providing the ingestion orchestrator."""
    return IngestionPipeline(
        embedding_service=get_embedding_service_dep(),
        vector_store=get_vector_store_dep(),
    )


def get_rag_engine_dep() -> RAGEngine:
    """Dependency providing the core RAG question-answering engine."""
    retriever = SemanticRetriever(
        vector_store=get_vector_store_dep(),
        embedding_service=get_embedding_service_dep(),
    )
    return RAGEngine(
        retriever=retriever,
        llm_provider=get_llm_provider(),
    )
