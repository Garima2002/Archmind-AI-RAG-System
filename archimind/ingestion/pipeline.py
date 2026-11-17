"""Ingestion pipeline coordinating fetching, cleaning, chunking, embedding, and storing."""

import logging
import time
from typing import List, Optional

from archimind.api.schemas import (
    DocumentChunkModel,
    DocumentMetadata,
    IngestRequest,
    IngestResponse,
)
from archimind.embeddings.service import EmbeddingService
from archimind.ingestion.chunker import DocumentChunker
from archimind.ingestion.fetcher import DocumentFetcher, RawDocument
from archimind.ingestion.parser import DocumentParser
from archimind.storage.base import VectorStore
from archimind.storage.factory import get_vector_store

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """End-to-end documentation ingestion and vector indexing orchestrator."""

    def __init__(
        self,
        fetcher: Optional[DocumentFetcher] = None,
        parser: Optional[DocumentParser] = None,
        chunker: Optional[DocumentChunker] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.fetcher = fetcher or DocumentFetcher()
        self.parser = parser or DocumentParser()
        self.chunker = chunker or DocumentChunker()
        self.embedding_service = embedding_service or EmbeddingService.get_instance()
        self.vector_store = vector_store or get_vector_store()

    def run(self, request: Optional[IngestRequest] = None) -> IngestResponse:
        """Executes full ingestion workflow with idempotent chunk insertion."""
        start_time = time.perf_counter()
        request = request or IngestRequest(use_curated_defaults=True)

        raw_docs: List[RawDocument] = []

        # 1. Fetch curated default sources if requested
        if request.use_curated_defaults:
            logger.info("Ingesting curated technical documentation set...")
            curated_docs = self.fetcher.fetch_all_curated()
            raw_docs.extend(curated_docs)

        # 2. Fetch any explicitly provided URLs
        if request.urls:
            for url in request.urls:
                try:
                    logger.info("Fetching custom documentation URL: %s", url)
                    doc = self.fetcher.fetch_url(str(url))
                    raw_docs.append(doc)
                except Exception as e:
                    logger.error("Failed to fetch custom URL %s: %s", url, e)

        if not raw_docs:
            elapsed = time.perf_counter() - start_time
            return IngestResponse(
                status="warning",
                documents_ingested=0,
                total_chunks=0,
                details=[],
                elapsed_seconds=round(elapsed, 3),
                message="No documents were fetched or available to ingest.",
            )

        all_chunks: List[DocumentChunkModel] = []
        doc_summaries: List[DocumentMetadata] = []

        # 3. Parse and chunk each document
        for raw in raw_docs:
            parsed = self.parser.parse(
                raw_content=raw.content,
                url=raw.url,
                fallback_title=raw.title,
                domain=raw.source_domain,
            )

            chunks = self.chunker.chunk_document(parsed)
            if not chunks:
                continue

            all_chunks.extend(chunks)

        logger.info(
            "Extracted total %d chunks from %d documents. Generating embeddings...",
            len(all_chunks),
            len(raw_docs),
        )

        # 4. Generate embeddings in batches
        texts_to_embed = [c.content for c in all_chunks]
        embeddings = self.embedding_service.embed_texts(texts_to_embed)

        for chunk, emb in zip(all_chunks, embeddings):
            chunk.embedding = emb

        # 5. Idempotent upsert into vector store
        upserted_count = self.vector_store.upsert_chunks(all_chunks)

        # 6. Retrieve updated document summaries
        doc_summaries = self.vector_store.list_documents()

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Ingestion completed in %.2fs: %d documents, %d chunks indexed.",
            elapsed,
            len(doc_summaries),
            upserted_count,
        )

        return IngestResponse(
            status="success",
            documents_ingested=len(doc_summaries),
            total_chunks=upserted_count,
            details=doc_summaries,
            elapsed_seconds=round(elapsed, 3),
            message=f"Successfully indexed {len(doc_summaries)} technical documents with {upserted_count} chunks.",
        )
