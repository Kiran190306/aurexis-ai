from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class PromptType(PyEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FEW_SHOT = "few_shot"


class PromptStatus(PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    prompt_type: Mapped[PromptType] = mapped_column(Enum(PromptType), default=PromptType.USER)
    status: Mapped[PromptStatus] = mapped_column(Enum(PromptStatus), default=PromptStatus.ACTIVE)
    
    # Content
    content = Column(Text, nullable=False)
    variables = Column(JSON)  # Array of variable definitions
    
    # Configuration
    model = Column(String(50), nullable=True)
    temperature = Column(Integer, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    
    # Versioning
    version = Column(String(20), default="1.0.0")
    parent_prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True)
    
    # Categories
    category = Column(String(50), nullable=True)
    tags = Column(JSON)  # Array of tags
    
    # Statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)  # 0-100
    
    # Sharing
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="prompts")
    parent_prompt = relationship("Prompt", remote_side=[id], backref="child_prompts")
    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    
    # Version Info
    version = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(JSON)
    
    # Change Log
    change_description = Column(Text, nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prompt = relationship("Prompt", back_populates="versions")


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    
    # Content
    template = Column(Text, nullable=False)
    variables = Column(JSON)  # Array of variable definitions
    
    # Configuration
    default_model = Column(String(50), nullable=True)
    default_temperature = Column(Integer, nullable=True)
    default_max_tokens = Column(Integer, nullable=True)
    
    # Metadata
    tags = Column(JSON)
    examples = Column(JSON)  # Array of usage examples
    
    # Statistics
    usage_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
