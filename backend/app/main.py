"""
FastAPI application entrypoint.
Registers routers, middleware, startup/shutdown lifecycle hooks.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.documents import router as documents_router
from app.api.routes.query import router as query_router
from app.config import get_settings
from app.database import engine
from app.middleware.latency import LatencyTrackingMiddleware
from app.models import Document, DocumentChunk  # noqa: F401 — ensure models are imported for Alembic
from app.services.cache import close_redis
from app.services.vector_store import create_hnsw_index
from app.database import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("🚀 Starting Smart RAG Search API (env=%s)", settings.environment)

    # Ensure HNSW index exists (idempotent)
    async with AsyncSessionLocal() as session:
        try:
            await create_hnsw_index(session)
        except Exception as e:
            logger.warning("Could not create HNSW index on startup: %s", e)

    yield

    # Shutdown — close Redis connection pool
    await close_redis()
    await engine.dispose()
    logger.info("👋 Smart RAG Search API shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart RAG Document Search API",
        description=(
            "Production-grade Retrieval-Augmented Generation API with pgvector semantic search, "
            "Gemini embeddings + generation, Redis caching, and streaming responses."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- CORS ---
    origins = settings.cors_origins_list
    allow_all = "*" in origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else origins,
        allow_credentials=not allow_all,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Total-Latency-Ms",
            "X-Embedding-Latency-Ms",
            "X-Vector-Search-Latency-Ms",
            "X-LLM-Latency-Ms",
        ],
    )

    # --- Latency Tracking Middleware ---
    app.add_middleware(LatencyTrackingMiddleware)

    # --- Routers ---
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(query_router, prefix="/api/v1")

    # --- Root & Health Check ---
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "Smart RAG Document Search API",
            "version": "1.0.0",
            "status": "healthy",
            "docs_url": "/docs",
            "health_url": "/health",
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "environment": settings.environment,
            "version": "1.0.0",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host if hasattr(settings, "backend_host") else "0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
