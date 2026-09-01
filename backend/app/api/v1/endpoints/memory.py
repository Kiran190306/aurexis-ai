from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.memory import Memory, MemoryStatus
from pydantic import BaseModel

router = APIRouter()


class MemoryCreate(BaseModel):
    content: str
    summary: Optional[str] = None
    memory_type: str = "episodic"
    embedding: Optional[list] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    tags: Optional[List[str]] = None
    entities: Optional[dict] = None
    metadata: Optional[dict] = None
    importance_score: float = 0.5
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    importance_score: Optional[float] = None
    is_pinned: Optional[bool] = None


@router.get("/", response_model=None)
async def list_memories(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[Memory]:
    """List all memories for the current user."""
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == current_user_id)
        .where(Memory.deleted_at.is_(None))
        .order_by(Memory.created_at.desc())
    )
    memories = result.scalars().all()
    return list(memories)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_memory(
    memory_data: MemoryCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Memory:
    """Create a new memory."""
    memory = Memory(
        user_id=current_user_id,
        content=memory_data.content,
        summary=memory_data.summary,
        memory_type=memory_data.memory_type,
        embedding=memory_data.embedding,
        embedding_model=memory_data.embedding_model,
        tags=memory_data.tags,
        entities=memory_data.entities,
        metadata=memory_data.metadata,
        importance_score=memory_data.importance_score,
        conversation_id=memory_data.conversation_id,
        message_id=memory_data.message_id,
        status=MemoryStatus.ACTIVE,
    )
    
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    
    logger.info(f"Memory created: {memory.id}")
    
    return memory


@router.get("/{memory_id}", response_model=None)
async def get_memory(
    memory_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Memory:
    """Get a specific memory."""
    result = await db.execute(
        select(Memory)
        .where(Memory.id == memory_id)
        .where(Memory.user_id == current_user_id)
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )
    
    # Update access count and last accessed
    memory.access_count += 1  # type: ignore[assignment]
    memory.last_accessed = datetime.utcnow()  # type: ignore[assignment]
    await db.commit()
    
    return memory  # type: ignore[no-any-return]


@router.patch("/{memory_id}", response_model=None)
async def update_memory(
    memory_id: int,
    memory_data: MemoryUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Memory:
    """Update a memory."""
    result = await db.execute(
        select(Memory)
        .where(Memory.id == memory_id)
        .where(Memory.user_id == current_user_id)
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )
    
    # Update fields
    update_data = memory_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(memory, field, value)
    
    await db.commit()
    await db.refresh(memory)
    
    logger.info(f"Memory updated: {memory_id}")
    
    return memory  # type: ignore[no-any-return]


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a memory."""
    result = await db.execute(
        select(Memory)
        .where(Memory.id == memory_id)
        .where(Memory.user_id == current_user_id)
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )
    
    memory.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    memory.status = MemoryStatus.DELETED  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Memory deleted: {memory_id}")
    
    return {"message": "Memory deleted successfully"}


@router.get("/search/{query}", response_model=None)
async def search_memories(
    query: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[Memory]:
    """Search memories by content."""
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == current_user_id)
        .where(Memory.content.ilike(f"%{query}%"))
        .where(Memory.deleted_at.is_(None))
        .order_by(Memory.importance_score.desc())
    )
    memories = result.scalars().all()
    return list(memories)
