import React, { useState } from 'react';
import {
  Search,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Key,
  ShieldAlert,
} from 'lucide-react';
import { BENCHMARK_QUESTIONS } from '../../data/benchmarkQuestions';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface BenchmarkQuestionsTableProps {
  onTestInChat: (question: string) => void;
}

export const BenchmarkQuestionsTable: React.FC<BenchmarkQuestionsTableProps> = ({
  onTestInChat,
}) => {
  const [selectedTopic, setSelectedTopic] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const topics = ['All', 'Kafka', 'Redis', 'DynamoDB', 'Envoy', 'Raft', 'PostgreSQL', 'Out-of-Scope'];

  const filteredQuestions = BENCHMARK_QUESTIONS.filter((q) => {
    const matchesTopic = selectedTopic === 'All' || q.topic === selectedTopic;
    const matchesSearch =
      q.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.groundTruthAnswer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.expectedKeywords.some((k) => k.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesTopic && matchesSearch;
  });

  return (
    <div className="rounded-2xl glass-card p-5 border border-white/10 mt-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            30-Question Evaluation Dataset Suite
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">
              Gold Standard
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Curated system design questions with ground-truth answers and out-of-scope negative samples
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search questions or keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60"
          />
        </div>
      </div>

      {/* Topic Filter Chips */}
      <div className="flex flex-wrap items-center gap-1.5 mb-4">
        {topics.map((t) => (
          <button
            key={t}
            onClick={() => setSelectedTopic(t)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
              selectedTopic === t
                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-white/5'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Questions List */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {filteredQuestions.map((item) => {
          const isExpanded = expandedId === item.id;
          const diffColor =
            item.difficulty === 'easy'
              ? 'emerald'
              : item.difficulty === 'medium'
              ? 'cyan'
              : 'amber';

          return (
            <div
              key={item.id}
              className="rounded-xl bg-slate-900/60 border border-white/5 p-3.5 hover:border-white/10 transition-all text-xs"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5 flex-1 min-w-0">
                  <span className="font-mono text-[11px] font-bold text-slate-500 shrink-0 mt-0.5">
                    #{item.id.toString().padStart(2, '0')}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {item.topic}
                      </span>
                      <Badge variant={diffColor as any} size="sm">
                        {item.difficulty}
                      </Badge>
                      {!item.isAnswerable && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/60 flex items-center gap-1">
                          <ShieldAlert className="w-2.5 h-2.5" />
                          Unanswerable Negative Sample
                        </span>
                      )}
                    </div>
                    <p className="font-medium text-slate-200 leading-relaxed">
                      {item.question}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <Button
                    variant="outline"
                    size="xs"
                    onClick={() => onTestInChat(item.question)}
                    leftIcon={<MessageSquare className="w-3 h-3 text-indigo-400" />}
                    title="Send this question to Chat Workspace"
                  >
                    Test in Chat
                  </Button>
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-white/5"
                    title={isExpanded ? 'Collapse' : 'Expand details'}
                  >
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Expanded Ground Truth and Keywords */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-white/5 space-y-2.5 animate-fade-in">
                  <div>
                    <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider">
                      Ground Truth Reference Answer:
                    </span>
                    <p className="mt-1 text-slate-300 bg-[#090d14] p-3 rounded-lg border border-white/5 leading-relaxed font-sans">
                      {item.groundTruthAnswer}
                    </p>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider flex items-center gap-1">
                      <Key className="w-3 h-3 text-amber-400" />
                      Key Facts & Evaluator Match Terms:
                    </span>
                    <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
                      {item.expectedKeywords.map((kw, kwIdx) => (
                        <span
                          key={kwIdx}
                          className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 border border-slate-700/60"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
