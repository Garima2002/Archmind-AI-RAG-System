import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Trash2,
  ShieldCheck,
  BookOpen,
} from 'lucide-react';
import { api, ApiError } from '../../services/api';
import type { ChatMessage as ChatMessageType, Citation, QueryRequest } from '../../types/api';
import { ChatMessage } from './ChatMessage';
import { StarterPrompts } from './StarterPrompts';
import { ParameterTuner } from './ParameterTuner';
import { CitationDrawer } from './CitationDrawer';
import { Button } from '../common/Button';

interface ChatWorkspaceProps {
  onProcessTimeUpdate?: (ms: number) => void;
  onNavigateToKnowledge?: () => void;
  prefillQuery?: string;
  onClearPrefill?: () => void;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  onProcessTimeUpdate,
  onNavigateToKnowledge,
  prefillQuery,
  onClearPrefill,
}) => {
  const [messages, setMessages] = useState<ChatMessageType[]>(() => {
    return [
      {
        id: 'welcome',
        role: 'assistant',
        content:
          "Welcome to **ArchiMind AI**! I am an evidence-grounded System Design Knowledge Assistant powered by RAG.\n\nAsk me any architecture question about **Apache Kafka**, **Redis**, **Amazon DynamoDB**, **Envoy Proxy**, **Raft Consensus**, or **PostgreSQL**. Every answer includes source citations and strict anti-hallucination guardrails.",
        timestamp: new Date().toISOString(),
        queryResponse: {
          query: "Welcome",
          answer: "Welcome to **ArchiMind AI**! I am an evidence-grounded System Design Knowledge Assistant powered by RAG.\n\nAsk me any architecture question about **Apache Kafka**, **Redis**, **Amazon DynamoDB**, **Envoy Proxy**, **Raft Consensus**, or **PostgreSQL**. Every answer includes source citations and strict anti-hallucination guardrails.",
          is_sufficient_evidence: true,
          citations: [],
          retrieved_chunks_count: 0,
          latency_ms: 0,
          llm_provider: "system",
          model_name: "archimind-v1",
        }
      }
    ];
  });

  const [inputQuery, setInputQuery] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [topK, setTopK] = useState<number>(4);
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.35);
  const [isTunerOpen, setIsTunerOpen] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSubmitting]);

  // Handle prefill query (e.g. from benchmark dataset "Test in Chat")
  useEffect(() => {
    if (prefillQuery) {
      setInputQuery(prefillQuery);
      textareaRef.current?.focus();
      onClearPrefill?.();
    }
  }, [prefillQuery, onClearPrefill]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || isSubmitting) return;

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    // Add user message
    const userMsg: ChatMessageType = {
      id: userMessageId,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };

    // Add placeholder assistant message
    const pendingAssistantMsg: ChatMessageType = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMsg, pendingAssistantMsg]);
    setInputQuery('');
    setIsSubmitting(true);

    try {
      // Extract preceding conversation history (excluding welcome prompt, loading/error states)
      const history = messages
        .filter((m) => m.id !== 'welcome' && !m.isLoading && !m.error && m.content)
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }));

      const payload: QueryRequest = {
        query,
        history,
        top_k: topK,
        similarity_threshold: similarityThreshold,
      };

      const result = await api.query(payload);

      if (result.processTimeMs !== undefined && onProcessTimeUpdate) {
        onProcessTimeUpdate(result.processTimeMs);
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessageId
            ? {
                ...m,
                isLoading: false,
                content: result.data.answer,
                queryResponse: result.data,
              }
            : m
        )
      );
    } catch (err) {
      const errorMsg =
        err instanceof ApiError ? err.detail : (err as Error).message;

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessageId
            ? {
                ...m,
                isLoading: false,
                content: 'Failed to retrieve answer from knowledge base.',
                error: errorMsg,
              }
            : m
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClearHistory = () => {
    setMessages([
      {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content:
          "Conversation cleared. Ready for your system design and distributed architecture questions.",
        timestamp: new Date().toISOString(),
        queryResponse: {
          query: "Reset",
          answer: "Conversation cleared. Ready for your system design and distributed architecture questions.",
          is_sufficient_evidence: true,
          citations: [],
          retrieved_chunks_count: 0,
          latency_ms: 0,
          llm_provider: "system",
          model_name: "archimind-v1",
        }
      }
    ]);
  };

  return (
    <div className="flex flex-col flex-1 max-w-5xl mx-auto w-full px-4 py-6">
      {/* Top Banner / Telemetry Notice */}
      <div className="flex items-center justify-between gap-3 p-3.5 mb-4 rounded-xl bg-slate-900/60 border border-white/5 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            Strict Evidence Grounding: Refuses speculation on out-of-scope topics.
          </span>
        </div>
        <div className="flex items-center gap-3">
          {onNavigateToKnowledge && (
            <button
              onClick={onNavigateToKnowledge}
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Knowledge Base</span>
            </button>
          )}
          <button
            onClick={handleClearHistory}
            className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors"
            title="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Parameter Tuner Drawer */}
      <ParameterTuner
        topK={topK}
        similarityThreshold={similarityThreshold}
        onTopKChange={setTopK}
        onSimilarityThresholdChange={setSimilarityThreshold}
        onReset={() => {
          setTopK(4);
          setSimilarityThreshold(0.35);
        }}
        isOpen={isTunerOpen}
        onToggle={() => setIsTunerOpen(!isTunerOpen)}
      />

      {/* Messages Scroll Area */}
      <div className="flex-1 space-y-2 mb-4 overflow-y-auto min-h-[400px]">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onOpenCitation={(citation) => setSelectedCitation(citation)}
          />
        ))}

        {/* Starter Prompts when conversation is short */}
        {messages.length <= 1 && (
          <StarterPrompts
            onSelectPrompt={(prompt) => {
              setInputQuery(prompt);
              textareaRef.current?.focus();
            }}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Area */}
      <div className="sticky bottom-4 z-20 w-full pt-2">
        <form
          onSubmit={handleSubmit}
          className="relative rounded-2xl bg-[#0f1422] border border-white/10 shadow-2xl focus-within:border-indigo-500/60 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all p-2"
        >
          <textarea
            ref={textareaRef}
            rows={2}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSubmitting}
            placeholder="Ask a system design question (e.g., 'How does Kafka guarantee message order within a partition?')..."
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-3 pt-2 font-sans leading-relaxed disabled:opacity-50"
          />

          <div className="flex items-center justify-between px-2 pt-2 border-t border-white/5 text-xs text-slate-500">
            <span className="hidden sm:flex items-center gap-1.5 font-mono text-[11px]">
              Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">Enter ↵</kbd> to send, <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">Shift + Enter</kbd> for newline
            </span>

            <div className="flex items-center gap-2 ml-auto">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={!inputQuery.trim() || isSubmitting}
                isLoading={isSubmitting}
                rightIcon={<Send className="w-3.5 h-3.5" />}
              >
                Synthesize Answer
              </Button>
            </div>
          </div>
        </form>
      </div>

      {/* Citation Detail Modal */}
      <CitationDrawer
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
};
