"""
Background tasks for asynchronous document processing.
Called by FastAPI BackgroundTasks after upload to avoid blocking the response.
"""
import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.services.embedding import embed_texts_batch
from app.services.ingestion import ingest_document
from app.services.vector_store import insert_chunk_embeddings
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def process_document(document_id: uuid.UUID, file_path: str, filename: str) -> None:
    """
    Full async pipeline for a newly uploaded document:
    1. Update status → PROCESSING
    2. Parse document into text chunks
    3. Generate Gemini embeddings in batches
    4. Bulk-insert chunks + embeddings into pgvector
    5. Update status → READY (or FAILED on error)
    """
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Mark document as processing
            doc = await session.get(Document, document_id)
            if not doc:
                logger.error("Document %s not found", document_id)
                return

            doc.status = DocumentStatus.PROCESSING
            await session.commit()
            logger.info("Processing document %s (%s)", document_id, filename)

            # Step 2: Parse document into chunks
            path = Path(file_path)
            chunks = ingest_document(
                file_path=path,
                filename=filename,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )

            if not chunks:
                raise ValueError("Document produced no text chunks")

            # Step 3: Generate embeddings in batches
            texts = [chunk.content for chunk in chunks]
            logger.info("Generating embeddings for %d chunks...", len(texts))
            embeddings = await embed_texts_batch(texts, batch_size=10)

            # Step 4: Prepare and insert chunk data
            chunks_data = [
                {
                    "content": chunk.content,
                    "embedding": embedding,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "metadata": {
                        **chunk.metadata,
                        "document_id": str(document_id),
                    },
                }
                for chunk, embedding in zip(chunks, embeddings)
            ]

            count = await insert_chunk_embeddings(session, document_id, chunks_data)

            # Step 5: Update document status to READY
            doc = await session.get(Document, document_id)
            if doc:
                doc.status = DocumentStatus.READY
                doc.total_chunks = count
            await session.commit()

            logger.info(
                "Document %s processed successfully: %d chunks indexed", document_id, count
            )

        except Exception as e:
            logger.error("Failed to process document %s: %s", document_id, e, exc_info=True)
            async with AsyncSessionLocal() as error_session:
                doc = await error_session.get(Document, document_id)
                if doc:
                    doc.status = DocumentStatus.FAILED
                    doc.error_message = str(e)[:1024]
                    await error_session.commit()

        finally:
            # Clean up the temporary upload file
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as cleanup_err:
                logger.warning("Failed to clean up file %s: %s", file_path, cleanup_err)
