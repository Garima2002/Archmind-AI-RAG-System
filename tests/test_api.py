"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoints(test_client: TestClient):
    """Verify both /health and /api/v1/health return healthy status and metadata."""
    res_root = test_client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "healthy"

    res_v1 = test_client.get("/api/v1/health")
    assert res_v1.status_code == 200
    data = res_v1.json()
    assert data["status"] == "healthy"
    assert data["vector_store_connected"] is True
    assert "version" in data


def test_process_time_header(test_client: TestClient):
    """Verify that every response includes X-Process-Time-Ms header."""
    res = test_client.get("/api/v1/health")
    assert "x-process-time-ms" in res.headers
    latency = float(res.headers["x-process-time-ms"])
    assert latency >= 0.0


def test_ingest_and_query_flow(test_client: TestClient):
    """Verify end-to-end ingestion and querying lifecycle."""
    # 1. Trigger curated document ingestion
    ingest_res = test_client.post(
        "/api/v1/ingest",
        json={"use_curated_defaults": True, "force_refresh": True},
    )
    assert ingest_res.status_code == 200
    ingest_data = ingest_res.json()
    assert ingest_data["status"] == "success"
    assert ingest_data["documents_ingested"] >= 5
    assert ingest_data["total_chunks"] > 0

    # 2. List documents
    docs_res = test_client.get("/api/v1/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) >= 5

    # 3. Query an answerable system design question
    query_res = test_client.post(
        "/api/v1/query",
        json={
            "query": "How does Kafka guarantee message ordering within a partition?",
            "top_k": 4,
        },
    )
    assert query_res.status_code == 200
    q_data = query_res.json()
    assert q_data["is_sufficient_evidence"] is True
    assert len(q_data["citations"]) > 0
    assert "partition" in q_data["answer"].lower()
    assert q_data["latency_ms"] > 0

    # 4. Query an out-of-scope question (insufficient evidence detection)
    unans_res = test_client.post(
        "/api/v1/query",
        json={"query": "How do I bake a vanilla cupcake with chocolate frosting?"},
    )
    assert unans_res.status_code == 200
    unans_data = unans_res.json()
    assert unans_data["is_sufficient_evidence"] is False
    assert "not have enough evidence" in unans_data["answer"].lower()
    assert len(unans_data["citations"]) == 0


def test_validation_error_handling(test_client: TestClient):
    """Verify standard 422 Unprocessable Entity error for invalid payloads."""
    # Query string too short (<3 chars)
    res = test_client.post("/api/v1/query", json={"query": "a"})
    assert res.status_code == 422


def test_evaluation_endpoint(test_client: TestClient):
    """Verify the /api/v1/evaluate endpoint runs and returns benchmark metrics."""
    # Run evaluation on a small subset of 3 questions for fast integration test
    res = test_client.post("/api/v1/evaluate", json={"max_questions": 3, "sync_to_langsmith": False})
    assert res.status_code == 200
    data = res.json()
    assert data["total_questions"] == 3
    assert "retrieval_metrics" in data
    assert "answer_metrics" in data
    assert data["retrieval_metrics"]["recall_at_3"] >= 0.0
    assert data["answer_metrics"]["mean_faithfulness"] >= 0.0
