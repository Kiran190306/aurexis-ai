from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.repositories.conversation import ConversationRepository, MessageRepository
from app.models.conversation import Conversation, Message, ConversationStatus
from app.core.security import get_password_hash
from pydantic import BaseModel


class ConversationService:
    """Service for conversation operations."""

    def __init__(self) -> None:
        self.conversation_repo = ConversationRepository(Conversation)
        self.message_repo = MessageRepository(Message)

    async def create_conversation(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        temperature: int = 70,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Conversation:
        """Create a new conversation."""
        conversation_data = {
            "user_id": user_id,
            "title": title,
            "description": description,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_prompt": system_prompt,
            "tags": tags or [],
            "status": ConversationStatus.active,
        }
        
        conversation = await self.conversation_repo.create(db, BaseModel(**conversation_data))
        
        logger.info(f"Conversation created: {conversation.id}")
        return conversation

    async def get_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        load_messages: bool = False,
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        if load_messages:
            return await self.conversation_repo.get_with_messages(db, conversation_id, user_id)
        return await self.conversation_repo.get(db, conversation_id)

    async def list_conversations(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> Any:
        """List conversations for a user."""
        return await self.conversation_repo.get_by_user(
            db, user_id, skip=skip, limit=limit, status=status
        )

    async def update_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        **updates: Any,
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = await self.conversation_repo.get(db, conversation_id)
        if not conversation or conversation.user_id != user_id:
            return None
        
        return await self.conversation_repo.update(db, conversation, BaseModel(**updates))

    async def delete_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> Any:
        """Delete a conversation."""
        conversation = await self.conversation_repo.get(db, conversation_id)
        if not conversation or conversation.user_id != user_id:
            return False
        
        return await self.conversation_repo.delete(db, conversation_id)

    async def archive_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> Any:
        """Archive a conversation."""
        return await self.conversation_repo.archive(db, conversation_id, user_id)

    async def pin_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> Any:
        """Pin a conversation."""
        return await self.conversation_repo.pin(db, conversation_id, user_id)

    async def share_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        password: Optional[str] = None,
        max_accesses: Optional[int] = None,
    ) -> Optional[str]:
        """Share a conversation and return share token."""
        import secrets
        from datetime import datetime, timedelta
        
        conversation = await self.conversation_repo.get(db, conversation_id)
        if not conversation or conversation.user_id != user_id:
            return None
        
        # Generate share token
        share_token = secrets.token_urlsafe(32)
        
        # Update conversation
        conversation.is_shared = True  # type: ignore[assignment]
        conversation.share_token = share_token  # type: ignore[assignment]
        
        # Create share record
        from app.models.conversation import ConversationShare
        share = ConversationShare(
            conversation_id=conversation_id,
            share_token=share_token,
            shared_by=user_id,
            password_hash=get_password_hash(password) if password else None,
            max_accesses=max_accesses,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db.add(share)
        
        await db.commit()
        
        logger.info(f"Conversation shared: {conversation_id}")
        return share_token

    async def get_shared_conversation(
        self,
        db: AsyncSession,
        share_token: str,
        password: Optional[str] = None,
    ) -> Optional[Conversation]:
        """Get a shared conversation by token."""
        from app.core.security import verify_password
        
        conversation = await self.conversation_repo.get_by_share_token(db, share_token)
        if not conversation:
            return None
        
        # Check password if required
        if password:
            from app.models.conversation import ConversationShare
            from sqlalchemy import select
            
            query = select(ConversationShare).where(
                ConversationShare.share_token == share_token
            )
            result = await db.execute(query)
            share = result.scalar_one_or_none()
            
            if share and share.password_hash:
                if not verify_password(password, str(share.password_hash)):
                    return None
        
        return conversation


class MessageService:
    """Service for message operations."""

    def __init__(self) -> None:
        self.message_repo = MessageRepository(Message)

    async def create_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        role: str,
        content: str,
        message_type: str = "text",
        **kwargs: Any,
    ) -> Message:
        """Create a new message."""
        message_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "message_type": message_type,
            **kwargs,
        }
        
        message = await self.message_repo.create(db, BaseModel(**message_data))
        
        # Update conversation stats
        from app.repositories.conversation import ConversationRepository
        conv_repo = ConversationRepository(Conversation)
        await conv_repo.update_stats(db, conversation_id)
        
        logger.info(f"Message created: {message.id}")
        return message

    async def get_message(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
    ) -> Optional[Message]:
        """Get a message by ID."""
        return await self.message_repo.get(db, message_id)

    async def list_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
    ) -> Any:
        """List messages for a conversation."""
        return await self.message_repo.get_by_conversation(
            db, conversation_id, skip=skip, limit=limit, role=role
        )

    async def update_message(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
        **updates: Any,
    ) -> Optional[Message]:
        """Update a message."""
        message = await self.message_repo.get(db, message_id)
        if not message or message.user_id != user_id:
            return None
        
        return await self.message_repo.update(db, message, BaseModel(**updates))

    async def delete_message(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int,
    ) -> Any:
        """Delete a message."""
        return await self.message_repo.soft_delete(db, message_id, user_id)

    async def update_token_usage(
        self,
        db: AsyncSession,
        message_id: int,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> Optional[Message]:
        """Update token usage for a message."""
        return await self.message_repo.update_token_usage(
            db, message_id, prompt_tokens, completion_tokens
        )
