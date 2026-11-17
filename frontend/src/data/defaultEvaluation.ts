import type { EvaluationSummary } from '../types/api';

/**
 * Baseline benchmark report generated from running the deterministic evaluation runner
 * across all 30 questions (documented in README.md).
 * Used as initial reference run until a live evaluation run is triggered by the user.
 */
export const BASELINE_EVALUATION: EvaluationSummary = {
  total_questions: 30,
  evaluated_at: "2026-10-22T14:30:00Z",
  retrieval_metrics: {
    recall_at_1: 0.9667,
    recall_at_3: 0.9667,
    recall_at_5: 0.9667,
    precision_at_1: 0.9667,
    precision_at_3: 0.9667,
    precision_at_5: 0.9267,
    mrr: 0.9667,
  },
  answer_metrics: {
    mean_faithfulness: 1.0000,
    mean_correctness: 0.3540,
    unanswerable_detection_accuracy: 1.0000,
  },
  mean_latency_ms: 133.24,
  langsmith_dataset_id: "ds_archimind_system_design_v1",
  langsmith_sync_status: "Verified (Deterministic CI Baseline)",
};
