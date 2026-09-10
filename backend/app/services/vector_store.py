"""
Vector store service — pgvector HNSW index management and similarity search.
"""
import logging
import uuid
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.chunk import DocumentChunk
from app.schemas.query import SourceCitation

logger = logging.getLogger(__name__)
settings = get_settings()


async def create_hnsw_index(session: AsyncSession) -> None:
    """
    Create the HNSW index on the embedding column for fast cosine similarity search.
    Called once during database initialization.
    """
    index_sql = text("""
        CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    await session.execute(index_sql)
    await session.commit()
    logger.info("HNSW index created (or already exists)")


async def similarity_search(
    session: AsyncSession,
    query_embedding: list[float],
    top_k: int = 5,
    document_ids: Optional[list[uuid.UUID]] = None,
) -> list[SourceCitation]:
    """
    Perform cosine similarity search against the pgvector HNSW index.

    Returns the top-K most similar DocumentChunks as SourceCitation objects,
    sorted by similarity score descending.
    """
    # Build the query using pgvector's <=> operator (cosine distance)
    # Cosine similarity = 1 - cosine_distance
    embedding_literal = str(query_embedding)

    stmt = (
        select(
            DocumentChunk,
            (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label("similarity"),
        )
        .join(DocumentChunk.document)
        .order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        )
        .limit(top_k)
    )

    if document_ids:
        stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

    result = await session.execute(stmt)
    rows = result.all()

    citations: list[SourceCitation] = []
    for chunk, similarity in rows:
        citations.append(
            SourceCitation(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=chunk.chunk_metadata.get("filename", "Unknown"),
                content_snippet=chunk.content[:500],
                page_number=chunk.page_number,
                section=chunk.section,
                similarity_score=float(similarity),
            )
        )

    logger.info("Vector search returned %d results (top_k=%d)", len(citations), top_k)
    return citations


async def insert_chunk_embeddings(
    session: AsyncSession,
    document_id: uuid.UUID,
    chunks_data: list[dict],
) -> int:
    """
    Bulk-insert chunk embeddings into the database.

    Args:
        session: Async SQLAlchemy session
        document_id: Parent document UUID
        chunks_data: List of dicts with keys: content, embedding, chunk_index,
                     page_number, section, metadata

    Returns:
        Number of chunks inserted.
    """
    chunk_objects = [
        DocumentChunk(
            document_id=document_id,
            content=cd["content"],
            embedding=cd["embedding"],
            chunk_index=cd["chunk_index"],
            page_number=cd.get("page_number"),
            section=cd.get("section"),
            chunk_metadata=cd.get("metadata", {}),
        )
        for cd in chunks_data
    ]

    session.add_all(chunk_objects)
    await session.flush()
    logger.info("Inserted %d chunk embeddings for document %s", len(chunk_objects), document_id)
    return len(chunk_objects)
