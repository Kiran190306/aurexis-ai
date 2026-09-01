"""
Pydantic schemas for Computer Use & Automation System API.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ComputerActionType(str, Enum):
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


class PermissionStatus(str, Enum):
    """Permission status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# File System Schemas
class BrowseDirectoryRequest(BaseModel):
    path: str = Field(..., description="Directory path to browse")
    depth: int = Field(default=1, description="Browsing depth")


class ReadFileRequest(BaseModel):
    path: str = Field(..., description="File path to read")


class WriteFileRequest(BaseModel):
    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="File content")
    overwrite: bool = Field(default=False, description="Overwrite existing file")


class DeleteFileRequest(BaseModel):
    path: str = Field(..., description="File/directory path to delete")


class RenameFileRequest(BaseModel):
    source: str = Field(..., description="Source path")
    target: str = Field(..., description="Target path")


class MoveFileRequest(BaseModel):
    source: str = Field(..., description="Source path")
    target: str = Field(..., description="Target path")


class CopyFileRequest(BaseModel):
    source: str = Field(..., description="Source path")
    target: str = Field(..., description="Target path")


class SearchFilesRequest(BaseModel):
    path: str = Field(..., description="Search path")
    pattern: str = Field(..., description="File pattern to search")


class ArchiveRequest(BaseModel):
    source: str = Field(..., description="Source path")
    target: str = Field(..., description="Target archive path")


class ExtractRequest(BaseModel):
    source: str = Field(..., description="Archive path")
    target: str = Field(..., description="Extraction path")


# Terminal Schemas
class ExecuteCommandRequest(BaseModel):
    command: str = Field(..., description="Command to execute")
    working_directory: Optional[str] = Field(default=None, description="Working directory")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    timeout: int = Field(default=300, description="Timeout in seconds")
    stream_output: bool = Field(default=True, description="Stream output")


class CancelCommandRequest(BaseModel):
    action_id: str = Field(..., description="Action ID to cancel")


class SetWorkingDirectoryRequest(BaseModel):
    path: str = Field(..., description="Working directory path")


class SetEnvironmentVariableRequest(BaseModel):
    name: str = Field(..., description="Variable name")
    value: str = Field(..., description="Variable value")


# Browser Schemas
class OpenBrowserRequest(BaseModel):
    url: Optional[str] = Field(default=None, description="URL to navigate to")


class NavigateRequest(BaseModel):
    page_id: str = Field(..., description="Page ID")
    url: str = Field(..., description="URL to navigate to")


class ClickElementRequest(BaseModel):
    page_id: str = Field(..., description="Page ID")
    selector: str = Field(..., description="CSS selector")


class FillFormRequest(BaseModel):
    page_id: str = Field(..., description="Page ID")
    selector: str = Field(..., description="CSS selector")
    value: str = Field(..., description="Value to fill")


class ExtractContentRequest(BaseModel):
    page_id: str = Field(..., description="Page ID")
    selector: Optional[str] = Field(default=None, description="CSS selector")


class DownloadFileRequest(BaseModel):
    page_id: str = Field(..., description="Page ID")
    url: str = Field(..., description="URL to download from")


class UploadFileRequest(BaseModel):
    page_id: str = Field(..., description="Page ID")
    selector: str = Field(..., description="CSS selector")
    file_path: str = Field(..., description="File path to upload")


class TakeScreenshotRequest(BaseModel):
    page_id: str = Field(..., description="Page ID")


class CloseBrowserRequest(BaseModel):
    page_id: Optional[str] = Field(default=None, description="Page ID to close (None for all)")


# Desktop Schemas
class LaunchApplicationRequest(BaseModel):
    application: str = Field(..., description="Application name or path")


class CloseApplicationRequest(BaseModel):
    application: str = Field(..., description="Application name")


class ManageWindowRequest(BaseModel):
    action: str = Field(..., description="Window action (minimize, maximize, restore)")
    window_title: Optional[str] = Field(default=None, description="Window title")


class SetClipboardRequest(BaseModel):
    content: str = Field(..., description="Clipboard content")


class SendNotificationRequest(BaseModel):
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")


# Workflow Schemas
class WorkflowStepSchema(BaseModel):
    step_id: str = Field(..., description="Step ID")
    action_type: ComputerActionType = Field(..., description="Action type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    depends_on: List[str] = Field(default_factory=list, description="Step dependencies")
    retry_policy: Optional[Dict[str, Any]] = Field(default=None, description="Retry policy")
    rollback_action: Optional[Dict[str, Any]] = Field(default=None, description="Rollback action")


class CreateWorkflowRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStepSchema] = Field(..., description="Workflow steps")
    parallel: bool = Field(default=False, description="Execute steps in parallel")
    requires_approval: bool = Field(default=True, description="Requires user approval")
    timeout: int = Field(default=600, description="Total timeout in seconds")


class ExecuteWorkflowRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")


class CancelWorkflowRequest(BaseModel):
    execution_id: str = Field(..., description="Execution ID to cancel")


# Permission Schemas
class PermissionRequestSchema(BaseModel):
    action_type: ComputerActionType = Field(..., description="Action type")
    target_path: Optional[str] = Field(default=None, description="Target path")
    command: Optional[str] = Field(default=None, description="Command")
    url: Optional[str] = Field(default=None, description="URL")
    description: str = Field(..., description="Description")
    risk_level: str = Field(default="medium", description="Risk level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class ApprovePermissionRequest(BaseModel):
    request_id: str = Field(..., description="Request ID")
    approve_for_session: bool = Field(default=False, description="Approve for session")


class DenyPermissionRequest(BaseModel):
    request_id: str = Field(..., description="Request ID")
    reason: Optional[str] = Field(default=None, description="Denial reason")


# Response Schemas
class ExecutionResultResponse(BaseModel):
    action_id: str = Field(..., description="Action ID")
    action_type: ComputerActionType = Field(..., description="Action type")
    status: ExecutionStatus = Field(..., description="Execution status")
    success: bool = Field(..., description="Success status")
    output: Optional[str] = Field(default=None, description="Output")
    error: Optional[str] = Field(default=None, description="Error message")
    duration_seconds: float = Field(..., description="Duration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class PermissionResponseSchema(BaseModel):
    request_id: str = Field(..., description="Request ID")
    status: PermissionStatus = Field(..., description="Permission status")
    approved_by: Optional[str] = Field(default=None, description="Approver")
    approved_at: Optional[datetime] = Field(default=None, description="Approval time")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration time")
    reason: Optional[str] = Field(default=None, description="Reason")


class WorkflowExecutionResponse(BaseModel):
    execution_id: str = Field(..., description="Execution ID")
    workflow_id: str = Field(..., description="Workflow ID")
    status: ExecutionStatus = Field(..., description="Execution status")
    current_step: Optional[str] = Field(default=None, description="Current step")
    completed_steps: List[str] = Field(default_factory=list, description="Completed steps")
    failed_steps: List[str] = Field(default_factory=list, description="Failed steps")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    results: Dict[str, Any] = Field(default_factory=dict, description="Results")


class ComputerHistoryResponse(BaseModel):
    id: int = Field(..., description="Record ID")
    uuid: str = Field(..., description="Record UUID")
    action_type: ComputerActionType = Field(..., description="Action type")
    status: ExecutionStatus = Field(..., description="Execution status")
    success: bool = Field(..., description="Success status")
    duration_seconds: Optional[float] = Field(default=None, description="Duration")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")


class WorkflowDefinitionResponse(BaseModel):
    id: int = Field(..., description="Record ID")
    uuid: str = Field(..., description="Record UUID")
    workflow_id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStepSchema] = Field(..., description="Steps")
    parallel: bool = Field(..., description="Parallel execution")
    requires_approval: bool = Field(..., description="Requires approval")
    timeout: int = Field(..., description="Timeout")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation time")
