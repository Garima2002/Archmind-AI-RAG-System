import React, { useState, useEffect } from 'react';
import { X, Play, Loader2, AlertCircle, Gauge } from 'lucide-react';
import { api, ApiError } from '../../services/api';
import type { EvaluationRunRequest, EvaluationSummary } from '../../types/api';
import { Button } from '../common/Button';

interface BenchmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunComplete: (summary: EvaluationSummary) => void;
}

export const BenchmarkModal: React.FC<BenchmarkModalProps> = ({
  isOpen,
  onClose,
  onRunComplete,
}) => {
  const [maxQuestions, setMaxQuestions] = useState<number>(5);
  const [syncToLangSmith, setSyncToLangSmith] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: any = null;
    if (isRunning) {
      setElapsedSeconds(0);
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timer);
    }
    return () => clearInterval(timer);
  }, [isRunning]);

  if (!isOpen) return null;

  const handleRun = async () => {
    setIsRunning(true);
    setError(null);

    try {
      const payload: EvaluationRunRequest = {
        max_questions: maxQuestions,
        sync_to_langsmith: syncToLangSmith,
      };

      const result = await api.evaluate(payload);
      onRunComplete(result.data);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : (err as Error).message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-[#0e1422] border border-white/10 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Gauge className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">
                Execute Benchmark Evaluation
              </h3>
              <p className="text-xs text-slate-400">
                Run automated Information Retrieval & Faithfulness tests
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isRunning}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6 space-y-5 text-xs">
          {/* Question Count Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-200 mb-2">
              Select Number of Questions to Evaluate:
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[5, 10, 20, 30].map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => setMaxQuestions(count)}
                  disabled={isRunning}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    maxQuestions === count
                      ? 'bg-indigo-600/20 border-indigo-500/80 text-white font-bold ring-1 ring-indigo-500/30'
                      : 'bg-slate-900/70 border-white/5 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <span className="block text-base font-mono">{count}</span>
                  <span className="text-[10px] text-slate-400 font-sans">
                    {count === 5 ? 'Fast' : count === 30 ? 'Full suite' : 'Medium'}
                  </span>
                </button>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              Evaluates Recall@K, Precision@K, MRR, Faithfulness, and Out-of-Scope Hallucination Resistance.
            </p>
          </div>

          {/* LangSmith Sync Toggle */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200">LangSmith Dataset Sync</span>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Upload evaluation trace metrics to configured LangSmith project
              </p>
            </div>
            <input
              type="checkbox"
              checked={syncToLangSmith}
              onChange={(e) => setSyncToLangSmith(e.target.checked)}
              disabled={isRunning}
              className="w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500"
            />
          </div>

          {/* Running State Banner */}
          {isRunning && (
            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/40 text-indigo-200 flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-indigo-400 shrink-0" />
              <div>
                <p className="font-semibold text-xs text-indigo-200">
                  Running {maxQuestions}-Question Evaluation Benchmark...
                </p>
                <p className="text-[11px] text-indigo-300/80 font-mono mt-0.5">
                  Elapsed: {elapsedSeconds}s (Embedding queries & computing IR metrics)
                </p>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-semibold text-rose-300">Execution Error:</span>
                <p className="mt-0.5 font-mono text-[11px] text-rose-200/90">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 bg-slate-900/60 flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isRunning}>
            Cancel
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleRun}
            isLoading={isRunning}
            leftIcon={<Play className="w-3.5 h-3.5" />}
          >
            {isRunning ? 'Evaluating...' : `Run (${maxQuestions} Questions)`}
          </Button>
        </div>
      </div>
    </div>
  );
};
