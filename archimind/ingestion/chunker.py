"""Deterministic text chunker with stable chunk IDs and rich metadata."""

import hashlib
import logging
from typing import List, Optional

from archimind.api.schemas import DocumentChunkModel
from archimind.ingestion.parser import ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


def generate_stable_id(*args: str) -> str:
    """Generates a deterministic 16-character hexadecimal hash ID."""
    hasher = hashlib.sha256()
    for arg in args:
        hasher.update(str(arg).encode("utf-8"))
    return hasher.hexdigest()[:16]


def compute_content_hash(text: str) -> str:
    """Computes SHA-256 hash of normalized text."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


class DocumentChunker:
    """Chunks structured technical documentation with stable IDs and boundary preservation."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        min_chunk_size: int = 60,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def _split_text_by_delimiters(self, text: str) -> List[str]:
        """Splits long text recursively using natural boundaries."""
        if len(text) <= self.chunk_size:
            return [text]

        # Candidate split delimiters in priority order
        delimiters = ["\n\n", "\n", ". ", "; ", ", ", " "]

        for delim in delimiters:
            if delim in text:
                parts = text.split(delim)
                chunks: List[str] = []
                current = ""

                for part in parts:
                    candidate = f"{current}{delim}{part}" if current else part
                    if len(candidate) <= self.chunk_size:
                        current = candidate
                    else:
                        if current and len(current.strip()) >= self.min_chunk_size:
                            chunks.append(current.strip())
                        # Check overlap from end of current
                        overlap_seed = current[-self.chunk_overlap :] if len(current) > self.chunk_overlap else ""
                        current = f"{overlap_seed} {part}".strip()

                if current and len(current.strip()) >= self.min_chunk_size:
                    chunks.append(current.strip())

                if chunks:
                    return chunks

        # Fallback hard chunking if no natural boundary
        return [
            text[i : i + self.chunk_size]
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
        ]

    def chunk_document(self, doc: ParsedDocument) -> List[DocumentChunkModel]:
        """Generates deterministic chunks with metadata from a parsed document."""
        doc_id = generate_stable_id(doc.url)
        all_chunks: List[DocumentChunkModel] = []
        chunk_index = 0

        for section in doc.sections:
            section_chunks = self._split_text_by_delimiters(section.text)

            for chunk_text in section_chunks:
                chunk_text = chunk_text.strip()
                if len(chunk_text) < self.min_chunk_size:
                    continue

                content_hash = compute_content_hash(chunk_text)
                # Stable deterministic ID incorporates doc_id, chunk_index, and content_hash
                chunk_id = generate_stable_id(doc_id, str(chunk_index), content_hash[:8])

                # Approximate token count (~0.75 words per token)
                word_count = len(chunk_text.split())
                approx_tokens = int(word_count * 1.3)

                chunk = DocumentChunkModel(
                    id=chunk_id,
                    document_id=doc_id,
                    document_title=doc.title,
                    document_url=doc.url,
                    section_title=section.section_title,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    content_hash=content_hash,
                    token_count=approx_tokens,
                )
                all_chunks.append(chunk)
                chunk_index += 1

        logger.info(
            "Document '%s' chunked into %d stable chunks", doc.title, len(all_chunks)
        )
        return all_chunks
