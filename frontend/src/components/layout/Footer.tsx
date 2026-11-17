import React from 'react';
import { Layers, ShieldCheck, ExternalLink, Terminal } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-white/10 bg-[#090d14]/90 backdrop-blur-md px-4 lg:px-8 py-6 text-xs text-slate-500 mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-6 h-6 rounded-lg bg-indigo-600/30 text-indigo-400 border border-indigo-500/30">
            <Layers className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-semibold text-slate-300">ArchiMind AI</span>
            <span className="text-slate-500 ml-1.5 font-mono">v0.1.0</span>
            <p className="text-[11px] text-slate-500">
              Evidence-grounded System Design Assistant with strict anti-hallucination guardrails.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-6 text-[11px] font-mono">
          <div className="flex items-center gap-1.5 text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Zero Speculation Guardrails</span>
          </div>

          <a
            href={`${(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-200 flex items-center gap-1"
          >
            <Terminal className="w-3 h-3 text-indigo-400" />
            <span>OpenAPI Swagger</span>
            <ExternalLink className="w-2.5 h-2.5 opacity-60" />
          </a>

          <span className="text-slate-600">Apache 2.0 License</span>
        </div>
      </div>
    </footer>
  );
};
