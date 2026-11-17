import React from 'react';
import { HelpCircle } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  target?: string;
  isPercentage?: boolean;
  scoreRatio?: number; // 0.0 - 1.0 for progress bar
  color?: 'emerald' | 'cyan' | 'indigo' | 'amber' | 'slate';
  description?: string;
  subtitle?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  target,
  scoreRatio,
  color = 'indigo',
  description,
  subtitle,
}) => {
  const colorMap = {
    emerald: {
      border: 'border-emerald-500/20 hover:border-emerald-500/40',
      badge: 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60',
      bar: 'bg-emerald-500',
      text: 'text-emerald-400',
    },
    cyan: {
      border: 'border-cyan-500/20 hover:border-cyan-500/40',
      badge: 'text-cyan-400 bg-cyan-950/60 border-cyan-800/60',
      bar: 'bg-cyan-500',
      text: 'text-cyan-400',
    },
    indigo: {
      border: 'border-indigo-500/20 hover:border-indigo-500/40',
      badge: 'text-indigo-400 bg-indigo-950/60 border-indigo-800/60',
      bar: 'bg-indigo-500',
      text: 'text-indigo-400',
    },
    amber: {
      border: 'border-amber-500/20 hover:border-amber-500/40',
      badge: 'text-amber-400 bg-amber-950/60 border-amber-800/60',
      bar: 'bg-amber-500',
      text: 'text-amber-400',
    },
    slate: {
      border: 'border-slate-800 hover:border-slate-700',
      badge: 'text-slate-400 bg-slate-900 border-slate-800',
      bar: 'bg-slate-400',
      text: 'text-slate-300',
    },
  }[color];

  return (
    <div
      className={`rounded-2xl glass-card p-4 transition-all duration-150 flex flex-col justify-between ${colorMap.border}`}
    >
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            {title}
            {description && (
              <span title={description} className="text-slate-500 hover:text-slate-400 cursor-help">
                <HelpCircle className="w-3.5 h-3.5" />
              </span>
            )}
          </span>
          {target && (
            <span className="text-[10px] font-mono text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded-full border border-white/5">
              Target: {target}
            </span>
          )}
        </div>

        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl font-bold font-mono text-white tracking-tight">
            {value}
          </span>
          {subtitle && (
            <span className="text-xs text-slate-400 font-mono">{subtitle}</span>
          )}
        </div>
      </div>

      {scoreRatio !== undefined && (
        <div className="mt-3 pt-2">
          <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${colorMap.bar}`}
              style={{ width: `${Math.min(100, Math.max(0, scoreRatio * 100))}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
