"""FastAPI router defining endpoints for health, ingestion, query, and evaluation."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from archimind.api.dependencies import (
    get_embedding_service_dep,
    get_ingestion_pipeline_dep,
    get_rag_engine_dep,
    get_vector_store_dep,
)
from archimind.api.schemas import (
    DocumentMetadata,
    EvaluationRunRequest,
    EvaluationSummary,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from archimind.config import settings
from archimind.embeddings.service import EmbeddingService
from archimind.evaluation.runner import EvaluationRunner
from archimind.ingestion.pipeline import IngestionPipeline
from archimind.rag.engine import RAGEngine
from archimind.storage.base import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns system operational status, storage connectivity, and provider configurations.",
)
async def health_check(
    vector_store: VectorStore = Depends(get_vector_store_dep),
    embedding_service: EmbeddingService = Depends(get_embedding_service_dep),
):
    is_healthy = vector_store.is_healthy()
    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        vector_store_type=settings.VECTOR_STORE_TYPE,
        vector_store_connected=is_healthy,
        embedding_model=settings.EMBEDDING_MODEL_NAME,
        llm_provider=settings.LLM_PROVIDER,
        documents_count=vector_store.count_documents(),
        chunks_count=vector_store.count_chunks(),
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest Technical Documentation",
    description="Fetches, parses, chunks, embeds, and indexes official technical documentation with idempotency.",
)
async def ingest_documents(
    request: IngestRequest = IngestRequest(),
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline_dep),
):
    try:
        response = pipeline.run(request)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Ingestion failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline failed: {str(e)}",
        )


@router.get(
    "/documents",
    response_model=List[DocumentMetadata],
    summary="List Ingested Documents",
    description="Lists all technical documentation currently indexed in the vector store.",
)
async def list_documents(
    vector_store: VectorStore = Depends(get_vector_store_dep),
):
    return vector_store.list_documents()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query System Design Knowledge",
    description="Performs semantic retrieval over technical documentation and generates an evidence-grounded answer with source citations.",
)
async def query_knowledge_base(
    request: QueryRequest,
    rag_engine: RAGEngine = Depends(get_rag_engine_dep),
):
    try:
        response = rag_engine.answer_query(request)
        return response
    except TimeoutError as te:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"LLM provider request timed out: {str(te)}",
        )
    except Exception as e:
        logger.error("Query answering failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}",
        )


@router.post(
    "/evaluate",
    response_model=EvaluationSummary,
    status_code=status.HTTP_200_OK,
    summary="Run Evaluation Benchmark",
    description="Executes the 30-question system design benchmark to evaluate Recall@K, Precision@K, MRR, Faithfulness, and Correctness.",
)
async def run_evaluation(
    request: EvaluationRunRequest = EvaluationRunRequest(),
    rag_engine: RAGEngine = Depends(get_rag_engine_dep),
):
    try:
        runner = EvaluationRunner(rag_engine=rag_engine)
        summary = runner.run(request)
        return summary
    except Exception as e:
        logger.error("Evaluation run failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {str(e)}",
        )
