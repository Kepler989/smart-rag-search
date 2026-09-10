/**
 * TypeScript types matching backend Pydantic schemas.
 */

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  total_chunks: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  message: string;
}

export interface SourceCitation {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content_snippet: string;
  page_number?: number | null;
  section?: string | null;
  similarity_score: number;
}

export interface LatencyMetrics {
  embedding_ms: number;
  vector_search_ms: number;
  llm_generation_ms: number;
  total_ms: number;
  cached: boolean;
}

export interface RAGResponse {
  answer: string;
  sources: SourceCitation[];
  query: string;
  latency: LatencyMetrics;
  model_used: string;
  timestamp: string;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  document_ids?: string[] | null;
}

export interface StreamChunk {
  type: "token" | "sources" | "latency" | "done" | "error";
  content?: string;
  sources?: SourceCitation[];
  latency?: LatencyMetrics;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  latency?: LatencyMetrics;
  timestamp: Date;
  isStreaming?: boolean;
}
