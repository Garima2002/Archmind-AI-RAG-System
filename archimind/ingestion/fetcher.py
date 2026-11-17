"""Safe document fetcher with domain whitelisting, timeout protection, and curated sources."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

from archimind.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RawDocument:
    """Container for fetched raw document data."""

    url: str
    title: str
    content: str  # HTML or plain text
    source_domain: str
    is_cached_fallback: bool = False


# Official curated documentation registry
CURATED_DOCUMENTS: List[Dict[str, str]] = [
    {
        "url": "https://kafka.apache.org/documentation/#architecture",
        "title": "Apache Kafka Architecture and Design",
        "local_cache": "kafka_architecture.html",
        "domain": "kafka.apache.org",
    },
    {
        "url": "https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/",
        "title": "Redis Architecture: In-Memory Data Store, Persistence, and High Availability",
        "local_cache": "redis_architecture.html",
        "domain": "redis.io",
    },
    {
        "url": "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html",
        "title": "Amazon DynamoDB Core Architecture and Distributed Design",
        "local_cache": "dynamodb_architecture.html",
        "domain": "docs.aws.amazon.com",
    },
    {
        "url": "https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/overview",
        "title": "Envoy Proxy Architecture and Network Threading Model",
        "local_cache": "envoy_proxy_architecture.html",
        "domain": "www.envoyproxy.io",
    },
    {
        "url": "https://raft.github.io/raft.pdf",
        "title": "In Search of an Understandable Consensus Algorithm: Raft",
        "local_cache": "raft_consensus.html",
        "domain": "raft.github.io",
    },
    {
        "url": "https://www.postgresql.org/docs/current/mvcc.html",
        "title": "PostgreSQL Internal Architecture: MVCC, WAL, and Buffer Management",
        "local_cache": "postgresql_architecture.html",
        "domain": "www.postgresql.org",
    },
]


class DocumentFetcher:
    """Safe document fetcher respecting security rules and size limits."""

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        timeout: float = settings.FETCH_TIMEOUT_SECONDS,
        max_size_bytes: int = settings.MAX_DOC_SIZE_BYTES,
    ):
        self.allowed_domains = allowed_domains or settings.ALLOWED_DOC_DOMAINS
        self.timeout = timeout
        self.max_size_bytes = max_size_bytes
        self.curated_dir = Path(__file__).parent.parent / "data" / "curated_docs"

    def is_domain_allowed(self, url: str) -> bool:
        """Validates that a URL belongs to the allowed domain whitelist (SSRF prevention)."""
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False
        return any(
            hostname == domain.lower() or hostname.endswith("." + domain.lower())
            for domain in self.allowed_domains
        )

    def fetch_from_local_cache(self, filename: str, url: str, title: str) -> Optional[RawDocument]:
        """Loads a curated document from local disk cache."""
        file_path = self.curated_dir / filename
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                domain = urlparse(url).hostname or "local"
                logger.info("Loaded document from curated local cache: %s", filename)
                return RawDocument(
                    url=url,
                    title=title,
                    content=content,
                    source_domain=domain,
                    is_cached_fallback=True,
                )
            except Exception as e:
                logger.warning("Failed reading cached file %s: %s", filename, e)
        return None

    def fetch_url(self, url: str) -> RawDocument:
        """Fetches document from the web with SSRF validation, size limits, and fallback."""
        if not self.is_domain_allowed(url):
            raise ValueError(
                f"URL '{url}' is not permitted by domain whitelist: {self.allowed_domains}"
            )

        # Check if URL matches a curated document with local cache
        cached_match = next((item for item in CURATED_DOCUMENTS if item["url"] == url), None)

        try:
            headers = {"User-Agent": "ArchiMind-AI-Knowledge-Bot/1.0 (+system-design-research)"}
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                response = client.get(url)
                response.raise_for_status()

                # Content size limit guard
                content_len = len(response.content)
                if content_len > self.max_size_bytes:
                    raise ValueError(
                        f"Document size ({content_len} bytes) exceeds limit of {self.max_size_bytes} bytes"
                    )

                domain = urlparse(url).hostname or "unknown"
                title = cached_match["title"] if cached_match else f"Technical Docs ({domain})"
                return RawDocument(
                    url=url,
                    title=title,
                    content=response.text,
                    source_domain=domain,
                    is_cached_fallback=False,
                )
        except Exception as e:
            logger.warning("Live HTTP fetch failed for %s: %s", url, e)
            if cached_match and cached_match.get("local_cache"):
                cached_doc = self.fetch_from_local_cache(
                    cached_match["local_cache"], cached_match["url"], cached_match["title"]
                )
                if cached_doc:
                    return cached_doc
            raise RuntimeError(f"Failed to fetch document from {url}: {e}") from e

    def fetch_all_curated(self) -> List[RawDocument]:
        """Fetches all curated technical documentation documents."""
        docs: List[RawDocument] = []
        for item in CURATED_DOCUMENTS:
            url = item["url"]
            title = item["title"]
            cache_file = item.get("local_cache")

            # Try local cache first for curated docs to ensure fast, deterministic offline performance
            if cache_file:
                cached = self.fetch_from_local_cache(cache_file, url, title)
                if cached:
                    docs.append(cached)
                    continue

            # Fallback to live fetch
            try:
                doc = self.fetch_url(url)
                docs.append(doc)
            except Exception as e:
                logger.error("Failed to ingest curated doc %s: %s", url, e)
        return docs
