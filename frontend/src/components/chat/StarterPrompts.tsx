import React from 'react';
import { Sparkles, Terminal, ShieldAlert } from 'lucide-react';

interface StarterPromptsProps {
  onSelectPrompt: (prompt: string) => void;
}

export const StarterPrompts: React.FC<StarterPromptsProps> = ({ onSelectPrompt }) => {
  const prompts = [
    {
      topic: 'Kafka',
      color: 'from-amber-500/20 to-orange-500/10 border-amber-500/30 text-amber-300',
      tag: 'Ordering & Partitions',
      query: 'How does Kafka guarantee message ordering within a partition, and what is the role of partition keys?',
    },
    {
      topic: 'Redis',
      color: 'from-rose-500/20 to-red-500/10 border-rose-500/30 text-rose-300',
      tag: 'Persistence & HA',
      query: 'Compare Redis RDB snapshots and AOF persistence in terms of durability and performance trade-offs.',
    },
    {
      topic: 'DynamoDB',
      color: 'from-blue-500/20 to-indigo-500/10 border-blue-500/30 text-blue-300',
      tag: 'Storage & Paxos',
      query: 'How does DynamoDB use partition keys and consistent hashing to distribute items across storage nodes?',
    },
    {
      topic: 'Envoy',
      color: 'from-purple-500/20 to-violet-500/10 border-purple-500/30 text-purple-300',
      tag: 'Threading Model',
      query: "Explain Envoy Proxy's threading model and how worker threads process incoming client connections.",
    },
    {
      topic: 'Raft',
      color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/30 text-emerald-300',
      tag: 'Consensus',
      query: 'How does Raft prevent split votes during leader election, and how does a candidate win?',
    },
    {
      topic: 'Postgres',
      color: 'from-cyan-500/20 to-sky-500/10 border-cyan-500/30 text-cyan-300',
      tag: 'MVCC & WAL',
      query: 'How does PostgreSQL implement Multi-Version Concurrency Control (MVCC) using xmin and xmax headers?',
    },
    {
      topic: 'Guardrail Test',
      color: 'from-yellow-500/20 to-amber-500/10 border-yellow-500/30 text-yellow-300',
      tag: 'Out-of-Scope Fallback',
      isGuardrail: true,
      query: 'Can you give me a recipe for baking a dark chocolate sponge cake?',
    },
  ];

  return (
    <div className="w-full my-6">
      <div className="flex items-center gap-2 mb-3.5 text-xs text-slate-400 font-medium">
        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
        <span>Curated System Design Queries (Click to Run):</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {prompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(p.query)}
            className={`group text-left p-3.5 rounded-xl bg-gradient-to-br ${p.color} bg-slate-900/60 border hover:border-indigo-400/50 hover:bg-slate-800/80 transition-all duration-150 flex flex-col justify-between`}
          >
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">
                {p.topic}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-black/40 text-slate-300 border border-white/10 flex items-center gap-1">
                {p.isGuardrail ? <ShieldAlert className="w-2.5 h-2.5 text-amber-400" /> : <Terminal className="w-2.5 h-2.5 text-slate-400" />}
                {p.tag}
              </span>
            </div>
            <p className="text-xs text-slate-300 group-hover:text-white line-clamp-2 leading-relaxed">
              {p.query}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};
