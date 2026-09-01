from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.document import Document, DocumentStatus
from pydantic import BaseModel
from typing import Optional, Any

router = APIRouter()


class DocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: str
    file_id: Optional[int] = None
    raw_content: Optional[str] = None
    processed_content: Optional[str] = None
    content_hash: Optional[str] = None
    metadata: Optional[dict] = None
    author: Optional[str] = None
    language: Optional[str] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "all-MiniLM-L6-v2"


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None
    is_public: Optional[bool] = None


@router.get("/", response_model=None)
async def list_documents(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    """List all documents for the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user_id)
        .where(Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return list(documents)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_document(
    document_data: DocumentCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Create a new document."""
    document = Document(
        user_id=current_user_id,
        title=document_data.title,
        description=document_data.description,
        document_type=document_data.document_type,
        file_id=document_data.file_id,
        raw_content=document_data.raw_content,
        processed_content=document_data.processed_content,
        content_hash=document_data.content_hash,
        metadata=document_data.metadata,
        author=document_data.author,
        language=document_data.language,
        chunk_size=document_data.chunk_size,
        chunk_overlap=document_data.chunk_overlap,
        embedding_model=document_data.embedding_model,
        status=DocumentStatus.PROCESSING,
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    logger.info(f"Document created: {document.id}")
    
    return document


@router.get("/{document_id}", response_model=None)
async def get_document(
    document_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Get a specific document."""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.user_id == current_user_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Update access count
    document.access_count += 1  # type: ignore[assignment]
    await db.commit()
    
    return document  # type: ignore[no-any-return]


@router.patch("/{document_id}", response_model=None)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Update a document."""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.user_id == current_user_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Update fields
    update_data = document_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    await db.commit()
    await db.refresh(document)
    
    logger.info(f"Document updated: {document_id}")
    
    return document  # type: ignore[no-any-return]


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a document."""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.user_id == current_user_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    document.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    document.status = DocumentStatus.ARCHIVED  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Document deleted: {document_id}")
    
    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/index")
async def index_document(
    document_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Trigger document indexing."""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.user_id == current_user_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # This would trigger an async task to index the document
    document.status = DocumentStatus.INDEXED  # type: ignore[assignment]
    document.indexed_at = datetime.utcnow()  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Document indexed: {document_id}")
    
    return {"message": "Document indexing triggered"}
