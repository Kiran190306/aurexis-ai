from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.conversation import Conversation, Message, ConversationStatus
from pydantic import BaseModel


class ConversationRepository(BaseRepository[Conversation, BaseModel, BaseModel]):
    """Repository for Conversation model operations."""

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        load_messages: bool = False,
    ) -> List[Conversation]:
        """Get conversations for a user."""
        query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Conversation.status == status)
        
        if load_messages:
            query = query.options(selectinload(Conversation.messages))
        
        query = query.offset(skip).limit(limit).order_by(Conversation.updated_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_uuid(
        self,
        db: AsyncSession,
        uuid: str,
        user_id: int,
    ) -> Optional[Conversation]:
        """Get conversation by UUID."""
        query = select(Conversation).where(
            and_(
                Conversation.uuid == uuid,
                Conversation.user_id == user_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_share_token(
        self,
        db: AsyncSession,
        share_token: str,
    ) -> Optional[Conversation]:
        """Get conversation by share token."""
        query = select(Conversation).where(
            and_(
                Conversation.share_token == share_token,
                Conversation.is_shared == True,
                Conversation.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_with_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> Optional[Conversation]:
        """Get conversation with messages loaded."""
        query = select(Conversation).options(
            selectinload(Conversation.messages)
        ).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def update_stats(
        self,
        db: AsyncSession,
        conversation_id: int,
        message_count: Optional[int] = None,
        token_count: Optional[int] = None,
    ) -> Optional[Conversation]:
        """Update conversation statistics."""
        from datetime import datetime
        
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if conversation:
            if message_count is not None:
                conversation.message_count = message_count  # type: ignore[assignment]
            if token_count is not None:
                conversation.token_count = token_count  # type: ignore[assignment]
            conversation.last_message_at = datetime.utcnow()  # type: ignore[assignment]
            
            await db.commit()
            await db.refresh(conversation)
        
        return conversation

    async def archive(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> bool:
        """Archive a conversation."""
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if conversation:
            conversation.status = ConversationStatus.ARCHIVED
            await db.commit()
            return True
        
        return False

    async def pin(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> bool:
        """Pin a conversation."""
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if conversation:
            conversation.status = ConversationStatus.PINNED
            await db.commit()
            return True
        
        return False


class MessageRepository(BaseRepository[Message, BaseModel, BaseModel]):
    """Repository for Message model operations."""

    async def get_by_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
    ) -> List[Message]:
        """Get messages for a conversation."""
        query = select(Message).where(
            and_(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False
            )
        )
        
        if role:
            query = query.where(Message.role == role)
        
        query = query.offset(skip).limit(limit).order_by(Message.created_at.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_uuid(
        self,
        db: AsyncSession,
        uuid: str,
        user_id: int,
    ) -> Optional[Message]:
        """Get message by UUID."""
        query = select(Message).where(
            and_(
                Message.uuid == uuid,
                Message.user_id == user_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_thread(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
        depth: int = 10,
    ) -> List[Message]:
        """Get message thread (replies)."""
        # This is a simplified implementation
        # In production, you might want to use recursive CTEs
        query = select(Message).where(
            and_(
                Message.parent_message_id == message_id,
                Message.user_id == user_id,
                Message.is_deleted == False
            )
        ).limit(depth).order_by(Message.created_at.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_token_usage(
        self,
        db: AsyncSession,
        message_id: int,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> Optional[Message]:
        """Update token usage for a message."""
        query = select(Message).where(Message.id == message_id)
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if message:
            message.prompt_tokens = prompt_tokens  # type: ignore[assignment]
            message.completion_tokens = completion_tokens  # type: ignore[assignment]
            message.total_tokens = prompt_tokens + completion_tokens  # type: ignore[assignment]
            
            await db.commit()
            await db.refresh(message)
        
        return message  # type: ignore[no-any-return]

    async def soft_delete(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
    ) -> bool:
        """Soft delete a message."""
        query = select(Message).where(
            and_(
                Message.id == message_id,
                Message.user_id == user_id
            )
        )
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if message:
            message.is_deleted = True  # type: ignore[assignment]
            await db.commit()
            return True
        
        return False


class ConversationShareRepository(BaseRepository[Conversation, BaseModel, BaseModel]):
    """Repository for ConversationShare model operations."""
    
    async def get_by_token(
        self,
        db: AsyncSession,
        share_token: str,
    ) -> Optional[Conversation]:
        """Get shared conversation by token."""
        from app.models.conversation import ConversationShare
        from datetime import datetime
        
        query = select(ConversationShare).where(
            and_(
                ConversationShare.share_token == share_token,
                ConversationShare.is_active == True,
                or_(
                    ConversationShare.expires_at.is_(None),
                    ConversationShare.expires_at > datetime.utcnow()
                )
            )
        )
        result = await db.execute(query)
        share = result.scalar_one_or_none()
        
        if share:
            # Increment access count
            share.access_count += 1  # type: ignore[assignment]
            await db.commit()
            
            return await self.get(db, int(share.conversation_id))
        
        return None

    async def increment_access(
        self,
        db: AsyncSession,
        share_token: str,
    ) -> bool:
        """Increment access count for a shared conversation."""
        from app.models.conversation import ConversationShare
        
        query = select(ConversationShare).where(
            ConversationShare.share_token == share_token
        )
        result = await db.execute(query)
        share = result.scalar_one_or_none()
        
        if share:
            share.access_count += 1  # type: ignore[assignment]
            await db.commit()
            return True
        
        return False
