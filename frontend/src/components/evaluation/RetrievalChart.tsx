import React from 'react';
import type { RetrievalMetrics } from '../../types/api';

interface RetrievalChartProps {
  metrics: RetrievalMetrics;
}

export const RetrievalChart: React.FC<RetrievalChartProps> = ({ metrics }) => {
  const data = [
    { label: 'Recall@1', score: metrics.recall_at_1, target: 0.85, type: 'recall' },
    { label: 'Recall@3', score: metrics.recall_at_3, target: 0.90, type: 'recall' },
    { label: 'Recall@5', score: metrics.recall_at_5, target: 0.95, type: 'recall' },
    { label: 'Precision@1', score: metrics.precision_at_1, target: 0.85, type: 'precision' },
    { label: 'Precision@3', score: metrics.precision_at_3, target: 0.80, type: 'precision' },
    { label: 'Precision@5', score: metrics.precision_at_5, target: 0.75, type: 'precision' },
    { label: 'MRR', score: metrics.mrr, target: 0.85, type: 'mrr' },
  ];

  return (
    <div className="rounded-2xl glass-card p-5 border border-white/10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            Retrieval Quality Evaluation
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
              IR Benchmark
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Comparison of Recall@K and Precision@K against industry targets
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-gradient-to-t from-cyan-600 to-cyan-400" />
            <span className="text-slate-300">Achieved Score</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-amber-400" />
            <span className="text-slate-400">Industry Target</span>
          </div>
        </div>
      </div>

      {/* SVG Bar Chart */}
      <div className="space-y-4">
        {data.map((item, idx) => {
          const scorePercent = (item.score * 100).toFixed(1);
          const targetPercent = (item.target * 100).toFixed(0);
          const exceedsTarget = item.score >= item.target;

          const barColor =
            item.type === 'recall'
              ? 'from-cyan-600 to-cyan-400'
              : item.type === 'precision'
              ? 'from-indigo-600 to-indigo-400'
              : 'from-emerald-600 to-emerald-400';

          return (
            <div key={idx} className="group">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-medium text-slate-300 font-mono flex items-center gap-2">
                  {item.label}
                  {exceedsTarget && (
                    <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-1.5 py-0.2 rounded font-sans">
                      Target Exceeded
                    </span>
                  )}
                </span>
                <div className="flex items-center gap-3 font-mono text-xs">
                  <span className="text-slate-400 text-[11px]">
                    Target: {targetPercent}%
                  </span>
                  <span className="font-bold text-white w-14 text-right">
                    {item.type === 'mrr' ? item.score.toFixed(4) : `${scorePercent}%`}
                  </span>
                </div>
              </div>

              {/* Progress Bar Container with Target Marker */}
              <div className="relative w-full h-3 bg-slate-900/90 rounded-full overflow-hidden border border-white/5">
                {/* Target Marker Line */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-amber-400/90 z-10 shadow-sm shadow-amber-400"
                  style={{ left: `${item.target * 100}%` }}
                  title={`Target: ${targetPercent}%`}
                />

                {/* Achieved Score Bar */}
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-700`}
                  style={{ width: `${Math.min(100, Math.max(0, item.score * 100))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
