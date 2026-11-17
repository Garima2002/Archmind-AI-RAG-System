import React from 'react';
import { Database, ShieldCheck, CheckCircle2, Info } from 'lucide-react';
import type { HealthResponse } from '../../types/api';

interface StorageCapabilitiesCardProps {
  health: HealthResponse | null;
}

export const StorageCapabilitiesCard: React.FC<StorageCapabilitiesCardProps> = ({ health }) => {
  return (
    <div className="rounded-2xl glass-card p-6 border border-white/10 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              Storage Engine & Pipeline Architecture
            </h3>
            <p className="text-xs text-slate-400">
              Active configuration, connected APIs, and platform capabilities
            </p>
          </div>
        </div>
        {health && (
          <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded-full bg-slate-900 text-slate-300 border border-white/10">
            Engine: {health.vector_store_type.toUpperCase()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Connected Endpoints */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2.5">
          <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <CheckCircle2 className="w-4 h-4" />
            <span>Connected Backend Endpoints</span>
          </div>
          <ul className="space-y-1.5 text-slate-300 font-mono text-[11px]">
            <li className="flex items-center gap-2">
              <span className="text-cyan-400 font-bold">GET</span>
              <span>/api/v1/health</span>
              <span className="text-slate-500 text-[10px]">— System health & telemetry</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-emerald-400 font-bold">POST</span>
              <span>/api/v1/ingest</span>
              <span className="text-slate-500 text-[10px]">— Idempotent doc indexing</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-cyan-400 font-bold">GET</span>
              <span>/api/v1/documents</span>
              <span className="text-slate-500 text-[10px]">— Tracked doc metadata</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-emerald-400 font-bold">POST</span>
              <span>/api/v1/query</span>
              <span className="text-slate-500 text-[10px]">— RAG grounded Q&A</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-emerald-400 font-bold">POST</span>
              <span>/api/v1/evaluate</span>
              <span className="text-slate-500 text-[10px]">— 30-Question benchmark</span>
            </li>
          </ul>
        </div>

        {/* Security & Ingestion Guardrails */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2.5">
          <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
            <ShieldCheck className="w-4 h-4" />
            <span>SSRF Guardrails & Storage Rules</span>
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            <strong>Domain Whitelist:</strong> Ingestion strictly restricts external HTTP requests to authorized technical domains (Kafka, Redis, DynamoDB, Postgres, Envoy, Raft).
          </p>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            <strong>Deterministic Chunking:</strong> SHA-256 chunk identifiers guarantee idempotent re-indexing without duplicate vectors.
          </p>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            <strong>Offline Fallback:</strong> If documentation endpoints are unreachable, curated local HTML snapshots guarantee reproducible offline cold starts.
          </p>
        </div>
      </div>

      {/* Disconnected / Future Roadmap Capabilities */}
      <div className="p-4 rounded-xl bg-[#090d14] border border-white/5 flex items-start gap-3 text-xs">
        <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        <div className="text-slate-400 text-[11px] leading-relaxed">
          <strong className="text-slate-300">Backend Architectural Note:</strong> Individual document deletion via REST (e.g. <code className="text-slate-400 font-mono">DELETE /api/v1/documents/:id</code>) is implemented in vector store classes but not yet exposed on FastAPI routes. Document updates are achieved via idempotent re-ingestion with <code className="text-slate-400 font-mono">force_refresh=true</code>.
        </div>
      </div>
    </div>
  );
};
