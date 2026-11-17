/**
 * API Service for communicating with ArchiMind AI FastAPI backend.
 */

import type {
  DocumentMetadata,
  EvaluationRunRequest,
  EvaluationSummary,
  HealthResponse,
  IngestRequest,
  IngestResponse,
  QueryRequest,
  QueryResponse,
} from '../types/api';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(response: Response): Promise<{ data: T; processTimeMs?: number }> {
  const headerTime = response.headers.get('X-Process-Time-Ms');
  const processTimeMs = headerTime ? parseFloat(headerTime) : undefined;

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const errorJson = await response.json();
      if (typeof errorJson.detail === 'string') {
        detail = errorJson.detail;
      } else if (Array.isArray(errorJson.detail)) {
        // FastAPI validation errors
        detail = errorJson.detail.map((d: { msg?: string; loc?: string[] }) => `${d.loc?.join('.') || 'param'}: ${d.msg}`).join(', ');
      } else if (errorJson.message) {
        detail = errorJson.message;
      }
    } catch {
      // Non-JSON error body
    }
    throw new ApiError(response.status, detail);
  }

  const data = (await response.json()) as T;
  return { data, processTimeMs };
}

export const api = {
  getBaseUrl(): string {
    return API_BASE_URL || window.location.origin;
  },

  /**
   * Health check endpoint
   */
  async getHealth(): Promise<{ data: HealthResponse; processTimeMs?: number }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      });
      return await handleResponse<HealthResponse>(response);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(0, `Cannot connect to backend at ${API_BASE_URL || 'default port'}. Ensure FastAPI is running.`);
    }
  },

  /**
   * Send a system design question to RAG Engine
   */
  async query(request: QueryRequest): Promise<{ data: QueryResponse; processTimeMs?: number }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(request),
      });
      return await handleResponse<QueryResponse>(response);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(0, `Failed to query knowledge base: ${(err as Error).message}`);
    }
  },

  /**
   * List all ingested documents
   */
  async getDocuments(): Promise<{ data: DocumentMetadata[]; processTimeMs?: number }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents`, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      });
      return await handleResponse<DocumentMetadata[]>(response);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(0, `Failed to retrieve indexed documents: ${(err as Error).message}`);
    }
  },

  /**
   * Trigger documentation ingestion pipeline
   */
  async ingest(request: IngestRequest = { use_curated_defaults: true }): Promise<{ data: IngestResponse; processTimeMs?: number }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(request),
      });
      return await handleResponse<IngestResponse>(response);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(0, `Failed to ingest documentation: ${(err as Error).message}`);
    }
  },

  /**
   * Run benchmark evaluation
   */
  async evaluate(request: EvaluationRunRequest = {}): Promise<{ data: EvaluationSummary; processTimeMs?: number }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/evaluate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(request),
      });
      return await handleResponse<EvaluationSummary>(response);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(0, `Evaluation failed: ${(err as Error).message}`);
    }
  },
};
