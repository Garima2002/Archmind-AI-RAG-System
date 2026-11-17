"""Abstract Base Class for Vector Storage."""

from abc import ABC, abstractmethod
from typing import List, Optional

from archimind.api.schemas import DocumentChunkModel, DocumentMetadata


class VectorStore(ABC):
    """Abstract interface defining required vector store operations."""

    @abstractmethod
    def upsert_chunks(self, chunks: List[DocumentChunkModel]) -> int:
        """Upserts chunks idempotently. Returns count of chunks inserted/updated."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        min_score: float = 0.0,
    ) -> List[DocumentChunkModel]:
        """Performs top-k vector cosine similarity search."""
        pass

    @abstractmethod
    def list_documents(self) -> List[DocumentMetadata]:
        """Lists all indexed documents and their metadata."""
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Retrieves metadata for a specific document."""
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document and all its chunks from the store."""
        pass

    @abstractmethod
    def count_chunks(self) -> int:
        """Returns total number of chunks currently stored."""
        pass

    @abstractmethod
    def count_documents(self) -> int:
        """Returns total number of distinct documents stored."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Checks connectivity and operational health."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clears all stored documents and chunks (primarily for testing)."""
        pass
