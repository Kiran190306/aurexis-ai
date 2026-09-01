from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional, Any

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.conversation import Conversation, Message
from pydantic import BaseModel

router = APIRouter()


class MessageCreate(BaseModel):
    conversation_id: int
    role: str
    content: str
    message_type: str = "text"
    code_language: Optional[str] = None
    code_content: Optional[str] = None
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    file_id: Optional[int] = None
    tool_calls: Optional[List[dict]] = None
    tool_response: Optional[dict] = None
    metadata: Optional[dict] = None
    parent_message_id: Optional[int] = None


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_edited: Optional[bool] = None
    is_deleted: Optional[bool] = None


@router.get("/conversation/{conversation_id}", response_model=None)
async def list_messages(
    conversation_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[Message]:
    """List all messages in a conversation."""
    # Verify conversation belongs to user
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
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.is_deleted == False)
        .order_by(Message.created_at.asc())
    )
    messages: List[Message] = list(result.scalars().all())
    
    return messages


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_message(
    message_data: MessageCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Message:
    """Create a new message."""
    # Verify conversation belongs to user
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == message_data.conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    message = Message(
        conversation_id=message_data.conversation_id,
        user_id=current_user_id,
        role=message_data.role,
        content=message_data.content,
        message_type=message_data.message_type,
        code_language=message_data.code_language,
        code_content=message_data.code_content,
        image_url=message_data.image_url,
        image_alt=message_data.image_alt,
        file_id=message_data.file_id,
        tool_calls=message_data.tool_calls,
        tool_response=message_data.tool_response,
        metadata=message_data.metadata,
        parent_message_id=message_data.parent_message_id,
    )
    
    db.add(message)
    
    # Update conversation stats
    conversation.message_count += 1  # type: ignore[assignment]
    conversation.last_message_at = message.created_at  # type: ignore[assignment]
    
    await db.commit()
    await db.refresh(message)
    
    logger.info(f"Message created: {message.id}")
    
    return message


@router.get("/{message_id}", response_model=None)
async def get_message(
    message_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Message:
    """Get a specific message."""
    result = await db.execute(
        select(Message)
        .where(Message.id == message_id)
        .where(Message.user_id == current_user_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    return message  # type: ignore[no-any-return]


@router.patch("/{message_id}", response_model=None)
async def update_message(
    message_id: int,
    message_data: MessageUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Message:
    """Update a message."""
    result = await db.execute(
        select(Message)
        .where(Message.id == message_id)
        .where(Message.user_id == current_user_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Update fields
    update_data = message_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(message, field, value)
    
    await db.commit()
    await db.refresh(message)
    
    logger.info(f"Message updated: {message_id}")
    
    return message  # type: ignore[no-any-return]


@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a message."""
    result = await db.execute(
        select(Message)
        .where(Message.id == message_id)
        .where(Message.user_id == current_user_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    message.is_deleted = True  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Message deleted: {message_id}")
    
    return {"message": "Message deleted successfully"}
