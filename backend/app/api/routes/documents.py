"""
Documents API routes — upload, list, get, delete.
"""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.background.tasks import process_document
from app.config import get_settings
from app.database import get_db
from app.models.document import Document, DocumentStatus
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.cache import invalidate_document_cache

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt"}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """
    Upload a document (PDF, Markdown, or TXT) for processing.
    Processing happens asynchronously in the background.
    """
    # Validate file type
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read and size-check the file
    content = await file.read()
    size_bytes = len(content)
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_file_size_mb} MB",
        )

    # Save to uploads directory
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = f"{uuid.uuid4()}{suffix}"
    file_path = upload_dir / safe_filename
    file_path.write_bytes(content)

    # Create document record
    document = Document(
        filename=safe_filename,
        original_filename=file.filename or safe_filename,
        file_type=suffix.lstrip("."),
        file_size_bytes=size_bytes,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.flush()
    doc_id = document.id
    await db.commit()

    # Queue background processing
    background_tasks.add_task(
        process_document,
        document_id=doc_id,
        file_path=str(file_path),
        filename=file.filename or safe_filename,
    )

    logger.info("Document %s uploaded, queued for processing", doc_id)
    return DocumentUploadResponse(
        document_id=doc_id,
        filename=file.filename or safe_filename,
        status=DocumentStatus.PENDING,
        message="Document uploaded successfully. Processing started in background.",
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> DocumentListResponse:
    """List all uploaded documents with pagination."""
    count_result = await db.execute(select(func.count()).select_from(Document))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a single document by ID."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document and all its chunks (CASCADE)."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await db.delete(doc)
    await db.commit()
    await invalidate_document_cache(str(document_id))
    logger.info("Document %s deleted", document_id)
