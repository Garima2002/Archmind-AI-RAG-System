"""Information retrieval evaluation metrics: Recall@K, Precision@K, and MRR."""

from typing import List


def calculate_recall_at_k(
    retrieved_urls: List[str], expected_urls: List[str], k: int
) -> float:
    """Calculates Recall@K: proportion of relevant documents found in top-k results."""
    if not expected_urls:
        # For out-of-scope/unanswerable queries with no expected docs:
        # Perfect recall if retriever returned no docs, 0 if it pulled spurious docs
        return 1.0 if not retrieved_urls else 0.0

    top_k_retrieved = set(retrieved_urls[:k])
    expected_set = set(expected_urls)

    intersection = top_k_retrieved.intersection(expected_set)
    return len(intersection) / len(expected_set)


def calculate_precision_at_k(
    retrieved_urls: List[str], expected_urls: List[str], k: int
) -> float:
    """Calculates Precision@K: proportion of top-k retrieved documents that are relevant."""
    if k <= 0:
        return 0.0

    if not expected_urls:
        return 1.0 if not retrieved_urls else 0.0

    top_k_retrieved = retrieved_urls[:k]
    if not top_k_retrieved:
        return 0.0

    expected_set = set(expected_urls)
    relevant_retrieved = sum(1 for url in top_k_retrieved if url in expected_set)
    return relevant_retrieved / len(top_k_retrieved)


def calculate_mrr(
    retrieved_urls: List[str], expected_urls: List[str]
) -> float:
    """Calculates Mean Reciprocal Rank (MRR): reciprocal rank of the first relevant document."""
    if not expected_urls:
        return 1.0 if not retrieved_urls else 0.0

    expected_set = set(expected_urls)
    for rank, url in enumerate(retrieved_urls, start=1):
        if url in expected_set:
            return 1.0 / rank

    return 0.0
