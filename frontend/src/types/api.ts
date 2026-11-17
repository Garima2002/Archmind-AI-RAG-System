/**
 * TypeScript definitions mapping 1:1 to FastAPI Pydantic schemas in archimind/api/schemas.py
 */

export interface HealthResponse {
  status: 'healthy' | 'degraded' | string;
  version: string;
  environment: string;
  vector_store_type: 'pgvector' | 'memory' | string;
  vector_store_connected: boolean;
  embedding_model: string;
  llm_provider: 'mock' | 'openai' | 'anthropic' | 'gemini' | string;
  documents_count: number;
  chunks_count: number;
}

export interface Citation {
  citation_id: number;
  document_id: string;
  document_title: string;
  document_url: string;
  section_title: string | null;
  chunk_id: string;
  snippet: string;
  score: number;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatHistoryItem {
  role: 'user' | 'assistant';
  content: string;
}

export interface QueryRequest {
  query: string;
  history?: ChatHistoryItem[];
  top_k?: number;
  similarity_threshold?: number;
}

export interface QueryResponse {
  query: string;
  answer: string;
  is_sufficient_evidence: boolean;
  citations: Citation[];
  retrieved_chunks_count: number;
  latency_ms: number;
  llm_provider: string;
  model_name: string;
  token_usage?: TokenUsage | null;
  rephrased_query?: string | null;
  intent?: 'greeting' | 'technical' | 'conversational' | string;
}

export interface DocumentMetadata {
  id: string;
  title: string;
  url: string;
  source_domain: string;
  chunk_count: number;
  created_at: string;
}

export interface IngestRequest {
  urls?: string[];
  use_curated_defaults?: boolean;
  force_refresh?: boolean;
}

export interface IngestResponse {
  status: string;
  documents_ingested: number;
  total_chunks: number;
  details: DocumentMetadata[];
  elapsed_seconds: number;
  message: string;
}

export interface RetrievalMetrics {
  recall_at_1: number;
  recall_at_3: number;
  recall_at_5: number;
  precision_at_1: number;
  precision_at_3: number;
  precision_at_5: number;
  mrr: number;
}

export interface AnswerMetrics {
  mean_faithfulness: number;
  mean_correctness: number;
  unanswerable_detection_accuracy: number;
}

export interface EvaluationSummary {
  total_questions: number;
  evaluated_at: string;
  retrieval_metrics: RetrievalMetrics;
  answer_metrics: AnswerMetrics;
  mean_latency_ms: number;
  langsmith_dataset_id?: string | null;
  langsmith_sync_status: string;
}

export interface EvaluationRunRequest {
  max_questions?: number;
  sync_to_langsmith?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  queryResponse?: QueryResponse;
  error?: string;
  isLoading?: boolean;
}
