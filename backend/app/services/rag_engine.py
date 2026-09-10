"""
RAG Engine — Prompt construction, Gemini 2.5 Flash generation, and citation extraction.
Supports both standard and streaming generation.
"""
import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from google import genai
from google.genai import types

from app.config import get_settings
from app.schemas.query import LatencyMetrics, RAGResponse, SourceCitation

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# System Prompt Template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a precise, expert document assistant. Your task is to answer the user's question using ONLY the provided document context below.

Rules:
1. Answer ONLY from the provided context. If the context does not contain sufficient information, say so clearly.
2. For EVERY fact or statement you make, you MUST cite the source using the format: [Source: {document_name}, Page {page}] or [Source: {document_name}, Section: {section}].
3. Structure your answer clearly. Use bullet points or numbered lists where appropriate.
4. If multiple sources support a fact, cite all of them.
5. Do not fabricate or infer information beyond what is in the context.

---
DOCUMENT CONTEXT:
{context}
---

Answer the following question with proper citations:"""


def _build_context_block(sources: list[SourceCitation]) -> str:
    """Format source citations into a structured context block for the prompt."""
    blocks = []
    for i, source in enumerate(sources, start=1):
        location_parts = []
        if source.page_number:
            location_parts.append(f"Page {source.page_number}")
        if source.section:
            location_parts.append(f"Section: {source.section}")
        location = ", ".join(location_parts) if location_parts else "General"

        blocks.append(
            f"[Context {i}] — {source.document_name} ({location})\n"
            f"{source.content_snippet}\n"
        )
    return "\n".join(blocks)


def _build_prompt(query: str, sources: list[SourceCitation]) -> str:
    """Construct the full RAG prompt."""
    context = _build_context_block(sources)
    system = SYSTEM_PROMPT.format(context=context)
    return f"{system}\n\nQuestion: {query}"


# ---------------------------------------------------------------------------
# Standard Generation
# ---------------------------------------------------------------------------

async def generate_rag_response(
    query: str,
    sources: list[SourceCitation],
    embedding_ms: float,
    vector_search_ms: float,
    cached: bool = False,
) -> RAGResponse:
    """
    Generate a full RAG response using Gemini 2.5 Flash.
    Returns a complete RAGResponse with answer, citations, and latency metrics.
    """
    import time

    client = genai.Client(api_key=settings.google_api_key)
    prompt = _build_prompt(query, sources)

    start_llm = time.perf_counter()
    loop = asyncio.get_event_loop()

    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2048,
            ),
        ),
    )

    llm_ms = (time.perf_counter() - start_llm) * 1000
    answer = response.text or "I could not generate a response based on the provided context."

    total_ms = embedding_ms + vector_search_ms + llm_ms

    return RAGResponse(
        answer=answer,
        sources=sources,
        query=query,
        latency=LatencyMetrics(
            embedding_ms=round(embedding_ms, 2),
            vector_search_ms=round(vector_search_ms, 2),
            llm_generation_ms=round(llm_ms, 2),
            total_ms=round(total_ms, 2),
            cached=cached,
        ),
        model_used=settings.llm_model,
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Streaming Generation (SSE)
# ---------------------------------------------------------------------------

async def stream_rag_response(
    query: str,
    sources: list[SourceCitation],
    embedding_ms: float,
    vector_search_ms: float,
) -> AsyncGenerator[str, None]:
    """
    Stream a RAG response as Server-Sent Events (SSE).

    Yields SSE-formatted strings:
    - data: {"type": "token", "content": "..."}
    - data: {"type": "sources", "sources": [...]}
    - data: {"type": "latency", "latency": {...}}
    - data: {"type": "done"}
    """
    import json
    import time

    client = genai.Client(api_key=settings.google_api_key)
    prompt = _build_prompt(query, sources)

    # Yield sources immediately before streaming starts
    sources_payload = [s.model_dump(mode="json") for s in sources]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources_payload})}\n\n"

    start_llm = time.perf_counter()
    loop = asyncio.get_event_loop()

    try:
        # Run the streaming call in executor to not block the event loop
        def _stream():
            return client.models.generate_content_stream(
                model=settings.llm_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                ),
            )

        stream = await loop.run_in_executor(None, _stream)

        for chunk in stream:
            if chunk.text:
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.text})}\n\n"
                # Small sleep to allow other coroutines to run
                await asyncio.sleep(0)

    except Exception as e:
        logger.error("Streaming generation error: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        return

    llm_ms = (time.perf_counter() - start_llm) * 1000
    total_ms = embedding_ms + vector_search_ms + llm_ms

    latency = LatencyMetrics(
        embedding_ms=round(embedding_ms, 2),
        vector_search_ms=round(vector_search_ms, 2),
        llm_generation_ms=round(llm_ms, 2),
        total_ms=round(total_ms, 2),
        cached=False,
    )
    yield f"data: {json.dumps({'type': 'latency', 'latency': latency.model_dump()})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
