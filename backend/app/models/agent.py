from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class AgentType(PyEnum):
    GENERAL = "general"
    SPECIALIST = "specialist"
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"


class AgentStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Type & Status
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), default=AgentType.GENERAL)
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), default=AgentStatus.ACTIVE)
    
    # Capabilities
    capabilities = Column(JSON)  # Array of capabilities
    specializations = Column(JSON)  # Array of specializations
    
    # Configuration
    system_prompt = Column(Text, nullable=False)
    model = Column(String(50), default="gpt-4o-mini")
    temperature = Column(Integer, default=70)
    max_tokens = Column(Integer, default=4096)
    
    # Tools & Plugins
    tool_ids = Column(JSON)  # Array of tool IDs
    plugin_ids = Column(JSON)  # Array of plugin IDs
    
    # Behavior
    personality = Column(JSON)  # Personality traits
    behavior_rules = Column(JSON)  # Behavior rules
    constraints = Column(JSON)  # Constraints and limitations
    
    # Memory
    memory_enabled = Column(Boolean, default=True)
    memory_type = Column(String(50), default="episodic")
    
    # Collaboration
    parent_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    
    # Statistics
    task_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    avg_response_time = Column(Integer, default=0)  # milliseconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="agents")
    parent_agent = relationship("Agent", remote_side=[id], backref="child_agents")
    tasks = relationship("AgentTask", back_populates="agent", cascade="all, delete-orphan")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    
    # Task Info
    task_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    input_data = Column(JSON, nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    
    # Execution
    output_data = Column(JSON, nullable=True)
    result_summary = Column(Text, nullable=True)
    
    # Performance
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time = Column(Integer, nullable=True)  # milliseconds
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Dependencies
    depends_on = Column(JSON)  # Array of task IDs
    subtasks = Column(JSON)  # Array of subtask IDs
    
    # Priority
    priority = Column(Integer, default=5)  # 1-10
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="tasks")


class AgentCollaboration(Base):
    __tablename__ = "agent_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    
    # Participants
    agent_ids = Column(JSON, nullable=False)  # Array of agent IDs
    orchestrator_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    
    # Collaboration Type
    collaboration_type = Column(String(50), nullable=False)  # sequential, parallel, hierarchical
    
    # Workflow
    workflow = Column(JSON)  # Collaboration workflow
    communication_protocol = Column(JSON)  # Communication rules
    
    # Status
    status = Column(String(20), default="active")
    
    # Results
    final_output = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
