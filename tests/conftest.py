"""Pytest fixtures and configuration for ArchiMind AI."""

import os
import pytest
from fastapi.testclient import TestClient

# Prevent OpenMP crash
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["APP_ENV"] = "test"
os.environ["VECTOR_STORE_TYPE"] = "memory"
os.environ["LLM_PROVIDER"] = "mock"

from archimind.api.schemas import DocumentChunkModel
from archimind.embeddings.service import EmbeddingService
from archimind.ingestion.chunker import DocumentChunker
from archimind.ingestion.fetcher import DocumentFetcher
from archimind.ingestion.parser import DocumentParser, ParsedDocument, ParsedSection
from archimind.main import app
from archimind.rag.engine import RAGEngine
from archimind.rag.providers.mock import MockLLMProvider
from archimind.rag.retriever import SemanticRetriever
from archimind.storage.memory import InMemoryVectorStore


@pytest.fixture(scope="session")
def embedding_service():
    """Shared embedding service instance."""
    return EmbeddingService.get_instance()


@pytest.fixture
def memory_vector_store():
    """Fresh in-memory vector store for isolated test execution."""
    store = InMemoryVectorStore()
    yield store
    store.clear()


@pytest.fixture
def sample_parsed_document():
    """Sample parsed technical documentation."""
    return ParsedDocument(
        title="Apache Kafka Architecture and Design",
        url="https://kafka.apache.org/documentation/#architecture",
        source_domain="kafka.apache.org",
        sections=[
            ParsedSection(
                section_title="Partitioning and Ordering Guarantees",
                text=(
                    "Kafka provides a total order over records within a single partition, "
                    "but does not guarantee global ordering across multiple partitions. "
                    "Messages with the same key are assigned to the same partition using murmur2 hashing."
                ),
            ),
            ParsedSection(
                section_title="Replication and High Availability",
                text=(
                    "Kafka maintains an In-Sync Replicas (ISR) set for each partition. "
                    "A message is committed only after all ISR replicas have acknowledged writing it."
                ),
            ),
        ],
    )


@pytest.fixture
def mock_llm_provider():
    """Deterministic Mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def rag_engine(memory_vector_store, embedding_service, mock_llm_provider):
    """RAG engine configured with test vector store and mock LLM."""
    retriever = SemanticRetriever(
        vector_store=memory_vector_store,
        embedding_service=embedding_service,
        similarity_threshold=0.30,
    )
    return RAGEngine(
        retriever=retriever,
        llm_provider=mock_llm_provider,
    )


@pytest.fixture
def test_client():
    """FastAPI TestClient for API endpoint testing."""
    with TestClient(app) as client:
        yield client
