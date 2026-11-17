import React from 'react';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

interface InsufficientEvidenceAlertProps {
  answer: string;
}

export const InsufficientEvidenceAlert: React.FC<InsufficientEvidenceAlertProps> = ({ answer }) => {
  return (
    <div className="rounded-xl border border-amber-500/40 bg-amber-950/20 p-4 space-y-3">
      {/* Header Banner */}
      <div className="flex items-start gap-2.5">
        <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 shrink-0">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-300">
              Anti-Hallucination Guardrail Active
            </h4>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-200 border border-amber-500/30">
              Zero Speculation Policy
            </span>
          </div>
          <p className="text-xs text-amber-200/90 mt-1 leading-relaxed">
            {answer}
          </p>
        </div>
      </div>

      {/* Guidance box */}
      <div className="p-3 rounded-lg bg-black/40 border border-amber-500/20 text-[11px] text-amber-200/80 flex items-start gap-2">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-300">Supported System Design Sources:</span>
          <p className="mt-0.5 text-slate-300">
            ArchiMind AI retrieves evidence strictly from: <strong>Apache Kafka</strong>, <strong>Redis</strong>, <strong>Amazon DynamoDB</strong>, <strong>Envoy Proxy</strong>, <strong>Raft Consensus</strong>, and <strong>PostgreSQL</strong>.
          </p>
        </div>
      </div>
    </div>
  );
};
