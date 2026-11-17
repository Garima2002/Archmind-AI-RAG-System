"""Tests for vector storage, idempotent indexing, and similarity retrieval."""

from archimind.api.schemas import DocumentChunkModel
from archimind.storage.memory import InMemoryVectorStore


def test_idempotent_upsert():
    """Verify that inserting the same chunks multiple times is idempotent."""
    store = InMemoryVectorStore()

    chunks = [
        DocumentChunkModel(
            id="chunk_001",
            document_id="doc_kafka",
            document_title="Kafka Docs",
            document_url="https://kafka.apache.org",
            section_title="Partitions",
            chunk_index=0,
            content="Kafka topics are split into partitions.",
            content_hash="hash123",
            token_count=10,
            embedding=[0.5, 0.5, 0.0, 0.0],
        ),
        DocumentChunkModel(
            id="chunk_002",
            document_id="doc_kafka",
            document_title="Kafka Docs",
            document_url="https://kafka.apache.org",
            section_title="ISR",
            chunk_index=1,
            content="Kafka ISR maintains in-sync replicas.",
            content_hash="hash456",
            token_count=10,
            embedding=[0.0, 0.5, 0.5, 0.0],
        ),
    ]

    # First insertion
    count1 = store.upsert_chunks(chunks)
    assert count1 == 2
    assert store.count_chunks() == 2
    assert store.count_documents() == 1

    # Second insertion with identical chunk IDs (simulating re-ingestion)
    count2 = store.upsert_chunks(chunks)
    assert count2 == 2
    assert store.count_chunks() == 2  # Count must remain exactly 2, not 4
    assert store.count_documents() == 1


def test_cosine_similarity_search():
    """Verify vector search ranks closest vectors highest and respects min_score threshold."""
    store = InMemoryVectorStore()

    chunks = [
        DocumentChunkModel(
            id="c1",
            document_id="d1",
            document_title="Doc A",
            document_url="https://example.com/a",
            chunk_index=0,
            content="Vector pointing mostly in dimension 0",
            content_hash="h1",
            embedding=[1.0, 0.0, 0.0, 0.0],
        ),
        DocumentChunkModel(
            id="c2",
            document_id="d2",
            document_title="Doc B",
            document_url="https://example.com/b",
            chunk_index=0,
            content="Vector pointing equally in dim 0 and 1",
            content_hash="h2",
            embedding=[0.707, 0.707, 0.0, 0.0],
        ),
        DocumentChunkModel(
            id="c3",
            document_id="d3",
            document_title="Doc C",
            document_url="https://example.com/c",
            chunk_index=0,
            content="Orthogonal vector in dim 2",
            content_hash="h3",
            embedding=[0.0, 0.0, 1.0, 0.0],
        ),
    ]
    store.upsert_chunks(chunks)

    # Search with vector aligned with dim 0
    query_vec = [1.0, 0.0, 0.0, 0.0]
    results = store.search(query_vec, top_k=2, min_score=0.5)

    assert len(results) == 2
    assert results[0].id == "c1"
    assert results[0].score == 1.0
    assert results[1].id == "c2"
    assert results[1].score is not None and results[1].score > 0.7

    # Ensure orthogonal vector c3 was filtered out by min_score=0.5
    assert not any(r.id == "c3" for r in results)


def test_document_lifecycle():
    """Verify document metadata tracking and cascade deletion."""
    store = InMemoryVectorStore()
    chunk = DocumentChunkModel(
        id="c100",
        document_id="doc_redis",
        document_title="Redis Guide",
        document_url="https://redis.io/guide",
        chunk_index=0,
        content="Redis persistence guide.",
        content_hash="hash_redis",
        embedding=[0.1, 0.2, 0.3, 0.4],
    )
    store.upsert_chunks([chunk])

    assert store.count_documents() == 1
    docs = store.list_documents()
    assert len(docs) == 1
    assert docs[0].id == "doc_redis"
    assert docs[0].chunk_count == 1

    # Delete
    deleted = store.delete_document("doc_redis")
    assert deleted is True
    assert store.count_documents() == 0
    assert store.count_chunks() == 0
