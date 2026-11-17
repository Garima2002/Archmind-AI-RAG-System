import React, { useState } from 'react';
import {
  X,
  Database,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Plus,
  Trash2,
  Globe,
  RefreshCw,
} from 'lucide-react';
import { api, ApiError } from '../../services/api';
import type { IngestRequest, IngestResponse } from '../../types/api';
import { Button } from '../common/Button';

interface IngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIngestSuccess: (res: IngestResponse) => void;
}

export const IngestionModal: React.FC<IngestionModalProps> = ({
  isOpen,
  onClose,
  onIngestSuccess,
}) => {
  const [useCuratedDefaults, setUseCuratedDefaults] = useState<boolean>(true);
  const [forceRefresh, setForceRefresh] = useState<boolean>(false);
  const [customUrls, setCustomUrls] = useState<string[]>(['']);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<IngestResponse | null>(null);

  if (!isOpen) return null;

  const handleAddUrl = () => {
    setCustomUrls((prev) => [...prev, '']);
  };

  const handleUrlChange = (index: number, val: string) => {
    setCustomUrls((prev) => {
      const copy = [...prev];
      copy[index] = val;
      return copy;
    });
  };

  const handleRemoveUrl = (index: number) => {
    setCustomUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const handleIngest = async () => {
    setIsRunning(true);
    setError(null);
    setLastResponse(null);

    try {
      const validUrls = customUrls.map((u) => u.trim()).filter((u) => u.length > 0);

      const payload: IngestRequest = {
        use_curated_defaults: useCuratedDefaults,
        force_refresh: forceRefresh,
        urls: validUrls.length > 0 ? validUrls : undefined,
      };

      const result = await api.ingest(payload);
      setLastResponse(result.data);
      onIngestSuccess(result.data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : (err as Error).message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-[#0e1422] border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">
                Ingest Documentation & Index Vectors
              </h3>
              <p className="text-xs text-slate-400">
                Coordinated fetching, deterministic chunking, and embedding
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

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          {/* Curated Defaults Toggle */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex items-start justify-between gap-3">
            <div>
              <span className="font-semibold text-slate-200">
                Curated System Architecture Documentation Set
              </span>
              <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                Ingests official technical documentation from Kafka, Redis, DynamoDB, Envoy Proxy, Raft, and PostgreSQL (uses local cached snapshots when offline).
              </p>
            </div>
            <input
              type="checkbox"
              checked={useCuratedDefaults}
              onChange={(e) => setUseCuratedDefaults(e.target.checked)}
              disabled={isRunning}
              className="w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500 shrink-0 mt-1"
            />
          </div>

          {/* Force Refresh Toggle */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex items-start justify-between gap-3">
            <div>
              <span className="font-semibold text-slate-200">
                Force Re-indexing (Overwrite)
              </span>
              <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                Re-embed and re-index already existing documents even if their SHA-256 content hashes match.
              </p>
            </div>
            <input
              type="checkbox"
              checked={forceRefresh}
              onChange={(e) => setForceRefresh(e.target.checked)}
              disabled={isRunning}
              className="w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500 shrink-0 mt-1"
            />
          </div>

          {/* Custom URLs */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-cyan-400" />
                Custom Documentation URLs (Optional):
              </label>
              <button
                type="button"
                onClick={handleAddUrl}
                disabled={isRunning}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
              >
                <Plus className="w-3 h-3" />
                Add URL
              </button>
            </div>

            <p className="text-[10px] text-slate-500">
              Must match whitelist: <code className="text-slate-400">kafka.apache.org</code>, <code className="text-slate-400">redis.io</code>, <code className="text-slate-400">docs.aws.amazon.com</code>, <code className="text-slate-400">postgresql.org</code>, <code className="text-slate-400">envoyproxy.io</code>, <code className="text-slate-400">raft.github.io</code>
            </p>

            {customUrls.map((url, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="url"
                  placeholder="https://kafka.apache.org/documentation/#architecture"
                  value={url}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  disabled={isRunning}
                  className="flex-1 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/60 font-mono"
                />
                {customUrls.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveUrl(index)}
                    disabled={isRunning}
                    className="p-1.5 rounded text-slate-500 hover:text-rose-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Progress / Running state */}
          {isRunning && (
            <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-800/40 text-indigo-200 flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-indigo-400 shrink-0" />
              <div>
                <p className="font-semibold text-xs text-indigo-200">
                  Ingestion Pipeline Running...
                </p>
                <p className="text-[11px] text-indigo-300/80 mt-0.5">
                  Fetching HTML, extracting sections, chunking with SHA-256 IDs, and generating dense embeddings.
                </p>
              </div>
            </div>
          )}

          {/* Success Response */}
          {lastResponse && (
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-200 space-y-1.5">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Ingestion Completed Successfully!</span>
              </div>
              <p className="text-xs text-emerald-300/90">{lastResponse.message}</p>
              <div className="flex items-center gap-4 text-[11px] font-mono text-emerald-300/80 pt-1">
                <span>Docs Ingested: {lastResponse.documents_ingested}</span>
                <span>Total Chunks: {lastResponse.total_chunks}</span>
                <span>Elapsed: {lastResponse.elapsed_seconds.toFixed(2)}s</span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-rose-300">Ingestion Error:</span>
                <p className="font-mono text-[11px] text-rose-200/90 mt-0.5">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 bg-slate-900/60 flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isRunning}>
            Close
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleIngest}
            isLoading={isRunning}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            {isRunning ? 'Processing...' : 'Start Ingestion'}
          </Button>
        </div>
      </div>
    </div>
  );
};
