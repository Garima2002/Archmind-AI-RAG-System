import React from 'react';
import {
  Layers,
  Cpu,
  Database,
  ExternalLink,
  RefreshCw,
  Server,
  Zap,
} from 'lucide-react';
import type { HealthResponse } from '../../types/api';
import { Badge } from '../common/Badge';

interface HeaderProps {
  health: HealthResponse | null;
  isLoadingHealth: boolean;
  onRefreshHealth: () => void;
  lastProcessTimeMs?: number;
  backendError?: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  isLoadingHealth,
  onRefreshHealth,
  lastProcessTimeMs,
  backendError,
}) => {
  const isHealthy = health?.status === 'healthy' && !backendError;
  const isDegraded = health?.status === 'degraded';
  const isOffline = !!backendError || (!health && !isLoadingHealth);

  return (
    <header className="sticky top-0 z-40 w-full glass-header border-b border-white/10 px-4 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: Brand Identity */}
        <div className="flex items-center gap-3.5 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-700 shadow-md shadow-indigo-500/20 ring-1 ring-white/20">
              <Layers className="w-5 h-5 text-white" />
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-cyan-400 border-2 border-[#0a0d14]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                  ArchiMind <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">AI</span>
                </h1>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  RAG Platform
                </span>
              </div>
              <p className="text-xs text-slate-400">
                System Design Knowledge Assistant & Evaluation Engine
              </p>
            </div>
          </div>

          {/* Mobile Refresh Button */}
          <button
            onClick={onRefreshHealth}
            disabled={isLoadingHealth}
            aria-label="Refresh health status"
            className="md:hidden p-2 rounded-lg bg-slate-800/80 text-slate-400 hover:text-white"
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingHealth ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>

        {/* Right: Operational Telemetry & System Badges */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto justify-start md:justify-end text-xs">
          {/* Health Status Indicator */}
          {isHealthy && (
            <Badge variant="emerald" dot>
              System Online
            </Badge>
          )}
          {isDegraded && (
            <Badge variant="amber" dot>
              Degraded
            </Badge>
          )}
          {isOffline && (
            <Badge variant="rose" dot>
              Backend Unreachable
            </Badge>
          )}

          {/* Storage Mode */}
          {health && (
            <Badge variant="slate" className="font-mono">
              <Database className="w-3 h-3 text-cyan-400 mr-0.5" />
              {health.vector_store_type.toUpperCase()}
              {health.chunks_count > 0 && (
                <span className="text-slate-500 ml-1">({health.chunks_count} chunks)</span>
              )}
            </Badge>
          )}

          {/* LLM Provider */}
          {health && (
            <Badge variant="slate" className="font-mono">
              <Cpu className="w-3 h-3 text-indigo-400 mr-0.5" />
              {health.llm_provider}
            </Badge>
          )}

          {/* Server Process Latency Header */}
          {lastProcessTimeMs !== undefined && (
            <Badge variant="slate" className="font-mono hidden sm:inline-flex">
              <Zap className="w-3 h-3 text-amber-400 mr-0.5" />
              {lastProcessTimeMs.toFixed(1)}ms
            </Badge>
          )}

          {/* API Docs Link */}
          <a
            href={`${(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
            title="Open FastAPI Swagger Interactive API Documentation"
          >
            <Server className="w-3 h-3 text-indigo-400" />
            <span>API Docs</span>
            <ExternalLink className="w-2.5 h-2.5 opacity-60 ml-0.5" />
          </a>

          {/* Desktop Refresh Button */}
          <button
            onClick={onRefreshHealth}
            disabled={isLoadingHealth}
            aria-label="Refresh system health telemetry"
            title="Refresh system health telemetry"
            className="hidden md:flex p-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 text-slate-400 hover:text-slate-200 border border-slate-700/60 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingHealth ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
