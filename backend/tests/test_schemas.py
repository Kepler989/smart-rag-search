"""Unit tests for Pydantic schemas."""
import uuid
from datetime import datetime, timezone
import pytest
from app.schemas.query import QueryRequest, SourceCitation, LatencyMetrics, RAGResponse
from app.schemas.document import DocumentResponse, DocumentListResponse


def test_query_request_validation():
    req = QueryRequest(query="Explain RAG", top_k=5)
    assert req.query == "Explain RAG"
    assert req.top_k == 5
    assert req.document_ids is None


def test_source_citation_schema():
    chunk_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    citation = SourceCitation(
        chunk_id=chunk_id,
        document_id=doc_id,
        document_name="rag_guide.pdf",
        page_number=2,
        section="Architecture",
        similarity_score=0.92,
        content_snippet="RAG retrieves context before generation.",
    )
    assert citation.similarity_score == 0.92
    assert citation.page_number == 2
    assert citation.document_name == "rag_guide.pdf"


def test_rag_response_schema():
    metrics = LatencyMetrics(
        embedding_ms=12.5,
        vector_search_ms=8.0,
        llm_generation_ms=150.0,
        total_ms=170.5,
        cached=False,
    )
    resp = RAGResponse(
        query="What is RAG?",
        answer="RAG combines retrieval with generation.",
        sources=[],
        latency=metrics,
        model_used="gemini-2.5-flash",
        timestamp=datetime.now(timezone.utc),
    )
    assert resp.latency.cached is False
    assert resp.latency.total_ms == 170.5
    assert resp.model_used == "gemini-2.5-flash"
