"""Services package."""
from app.services.cache import (
    get_cached_embedding,
    get_cached_rag_response,
    set_cached_embedding,
    set_cached_rag_response,
)
from app.services.embedding import embed_query, embed_text, embed_texts_batch
from app.services.ingestion import TextChunk, ingest_document
from app.services.rag_engine import generate_rag_response, stream_rag_response
from app.services.vector_store import (
    create_hnsw_index,
    insert_chunk_embeddings,
    similarity_search,
)

__all__ = [
    "get_cached_embedding",
    "get_cached_rag_response",
    "set_cached_embedding",
    "set_cached_rag_response",
    "embed_query",
    "embed_text",
    "embed_texts_batch",
    "TextChunk",
    "ingest_document",
    "generate_rag_response",
    "stream_rag_response",
    "create_hnsw_index",
    "insert_chunk_embeddings",
    "similarity_search",
]
