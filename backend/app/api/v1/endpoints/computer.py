"""
API endpoints for Computer Use & Automation System.
"""
from typing import List, Any, cast
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.computer import (
    ComputerActionExecution,
    PermissionRequest,
    WorkflowDefinition,
    WorkflowExecution
)
from sqlalchemy import select
from app.schemas.computer import (
    # File System
    BrowseDirectoryRequest,
    ReadFileRequest,
    WriteFileRequest,
    DeleteFileRequest,
    RenameFileRequest,
    MoveFileRequest,
    CopyFileRequest,
    SearchFilesRequest,
    ArchiveRequest,
    ExtractRequest,
    # Terminal
    ExecuteCommandRequest,
    CancelCommandRequest,
    SetWorkingDirectoryRequest,
    SetEnvironmentVariableRequest,
    # Browser
    OpenBrowserRequest,
    NavigateRequest,
    ClickElementRequest,
    FillFormRequest,
    ExtractContentRequest,
    DownloadFileRequest,
    UploadFileRequest,
    TakeScreenshotRequest,
    CloseBrowserRequest,
    # Desktop
    LaunchApplicationRequest,
    CloseApplicationRequest,
    ManageWindowRequest,
    SetClipboardRequest,
    SendNotificationRequest,
    # Workflow
    CreateWorkflowRequest,
    ExecuteWorkflowRequest,
    CancelWorkflowRequest,
    # Permission
    ApprovePermissionRequest,
    DenyPermissionRequest,
    # Responses
    ExecutionResultResponse,
    PermissionResponseSchema,
    WorkflowExecutionResponse,
    ComputerHistoryResponse,
    WorkflowDefinitionResponse,
    ExecutionStatus as SchemaExecutionStatus
)
from app.computer.base import (
    WorkflowStep,
    WorkflowDefinition as WorkflowDef,
    ComputerActionType,
    ExecutionStatus
)
from app.core.config import settings


router = APIRouter()

# Lazy-loaded computer agents
_file_system_agent = None
_terminal_agent = None
_browser_agent = None
_desktop_agent = None
_workflow_engine = None
_permission_system = None


def get_file_system_agent():
    global _file_system_agent
    if _file_system_agent is None:
        from app.computer.file_system_agent import FileSystemAgent
        _file_system_agent = FileSystemAgent()
    return _file_system_agent


def get_terminal_agent():
    global _terminal_agent
    if _terminal_agent is None:
        from app.computer.terminal_agent import TerminalAgent
        _terminal_agent = TerminalAgent()
    return _terminal_agent


def get_browser_agent():
    global _browser_agent
    if _browser_agent is None:
        from app.computer.browser_agent import BrowserAgent
        _browser_agent = BrowserAgent()
    return _browser_agent


def get_desktop_agent():
    global _desktop_agent
    if _desktop_agent is None:
        from app.computer.desktop_agent import DesktopAgent
        _desktop_agent = DesktopAgent()
    return _desktop_agent


def get_workflow_engine():
    global _workflow_engine
    if _workflow_engine is None:
        from app.computer.workflow_engine import WorkflowEngine
        _workflow_engine = WorkflowEngine()
    return _workflow_engine


def get_permission_system():
    global _permission_system
    if _permission_system is None:
        from app.computer.permission_system import PermissionSystem
        _permission_system = PermissionSystem()
    return _permission_system


# ============================================================================
# File System Endpoints
# ============================================================================

@router.post("/files/browse", response_model=ExecutionResultResponse)
async def browse_directory(
    request: BrowseDirectoryRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Browse directory contents."""
    result = await get_file_system_agent().browse_directory(
        request.path,
        request.depth,
        current_user_id
    )
    return ExecutionResultResponse(**result.dict())


@router.post("/files/read", response_model=ExecutionResultResponse)
async def read_file(
    request: ReadFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Read file contents."""
    result = await get_file_system_agent().read_file(request.path, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/files/write", response_model=ExecutionResultResponse)
async def write_file(
    request: WriteFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Write content to file."""
    result = await get_file_system_agent().write_file(
        request.path,
        request.content,
        request.overwrite,
        current_user_id
    )
    return ExecutionResultResponse(**result.dict())


@router.post("/files/delete", response_model=ExecutionResultResponse)
async def delete_file(
    request: DeleteFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Delete file or directory."""
    result = await get_file_system_agent().delete_file(request.path, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/files/rename", response_model=ExecutionResultResponse)
async def rename_file(
    request: RenameFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Rename file or directory."""
    result = await get_file_system_agent().rename_file(request.source, request.target, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/files/move", response_model=ExecutionResultResponse)
async def move_file(
    request: MoveFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Move file or directory."""
    result = await get_file_system_agent().move_file(request.source, request.target, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/files/copy", response_model=ExecutionResultResponse)
async def copy_file(
    request: CopyFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Copy file or directory."""
    result = await get_file_system_agent().copy_file(request.source, request.target, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/files/search", response_model=ExecutionResultResponse)
async def search_files(
    request: SearchFilesRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Search for files matching pattern."""
    result = await get_file_system_agent().search_files(request.path, request.pattern, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/files/archive", response_model=ExecutionResultResponse)
async def create_archive(
    request: ArchiveRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Create ZIP archive."""
    result = await get_file_system_agent().create_archive(request.source, request.target, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/files/extract", response_model=ExecutionResultResponse)
async def extract_archive(
    request: ExtractRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Extract ZIP archive."""
    result = await get_file_system_agent().extract_archive(request.source, request.target, current_user_id)
    return ExecutionResultResponse(**result.dict())


# ============================================================================
# Terminal Endpoints
# ============================================================================

@router.post("/terminal/execute", response_model=ExecutionResultResponse)
async def execute_command(
    request: ExecuteCommandRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Execute shell command."""
    result = await get_terminal_agent().execute_command(
        request.command,
        request.working_directory,
        request.environment,
        request.timeout,
        request.stream_output,
        current_user_id
    )
    return ExecutionResultResponse(**result.dict())


@router.post("/terminal/cancel", response_model=ExecutionResultResponse)
async def cancel_command(
    request: CancelCommandRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Cancel running command."""
    result = await get_terminal_agent().cancel_command(request.action_id, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.get("/terminal/working-directory")
async def get_working_directory(current_user_id: int = Depends(get_current_user_id)) -> dict[str, str]:
    """Get current working directory."""
    return {"working_directory": get_terminal_agent().get_working_directory()}


@router.post("/terminal/working-directory", response_model=ExecutionResultResponse)
async def set_working_directory(
    request: SetWorkingDirectoryRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Set working directory."""
    result = get_terminal_agent().set_working_directory(request.path, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.get("/terminal/environment")
async def get_environment_variables(current_user_id: int = Depends(get_current_user_id)) -> dict[str, Any]:
    """Get environment variables."""
    return {"environment": get_terminal_agent().get_environment_variables()}


@router.post("/terminal/environment", response_model=ExecutionResultResponse)
async def set_environment_variable(
    request: SetEnvironmentVariableRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Set environment variable."""
    result = get_terminal_agent().set_environment_variable(request.name, request.value, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.get("/terminal/history")
async def get_command_history(
    limit: int = 50,
    current_user_id: int = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Get command execution history."""
    return {"history": get_terminal_agent().get_command_history(limit)}


@router.get("/terminal/running")
async def get_running_commands(current_user_id: int = Depends(get_current_user_id)) -> dict[str, Any]:
    """Get running commands."""
    return {"running": get_terminal_agent().get_running_commands()}


# ============================================================================
# Browser Automation Endpoints
# ============================================================================

@router.post("/browser/open", response_model=ExecutionResultResponse)
async def open_browser(
    request: OpenBrowserRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Open browser and optionally navigate to URL."""
    result = await get_browser_agent().open_browser(request.url, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/navigate", response_model=ExecutionResultResponse)
async def navigate(
    request: NavigateRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Navigate to URL."""
    result = await get_browser_agent().navigate(request.page_id, request.url, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/click", response_model=ExecutionResultResponse)
async def click_element(
    request: ClickElementRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Click element on page."""
    result = await get_browser_agent().click_element(request.page_id, request.selector, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/fill", response_model=ExecutionResultResponse)
async def fill_form(
    request: FillFormRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Fill form field."""
    result = await get_browser_agent().fill_form(request.page_id, request.selector, request.value, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/extract", response_model=ExecutionResultResponse)
async def extract_content(
    request: ExtractContentRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Extract content from page."""
    result = await get_browser_agent().extract_content(request.page_id, request.selector, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/download", response_model=ExecutionResultResponse)
async def download_file(
    request: DownloadFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Download file from URL."""
    result = await get_browser_agent().download_file(request.page_id, request.url, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/upload", response_model=ExecutionResultResponse)
async def upload_file(
    request: UploadFileRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Upload file via file input."""
    result = await get_browser_agent().upload_file(request.page_id, request.selector, request.file_path, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/screenshot", response_model=ExecutionResultResponse)
async def take_screenshot(
    request: TakeScreenshotRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Take screenshot of page."""
    result = await get_browser_agent().take_screenshot(request.page_id, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/browser/close", response_model=ExecutionResultResponse)
async def close_browser(
    request: CloseBrowserRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Close browser page or entire browser."""
    result = await get_browser_agent().close_browser(request.page_id, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.get("/browser/pages")
async def get_active_pages(current_user_id: int = Depends(get_current_user_id)) -> dict[str, Any]:
    """Get active browser pages."""
    return {"pages": get_browser_agent().get_active_pages()}


# ============================================================================
# Desktop Endpoints
# ============================================================================

@router.post("/desktop/launch", response_model=ExecutionResultResponse)
async def launch_application(
    request: LaunchApplicationRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Launch application."""
    result = await get_desktop_agent().launch_application(request.application, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/desktop/close", response_model=ExecutionResultResponse)
async def close_application(
    request: CloseApplicationRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Close application."""
    result = await get_desktop_agent().close_application(request.application, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/desktop/window", response_model=ExecutionResultResponse)
async def manage_window(
    request: ManageWindowRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Manage window."""
    result = await get_desktop_agent().manage_window(request.action, request.window_title, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.get("/desktop/clipboard", response_model=ExecutionResultResponse)
async def get_clipboard(current_user_id: int = Depends(get_current_user_id)) -> ExecutionResultResponse:
    """Get clipboard content."""
    result = await get_desktop_agent().get_clipboard(current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/desktop/clipboard", response_model=ExecutionResultResponse)
async def set_clipboard(
    request: SetClipboardRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Set clipboard content."""
    result = await get_desktop_agent().set_clipboard(request.content, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/desktop/notification", response_model=ExecutionResultResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> ExecutionResultResponse:
    """Send desktop notification."""
    result = await get_desktop_agent().send_notification(request.title, request.message, current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.post("/desktop/capture", response_model=ExecutionResultResponse)
async def capture_screen(current_user_id: int = Depends(get_current_user_id)) -> ExecutionResultResponse:
    """Capture screen screenshot."""
    result = await get_desktop_agent().capture_screen(current_user_id)
    return ExecutionResultResponse(**result.dict())


@router.get("/desktop/applications", response_model=ExecutionResultResponse)
async def get_running_applications(current_user_id: int = Depends(get_current_user_id)) -> ExecutionResultResponse:
    """Get running applications."""
    result = get_desktop_agent().get_running_applications()
    return ExecutionResultResponse(**result.dict())


@router.get("/desktop/platform")
async def get_platform(current_user_id: int = Depends(get_current_user_id)) -> dict[str, str]:
    """Get current platform."""
    return {"platform": get_desktop_agent().get_platform()}


# ============================================================================
# Workflow Endpoints
# ============================================================================

@router.post("/workflows", response_model=WorkflowDefinitionResponse)
async def create_workflow(
    request: CreateWorkflowRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> WorkflowDefinitionResponse:
    """Create workflow definition."""
    # Check if workflow ID already exists
    existing = await db.execute(
        select(WorkflowDefinition).where(
            WorkflowDefinition.workflow_id == request.workflow_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow ID already exists"
        )
    
    # Create workflow definition
    workflow = WorkflowDefinition(
        user_id=current_user_id,
        workflow_id=request.workflow_id,
        name=request.name,
        description=request.description,
        steps_json=[step.dict() for step in request.steps],
        parallel=request.parallel,
        requires_approval=request.requires_approval,
        timeout=request.timeout
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    # Register with workflow engine
    workflow_def = WorkflowDef(
        workflow_id=request.workflow_id,
        name=request.name,
        description=request.description,
        steps=[
            WorkflowStep(**step.dict())
            for step in request.steps
        ],
        parallel=request.parallel,
        requires_approval=request.requires_approval,
        timeout=request.timeout
    )
    get_workflow_engine().register_workflow(workflow_def)
    
    return WorkflowDefinitionResponse(
        id=workflow.id,  # type: ignore[arg-type]
        uuid=workflow.uuid,  # type: ignore[arg-type]
        workflow_id=workflow.workflow_id,  # type: ignore[arg-type]
        name=workflow.name,  # type: ignore[arg-type]
        description=workflow.description,  # type: ignore[arg-type]
        steps=request.steps,
        parallel=workflow.parallel,  # type: ignore[arg-type]
        requires_approval=workflow.requires_approval,  # type: ignore[arg-type]
        timeout=workflow.timeout,  # type: ignore[arg-type]
        is_active=workflow.is_active,  # type: ignore[arg-type]
        created_at=workflow.created_at  # type: ignore[arg-type]
    )


@router.get("/workflows", response_model=List[WorkflowDefinitionResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> List[WorkflowDefinitionResponse]:
    """List user's workflows."""
    result = await db.execute(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.user_id == current_user_id)
        .order_by(desc(WorkflowDefinition.created_at))
    )
    workflows = result.scalars().all()
    
    return [
        WorkflowDefinitionResponse(
            id=w.id,  # type: ignore[arg-type]
            uuid=w.uuid,  # type: ignore[arg-type]
            workflow_id=w.workflow_id,  # type: ignore[arg-type]
            name=w.name,  # type: ignore[arg-type]
            description=w.description,  # type: ignore[arg-type]
            steps=[WorkflowStep(**s) for s in cast(list, w.steps_json)] if isinstance(w.steps_json, list) else [],  # type: ignore[misc, arg-type]
            parallel=w.parallel,  # type: ignore[arg-type]
            requires_approval=w.requires_approval,  # type: ignore[arg-type]
            timeout=w.timeout,  # type: ignore[arg-type]
            is_active=w.is_active,  # type: ignore[arg-type]
            created_at=w.created_at  # type: ignore[arg-type]
        )
        for w in workflows
    ]


@router.get("/workflows/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> WorkflowDefinitionResponse:
    """Get workflow by ID."""
    result = await db.execute(
        select(WorkflowDefinition)
        .where(
            WorkflowDefinition.workflow_id == workflow_id,
            WorkflowDefinition.user_id == current_user_id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    return WorkflowDefinitionResponse(
        id=workflow.id,  # type: ignore[arg-type]
        uuid=workflow.uuid,  # type: ignore[arg-type]
        workflow_id=workflow.workflow_id,  # type: ignore[arg-type]
        name=workflow.name,  # type: ignore[arg-type]
        description=workflow.description,  # type: ignore[arg-type]
        steps=[WorkflowStep(**s) for s in cast(list, workflow.steps_json)] if isinstance(workflow.steps_json, list) else [],  # type: ignore[misc, arg-type, attr-defined]
        parallel=workflow.parallel,  # type: ignore[arg-type]
        requires_approval=workflow.requires_approval,  # type: ignore[arg-type]
        timeout=workflow.timeout,  # type: ignore[arg-type]
        is_active=workflow.is_active,  # type: ignore[arg-type]
        created_at=workflow.created_at  # type: ignore[arg-type]
    )


@router.post("/workflows/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: ExecuteWorkflowRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> WorkflowExecutionResponse:
    """Execute workflow."""
    # Get workflow definition
    result = await db.execute(
        select(WorkflowDefinition).where(
            WorkflowDefinition.workflow_id == request.workflow_id,
            WorkflowDefinition.user_id == current_user_id
        )
    )
    workflow_def = result.scalar_one_or_none()
    
    if not workflow_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Create workflow execution record
    execution = WorkflowExecution(
        user_id=current_user_id,
        workflow_id=workflow_def.id,
        parameters=request.parameters or {},
        status=ExecutionStatus.PENDING,
        started_at=None  # Will be set by Celery task
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # Queue Celery task for execution
    from app.worker import get_celery_app
    task = get_celery_app().send_task(
        'app.tasks.computer_tasks.execute_workflow',
        args=[execution.id],
        queue='computer'
    )
    
    return WorkflowExecutionResponse(
        execution_id=str(execution.uuid),
        workflow_id=workflow_def.workflow_id,
        status=SchemaExecutionStatus(execution.status.value),
        current_step=0,
        completed_steps=0,
        failed_steps=0,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        results={"task_id": task.id}
    )


@router.post("/workflows/cancel")
async def cancel_workflow(
    request: CancelWorkflowRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> dict[str, str]:
    """Cancel workflow execution."""
    success = get_workflow_engine().cancel_execution(request.execution_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel execution"
        )
    
    return {"message": "Execution cancelled"}


@router.get("/workflows/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_workflow_execution(
    execution_id: str,
    current_user_id: int = Depends(get_current_user_id)
) -> WorkflowExecutionResponse:
    """Get workflow execution by ID."""
    execution = get_workflow_engine().get_execution(execution_id)
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return WorkflowExecutionResponse(
        execution_id=execution.execution_id,
        workflow_id=execution.workflow_id,
        status=SchemaExecutionStatus(execution.status.value),
        current_step=execution.current_step,
        completed_steps=execution.completed_steps,
        failed_steps=execution.failed_steps,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        results=execution.results
    )


# ============================================================================
# Permission Endpoints
# ============================================================================

@router.get("/permissions/pending")
async def get_pending_permissions(current_user_id: int = Depends(get_current_user_id)) -> dict[str, Any]:
    """Get pending permission requests."""
    pending = get_permission_system().get_pending_requests()
    return {"pending": pending}


@router.get("/permissions/approved")
async def get_approved_permissions(current_user_id: int = Depends(get_current_user_id)) -> dict[str, Any]:
    """Get approved permissions."""
    approved = get_permission_system().get_approved_permissions(current_user_id)
    return {"approved": approved}


@router.get("/permissions/denied")
async def get_denied_permissions(current_user_id: int = Depends(get_current_user_id)) -> dict[str, Any]:
    """Get denied permissions."""
    denied = get_permission_system().get_denied_permissions(current_user_id)
    return {"denied": denied}


@router.post("/permissions/approve", response_model=PermissionResponseSchema)
async def approve_permission(
    request: ApprovePermissionRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> PermissionResponseSchema:
    """Approve permission request."""
    response = await get_permission_system().approve_permission(
        request.request_id,
        current_user_id,
        request.approve_for_session
    )
    return PermissionResponseSchema(**response.dict())


@router.post("/permissions/deny", response_model=PermissionResponseSchema)
async def deny_permission(
    request: DenyPermissionRequest,
    current_user_id: int = Depends(get_current_user_id)
) -> PermissionResponseSchema:
    """Deny permission request."""
    response = await get_permission_system().deny_permission(
        request.request_id,
        current_user_id,
        request.reason
    )
    return PermissionResponseSchema(**response.dict())


@router.post("/permissions/revoke")
async def revoke_permission(
    request_id: str,
    current_user_id: int = Depends(get_current_user_id)
) -> dict[str, str]:
    """Revoke approved permission."""
    get_permission_system().revoke_permission(request_id)
    return {"message": "Permission revoked"}


@router.post("/permissions/clear-expired")
async def clear_expired_permissions(current_user_id: int = Depends(get_current_user_id)) -> dict[str, int]:
    """Clear expired permissions."""
    count = get_permission_system().clear_expired_permissions()
    return {"cleared": count}


# ============================================================================
# History Endpoints
# ============================================================================

@router.get("/history", response_model=List[ComputerHistoryResponse])
async def get_computer_history(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> List[ComputerHistoryResponse]:
    """Get computer action history for current user."""
    result = await db.execute(
        select(ComputerActionExecution)
        .where(ComputerActionExecution.user_id == current_user_id)
        .order_by(desc(ComputerActionExecution.started_at))
        .offset(skip)
        .limit(limit)
    )
    executions = result.scalars().all()
    
    return [
        ComputerHistoryResponse(
            id=exec.id,  # type: ignore[arg-type]
            uuid=exec.uuid,  # type: ignore[arg-type]
            action_type=ComputerActionType(exec.action_type.value) if hasattr(exec.action_type, 'value') else ComputerActionType.UNKNOWN,  # type: ignore[arg-type]
            status=ExecutionStatus(exec.status.value) if hasattr(exec.status, 'value') else ExecutionStatus.PENDING,  # type: ignore[arg-type]
            success=bool(exec.success),  # type: ignore[arg-type]
            duration_seconds=float(exec.duration_seconds) if exec.duration_seconds is not None else None,  # type: ignore[arg-type]
            started_at=exec.started_at,  # type: ignore[arg-type]
            completed_at=exec.completed_at  # type: ignore[arg-type]
        )
        for exec in executions
    ]


@router.get("/workflows/history")
async def get_workflow_history(
    limit: int = 50,
    current_user_id: int = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Get workflow execution history."""
    history = get_workflow_engine().get_execution_history(limit)
    return {"history": history}
