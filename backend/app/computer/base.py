"""
Base classes and data models for Computer Use & Automation System.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ComputerActionType(str, Enum):
    """Types of computer actions."""
    UNKNOWN = "unknown"
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


class PermissionStatus(str, Enum):
    """Permission status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RiskLevel(str, Enum):
    """Risk level for computer actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PermissionRequest(BaseModel):
    """Request for permission to perform an action."""
    action_type: ComputerActionType = Field(..., description="Type of action")
    target_path: Optional[str] = Field(default=None, description="Target file/directory path")
    command: Optional[str] = Field(default=None, description="Command to execute")
    url: Optional[str] = Field(default=None, description="URL for browser actions")
    description: str = Field(..., description="Human-readable description")
    risk_level: str = Field(default="medium", description="Risk level: low, medium, high")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PermissionResponse(BaseModel):
    """Response to permission request."""
    request_id: str = Field(..., description="Unique request ID")
    status: PermissionStatus = Field(..., description="Permission status")
    approved_by: Optional[str] = Field(default=None, description="User who approved")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp")
    reason: Optional[str] = Field(default=None, description="Reason for denial")


class ExecutionResult(BaseModel):
    """Result of computer action execution."""
    action_id: str = Field(..., description="Action execution ID")
    action_type: ComputerActionType = Field(..., description="Type of action")
    status: ExecutionStatus = Field(..., description="Execution status")
    success: bool = Field(..., description="Whether execution succeeded")
    output: Optional[str] = Field(default=None, description="Command output")
    error: Optional[str] = Field(default=None, description="Error message")
    duration_seconds: float = Field(..., description="Execution duration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class FileOperation(BaseModel):
    """File system operation."""
    operation: str = Field(..., description="Operation type")
    source_path: Optional[str] = Field(default=None, description="Source path")
    target_path: Optional[str] = Field(default=None, description="Target path")
    content: Optional[str] = Field(default=None, description="File content")
    overwrite: bool = Field(default=False, description="Overwrite existing files")
    recursive: bool = Field(default=False, description="Recursive operation")


class TerminalCommand(BaseModel):
    """Terminal command execution."""
    command: str = Field(..., description="Command to execute")
    working_directory: Optional[str] = Field(default=None, description="Working directory")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    timeout: int = Field(default=300, description="Timeout in seconds")
    stream_output: bool = Field(default=True, description="Stream output")


class BrowserAction(BaseModel):
    """Browser automation action."""
    action: str = Field(..., description="Action type")
    url: Optional[str] = Field(default=None, description="URL")
    selector: Optional[str] = Field(default=None, description="CSS selector")
    value: Optional[str] = Field(default=None, description="Value to fill")
    screenshot: bool = Field(default=False, description="Take screenshot")
    wait_for: Optional[str] = Field(default=None, description="Wait for selector")


class DesktopAction(BaseModel):
    """Desktop automation action."""
    action: str = Field(..., description="Action type")
    application: Optional[str] = Field(default=None, description="Application name/path")
    window_title: Optional[str] = Field(default=None, description="Window title")
    clipboard_content: Optional[str] = Field(default=None, description="Clipboard content")
    screenshot: bool = Field(default=False, description="Take screenshot")


class WorkflowStep(BaseModel):
    """Workflow execution step."""
    step_id: str = Field(..., description="Step ID")
    action_type: ComputerActionType = Field(..., description="Action type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    depends_on: List[str] = Field(default_factory=list, description="Step dependencies")
    retry_policy: Optional[Dict[str, Any]] = Field(default=None, description="Retry policy")
    rollback_action: Optional[Dict[str, Any]] = Field(default=None, description="Rollback action")


class WorkflowDefinition(BaseModel):
    """Workflow definition."""
    workflow_id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStep] = Field(..., description="Workflow steps")
    parallel: bool = Field(default=False, description="Execute steps in parallel")
    requires_approval: bool = Field(default=True, description="Requires user approval")
    timeout: int = Field(default=600, description="Total timeout in seconds")


class WorkflowExecution(BaseModel):
    """Workflow execution instance."""
    execution_id: str = Field(..., description="Execution ID")
    workflow_id: str = Field(..., description="Workflow ID")
    status: ExecutionStatus = Field(..., description="Execution status")
    current_step: Optional[str] = Field(default=None, description="Current step ID")
    completed_steps: List[str] = Field(default_factory=list, description="Completed steps")
    failed_steps: List[str] = Field(default_factory=list, description="Failed steps")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    results: Dict[str, Any] = Field(default_factory=dict, description="Step results")
