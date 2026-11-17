"""Pydantic schemas and data models for ArchiMind AI API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class DocumentChunkModel(BaseModel):
    """Schema representing an extracted, embedded document chunk."""

    id: str = Field(description="Deterministic SHA-256 chunk identifier")
    document_id: str = Field(description="Deterministic document identifier")
    document_title: str = Field(description="Document title")
    document_url: str = Field(description="Original source URL")
    section_title: Optional[str] = Field(default=None, description="Heading/section title")
    chunk_index: int = Field(description="Sequential index of chunk within document")
    content: str = Field(description="Text content of the chunk")
    content_hash: str = Field(description="SHA-256 hash of the content")
    token_count: int = Field(default=0, description="Approximate token count")
    embedding: Optional[List[float]] = Field(default=None, description="Dense embedding vector")
    score: Optional[float] = Field(default=None, description="Similarity score when retrieved")


class IngestRequest(BaseModel):
    """Request payload for ingesting technical documentation."""

    urls: Optional[List[str]] = Field(
        default=None,
        description="Optional list of documentation URLs to ingest. Must match ALLOWED_DOC_DOMAINS.",
    )
    use_curated_defaults: bool = Field(
        default=True,
        description="Whether to ingest the official curated set of system design documentation.",
    )
    force_refresh: bool = Field(
        default=False,
        description="Whether to force re-indexing of already existing documents.",
    )


class DocumentMetadata(BaseModel):
    """Metadata summary of an ingested document."""

    id: str
    title: str
    url: str
    source_domain: str
    chunk_count: int
    created_at: str


class IngestResponse(BaseModel):
    """Response payload after running document ingestion."""

    status: str
    documents_ingested: int
    total_chunks: int
    details: List[DocumentMetadata]
    elapsed_seconds: float
    message: str


class Citation(BaseModel):
    """Citation attribution linking answer claims back to technical documentation."""

    citation_id: int = Field(description="Sequential citation marker [1], [2], etc.")
    document_id: str = Field(description="Document ID")
    document_title: str = Field(description="Title of the source document")
    document_url: str = Field(description="Official URL of the source documentation")
    section_title: Optional[str] = Field(default=None, description="Document section/heading")
    chunk_id: str = Field(description="Specific chunk ID used as evidence")
    snippet: str = Field(description="Excerpt of text used as evidence")
    score: float = Field(description="Cosine similarity retrieval score")


class ChatHistoryItem(BaseModel):
    """Single preceding turn in a conversation."""

    role: str = Field(description="'user' or 'assistant'")
    content: str = Field(description="Message text")


class QueryRequest(BaseModel):
    """Query payload for asking system design questions."""

    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="System design question (e.g., 'How does Kafka guarantee message order within a partition?')",
    )
    history: Optional[List[ChatHistoryItem]] = Field(
        default=None,
        description="Preceding conversation turns for follow-up resolution and query contextualization",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of relevant chunks to retrieve (defaults to config DEFAULT_TOP_K)",
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity cutoff score",
    )


class QueryResponse(BaseModel):
    """Grounded answer response with citations and evidence verification."""

    query: str
    answer: str
    is_sufficient_evidence: bool = Field(
        description="True if confident evidence was retrieved; False if fallback was triggered"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of exact citations referenced in the answer",
    )
    retrieved_chunks_count: int
    latency_ms: float
    llm_provider: str
    model_name: str
    token_usage: Optional[Dict[str, int]] = None
    rephrased_query: Optional[str] = Field(
        default=None,
        description="The contextualized standalone query used for vector retrieval if rewritten",
    )
    intent: Optional[str] = Field(
        default="technical",
        description="Detected user intent: 'greeting' | 'technical' | 'conversational'",
    )


class HealthResponse(BaseModel):
    """Service health and component status."""

    status: str
    version: str
    environment: str
    vector_store_type: str
    vector_store_connected: bool
    embedding_model: str
    llm_provider: str
    documents_count: int
    chunks_count: int


class RetrievalMetrics(BaseModel):
    """Standard information retrieval evaluation metrics."""

    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    mrr: float  # Mean Reciprocal Rank


class AnswerMetrics(BaseModel):
    """Evaluation metrics for RAG answer quality and guardrails."""

    mean_faithfulness: float = Field(
        description="Proportion of claims strictly grounded in retrieved evidence [0.0 - 1.0]"
    )
    mean_correctness: float = Field(
        description="Semantic similarity and key fact overlap against ground truth [0.0 - 1.0]"
    )
    unanswerable_detection_accuracy: float = Field(
        description="Accuracy in correctly flagging out-of-scope/unsupported questions [0.0 - 1.0]"
    )


class EvaluationSummary(BaseModel):
    """Full benchmark evaluation run report."""

    total_questions: int
    evaluated_at: str
    retrieval_metrics: RetrievalMetrics
    answer_metrics: AnswerMetrics
    mean_latency_ms: float
    langsmith_dataset_id: Optional[str] = None
    langsmith_sync_status: str


class EvaluationRunRequest(BaseModel):
    """Request to trigger automated evaluation pipeline."""

    max_questions: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Limit the number of benchmark questions to evaluate",
    )
    sync_to_langsmith: bool = Field(
        default=False,
        description="Whether to upload dataset & metrics to LangSmith",
    )
