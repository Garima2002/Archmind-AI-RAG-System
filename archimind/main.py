"""FastAPI Application entrypoint for ArchiMind AI."""

import os
import time
from contextlib import asynccontextmanager

# Prevent OpenMP crash on Windows / conda environments
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from archimind.api.router import router as api_v1_router
from archimind.config import settings
from archimind.embeddings.service import EmbeddingService
from archimind.logging_config import setup_logging
from archimind.storage.factory import get_vector_store

logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and graceful shutdown."""
    logger.info("Initializing %s v%s (%s)...", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)

    # 1. Warm up vector store
    store = get_vector_store()
    logger.info("Vector store initialized (type=%s, healthy=%s)", settings.VECTOR_STORE_TYPE, store.is_healthy())

    # 2. Pre-warm embedding service
    logger.info("Pre-warming embedding service model '%s'...", settings.EMBEDDING_MODEL_NAME)
    emb_service = EmbeddingService.get_instance()
    _ = emb_service.embed_query("warmup system design query")
    logger.info("Embedding service ready.")

    # 3. Auto-populate curated docs if store is empty (e.g. In-Memory store on startup)
    if store.count_chunks() == 0:
        logger.info("Vector store is empty on startup. Automatically ingesting curated documentation...")
        try:
            from archimind.ingestion.pipeline import IngestionPipeline
            pipeline = IngestionPipeline(vector_store=store, embedding_service=emb_service)
            res = pipeline.run()
            logger.info(
                "Auto-ingestion complete: indexed %d chunks across %d docs in %.2fs",
                res.total_chunks,
                res.documents_ingested,
                res.elapsed_seconds,
            )
        except Exception as e:
            logger.warning("Auto-ingestion failed during startup: %s", e)

    logger.info("ArchiMind AI application startup complete. Listening on %s:%d", settings.APP_HOST, settings.APP_PORT)
    yield
    logger.info("ArchiMind AI application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "ArchiMind AI: An evidence-grounded System Design Knowledge Assistant using RAG. "
        "Answers technical architecture queries with source citations and strict hallucination guardrails."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Measures request latency and adds X-Process-Time-Ms header."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

    # Log request metrics
    logger.info(
        "%s %s - status=%d latency=%.2fms",
        request.method,
        request.url.path,
        response.status_code,
        process_time_ms,
    )
    return response


@app.get("/", tags=["Root"])
async def root():
    """Service root endpoint returning project metadata and quick links."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Evidence-grounded System Design Knowledge Assistant using RAG",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "query_endpoint": "/api/v1/query",
        "evaluate_endpoint": "/api/v1/evaluate",
    }


# Health alias at root level
@app.get("/health", tags=["Health"])
async def health_alias():
    store = get_vector_store()
    return {
        "status": "healthy" if store.is_healthy() else "degraded",
        "version": settings.APP_VERSION,
        "vector_store": settings.VECTOR_STORE_TYPE,
    }


# Include API v1 routes
app.include_router(api_v1_router, prefix="/api/v1", tags=["ArchiMind AI v1"])
