"""Tests for secure document fetching, domain whitelisting, and SSRF prevention."""

import pytest
from archimind.ingestion.fetcher import DocumentFetcher


def test_allowed_domain_validation():
    """Verify whitelist allows approved technical documentation domains and subdomains."""
    fetcher = DocumentFetcher(
        allowed_domains=["kafka.apache.org", "redis.io", "postgresql.org"]
    )

    assert fetcher.is_domain_allowed("https://kafka.apache.org/documentation")
    assert fetcher.is_domain_allowed("https://redis.io/docs/latest")
    assert fetcher.is_domain_allowed("https://www.postgresql.org/docs/current")


def test_disallowed_domain_rejection_and_ssrf_guard():
    """Verify fetcher blocks unauthorized internal or external domains to prevent SSRF."""
    fetcher = DocumentFetcher(allowed_domains=["kafka.apache.org"])

    # Disallowed external domains
    assert not fetcher.is_domain_allowed("https://malicious-site.com/doc")
    assert not fetcher.is_domain_allowed("https://google.com")

    # Disallowed private / cloud metadata IPs (SSRF vectors)
    assert not fetcher.is_domain_allowed("http://169.254.169.254/latest/meta-data/")
    assert not fetcher.is_domain_allowed("http://localhost:8080/admin")
    assert not fetcher.is_domain_allowed("http://127.0.0.1:5432")

    # Fetching should raise ValueError
    with pytest.raises(ValueError, match="not permitted by domain whitelist"):
        fetcher.fetch_url("http://169.254.169.254/latest/meta-data/")


def test_curated_local_cache_fallback():
    """Verify that curated documentation can be fetched from local cache without network."""
    fetcher = DocumentFetcher()
    doc = fetcher.fetch_from_local_cache(
        filename="kafka_architecture.html",
        url="https://kafka.apache.org/documentation/#architecture",
        title="Apache Kafka Architecture and Design",
    )

    assert doc is not None
    assert doc.url == "https://kafka.apache.org/documentation/#architecture"
    assert doc.title == "Apache Kafka Architecture and Design"
    assert "commit log" in doc.content
    assert doc.is_cached_fallback is True
