import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/layout/Header';
import { Navigation, type NavTab } from './components/layout/Navigation';
import { Footer } from './components/layout/Footer';
import { ChatWorkspace } from './components/chat/ChatWorkspace';
import { EvaluationDashboard } from './components/evaluation/EvaluationDashboard';
import { KnowledgeBase } from './components/knowledge/KnowledgeBase';
import { api, ApiError } from './services/api';
import type { HealthResponse } from './types/api';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './components/common/Button';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('chat');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState<boolean>(true);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [lastProcessTimeMs, setLastProcessTimeMs] = useState<number | undefined>(undefined);
  const [prefillChatQuery, setPrefillChatQuery] = useState<string | undefined>(undefined);

  const fetchHealth = useCallback(async () => {
    setIsLoadingHealth(true);
    setBackendError(null);
    try {
      const res = await api.getHealth();
      setHealth(res.data);
      if (res.processTimeMs !== undefined) {
        setLastProcessTimeMs(res.processTimeMs);
      }
    } catch (err) {
      const errorMsg =
        err instanceof ApiError ? err.detail : (err as Error).message;
      setBackendError(errorMsg);
    } finally {
      setIsLoadingHealth(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    // Poll health status every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const handleTestInChat = (question: string) => {
    setPrefillChatQuery(question);
    setActiveTab('chat');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0d14] text-slate-100 font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* System Health Header */}
      <Header
        health={health}
        isLoadingHealth={isLoadingHealth}
        onRefreshHealth={fetchHealth}
        lastProcessTimeMs={lastProcessTimeMs}
        backendError={backendError}
      />

      {/* Backend Disconnected Alert Banner */}
      {backendError && (
        <div className="w-full bg-rose-950/60 border-b border-rose-800/60 px-4 lg:px-8 py-3 text-xs text-rose-200">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-rose-300">
                  Backend API Server Not Detected ({api.getBaseUrl()}):
                </span>
                <p className="mt-0.5 text-rose-200/90 leading-relaxed font-mono text-[11px]">
                  Start the server locally using:{' '}
                  <code className="bg-black/40 px-1.5 py-0.5 rounded text-white border border-rose-700/50">
                    uvicorn archimind.main:app --host 0.0.0.0 --port 8000 --reload
                  </code>
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="xs"
              onClick={fetchHealth}
              disabled={isLoadingHealth}
              leftIcon={<RefreshCw className={`w-3 h-3 ${isLoadingHealth ? 'animate-spin' : ''}`} />}
              className="border-rose-700 text-rose-200 hover:bg-rose-900/40 shrink-0"
            >
              Reconnect
            </Button>
          </div>
        </div>
      )}

      {/* Navigation Bar */}
      <Navigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
        documentsCount={health?.documents_count}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col">
        {activeTab === 'chat' && (
          <ChatWorkspace
            onProcessTimeUpdate={setLastProcessTimeMs}
            onNavigateToKnowledge={() => setActiveTab('knowledge')}
            prefillQuery={prefillChatQuery}
            onClearPrefill={() => setPrefillChatQuery(undefined)}
          />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationDashboard onTestInChat={handleTestInChat} />
        )}

        {activeTab === 'knowledge' && (
          <KnowledgeBase
            health={health}
            onRefreshHealth={fetchHealth}
          />
        )}
      </main>

      {/* Global Footer */}
      <Footer />
    </div>
  );
};

export default App;
