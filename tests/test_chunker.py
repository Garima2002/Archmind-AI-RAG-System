"""Tests for deterministic chunking, stable IDs, and metadata integrity."""

from archimind.ingestion.chunker import (
    DocumentChunker,
    compute_content_hash,
    generate_stable_id,
)
from archimind.ingestion.parser import ParsedDocument, ParsedSection


def test_stable_id_determinism():
    """Verify that generate_stable_id produces the exact same hash across independent calls."""
    id1 = generate_stable_id("https://kafka.apache.org", "0", "abc12345")
    id2 = generate_stable_id("https://kafka.apache.org", "0", "abc12345")
    id3 = generate_stable_id("https://kafka.apache.org", "1", "abc12345")

    assert id1 == id2
    assert id1 != id3
    assert len(id1) == 16


def test_chunking_metadata_preservation(sample_parsed_document):
    """Verify that chunking preserves URLs, titles, section headers, and generates valid hashes."""
    chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_document(sample_parsed_document)

    assert len(chunks) >= 2
    for idx, chunk in enumerate(chunks):
        assert chunk.document_url == sample_parsed_document.url
        assert chunk.document_title == sample_parsed_document.title
        assert chunk.document_id == generate_stable_id(sample_parsed_document.url)
        assert chunk.chunk_index == idx
        assert chunk.content_hash == compute_content_hash(chunk.content)
        assert chunk.token_count > 0
        assert chunk.id is not None and len(chunk.id) == 16


def test_chunking_deterministic_across_runs(sample_parsed_document):
    """Verify that identical input always produces identical chunk IDs and contents."""
    chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
    run1 = chunker.chunk_document(sample_parsed_document)
    run2 = chunker.chunk_document(sample_parsed_document)

    assert len(run1) == len(run2)
    for c1, c2 in zip(run1, run2):
        assert c1.id == c2.id
        assert c1.content == c2.content
        assert c1.content_hash == c2.content_hash


def test_chunking_respects_max_size():
    """Verify that chunks respect the configured maximum character boundary."""
    long_text = "Kafka distributed commit log architecture. " * 30
    doc = ParsedDocument(
        title="Long Test Doc",
        url="https://example.com/long",
        source_domain="example.com",
        sections=[ParsedSection(section_title="Architecture", text=long_text)],
    )

    chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 1
    for chunk in chunks:
        # Chunks should be within bounds
        assert len(chunk.content) <= 300
