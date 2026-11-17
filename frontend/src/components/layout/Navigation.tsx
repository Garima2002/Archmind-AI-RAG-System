import React from 'react';
import { MessageSquare, BarChart3, BookOpen } from 'lucide-react';

export type NavTab = 'chat' | 'evaluation' | 'knowledge';

interface NavigationProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  documentsCount?: number;
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onTabChange,
  documentsCount,
}) => {
  const tabs = [
    {
      id: 'chat' as NavTab,
      label: 'Chat Workspace',
      icon: MessageSquare,
      badge: null,
      description: 'System design Q&A with grounded citations',
    },
    {
      id: 'evaluation' as NavTab,
      label: 'Evaluation Dashboard',
      icon: BarChart3,
      badge: '30 Qs',
      description: 'Recall@K, MRR & Faithfulness metrics',
    },
    {
      id: 'knowledge' as NavTab,
      label: 'Knowledge Base',
      icon: BookOpen,
      badge: documentsCount !== undefined ? `${documentsCount} docs` : null,
      description: 'Indexed documentation & ingestion pipeline',
    },
  ];

  return (
    <nav className="border-b border-white/10 bg-[#0c101a]/95 backdrop-blur-md px-4 lg:px-8 py-2">
      <div className="max-w-7xl mx-auto flex items-center gap-2 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center gap-2.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-150 whitespace-nowrap select-none ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-sm shadow-indigo-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
                    isActive
                      ? 'bg-indigo-500/25 text-indigo-200 border border-indigo-400/30'
                      : 'bg-slate-800 text-slate-400 border border-slate-700/60'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
