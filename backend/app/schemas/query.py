"""
Pydantic schemas for RAG query requests and responses.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    document_ids: list[uuid.UUID] | None = Field(
        default=None, description="Filter to specific documents (None = search all)"
    )


class SourceCitation(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    content_snippet: str
    page_number: int | None = None
    section: str | None = None
    similarity_score: float


class LatencyMetrics(BaseModel):
    embedding_ms: float
    vector_search_ms: float
    llm_generation_ms: float
    total_ms: float
    cached: bool = False


class RAGResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    answer: str
    sources: list[SourceCitation]
    query: str
    latency: LatencyMetrics
    model_used: str
    timestamp: datetime


class StreamChunk(BaseModel):
    """Schema for a single SSE chunk in streaming responses."""
    type: str  # "token" | "sources" | "latency" | "done" | "error"
    content: str | None = None
    sources: list[SourceCitation] | None = None
    latency: LatencyMetrics | None = None
