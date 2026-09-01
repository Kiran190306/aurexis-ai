from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class ToolType(PyEnum):
    BUILT_IN = "built_in"
    CUSTOM = "custom"
    PLUGIN = "plugin"


class ToolStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    version = Column(String(20), default="1.0.0")
    
    # Type & Status
    tool_type: Mapped[ToolType] = mapped_column(Enum(ToolType), default=ToolType.CUSTOM)
    status: Mapped[ToolStatus] = mapped_column(Enum(ToolStatus), default=ToolStatus.ACTIVE)
    
    # Configuration
    config_schema = Column(JSON)  # JSON Schema for tool configuration
    config = Column(JSON)  # Default configuration
    parameters = Column(JSON)  # Tool parameters definition
    
    # Execution
    execution_type = Column(String(50), default="http")  # http, function, script
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), default="POST")
    headers = Column(JSON, nullable=True)
    authentication = Column(JSON, nullable=True)
    
    # Code-based tools
    code = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)  # python, javascript, etc.
    
    # Plugin integration
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="SET NULL"), nullable=True)
    
    # Permissions
    required_permissions = Column(JSON)  # Array of required permissions
    sandbox_enabled = Column(Boolean, default=True)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=10)
    rate_limit_per_hour = Column(Integer, default=100)
    
    # Statistics
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    avg_execution_time = Column(Integer, default=0)  # milliseconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="tools")
    plugin = relationship("Plugin", back_populates="tools")
    executions = relationship("ToolExecution", back_populates="tool", cascade="all, delete-orphan")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    
    # Execution
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    
    # Performance
    execution_time = Column(Integer, nullable=True)  # milliseconds
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tool = relationship("Tool", back_populates="executions")
