"""Tests for RAG engine, evidence grounding, citations, and insufficient-evidence handling."""

import pytest
from unittest.mock import MagicMock

from archimind.api.schemas import DocumentChunkModel, QueryRequest
from archimind.rag.engine import RAGEngine
from archimind.rag.prompt import INSUFFICIENT_EVIDENCE_FALLBACK
from archimind.rag.providers.base import LLMProvider, LLMResponse
from archimind.rag.retriever import SemanticRetriever
from archimind.storage.memory import InMemoryVectorStore


def test_rag_query_with_grounded_citations(rag_engine, memory_vector_store, embedding_service):
    """Verify that a valid question retrieves relevant evidence and attaches citations."""
    # Seed vector store with Kafka partitioning text
    content = (
        "Kafka provides a total order over records within a single partition, "
        "but does not guarantee global ordering across multiple partitions within the same topic. "
        "Messages with the same key are assigned to the same partition using murmur2 hashing."
    )
    emb = embedding_service.embed_query(content)
    chunk = DocumentChunkModel(
        id="chunk_kafka_001",
        document_id="doc_kafka",
        document_title="Apache Kafka Architecture and Design",
        document_url="https://kafka.apache.org/documentation/#architecture",
        section_title="Partitioning and Ordering",
        chunk_index=0,
        content=content,
        content_hash="khash1",
        embedding=emb,
    )
    memory_vector_store.upsert_chunks([chunk])

    request = QueryRequest(query="How does Kafka guarantee message order within a partition?")
    response = rag_engine.answer_query(request)

    assert response.is_sufficient_evidence is True
    assert len(response.citations) > 0
    assert response.citations[0].document_title == "Apache Kafka Architecture and Design"
    assert response.citations[0].document_url == "https://kafka.apache.org/documentation/#architecture"
    assert "murmur2" in response.answer or "partition" in response.answer
    assert response.latency_ms > 0


def test_rag_empty_retrieval_insufficient_evidence(rag_engine, memory_vector_store):
    """Verify that an empty vector store triggers the insufficient evidence fallback."""
    # Ensure memory_vector_store is completely empty
    memory_vector_store.clear()

    request = QueryRequest(query="What is the internal threading model of Envoy Proxy?")
    response = rag_engine.answer_query(request)

    assert response.is_sufficient_evidence is False
    assert response.answer == INSUFFICIENT_EVIDENCE_FALLBACK
    assert len(response.citations) == 0
    assert response.retrieved_chunks_count == 0


def test_rag_unsupported_out_of_scope_query(rag_engine, memory_vector_store, embedding_service):
    """Verify that out-of-scope questions (e.g. recipe, quantum physics) trigger insufficient evidence."""
    # Even if some unrelated text is in the store
    content = "PostgreSQL MVCC uses xmin and xmax for row visibility."
    emb = embedding_service.embed_query(content)
    chunk = DocumentChunkModel(
        id="c_pg",
        document_id="d_pg",
        document_title="PostgreSQL Docs",
        document_url="https://www.postgresql.org/docs/current/mvcc.html",
        chunk_index=0,
        content=content,
        content_hash="pg_hash",
        embedding=emb,
    )
    memory_vector_store.upsert_chunks([chunk])

    # Ask completely unrelated question
    request = QueryRequest(query="Can you give me a recipe for baking a chocolate cake?")
    response = rag_engine.answer_query(request)

    assert response.is_sufficient_evidence is False
    assert "not have enough evidence" in response.answer.lower()
    assert len(response.citations) == 0


def test_rag_provider_failure_handling(memory_vector_store, embedding_service):
    """Verify that provider timeouts or network exceptions are raised clearly."""
    # Seed storage so retrieval succeeds
    chunk = DocumentChunkModel(
        id="c1",
        document_id="d1",
        document_title="Sample",
        document_url="https://example.com",
        chunk_index=0,
        content="Sample content for retrieval test.",
        content_hash="h1",
        embedding=embedding_service.embed_query("Sample content"),
    )
    memory_vector_store.upsert_chunks([chunk])

    # Mock provider that throws TimeoutError
    failing_provider = MagicMock(spec=LLMProvider)
    failing_provider.provider_name = "failing-mock"
    failing_provider.model_name = "fail-v1"
    failing_provider.generate.side_effect = TimeoutError("Simulated LLM connection timeout")

    retriever = SemanticRetriever(
        vector_store=memory_vector_store,
        embedding_service=embedding_service,
        similarity_threshold=0.1,
    )
    engine = RAGEngine(retriever=retriever, llm_provider=failing_provider)

    with pytest.raises(TimeoutError, match="Simulated LLM connection timeout"):
        engine.answer_query(QueryRequest(query="Sample query"))
