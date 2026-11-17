import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  RefreshCw,
  Plus,
  AlertCircle,
} from 'lucide-react';
import { api, ApiError } from '../../services/api';
import type { DocumentMetadata, HealthResponse, IngestResponse } from '../../types/api';
import { DocumentCard } from './DocumentCard';
import { IngestionModal } from './IngestionModal';
import { StorageCapabilitiesCard } from './StorageCapabilitiesCard';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface KnowledgeBaseProps {
  health: HealthResponse | null;
  onRefreshHealth: () => void;
}

export const KnowledgeBase: React.FC<KnowledgeBaseProps> = ({
  health,
  onRefreshHealth,
}) => {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  const fetchDocuments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.getDocuments();
      setDocuments(result.data || []);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : (err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleIngestSuccess = (_res: IngestResponse) => {
    fetchDocuments();
    onRefreshHealth();
  };

  const filteredDocuments = documents.filter(
    (doc) =>
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.source_domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.url.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);

  return (
    <div className="flex-1 max-w-7xl mx-auto w-full px-4 lg:px-8 py-6 space-y-6">
      {/* Top Banner & Ingestion Action */}
      <div className="rounded-2xl glass-panel p-6 border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              Knowledge Base & Vector Store
            </h2>
            <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">
              {documents.length} Indexed Docs
            </span>
            <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
              {totalChunks} Chunks
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Official system design technical documentation parsed and indexed for dense semantic retrieval.
          </p>
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <Button
            variant="secondary"
            size="md"
            onClick={fetchDocuments}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Ingest Documentation
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search indexed documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60"
          />
        </div>

        <span className="text-xs text-slate-500 font-mono">
          Showing {filteredDocuments.length} of {documents.length} sources
        </span>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="py-12 flex flex-col items-center justify-center">
          <LoadingSpinner size="lg" text="Loading indexed documentation metadata..." />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 text-xs flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-rose-300">Failed to load documents:</span>
            <p className="mt-0.5 font-mono text-[11px] text-rose-200/90">{error}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && documents.length === 0 && (
        <div className="rounded-2xl glass-card p-12 text-center border border-white/10 flex flex-col items-center justify-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">No Documentation Indexed Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mt-1 leading-relaxed">
              The vector store is currently empty. Ingest the official curated system design documentation set (Kafka, Redis, DynamoDB, Envoy, Raft, PostgreSQL) to activate semantic retrieval.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => setIsModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Ingest Curated Sources
          </Button>
        </div>
      )}

      {/* Documents Grid */}
      {!isLoading && filteredDocuments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocuments.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} />
          ))}
        </div>
      )}

      {/* Storage & Architecture Capabilities Card */}
      <StorageCapabilitiesCard health={health} />

      {/* Ingestion Modal */}
      <IngestionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onIngestSuccess={handleIngestSuccess}
      />
    </div>
  );
};
