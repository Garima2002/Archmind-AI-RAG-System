import React from 'react';
import { ExternalLink, Layers, Calendar, Hash } from 'lucide-react';
import type { DocumentMetadata } from '../../types/api';

interface DocumentCardProps {
  doc: DocumentMetadata;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ doc }) => {
  const domainColors: Record<string, string> = {
    'kafka.apache.org': 'text-amber-300 bg-amber-950/60 border-amber-800/60',
    'redis.io': 'text-rose-300 bg-rose-950/60 border-rose-800/60',
    'docs.aws.amazon.com': 'text-blue-300 bg-blue-950/60 border-blue-800/60',
    'www.envoyproxy.io': 'text-purple-300 bg-purple-950/60 border-purple-800/60',
    'raft.github.io': 'text-emerald-300 bg-emerald-950/60 border-emerald-800/60',
    'www.postgresql.org': 'text-cyan-300 bg-cyan-950/60 border-cyan-800/60',
  };

  const domainColorClass =
    domainColors[doc.source_domain] || 'text-slate-300 bg-slate-800 border-slate-700';

  return (
    <div className="rounded-2xl glass-card p-5 border border-white/10 hover:border-indigo-500/40 hover:bg-slate-900/80 transition-all flex flex-col justify-between">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className={`text-[11px] font-mono font-medium px-2.5 py-0.5 rounded-full border ${domainColorClass}`}>
            {doc.source_domain}
          </span>
          <span className="text-[11px] font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded-full flex items-center gap-1">
            <Layers className="w-3 h-3" />
            {doc.chunk_count} chunks
          </span>
        </div>

        {/* Document Title */}
        <h4 className="text-sm font-semibold text-slate-100 group-hover:text-indigo-300 leading-snug">
          {doc.title}
        </h4>

        {/* Document URL link */}
        <a
          href={doc.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 hover:underline mt-2 break-all"
        >
          <span className="truncate">{doc.url}</span>
          <ExternalLink className="w-3 h-3 shrink-0" />
        </a>
      </div>

      {/* Footer Info */}
      <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-500">
        <span className="flex items-center gap-1">
          <Hash className="w-3 h-3 text-slate-500" />
          ID: {doc.id.slice(0, 10)}
        </span>
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3 text-slate-500" />
          {new Date(doc.created_at).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
};
