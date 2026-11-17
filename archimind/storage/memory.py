"""High-performance in-memory vector store with cosine similarity search."""

import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

import numpy as np

from archimind.api.schemas import DocumentChunkModel, DocumentMetadata
from archimind.storage.base import VectorStore

logger = logging.getLogger(__name__)


class InMemoryVectorStore(VectorStore):
    """In-memory vector store for ultra-fast deterministic testing and standalone runs."""

    def __init__(self):
        self._lock = threading.RLock()
        self._chunks: Dict[str, DocumentChunkModel] = {}
        self._documents: Dict[str, DocumentMetadata] = {}

    def upsert_chunks(self, chunks: List[DocumentChunkModel]) -> int:
        """Stores or updates chunks in memory."""
        with self._lock:
            if not chunks:
                return 0

            count = 0
            doc_groups: Dict[str, List[DocumentChunkModel]] = {}

            for chunk in chunks:
                if chunk.embedding is None:
                    continue
                self._chunks[chunk.id] = chunk
                count += 1
                doc_groups.setdefault(chunk.document_id, []).append(chunk)

            # Update document-level registry
            for doc_id, doc_chunks in doc_groups.items():
                first = doc_chunks[0]
                domain = urlparse(first.document_url).hostname or "unknown"
                now_iso = datetime.now(timezone.utc).isoformat()

                # Count all chunks belonging to this doc_id
                total_doc_chunks = sum(
                    1 for c in self._chunks.values() if c.document_id == doc_id
                )

                self._documents[doc_id] = DocumentMetadata(
                    id=doc_id,
                    title=first.document_title,
                    url=first.document_url,
                    source_domain=domain,
                    chunk_count=total_doc_chunks,
                    created_at=now_iso,
                )

            logger.info("InMemoryVectorStore: Upserted %d chunks across %d docs", count, len(doc_groups))
            return count

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        min_score: float = 0.0,
    ) -> List[DocumentChunkModel]:
        """Performs cosine similarity search over stored vectors."""
        with self._lock:
            if not self._chunks:
                return []

            q_vec = np.array(query_embedding, dtype=np.float32)
            q_norm = np.linalg.norm(q_vec)
            if q_norm > 0:
                q_vec = q_vec / q_norm

            results = []
            for chunk in self._chunks.values():
                if chunk.embedding is None:
                    continue
                c_vec = np.array(chunk.embedding, dtype=np.float32)
                c_norm = np.linalg.norm(c_vec)
                if c_norm > 0:
                    c_vec = c_vec / c_norm

                # Cosine similarity for normalized vectors is the dot product
                score = float(np.dot(q_vec, c_vec))
                if score >= min_score:
                    # Return a copy with score attached
                    chunk_copy = chunk.model_copy()
                    chunk_copy.score = round(score, 4)
                    results.append(chunk_copy)

            # Sort descending by similarity score
            results.sort(key=lambda x: x.score or 0.0, reverse=True)
            return results[:top_k]

    def list_documents(self) -> List[DocumentMetadata]:
        """Returns metadata for all tracked documents."""
        with self._lock:
            return list(self._documents.values())

    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Returns metadata for a specific document."""
        with self._lock:
            return self._documents.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document and its corresponding chunks."""
        with self._lock:
            if doc_id not in self._documents:
                return False
            del self._documents[doc_id]
            self._chunks = {
                cid: c for cid, c in self._chunks.items() if c.document_id != doc_id
            }
            return True

    def count_chunks(self) -> int:
        with self._lock:
            return len(self._chunks)

    def count_documents(self) -> int:
        with self._lock:
            return len(self._documents)

    def is_healthy(self) -> bool:
        return True

    def clear(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._documents.clear()
