/**
 * Typed API client for the Smart RAG FastAPI backend.
 */
import type {
  Document,
  DocumentListResponse,
  DocumentUploadResponse,
  QueryRequest,
  RAGResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

// -----------------------------------------------------------------------
// Documents API
// -----------------------------------------------------------------------

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_V1}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail ?? "Upload failed");
  }

  return res.json();
}

export async function fetchDocuments(
  limit = 50,
  offset = 0
): Promise<DocumentListResponse> {
  const res = await fetch(
    `${API_V1}/documents/?limit=${limit}&offset=${offset}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function fetchDocument(id: string): Promise<Document> {
  const res = await fetch(`${API_V1}/documents/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch document");
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${API_V1}/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete document");
}

// -----------------------------------------------------------------------
// Query / RAG API
// -----------------------------------------------------------------------

export async function queryDocuments(request: QueryRequest): Promise<RAGResponse> {
  const res = await fetch(`${API_V1}/query/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Query failed" }));
    throw new Error(err.detail ?? "Query failed");
  }

  return res.json();
}

/**
 * Create a streaming query request and return the EventSource-like ReadableStream.
 * Caller should parse SSE events manually.
 */
export async function streamQuery(
  request: QueryRequest,
  onToken: (token: string) => void,
  onSources: (sources: import("./types").SourceCitation[]) => void,
  onLatency: (latency: import("./types").LatencyMetrics) => void,
  onDone: () => void,
  onError: (err: string) => void
): Promise<void> {
  const res = await fetch(`${API_V1}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => ({ detail: "Stream failed" }));
    onError(err.detail ?? "Stream failed");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const json = line.slice(6).trim();
      if (!json) continue;

      try {
        const chunk = JSON.parse(json) as import("./types").StreamChunk;
        switch (chunk.type) {
          case "token":
            if (chunk.content) onToken(chunk.content);
            break;
          case "sources":
            if (chunk.sources) onSources(chunk.sources);
            break;
          case "latency":
            if (chunk.latency) onLatency(chunk.latency);
            break;
          case "done":
            onDone();
            return;
          case "error":
            onError(chunk.content ?? "Unknown streaming error");
            return;
        }
      } catch {
        // Ignore malformed SSE lines
      }
    }
  }

  onDone();
}

// -----------------------------------------------------------------------
// Health Check
// -----------------------------------------------------------------------

export async function checkHealth(): Promise<{ status: string; environment: string }> {
  const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Backend unavailable");
  return res.json();
}
