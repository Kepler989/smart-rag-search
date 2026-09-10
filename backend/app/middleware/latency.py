"""
Latency tracking middleware.
Measures embedding, vector search, and LLM generation latencies
and injects them as response headers.
"""
import time
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variables for per-request latency tracking
embedding_latency_var: ContextVar[float] = ContextVar("embedding_latency", default=0.0)
vector_search_latency_var: ContextVar[float] = ContextVar("vector_search_latency", default=0.0)
llm_latency_var: ContextVar[float] = ContextVar("llm_latency", default=0.0)


class LatencyTrackingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that measures total request latency and
    injects granular latency headers into each response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Reset per-request latency context vars
        token_emb = embedding_latency_var.set(0.0)
        token_vec = vector_search_latency_var.set(0.0)
        token_llm = llm_latency_var.set(0.0)

        start = time.perf_counter()
        response = await call_next(request)
        total_ms = (time.perf_counter() - start) * 1000

        # Inject latency headers
        response.headers["X-Total-Latency-Ms"] = f"{total_ms:.2f}"
        response.headers["X-Embedding-Latency-Ms"] = f"{embedding_latency_var.get():.2f}"
        response.headers["X-Vector-Search-Latency-Ms"] = f"{vector_search_latency_var.get():.2f}"
        response.headers["X-LLM-Latency-Ms"] = f"{llm_latency_var.get():.2f}"

        # Restore context vars
        embedding_latency_var.reset(token_emb)
        vector_search_latency_var.reset(token_vec)
        llm_latency_var.reset(token_llm)

        return response


def record_embedding_latency(ms: float) -> None:
    """Call this after embedding generation to record the latency."""
    embedding_latency_var.set(ms)


def record_vector_search_latency(ms: float) -> None:
    """Call this after vector search to record the latency."""
    vector_search_latency_var.set(ms)


def record_llm_latency(ms: float) -> None:
    """Call this after LLM generation to record the latency."""
    llm_latency_var.set(ms)
