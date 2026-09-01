"""
Database models for Computer Use & Automation System.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class ComputerActionType(PyEnum):
    """Types of computer actions."""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_RENAME = "file_rename"
    FILE_MOVE = "file_move"
    FILE_COPY = "file_copy"
    DIRECTORY_BROWSE = "directory_browse"
    DIRECTORY_CREATE = "directory_create"
    DIRECTORY_DELETE = "directory_delete"
    FILE_SEARCH = "file_search"
    FILE_ARCHIVE = "file_archive"
    FILE_EXTRACT = "file_extract"
    TERMINAL_EXECUTE = "terminal_execute"
    TERMINAL_CANCEL = "terminal_cancel"
    TERMINAL_STREAM = "terminal_stream"
    BROWSER_OPEN = "browser_open"
    BROWSER_NAVIGATE = "browser_navigate"
    BROWSER_CLICK = "browser_click"
    BROWSER_FILL = "browser_fill"
    BROWSER_EXTRACT = "browser_extract"
    BROWSER_DOWNLOAD = "browser_download"
    BROWSER_UPLOAD = "browser_upload"
    BROWSER_SCREENSHOT = "browser_screenshot"
    BROWSER_CLOSE = "browser_close"
    DESKTOP_LAUNCH = "desktop_launch"
    DESKTOP_CLOSE = "desktop_close"
    DESKTOP_WINDOW = "desktop_window"
    DESKTOP_CLIPBOARD = "desktop_clipboard"
    DESKTOP_NOTIFICATION = "desktop_notification"
    DESKTOP_CAPTURE = "desktop_capture"


class PermissionStatus(PyEnum):
    """Permission status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ExecutionStatus(PyEnum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PermissionRequest(Base):
    """Permission requests for computer actions."""
    __tablename__ = "computer_permission_requests"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request details
    action_type: Mapped[ComputerActionType] = mapped_column(Enum(ComputerActionType), nullable=False)
    target_path = Column(String(500), nullable=True)
    command = Column(Text, nullable=True)
    url = Column(String(1000), nullable=True)
    description = Column(Text, nullable=False)
    risk_level = Column(String(20), default="medium")
    
    # Response details
    status: Mapped[PermissionStatus] = mapped_column(Enum(PermissionStatus), default=PermissionStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="permission_requests")
    approver = relationship("User", foreign_keys=[approved_by])


class ComputerActionExecution(Base):
    """Computer action execution records."""
    __tablename__ = "computer_action_executions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_request_id = Column(Integer, ForeignKey("computer_permission_requests.id", ondelete="SET NULL"), nullable=True)
    
    # Execution details
    action_type: Mapped[ComputerActionType] = mapped_column(Enum(ComputerActionType), nullable=False)
    action_id = Column(String(100), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    success = Column(Boolean, nullable=True)
    
    # Results
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="computer_action_executions")
    permission_request = relationship("PermissionRequest")


class WorkflowDefinition(Base):
    """Workflow definitions for multi-step automation."""
    __tablename__ = "computer_workflow_definitions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Workflow details
    workflow_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Workflow configuration
    steps_json = Column(JSON, nullable=False)  # List of workflow steps
    parallel = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=True)
    timeout = Column(Integer, default=600)  # seconds
    
    # Metadata
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="workflow_definitions")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowExecution(Base):
    """Workflow execution instances."""
    __tablename__ = "computer_workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey("computer_workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Execution details
    execution_id = Column(String(100), unique=True, nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    current_step = Column(String(100), nullable=True)
    
    # Step tracking
    completed_steps_json = Column(JSON, nullable=True)  # List of completed step IDs
    failed_steps_json = Column(JSON, nullable=True)  # List of failed step IDs
    
    # Results
    results_json = Column(JSON, nullable=True)  # Step results
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="workflow_executions")
    workflow = relationship("WorkflowDefinition", back_populates="executions")


class ComputerUseSettings(Base):
    """User computer use settings."""
    __tablename__ = "computer_use_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Sandbox settings
    sandboxed = Column(Boolean, default=True)
    allowed_paths = Column(JSON, nullable=True)  # List of allowed paths
    max_file_size = Column(Integer, default=104857600)  # 100MB
    
    # Permission settings
    auto_approve_low_risk = Column(Boolean, default=False)
    permission_duration = Column(Integer, default=3600)  # 1 hour
    remember_approvals = Column(Boolean, default=True)
    
    # Terminal settings
    command_timeout = Column(Integer, default=300)  # 5 minutes
    default_working_directory = Column(String(500), nullable=True)
    
    # Browser settings
    browser_type = Column(String(20), default="chromium")
    headless = Column(Boolean, default=True)
    browser_timeout = Column(Integer, default=60)
    
    # Audit settings
    audit_log_enabled = Column(Boolean, default=True)
    log_retention_days = Column(Integer, default=30)
    
    # Notifications
    notify_on_action = Column(Boolean, default=True)
    notify_on_permission = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="computer_use_settings")
