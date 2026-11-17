"""PostgreSQL Vector Store implementation using pgvector."""

import json
import logging
from typing import List, Optional
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from archimind.api.schemas import DocumentChunkModel, DocumentMetadata
from archimind.config import settings
from archimind.storage.base import VectorStore

logger = logging.getLogger(__name__)


class PgVectorStore(VectorStore):
    """PostgreSQL vector store using pgvector extension."""

    def __init__(self, db_url: str = settings.POSTGRES_URL):
        self.db_url = db_url
        self._engine: Optional[Engine] = None
        self._init_db()

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args={"connect_timeout": 5},
            )
        return self._engine

    def _init_db(self) -> None:
        """Initializes tables and vector extension if they do not exist."""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS documents (
                            id VARCHAR(64) PRIMARY KEY,
                            title TEXT NOT NULL,
                            url TEXT NOT NULL UNIQUE,
                            source_domain VARCHAR(255) NOT NULL,
                            chunk_count INTEGER NOT NULL DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        """
                    )
                )

                conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS document_chunks (
                            id VARCHAR(64) PRIMARY KEY,
                            document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                            document_title TEXT NOT NULL,
                            document_url TEXT NOT NULL,
                            section_title TEXT,
                            chunk_index INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            content_hash VARCHAR(64) NOT NULL,
                            token_count INTEGER NOT NULL DEFAULT 0,
                            embedding vector({settings.EMBEDDING_DIMENSION}) NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        """
                    )
                )

                conn.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(document_id);
                        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
                        ON document_chunks 
                        USING hnsw (embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64);
                        """
                    )
                )
            logger.info("PgVectorStore database tables and vector indexes initialized.")
        except Exception as e:
            logger.warning("Could not initialize PgVectorStore schema: %s", e)

    def upsert_chunks(self, chunks: List[DocumentChunkModel]) -> int:
        """Idempotently inserts or updates document chunks in PostgreSQL."""
        if not chunks:
            return 0

        # Group by document
        doc_map = {}
        for c in chunks:
            if c.document_id not in doc_map:
                domain = urlparse(c.document_url).hostname or "unknown"
                doc_map[c.document_id] = {
                    "id": c.document_id,
                    "title": c.document_title,
                    "url": c.document_url,
                    "source_domain": domain,
                }

        upsert_doc_sql = text(
            """
            INSERT INTO documents (id, title, url, source_domain, chunk_count)
            VALUES (:id, :title, :url, :source_domain, :chunk_count)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                source_domain = EXCLUDED.source_domain,
                chunk_count = EXCLUDED.chunk_count;
            """
        )

        upsert_chunk_sql = text(
            """
            INSERT INTO document_chunks (
                id, document_id, document_title, document_url, section_title,
                chunk_index, content, content_hash, token_count, embedding
            )
            VALUES (
                :id, :document_id, :document_title, :document_url, :section_title,
                :chunk_index, :content, :content_hash, :token_count, :embedding
            )
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash,
                embedding = EXCLUDED.embedding,
                section_title = EXCLUDED.section_title;
            """
        )

        with self.engine.begin() as conn:
            # 1. Update documents
            for doc_id, doc_info in doc_map.items():
                chunk_count = sum(1 for c in chunks if c.document_id == doc_id)
                conn.execute(
                    upsert_doc_sql,
                    {**doc_info, "chunk_count": chunk_count},
                )

            # 2. Insert chunks
            for c in chunks:
                if c.embedding is None:
                    continue
                # Format embedding as string '[0.1, 0.2, ...]' for pgvector
                vec_str = "[" + ",".join(str(val) for val in c.embedding) + "]"
                conn.execute(
                    upsert_chunk_sql,
                    {
                        "id": c.id,
                        "document_id": c.document_id,
                        "document_title": c.document_title,
                        "document_url": c.document_url,
                        "section_title": c.section_title,
                        "chunk_index": c.chunk_index,
                        "content": c.content,
                        "content_hash": c.content_hash,
                        "token_count": c.token_count,
                        "embedding": vec_str,
                    },
                )

        logger.info("PgVectorStore: upserted %d chunks", len(chunks))
        return len(chunks)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        min_score: float = 0.0,
    ) -> List[DocumentChunkModel]:
        """Queries pgvector for top-k chunks with cosine similarity."""
        vec_str = "[" + ",".join(str(val) for val in query_embedding) + "]"
        query_sql = text(
            """
            SELECT 
                id, document_id, document_title, document_url, section_title,
                chunk_index, content, content_hash, token_count,
                1 - (embedding <=> :query_vec) AS similarity
            FROM document_chunks
            WHERE 1 - (embedding <=> :query_vec) >= :min_score
            ORDER BY embedding <=> :query_vec ASC
            LIMIT :top_k;
            """
        )

        with self.engine.connect() as conn:
            result = conn.execute(
                query_sql,
                {"query_vec": vec_str, "min_score": min_score, "top_k": top_k},
            )
            rows = result.fetchall()

        chunks = []
        for row in rows:
            chunks.append(
                DocumentChunkModel(
                    id=row.id,
                    document_id=row.document_id,
                    document_title=row.document_title,
                    document_url=row.document_url,
                    section_title=row.section_title,
                    chunk_index=row.chunk_index,
                    content=row.content,
                    content_hash=row.content_hash,
                    token_count=row.token_count,
                    score=round(float(row.similarity), 4),
                )
            )
        return chunks

    def list_documents(self) -> List[DocumentMetadata]:
        with self.engine.connect() as conn:
            res = conn.execute(
                text(
                    "SELECT id, title, url, source_domain, chunk_count, created_at FROM documents"
                )
            )
            return [
                DocumentMetadata(
                    id=row.id,
                    title=row.title,
                    url=row.url,
                    source_domain=row.source_domain,
                    chunk_count=row.chunk_count,
                    created_at=str(row.created_at),
                )
                for row in res.fetchall()
            ]

    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        with self.engine.connect() as conn:
            res = conn.execute(
                text("SELECT id, title, url, source_domain, chunk_count, created_at FROM documents WHERE id = :id"),
                {"id": doc_id},
            ).fetchone()
            if not res:
                return None
            return DocumentMetadata(
                id=res.id,
                title=res.title,
                url=res.url,
                source_domain=res.source_domain,
                chunk_count=res.chunk_count,
                created_at=str(res.created_at),
            )

    def delete_document(self, doc_id: str) -> bool:
        with self.engine.begin() as conn:
            res = conn.execute(
                text("DELETE FROM documents WHERE id = :id"),
                {"id": doc_id},
            )
            return res.rowcount > 0

    def count_chunks(self) -> int:
        with self.engine.connect() as conn:
            return conn.execute(text("SELECT count(*) FROM document_chunks")).scalar() or 0

    def count_documents(self) -> int:
        with self.engine.connect() as conn:
            return conn.execute(text("SELECT count(*) FROM documents")).scalar() or 0

    def is_healthy(self) -> bool:
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT 1")).scalar()
                return res == 1
        except Exception:
            return False

    def clear(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM document_chunks;"))
            conn.execute(text("DELETE FROM documents;"))
