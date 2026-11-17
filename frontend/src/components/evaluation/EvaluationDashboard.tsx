import React, { useState } from 'react';
import {
  Play,
  RotateCcw,
  Clock,
  Award,
} from 'lucide-react';
import { BASELINE_EVALUATION } from '../../data/defaultEvaluation';
import type { EvaluationSummary } from '../../types/api';
import { MetricCard } from './MetricCard';
import { RetrievalChart } from './RetrievalChart';
import { AnswerQualityChart } from './AnswerQualityChart';
import { BenchmarkModal } from './BenchmarkModal';
import { BenchmarkQuestionsTable } from './BenchmarkQuestionsTable';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface EvaluationDashboardProps {
  onTestInChat: (question: string) => void;
}

export const EvaluationDashboard: React.FC<EvaluationDashboardProps> = ({
  onTestInChat,
}) => {
  const [history, setHistory] = useState<EvaluationSummary[]>(() => {
    try {
      const saved = localStorage.getItem('archimind_eval_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return [BASELINE_EVALUATION];
  });

  const [activeSummaryIndex, setActiveSummaryIndex] = useState<number>(0);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  const activeSummary = history[activeSummaryIndex] || BASELINE_EVALUATION;
  const isBaseline = activeSummary === BASELINE_EVALUATION || activeSummary.evaluated_at === BASELINE_EVALUATION.evaluated_at;

  const handleNewEvaluation = (newSummary: EvaluationSummary) => {
    const updated = [newSummary, ...history];
    setHistory(updated);
    setActiveSummaryIndex(0);
    try {
      localStorage.setItem('archimind_eval_history', JSON.stringify(updated.slice(0, 10)));
    } catch {}
  };

  const handleClearHistory = () => {
    setHistory([BASELINE_EVALUATION]);
    setActiveSummaryIndex(0);
    localStorage.removeItem('archimind_eval_history');
  };

  return (
    <div className="flex-1 max-w-7xl mx-auto w-full px-4 lg:px-8 py-6 space-y-6">
      {/* Top Banner: Benchmark Run Status & Controls */}
      <div className="rounded-2xl glass-panel p-6 border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              System Design Benchmark Evaluation
            </h2>
            {isBaseline ? (
              <Badge variant="cyan" dot>
                Reproducible Baseline Run
              </Badge>
            ) : (
              <Badge variant="emerald" dot>
                Live Benchmark Run
              </Badge>
            )}
            <Badge variant="slate" className="font-mono">
              {activeSummary.total_questions} Questions
            </Badge>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              Evaluated: {new Date(activeSummary.evaluated_at).toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              Latency: {activeSummary.mean_latency_ms.toFixed(2)} ms / query
            </span>
            <span className="text-slate-500">
              LangSmith: {activeSummary.langsmith_sync_status}
            </span>
          </div>
        </div>

        {/* Action Buttons & History Selector */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {history.length > 1 && (
            <div className="flex items-center gap-2">
              <select
                value={activeSummaryIndex}
                onChange={(e) => setActiveSummaryIndex(parseInt(e.target.value, 10))}
                className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none"
              >
                {history.map((h, i) => (
                  <option key={i} value={i}>
                    {i === 0 && !isBaseline ? 'Latest Run' : `Run #${history.length - i}`} ({h.total_questions} Qs - {new Date(h.evaluated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                  </option>
                ))}
              </select>
              <button
                onClick={handleClearHistory}
                title="Reset history to baseline"
                className="text-xs text-slate-500 hover:text-slate-300 p-1.5 rounded hover:bg-white/5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsModalOpen(true)}
            leftIcon={<Play className="w-4 h-4 fill-current" />}
          >
            Run Live Benchmark
          </Button>
        </div>
      </div>

      {/* Primary KPI Metric Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-3 text-xs text-slate-400 font-medium">
          <span>Information Retrieval Performance</span>
          <span className="font-mono text-[11px] text-slate-500">Strict Evaluation on Technical Docs</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <MetricCard
            title="Recall@1"
            value={`${(activeSummary.retrieval_metrics.recall_at_1 * 100).toFixed(1)}%`}
            target="> 85.0%"
            scoreRatio={activeSummary.retrieval_metrics.recall_at_1}
            color="cyan"
            description="Proportion of queries where relevant documentation URL is retrieved in top 1."
          />
          <MetricCard
            title="Recall@3"
            value={`${(activeSummary.retrieval_metrics.recall_at_3 * 100).toFixed(1)}%`}
            target="> 90.0%"
            scoreRatio={activeSummary.retrieval_metrics.recall_at_3}
            color="cyan"
            description="Proportion of queries where relevant documentation URL is retrieved in top 3."
          />
          <MetricCard
            title="Recall@5"
            value={`${(activeSummary.retrieval_metrics.recall_at_5 * 100).toFixed(1)}%`}
            target="> 95.0%"
            scoreRatio={activeSummary.retrieval_metrics.recall_at_5}
            color="cyan"
            description="Proportion of queries where relevant documentation URL is retrieved in top 5."
          />
          <MetricCard
            title="Mean Reciprocal Rank"
            value={activeSummary.retrieval_metrics.mrr.toFixed(4)}
            target="> 0.850"
            scoreRatio={activeSummary.retrieval_metrics.mrr}
            color="emerald"
            subtitle="MRR"
            description="Average reciprocal rank of the first relevant document chunk across all questions."
          />
          <MetricCard
            title="Precision@1"
            value={`${(activeSummary.retrieval_metrics.precision_at_1 * 100).toFixed(1)}%`}
            target="> 85.0%"
            scoreRatio={activeSummary.retrieval_metrics.precision_at_1}
            color="indigo"
            description="Precision of the single top retrieved chunk."
          />
          <MetricCard
            title="Precision@3"
            value={`${(activeSummary.retrieval_metrics.precision_at_3 * 100).toFixed(1)}%`}
            target="> 80.0%"
            scoreRatio={activeSummary.retrieval_metrics.precision_at_3}
            color="indigo"
            description="Precision of the top 3 retrieved chunks."
          />
          <MetricCard
            title="Precision@5"
            value={`${(activeSummary.retrieval_metrics.precision_at_5 * 100).toFixed(1)}%`}
            target="> 75.0%"
            scoreRatio={activeSummary.retrieval_metrics.precision_at_5}
            color="indigo"
            description="Precision of the top 5 retrieved chunks."
          />
          <MetricCard
            title="Mean Latency"
            value={`${activeSummary.mean_latency_ms.toFixed(1)} ms`}
            target="< 500 ms"
            scoreRatio={Math.max(0, 1 - activeSummary.mean_latency_ms / 500)}
            color="slate"
            subtitle="per query"
            description="Mean end-to-end embedding, retrieval, and generation latency."
          />
        </div>
      </div>

      {/* Visual Charts: IR Chart & Answer Quality */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RetrievalChart metrics={activeSummary.retrieval_metrics} />
        <AnswerQualityChart metrics={activeSummary.answer_metrics} />
      </div>

      {/* Critical Analysis Callout */}
      <div className="rounded-2xl p-5 bg-[#0d1320] border border-white/5 space-y-2.5 text-xs text-slate-300">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold">
          <Award className="w-4 h-4 text-indigo-400" />
          <span>Evaluation Methodology: Mitigating LLM-as-a-Judge Biases</span>
        </div>
        <p className="leading-relaxed text-slate-400">
          Traditional LLM judges frequently suffer from verbosity bias, order sensitivity, and self-enhancement blindspots. ArchiMind AI pairs deterministic evaluation metrics (lexical key-concept coverage, deterministic claim grounding verification, and unanswerable detection accuracy) alongside LLM judge interfaces to guarantee deterministic reproducibility.
        </p>
      </div>

      {/* 30-Question Benchmark Dataset Suite */}
      <BenchmarkQuestionsTable onTestInChat={onTestInChat} />

      {/* Live Benchmark Execution Modal */}
      <BenchmarkModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onRunComplete={handleNewEvaluation}
      />
    </div>
  );
};
