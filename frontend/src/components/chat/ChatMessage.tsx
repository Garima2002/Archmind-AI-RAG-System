import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  User,
  Layers,
  Clock,
  Cpu,
  Check,
  Copy,
  FileText,
  Coins,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import type { ChatMessage as ChatMessageType, Citation } from '../../types/api';
import { CitationCard } from './CitationCard';
import { InsufficientEvidenceAlert } from './InsufficientEvidenceAlert';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ChatMessageProps {
  message: ChatMessageType;
  onOpenCitation: (citation: Citation) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onOpenCitation,
}) => {
  const isUser = message.role === 'user';
  const queryResponse = message.queryResponse;
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [showCitations, setShowCitations] = useState<boolean>(true);

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end my-4 animate-fade-in">
        <div className="max-w-2xl flex items-start gap-3">
          <div className="p-4 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-slate-100 shadow-sm shadow-indigo-500/10">
            <p className="text-sm font-medium leading-relaxed whitespace-pre-wrap">{message.content}</p>
            <span className="block text-[10px] text-indigo-300/70 font-mono mt-1 text-right">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <div className="w-8 h-8 rounded-xl bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0 text-indigo-300">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant response
  return (
    <div className="flex justify-start my-4 animate-fade-in">
      <div className="w-full max-w-4xl flex items-start gap-3">
        {/* Assistant Avatar */}
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-700 flex items-center justify-center shrink-0 text-white shadow-sm shadow-indigo-500/30 ring-1 ring-white/20 mt-1">
          <Layers className="w-4 h-4" />
        </div>

        {/* Assistant Message Bubble */}
        <div className="flex-1 min-w-0 rounded-2xl glass-panel p-5 space-y-4">
          {/* Header Line */}
          <div className="flex items-center justify-between text-xs pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-200">ArchiMind AI</span>
              {queryResponse && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                  {queryResponse.model_name || queryResponse.llm_provider}
                </span>
              )}
              {queryResponse?.intent === 'greeting' && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  Architect Persona
                </span>
              )}
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          {/* Contextualized Rephrased Query Pill */}
          {queryResponse?.rephrased_query && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300 animate-fade-in">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span className="font-semibold text-indigo-200 shrink-0">Contextualized Search:</span>
              <span className="text-slate-300 italic truncate">"{queryResponse.rephrased_query}"</span>
            </div>
          )}

          {/* Loading state */}
          {message.isLoading && (
            <div className="py-6 flex flex-col items-center justify-center">
              <LoadingSpinner
                size="md"
                text="Retrieving technical documentation vectors & synthesizing grounded answer..."
              />
            </div>
          )}

          {/* Error State */}
          {message.error && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 text-xs">
              <p className="font-semibold text-rose-300">Error generating answer:</p>
              <p className="mt-1 font-mono text-[11px] text-rose-200/90 leading-relaxed">{message.error}</p>
            </div>
          )}

          {/* Fallback Guardrail State */}
          {queryResponse && !queryResponse.is_sufficient_evidence && (
            <InsufficientEvidenceAlert answer={queryResponse.answer} />
          )}

          {/* Evidence Grounded Answer Markdown */}
          {queryResponse && queryResponse.is_sufficient_evidence && (
            <div className="markdown-body">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Code block with copy button
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeString = String(children).replace(/\n$/, '');
                    const isInline = !match && !codeString.includes('\n');

                    if (isInline) {
                      return (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }

                    return (
                      <div className="relative group my-3 rounded-lg overflow-hidden border border-white/10 bg-[#0c101a]">
                        <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-900/80 border-b border-white/5 text-[11px] font-mono text-slate-400">
                          <span>{match ? match[1] : 'code'}</span>
                          <button
                            onClick={() => handleCopy(codeString)}
                            className="flex items-center gap-1 hover:text-white transition-colors"
                          >
                            {copiedCode === codeString ? (
                              <>
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                                <span className="text-emerald-400">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                        <pre className="p-3.5 overflow-x-auto text-xs text-slate-200 font-mono">
                          <code>{children}</code>
                        </pre>
                      </div>
                    );
                  },
                }}
              >
                {queryResponse.answer}
              </ReactMarkdown>
            </div>
          )}

          {/* Source Citations Section */}
          {queryResponse && queryResponse.citations && queryResponse.citations.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="flex items-center justify-between mb-3">
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
                >
                  <FileText className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Retrieved Evidence Citations ({queryResponse.citations.length})</span>
                  {showCitations ? (
                    <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </button>
                <span className="text-[10px] text-slate-500 font-mono">
                  Cosine similarity ranking
                </span>
              </div>

              {showCitations && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 animate-fade-in">
                  {queryResponse.citations.map((c) => (
                    <CitationCard
                      key={c.citation_id}
                      citation={c}
                      onOpenDetails={onOpenCitation}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Technical Telemetry Footer */}
          {queryResponse && (
            <div className="pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-slate-400">
              <div className="flex flex-wrap items-center gap-3">
                <span className="flex items-center gap-1 text-slate-400">
                  <Clock className="w-3 h-3 text-cyan-400" />
                  Latency: <strong className="text-slate-200 font-semibold">{queryResponse.latency_ms.toFixed(1)}ms</strong>
                </span>

                <span className="flex items-center gap-1 text-slate-400">
                  <Cpu className="w-3 h-3 text-indigo-400" />
                  Provider: <strong className="text-slate-200 font-semibold">{queryResponse.llm_provider}</strong>
                </span>

                <span className="flex items-center gap-1 text-slate-400">
                  <Layers className="w-3 h-3 text-emerald-400" />
                  Retrieved: <strong className="text-slate-200 font-semibold">{queryResponse.retrieved_chunks_count} chunks</strong>
                </span>
              </div>

              {/* Token counts if returned */}
              {queryResponse.token_usage && (
                <div className="flex items-center gap-1.5 text-slate-400">
                  <Coins className="w-3 h-3 text-amber-400" />
                  <span>Tokens:</span>
                  <span className="text-slate-200">
                    {queryResponse.token_usage.total_tokens || (queryResponse.token_usage.prompt_tokens + queryResponse.token_usage.completion_tokens)}
                  </span>
                  <span className="text-slate-500 text-[10px]">
                    ({queryResponse.token_usage.prompt_tokens}p / {queryResponse.token_usage.completion_tokens}c)
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
