import React from 'react';
import { ExternalLink, Bookmark, Hash } from 'lucide-react';
import type { Citation } from '../../types/api';

interface CitationCardProps {
  citation: Citation;
  onOpenDetails?: (citation: Citation) => void;
}

export const CitationCard: React.FC<CitationCardProps> = ({
  citation,
  onOpenDetails,
}) => {
  // Score percentage and color coding
  const scorePercent = Math.min(100, Math.max(0, Math.round(citation.score * 100)));
  const scoreColor =
    scorePercent >= 70
      ? 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60'
      : scorePercent >= 45
      ? 'text-cyan-400 bg-cyan-950/60 border-cyan-800/60'
      : 'text-amber-400 bg-amber-950/60 border-amber-800/60';

  return (
    <div className="group rounded-xl bg-slate-900/70 border border-white/10 p-3.5 hover:border-indigo-500/40 hover:bg-slate-900/90 transition-all flex flex-col justify-between">
      <div>
        {/* Top Header: Marker, Section, Score */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              [Doc {citation.citation_id}]
            </span>
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border ${scoreColor}`}>
              Score: {citation.score.toFixed(3)}
            </span>
          </div>

          <a
            href={citation.document_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-slate-400 hover:text-indigo-300 p-1 rounded hover:bg-white/5 transition-colors"
            title="Open official documentation in new tab"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Document Title */}
        <h4 className="text-xs font-semibold text-slate-200 line-clamp-1 group-hover:text-indigo-300 transition-colors">
          {citation.document_title}
        </h4>

        {/* Section Title if present */}
        {citation.section_title && (
          <p className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5 line-clamp-1 font-medium">
            <Bookmark className="w-3 h-3 text-cyan-400 shrink-0" />
            {citation.section_title}
          </p>
        )}

        {/* Evidence Snippet Excerpt */}
        <div className="mt-2 text-xs text-slate-300/90 bg-[#090d14]/70 rounded-lg p-2.5 border border-white/5 font-sans leading-relaxed line-clamp-3">
          "{citation.snippet}"
        </div>
      </div>

      {/* Footer Details */}
      <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
        <span className="flex items-center gap-1">
          <Hash className="w-2.5 h-2.5" />
          Chunk: {citation.chunk_id.slice(0, 8)}
        </span>
        {onOpenDetails && (
          <button
            onClick={() => onOpenDetails(citation)}
            className="text-indigo-400 hover:text-indigo-300 hover:underline"
          >
            View Full Evidence
          </button>
        )}
      </div>
    </div>
  );
};
