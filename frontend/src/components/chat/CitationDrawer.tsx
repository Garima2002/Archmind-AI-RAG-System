import React from 'react';
import { X, ExternalLink, Bookmark, ShieldCheck, Database, Layers } from 'lucide-react';
import type { Citation } from '../../types/api';
import { Button } from '../common/Button';

interface CitationDrawerProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  citation,
  onClose,
}) => {
  if (!citation) return null;

  const scorePercent = Math.min(100, Math.max(0, Math.round(citation.score * 100)));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl rounded-2xl bg-[#0e1422] border border-white/10 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                Source Citation [Doc {citation.citation_id}]
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
                  Cosine Similarity: {citation.score.toFixed(4)} ({scorePercent}%)
                </span>
              </h3>
              <p className="text-xs text-slate-400">Verifiable RAG Evidence Grounding</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-white/5">
            <div>
              <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider">Source Document</span>
              <p className="font-semibold text-slate-200 mt-0.5">{citation.document_title}</p>
            </div>
            {citation.section_title && (
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1">
                  <Bookmark className="w-3 h-3 text-cyan-400" />
                  Section
                </span>
                <p className="font-medium text-cyan-300 mt-0.5">{citation.section_title}</p>
              </div>
            )}
            <div>
              <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1">
                <Database className="w-3 h-3 text-indigo-400" />
                Document ID
              </span>
              <p className="font-mono text-slate-300 text-[11px] mt-0.5">{citation.document_id}</p>
            </div>
            <div>
              <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1">
                <Layers className="w-3 h-3 text-emerald-400" />
                Deterministic Chunk ID
              </span>
              <p className="font-mono text-slate-300 text-[11px] mt-0.5">{citation.chunk_id}</p>
            </div>
          </div>

          {/* Evidence Snippet */}
          <div>
            <h4 className="text-[11px] uppercase font-mono text-slate-400 tracking-wider mb-2">
              Verbatim Evidence Snippet
            </h4>
            <div className="p-4 rounded-xl bg-[#090d14] border border-white/10 text-slate-200 leading-relaxed font-sans text-xs whitespace-pre-wrap selection:bg-indigo-500/30">
              "{citation.snippet}"
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-white/10 bg-slate-900/60 flex items-center justify-between">
          <a
            href={citation.document_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300"
          >
            <span>Visit Official Documentation Source</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
