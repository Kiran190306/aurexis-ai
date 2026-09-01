from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class ConversationStatus(PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PINNED = "pinned"


class MessageType(PyEnum):
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"


class MessageRole(PyEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    
    # AI Configuration
    model = Column(String(50), default="gpt-4-turbo-preview")
    temperature = Column(Integer, default=70)  # 0-100
    max_tokens = Column(Integer, default=4096)
    system_prompt = Column(Text, nullable=True)
    
    # Metadata
    tags = Column(JSON)  # Array of tags
    metadata_json = Column(JSON, nullable=True)  # Additional metadata
    is_shared = Column(Boolean, default=False)
    share_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Statistics
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType), default=MessageType.TEXT)
    
    # Code-specific
    code_language = Column(String(50), nullable=True)
    code_content = Column(Text, nullable=True)
    
    # Image-specific
    image_url = Column(String(500), nullable=True)
    image_alt = Column(String(255), nullable=True)
    
    # File-specific
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    
    # Tool-specific
    tool_calls = Column(JSON, nullable=True)  # Array of tool calls
    tool_response = Column(JSON, nullable=True)  # Tool response data
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Additional metadata
    parent_message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    
    # Token usage
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")
    file = relationship("File", foreign_keys=[file_id])
    parent_message = relationship("Message", remote_side=[id], backref="replies")


class ConversationShare(Base):
    __tablename__ = "conversation_shares"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    
    # Share Info
    share_token = Column(String(255), unique=True, index=True, nullable=False)
    shared_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Access Control
    access_count = Column(Integer, default=0)
    max_accesses = Column(Integer, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password Protection
    password_hash = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
