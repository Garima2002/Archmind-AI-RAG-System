"""Evaluation runner orchestrating retrieval metrics, faithfulness, and answer correctness."""

import logging
import sys
import time
from datetime import datetime, timezone
from typing import List, Optional

from archimind.api.schemas import (
    AnswerMetrics,
    EvaluationRunRequest,
    EvaluationSummary,
    QueryRequest,
    RetrievalMetrics,
)
from archimind.evaluation.dataset import BENCHMARK_DATASET, BenchmarkQuestion
from archimind.evaluation.evaluators import (
    AnswerCorrectnessEvaluator,
    FaithfulnessEvaluator,
)
from archimind.evaluation.langsmith_sync import LangSmithSync
from archimind.evaluation.metrics import (
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
)
from archimind.ingestion.pipeline import IngestionPipeline
from archimind.rag.engine import RAGEngine
from archimind.storage.factory import get_vector_store

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """Executes the 30-question system design evaluation benchmark."""

    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        faithfulness_evaluator: Optional[FaithfulnessEvaluator] = None,
        correctness_evaluator: Optional[AnswerCorrectnessEvaluator] = None,
        langsmith_sync: Optional[LangSmithSync] = None,
    ):
        self.rag_engine = rag_engine or RAGEngine()
        self.faithfulness_evaluator = faithfulness_evaluator or FaithfulnessEvaluator()
        self.correctness_evaluator = (
            correctness_evaluator or AnswerCorrectnessEvaluator()
        )
        self.langsmith_sync = langsmith_sync or LangSmithSync()

    def run(self, request: Optional[EvaluationRunRequest] = None) -> EvaluationSummary:
        """Runs the benchmark questions and returns aggregate metrics."""
        request = request or EvaluationRunRequest()

        # Ensure documents are ingested into vector store before evaluating
        store = get_vector_store()
        if store.count_chunks() == 0:
            logger.info("Vector store is empty. Ingesting curated technical documentation...")
            pipeline = IngestionPipeline(vector_store=store)
            pipeline.run()

        questions = BENCHMARK_DATASET
        if request.max_questions is not None:
            questions = questions[: request.max_questions]

        total_q = len(questions)
        logger.info("Starting ArchiMind AI Benchmark Evaluation on %d questions...", total_q)

        # Metrics accumulators
        recalls_1: List[float] = []
        recalls_3: List[float] = []
        recalls_5: List[float] = []

        precisions_1: List[float] = []
        precisions_3: List[float] = []
        precisions_5: List[float] = []

        mrrs: List[float] = []
        faithfulness_scores: List[float] = []
        correctness_scores: List[float] = []
        unanswerable_checks: List[float] = []
        latencies: List[float] = []

        start_time = time.perf_counter()

        for idx, item in enumerate(questions, start=1):
            q_start = time.perf_counter()

            # 1. Retrieve candidates directly to evaluate full top-k retrieval performance
            retrieved_chunks = self.rag_engine.retriever.retrieve(
                query=item.question,
                top_k=5,
                similarity_threshold=0.20,  # Broader threshold for metric measurement
            )
            retrieved_urls = [c.document_url for c in retrieved_chunks]

            # 2. Execute RAG query to generate grounded answer
            query_req = QueryRequest(query=item.question, top_k=4)
            query_resp = self.rag_engine.answer_query(query_req)

            q_elapsed_ms = (time.perf_counter() - q_start) * 1000.0
            latencies.append(q_elapsed_ms)

            # 3. Calculate Retrieval Metrics
            r1 = calculate_recall_at_k(retrieved_urls, item.expected_doc_urls, k=1)
            r3 = calculate_recall_at_k(retrieved_urls, item.expected_doc_urls, k=3)
            r5 = calculate_recall_at_k(retrieved_urls, item.expected_doc_urls, k=5)

            p1 = calculate_precision_at_k(retrieved_urls, item.expected_doc_urls, k=1)
            p3 = calculate_precision_at_k(retrieved_urls, item.expected_doc_urls, k=3)
            p5 = calculate_precision_at_k(retrieved_urls, item.expected_doc_urls, k=5)

            mrr = calculate_mrr(retrieved_urls, item.expected_doc_urls)

            recalls_1.append(r1)
            recalls_3.append(r3)
            recalls_5.append(r5)
            precisions_1.append(p1)
            precisions_3.append(p3)
            precisions_5.append(p5)
            mrrs.append(mrr)

            # 4. Calculate Answer Faithfulness
            faith_score, faith_reason = self.faithfulness_evaluator.evaluate(
                answer=query_resp.answer,
                retrieved_chunks=retrieved_chunks,
                is_sufficient_evidence=query_resp.is_sufficient_evidence,
            )
            faithfulness_scores.append(faith_score)

            # 5. Calculate Answer Correctness
            corr_score, corr_reason = self.correctness_evaluator.evaluate(
                generated_answer=query_resp.answer,
                ground_truth_answer=item.ground_truth_answer,
                expected_keywords=item.expected_keywords,
                is_answerable=item.is_answerable,
            )
            correctness_scores.append(corr_score)

            # 6. Unanswerable check
            if not item.is_answerable:
                # 1.0 if successfully abstained / flagged insufficient evidence
                unans_acc = 1.0 if not query_resp.is_sufficient_evidence else 0.0
                unanswerable_checks.append(unans_acc)

            logger.debug(
                "[%d/%d] Topic: %-12s | R@3: %.2f | MRR: %.2f | Faith: %.2f | Corr: %.2f",
                idx,
                total_q,
                item.topic,
                r3,
                mrr,
                faith_score,
                corr_score,
            )

        mean_r1 = sum(recalls_1) / total_q if total_q else 0.0
        mean_r3 = sum(recalls_3) / total_q if total_q else 0.0
        mean_r5 = sum(recalls_5) / total_q if total_q else 0.0

        mean_p1 = sum(precisions_1) / total_q if total_q else 0.0
        mean_p3 = sum(precisions_3) / total_q if total_q else 0.0
        mean_p5 = sum(precisions_5) / total_q if total_q else 0.0

        mean_mrr = sum(mrrs) / total_q if total_q else 0.0
        mean_faith = sum(faithfulness_scores) / total_q if total_q else 0.0
        mean_corr = sum(correctness_scores) / total_q if total_q else 0.0
        mean_unans = (
            sum(unanswerable_checks) / len(unanswerable_checks)
            if unanswerable_checks
            else 1.0
        )
        mean_lat = sum(latencies) / total_q if total_q else 0.0

        # LangSmith sync
        langsmith_dataset_id = None
        langsmith_status = "Skipped (sync_to_langsmith=False)"
        if request.sync_to_langsmith or self.langsmith_sync.is_configured():
            synced, ds_id, msg = self.langsmith_sync.sync_benchmark_dataset()
            langsmith_dataset_id = ds_id
            langsmith_status = msg

        return EvaluationSummary(
            total_questions=total_q,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            retrieval_metrics=RetrievalMetrics(
                recall_at_1=round(mean_r1, 4),
                recall_at_3=round(mean_r3, 4),
                recall_at_5=round(mean_r5, 4),
                precision_at_1=round(mean_p1, 4),
                precision_at_3=round(mean_p3, 4),
                precision_at_5=round(mean_p5, 4),
                mrr=round(mean_mrr, 4),
            ),
            answer_metrics=AnswerMetrics(
                mean_faithfulness=round(mean_faith, 4),
                mean_correctness=round(mean_corr, 4),
                unanswerable_detection_accuracy=round(mean_unans, 4),
            ),
            mean_latency_ms=round(mean_lat, 2),
            langsmith_dataset_id=langsmith_dataset_id,
            langsmith_sync_status=langsmith_status,
        )


def main():
    """CLI entrypoint for running the evaluation suite."""
    from archimind.logging_config import setup_logging

    setup_logging("INFO")
    runner = EvaluationRunner()
    summary = runner.run()

    print("\n" + "=" * 60)
    print("      ARCHIMIND AI - 30-QUESTION BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total Questions Evaluated: {summary.total_questions}")
    print(f"Timestamp:                 {summary.evaluated_at}")
    print(f"Mean Query Latency:        {summary.mean_latency_ms:.2f} ms")
    print("-" * 60)
    print("RETRIEVAL QUALITY METRICS:")
    print(f"  Recall@1:    {summary.retrieval_metrics.recall_at_1 * 100:.1f}%")
    print(f"  Recall@3:    {summary.retrieval_metrics.recall_at_3 * 100:.1f}%")
    print(f"  Recall@5:    {summary.retrieval_metrics.recall_at_5 * 100:.1f}%")
    print(f"  Precision@1: {summary.retrieval_metrics.precision_at_1 * 100:.1f}%")
    print(f"  Precision@3: {summary.retrieval_metrics.precision_at_3 * 100:.1f}%")
    print(f"  Precision@5: {summary.retrieval_metrics.precision_at_5 * 100:.1f}%")
    print(f"  MRR:         {summary.retrieval_metrics.mrr:.4f}")
    print("-" * 60)
    print("ANSWER GENERATION & SAFETY METRICS:")
    print(f"  Mean Faithfulness:            {summary.answer_metrics.mean_faithfulness * 100:.1f}%")
    print(f"  Mean Answer Correctness:      {summary.answer_metrics.mean_correctness * 100:.1f}%")
    print(f"  Unanswerable Detection Acc:   {summary.answer_metrics.unanswerable_detection_accuracy * 100:.1f}%")
    print("-" * 60)
    print(f"LangSmith Sync: {summary.langsmith_sync_status}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
