from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class MemoryType(PyEnum):
    EPISODIC = "episodic"  # Personal experiences
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # Skills and how-to
    DECLARATIVE = "declarative"  # Facts and events
    WORKING = "working"  # Short-term working memory


class MemoryStatus(PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    CONSOLIDATED = "consolidated"


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    memory_type: Mapped[MemoryType] = mapped_column(Enum(MemoryType), default=MemoryType.EPISODIC)
    
    # Vector Embedding
    embedding = Column(JSON)  # Vector embedding
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    
    # Metadata
    tags = Column(JSON)  # Array of tags
    entities = Column(JSON)  # Extracted entities
    metadata_json = Column(JSON, nullable=True)  # Additional metadata
    
    # Importance & Relevance
    importance_score = Column(Float, default=0.5)  # 0-1
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Context
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    
    # Status
    status: Mapped[MemoryStatus] = mapped_column(Enum(MemoryStatus), default=MemoryStatus.ACTIVE)
    is_pinned = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="memories")


class MemoryAssociation(Base):
    __tablename__ = "memory_associations"

    id = Column(Integer, primary_key=True, index=True)
    memory_id_1 = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    memory_id_2 = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    
    # Association Type
    association_type = Column(String(50), nullable=False)  # related, causal, temporal, etc.
    strength = Column(Float, default=0.5)  # 0-1
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MemoryConsolidation(Base):
    __tablename__ = "memory_consolidations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Consolidation Info
    source_memory_ids = Column(JSON, nullable=False)  # Array of memory IDs
    consolidated_memory_id = Column(Integer, ForeignKey("memories.id", ondelete="SET NULL"), nullable=True)
    
    # Process
    consolidation_type = Column(String(50), nullable=False)  # merge, summarize, abstract
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Results
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class WorkingMemory(Base):
    __tablename__ = "working_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    
    # Context
    context_data = Column(JSON, nullable=False)  # Current context
    context_window = Column(JSON)  # Context window with recent messages
    
    # State
    current_task = Column(Text, nullable=True)
    current_goal = Column(Text, nullable=True)
    intermediate_steps = Column(JSON)  # Array of intermediate steps
    
    # Token Management
    token_count = Column(Integer, default=0)
    max_tokens = Column(Integer, default=4096)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
