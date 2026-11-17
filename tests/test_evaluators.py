"""Tests for evaluation metrics: Recall@K, Precision@K, MRR, Faithfulness, and Correctness."""

from archimind.api.schemas import DocumentChunkModel
from archimind.evaluation.evaluators import (
    AnswerCorrectnessEvaluator,
    FaithfulnessEvaluator,
)
from archimind.evaluation.metrics import (
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
)
from archimind.rag.prompt import INSUFFICIENT_EVIDENCE_FALLBACK


def test_retrieval_metrics_calculation():
    """Verify Recall@K, Precision@K, and MRR calculations with known ground truth."""
    ground_truth = ["https://kafka.apache.org/doc", "https://redis.io/doc"]
    retrieved = [
        "https://kafka.apache.org/doc",  # rank 1 (relevant)
        "https://other.com/doc",         # rank 2 (irrelevant)
        "https://redis.io/doc",          # rank 3 (relevant)
        "https://random.com/doc",        # rank 4 (irrelevant)
    ]

    # Recall
    # Top 1 contains 1 out of 2 => Recall@1 = 0.5
    assert calculate_recall_at_k(retrieved, ground_truth, k=1) == 0.5
    # Top 3 contains both 2 => Recall@3 = 1.0
    assert calculate_recall_at_k(retrieved, ground_truth, k=3) == 1.0

    # Precision
    # Top 1 has 1 relevant out of 1 => 1.0
    assert calculate_precision_at_k(retrieved, ground_truth, k=1) == 1.0
    # Top 2 has 1 relevant out of 2 => 0.5
    assert calculate_precision_at_k(retrieved, ground_truth, k=2) == 0.5
    # Top 3 has 2 relevant out of 3 => 2/3
    assert round(calculate_precision_at_k(retrieved, ground_truth, k=3), 2) == 0.67

    # MRR (first relevant at rank 1 => 1/1 = 1.0)
    assert calculate_mrr(retrieved, ground_truth) == 1.0

    # Test MRR when first relevant is at rank 2
    retrieved_lagged = ["https://other.com/doc", "https://kafka.apache.org/doc"]
    assert calculate_mrr(retrieved_lagged, ground_truth) == 0.5

    # Test MRR when no relevant docs found
    assert calculate_mrr(["https://unrelated.com"], ground_truth) == 0.0


def test_faithfulness_evaluator():
    """Verify faithfulness evaluator detects grounded claims vs ungrounded hallucinations."""
    evaluator = FaithfulnessEvaluator()

    chunks = [
        DocumentChunkModel(
            id="c1",
            document_id="d1",
            document_title="Kafka",
            document_url="https://kafka.apache.org",
            chunk_index=0,
            content="Kafka partitions are commit logs written sequentially to disk with zero-copy page cache.",
            content_hash="h1",
        )
    ]

    # Grounded answer
    grounded_ans = "Kafka commit logs are written sequentially to disk using zero-copy page cache [Doc 1]."
    score1, reason1 = evaluator.evaluate(grounded_ans, chunks, is_sufficient_evidence=True)
    assert score1 >= 0.8

    # Completely ungrounded hallucination
    hallucinated_ans = "Kafka uses multi-dimensional neural quantum tensor processing networks."
    score2, reason2 = evaluator.evaluate(hallucinated_ans, chunks, is_sufficient_evidence=True)
    assert score2 <= 0.3

    # Insufficient evidence honest fallback should score 1.0 faithfulness
    score3, _ = evaluator.evaluate(
        INSUFFICIENT_EVIDENCE_FALLBACK, [], is_sufficient_evidence=False
    )
    assert score3 == 1.0


def test_answer_correctness_evaluator():
    """Verify correctness evaluator scores keyword coverage and unanswerable detection."""
    evaluator = AnswerCorrectnessEvaluator()

    gt_answer = (
        "Kafka partitions provide total ordering per partition using murmur2 hashing on keys."
    )
    keywords = ["partition", "ordering", "murmur2", "key"]

    # Accurate answer with high keyword recall
    candidate = "Kafka guarantees ordering within a partition by hashing keys using murmur2."
    score1, _ = evaluator.evaluate(
        generated_answer=candidate,
        ground_truth_answer=gt_answer,
        expected_keywords=keywords,
        is_answerable=True,
    )
    assert score1 >= 0.75

    # Out of scope query correctly rejected
    score2, _ = evaluator.evaluate(
        generated_answer=INSUFFICIENT_EVIDENCE_FALLBACK,
        ground_truth_answer=INSUFFICIENT_EVIDENCE_FALLBACK,
        expected_keywords=["not have enough evidence"],
        is_answerable=False,
    )
    assert score2 == 1.0
