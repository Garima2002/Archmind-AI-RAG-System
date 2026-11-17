"""Configuration management for ArchiMind AI using Pydantic Settings."""

import os
from typing import List, Literal, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Guard against OpenMP duplicate library errors on Windows/conda
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "ArchiMind AI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Storage Engine
    VECTOR_STORE_TYPE: Literal["pgvector", "memory"] = "memory"

    # PostgreSQL / pgvector settings
    POSTGRES_USER: str = "archimind"
    POSTGRES_PASSWORD: str = "archimind_secret"
    POSTGRES_DB: str = "archimind_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_URL: str = (
        "postgresql+psycopg://archimind:archimind_secret@localhost:5432/archimind_db"
    )

    # Embedding settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_DIMENSION: int = 384

    # LLM Provider settings
    LLM_PROVIDER: Literal["mock", "openai", "anthropic", "gemini"] = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # RAG & Retrieval Guardrails
    DEFAULT_TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = Field(default=0.35, ge=0.0, le=1.0)
    MAX_CONTEXT_LENGTH: int = 4000

    # Ingestion & Security Whitelist (raw string from env or comma-separated)
    ALLOWED_DOC_DOMAINS_RAW: str = Field(
        default="kafka.apache.org,redis.io,docs.aws.amazon.com,www.postgresql.org,www.envoyproxy.io,raft.github.io,raw.githubusercontent.com",
        validation_alias="ALLOWED_DOC_DOMAINS",
    )
    MAX_DOC_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB safe limit
    FETCH_TIMEOUT_SECONDS: float = 15.0

    # LangSmith Observability
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "archimind-ai"

    @property
    def ALLOWED_DOC_DOMAINS(self) -> List[str]:
        """Parsed list of allowed domains."""
        raw = self.ALLOWED_DOC_DOMAINS_RAW
        if isinstance(raw, list):
            return raw
        return [d.strip() for d in raw.split(",") if d.strip()]


# Global singleton instance
settings = Settings()
