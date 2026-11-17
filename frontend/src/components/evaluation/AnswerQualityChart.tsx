import React from 'react';
import { ShieldCheck, Target, AlertTriangle } from 'lucide-react';
import type { AnswerMetrics } from '../../types/api';

interface AnswerQualityChartProps {
  metrics: AnswerMetrics;
}

export const AnswerQualityChart: React.FC<AnswerQualityChartProps> = ({ metrics }) => {
  const cards = [
    {
      title: 'Evidence Faithfulness',
      score: metrics.mean_faithfulness,
      target: 0.95,
      icon: ShieldCheck,
      color: 'emerald',
      description:
        'Proportion of answer claims strictly grounded in retrieved evidence chunks. High score indicates absence of unverified hallucinations.',
    },
    {
      title: 'Unanswerable Detection Acc.',
      score: metrics.unanswerable_detection_accuracy,
      target: 0.90,
      icon: AlertTriangle,
      color: 'cyan',
      description:
        'Accuracy in correctly abstaining and returning the insufficient-evidence fallback when asked questions outside indexed documentation.',
    },
    {
      title: 'Answer Correctness',
      score: metrics.mean_correctness,
      target: 0.35,
      icon: Target,
      color: 'indigo',
      description:
        'Lexical key-fact overlap and semantic coverage against curated golden ground-truth architectural specifications.',
    },
  ];

  return (
    <div className="rounded-2xl glass-card p-5 border border-white/10">
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
          Generation Quality & Guardrail Reliability
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800/60">
            Safety Guardrails
          </span>
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Hallucination resistance, evidence verification, and ground-truth alignment
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cards.map((c, idx) => {
          const scorePercent = (c.score * 100).toFixed(1);
          const targetPercent = (c.target * 100).toFixed(0);
          const Icon = c.icon;

          const colorTheme = {
            emerald: {
              border: 'border-emerald-500/30',
              text: 'text-emerald-400',
              bg: 'bg-emerald-500/10',
              bar: 'from-emerald-500 to-teal-400',
            },
            cyan: {
              border: 'border-cyan-500/30',
              text: 'text-cyan-400',
              bg: 'bg-cyan-500/10',
              bar: 'from-cyan-500 to-sky-400',
            },
            indigo: {
              border: 'border-indigo-500/30',
              text: 'text-indigo-400',
              bg: 'bg-indigo-500/10',
              bar: 'from-indigo-500 to-violet-400',
            },
          }[c.color as 'emerald' | 'cyan' | 'indigo'];

          return (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className={`p-2 rounded-lg ${colorTheme.bg} border ${colorTheme.border} ${colorTheme.text}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 bg-black/40 px-2 py-0.5 rounded-full border border-white/5">
                    Target: &gt;{targetPercent}%
                  </span>
                </div>

                <h4 className="text-xs font-semibold text-slate-200">{c.title}</h4>
                <div className="text-2xl font-bold font-mono text-white mt-1">
                  {scorePercent}%
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                  {c.description}
                </p>
              </div>

              {/* Progress bar */}
              <div className="mt-4 pt-2">
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-white/5">
                  <div
                    className={`h-full rounded-full bg-gradient-to-r ${colorTheme.bar} transition-all duration-700`}
                    style={{ width: `${Math.min(100, Math.max(0, c.score * 100))}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
