from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.conversation import Conversation, ConversationStatus
from pydantic import BaseModel

router = APIRouter()


class ConversationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    model: str = "gpt-4-turbo-preview"
    temperature: int = 70
    max_tokens: int = 4096
    system_prompt: Optional[str] = None
    tags: List[str] = []


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[int] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/", response_model=None)
async def list_conversations(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[Conversation]:
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user_id)
        .where(Conversation.deleted_at.is_(None))
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return list(conversations)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=current_user_id,
        title=conversation_data.title,
        description=conversation_data.description,
        model=conversation_data.model,
        temperature=conversation_data.temperature,
        max_tokens=conversation_data.max_tokens,
        system_prompt=conversation_data.system_prompt,
        tags=conversation_data.tags,
        status=ConversationStatus.ACTIVE,
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    logger.info(f"Conversation created: {conversation.id}")
    
    return conversation


@router.get("/{conversation_id}", response_model=None)
async def get_conversation(
    conversation_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Get a specific conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    return conversation  # type: ignore[no-any-return]


@router.patch("/{conversation_id}", response_model=None)
async def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Update a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    # Update fields
    update_data = conversation_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)
    
    conversation.updated_at = datetime.utcnow()  # type: ignore[assignment]
    
    await db.commit()
    await db.refresh(conversation)
    
    logger.info(f"Conversation updated: {conversation_id}")
    
    return conversation  # type: ignore[no-any-return]


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    conversation.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    conversation.status = ConversationStatus.DELETED  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Conversation deleted: {conversation_id}")
    
    return {"message": "Conversation deleted successfully"}
