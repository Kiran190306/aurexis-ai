# Computer Use & Automation System Architecture

## Overview

The Computer Use & Automation System (EPIC-014) enables Jarvis AI to safely interact with the user's computer under explicit user approval. This production-grade system provides comprehensive file system operations, terminal command execution, browser automation, desktop control, and multi-step workflow automation with permission-based security.

## Architecture Principles

- **Permission-Based Execution**: All computer actions require user approval before execution
- **Sandboxed Where Possible**: File system operations restricted to allowed paths
- **Full Audit Logging**: All actions logged with timestamps and results
- **Cross-Platform**: Windows, Linux, macOS support where feasible
- **Backward Compatibility**: Maintains compatibility with existing Jarvis AI architecture
- **Production-Grade**: Comprehensive error handling, validation, and logging

## System Components

### 1. Permission System (`app/computer/permission_system.py`)

**Purpose**: Central permission management for all computer actions.

**Responsibilities**:
- Request permissions for computer actions
- Approve/deny permission requests
- Session-based permission caching
- Permission expiration management
- Risk level assessment per action type
- Audit trail of all permissions

**Key Methods**:
- `request_permission()`: Request permission for an action
- `approve_permission()`: Approve a pending request
- `deny_permission()`: Deny a pending request
- `check_permission()`: Check if permission is valid
- `revoke_permission()`: Revoke an approved permission
- `get_pending_requests()`: Get pending permission requests
- `clear_expired_permissions()`: Clear expired permissions

**Risk Levels**:
- **Low**: Directory browse, file read, browser open/navigate, content extraction, screenshot
- **Medium**: File write/rename/move/copy, archive/extract, terminal stream, browser fill/download/upload, desktop launch/close/clipboard
- **High**: File/directory delete, terminal execute, wake word detection

**Configuration**:
- `COMPUTER_USE_SANDBOXED`: Enable sandbox mode
- `COMPUTER_USE_ALLOWED_PATHS`: Allowed file system paths
- `COMPUTER_USE_PERMISSION_DURATION`: Permission validity duration (default: 1 hour)
- `COMPUTER_USE_AUDIT_LOG_ENABLED`: Enable audit logging

### 2. File System Agent (`app/computer/file_system_agent.py`)

**Purpose**: Safe file system operations with permission checks.

**Responsibilities**:
- Directory browsing with depth control
- File reading with size limits
- File writing with overwrite protection
- File/directory deletion (requires confirmation)
- File rename, move, copy operations
- File search with pattern matching
- ZIP archive creation and extraction
- Path validation against sandbox rules

**Key Methods**:
- `browse_directory()`: Browse directory contents
- `read_file()`: Read file contents
- `write_file()`: Write content to file
- `delete_file()`: Delete file or directory
- `rename_file()`: Rename file or directory
- `move_file()`: Move file or directory
- `copy_file()`: Copy file or directory
- `search_files()`: Search for files matching pattern
- `create_archive()`: Create ZIP archive
- `extract_archive()`: Extract ZIP archive

**Configuration**:
- `FILE_SYSTEM_MAX_DEPTH`: Maximum browsing depth (default: 10)
- `FILE_SYSTEM_MAX_RESULTS`: Maximum search results (default: 1000)
- `COMPUTER_USE_MAX_FILE_SIZE`: Maximum file size (default: 100MB)

### 3. Terminal Agent (`app/computer/terminal_agent.py`)

**Purpose**: Safe shell command execution with permission checks.

**Responsibilities**:
- Shell command execution with timeout
- Streaming output support
- Command cancellation
- Working directory management
- Environment variable management
- Command execution history
- Running command tracking

**Key Methods**:
- `execute_command()`: Execute shell command
- `execute_command_stream()`: Execute with streaming output
- `cancel_command()`: Cancel running command
- `get_working_directory()`: Get current working directory
- `set_working_directory()`: Set working directory
- `get_environment_variables()`: Get environment variables
- `set_environment_variable()`: Set environment variable
- `get_command_history()`: Get command history
- `get_running_commands()`: Get running commands

**Configuration**:
- `COMPUTER_USE_COMMAND_TIMEOUT`: Default command timeout (default: 5 minutes)

### 4. Browser Automation Agent (`app/computer/browser_agent.py`)

**Purpose**: Browser automation using Playwright.

**Responsibilities**:
- Browser instance management
- Page navigation
- Element interaction (click, fill)
- Content extraction
- File download/upload
- Screenshot capture
- Multi-tab support

**Key Methods**:
- `initialize()`: Initialize browser instance
- `shutdown()`: Shutdown browser instance
- `open_browser()`: Open browser and optionally navigate
- `navigate()`: Navigate to URL
- `click_element()`: Click element by selector
- `fill_form()`: Fill form field
- `extract_content()`: Extract page content
- `download_file()`: Download file from URL
- `upload_file()`: Upload file via file input
- `take_screenshot()`: Take page screenshot
- `close_browser()`: Close page or browser
- `get_active_pages()`: Get active page IDs

**Configuration**:
- `PLAYWRIGHT_HEADLESS`: Run browser headless (default: true)
- `PLAYWRIGHT_BROWSER`: Browser type (chromium, firefox, webkit)
- `PLAYWRIGHT_DOWNLOAD_PATH`: Browser download path
- `COMPUTER_USE_BROWSER_TIMEOUT`: Browser operation timeout (default: 60s)

### 5. Desktop Agent (`app/computer/desktop_agent.py`)

**Purpose**: Desktop automation and control.

**Responsibilities**:
- Application launch/close
- Window management
- Clipboard operations
- Desktop notifications
- Screen capture
- Running applications list

**Key Methods**:
- `launch_application()`: Launch application
- `close_application()`: Close application
- `manage_window()`: Manage window (minimize, maximize, restore)
- `get_clipboard()`: Get clipboard content
- `set_clipboard()`: Set clipboard content
- `send_notification()`: Send desktop notification
- `capture_screen()`: Capture screen screenshot
- `get_running_applications()`: Get running applications
- `get_platform()`: Get current platform

**Platform Support**:
- **Windows**: Full support with platform-specific commands
- **macOS**: Full support with platform-specific commands
- **Linux**: Basic support (some features require additional libraries)

**Dependencies**:
- `pyperclip`: Clipboard operations
- `plyer`: Desktop notifications
- `mss`: Screen capture
- `psutil`: Process management (optional)

### 6. Workflow Engine (`app/computer/workflow_engine.py`)

**Purpose**: Multi-step task execution with conditional logic and retry policies.

**Responsibilities**:
- Workflow registration and management
- Sequential and parallel step execution
- Dependency resolution
- Retry policies with configurable delays
- Rollback actions on failure
- Workflow execution tracking
- Execution cancellation

**Key Methods**:
- `register_workflow()`: Register workflow definition
- `get_workflow()`: Get workflow by ID
- `list_workflows()`: List all workflows
- `execute_workflow()`: Execute workflow
- `cancel_execution()`: Cancel running execution
- `get_execution()`: Get execution by ID
- `get_execution_history()`: Get execution history

**Workflow Features**:
- **Sequential Execution**: Steps execute in order
- **Parallel Execution**: Independent steps execute concurrently
- **Dependencies**: Steps can depend on other steps
- **Retry Policies**: Configurable max retries and delays
- **Rollback Actions**: Automatic rollback on failure
- **Timeout**: Total workflow timeout
- **Approval**: Optional user approval required

**Retry Policy**:
- `max_retries`: Maximum retry attempts (default: 0)
- `delay`: Delay between retries in seconds (default: 1)

## Database Schema

### PermissionRequest

Stores permission requests for computer actions.

**Fields**:
- `id`, `uuid`, `user_id`
- `action_type`: Type of computer action
- `target_path`: Target file/directory path
- `command`: Shell command (for terminal)
- `url`: URL (for browser)
- `description`: Human-readable description
- `risk_level`: Risk assessment (low, medium, high)
- `status`: pending, approved, denied, expired, revoked
- `approved_by`: User who approved
- `approved_at`: Approval timestamp
- `expires_at`: Permission expiration
- `reason`: Denial reason
- `metadata_json`: Additional metadata
- `created_at`, `updated_at`

### ComputerActionExecution

Stores computer action execution records.

**Fields**:
- `id`, `uuid`, `user_id`, `permission_request_id`
- `action_type`: Type of action executed
- `action_id`: Action execution ID
- `status`: pending, running, completed, failed, cancelled
- `success`: Whether execution succeeded
- `output`: Command output
- `error`: Error message
- `duration_seconds`: Execution duration
- `metadata_json`: Additional metadata
- `started_at`, `completed_at`, `created_at`, `updated_at`

### WorkflowDefinition

Stores workflow definitions for multi-step automation.

**Fields**:
- `id`, `uuid`, `user_id`
- `workflow_id`: Unique workflow identifier
- `name`: Workflow name
- `description`: Workflow description
- `steps_json`: Workflow steps (JSON)
- `parallel`: Execute steps in parallel
- `requires_approval`: Requires user approval
- `timeout`: Total timeout in seconds
- `is_active`: Active status
- `metadata_json`: Additional metadata
- `created_at`, `updated_at`

### WorkflowExecution

Stores workflow execution instances.

**Fields**:
- `id`, `uuid`, `user_id`, `workflow_id`
- `execution_id`: Unique execution identifier
- `status`: pending, running, completed, failed, cancelled
- `current_step`: Currently executing step
- `completed_steps_json`: Completed step IDs
- `failed_steps_json`: Failed step IDs
- `results_json`: Step execution results
- `started_at`, `completed_at`, `created_at`, `updated_at`

### ComputerUseSettings

Stores user computer use preferences.

**Fields**:
- `id`, `user_id`
- `sandboxed`: Enable sandbox mode
- `allowed_paths`: Allowed file system paths
- `max_file_size`: Maximum file size
- `auto_approve_low_risk`: Auto-approve low-risk actions
- `permission_duration`: Permission validity duration
- `remember_approvals`: Remember session approvals
- `command_timeout`: Default command timeout
- `default_working_directory`: Default working directory
- `browser_type`: Browser type (chromium, firefox, webkit)
- `headless`: Run browser headless
- `browser_timeout`: Browser operation timeout
- `audit_log_enabled`: Enable audit logging
- `log_retention_days`: Log retention period
- `notify_on_action`: Notify on actions
- `notify_on_permission`: Notify on permissions
- `created_at`, `updated_at`

## API Endpoints

### File System Endpoints

- `POST /computer/files/browse` - Browse directory contents
- `POST /computer/files/read` - Read file contents
- `POST /computer/files/write` - Write content to file
- `POST /computer/files/delete` - Delete file or directory
- `POST /computer/files/rename` - Rename file or directory
- `POST /computer/files/move` - Move file or directory
- `POST /computer/files/copy` - Copy file or directory
- `POST /computer/files/search` - Search for files
- `POST /computer/files/archive` - Create ZIP archive
- `POST /computer/files/extract` - Extract ZIP archive

### Terminal Endpoints

- `POST /computer/terminal/execute` - Execute shell command
- `POST /computer/terminal/cancel` - Cancel running command
- `GET /computer/terminal/working-directory` - Get working directory
- `POST /computer/terminal/working-directory` - Set working directory
- `GET /computer/terminal/environment` - Get environment variables
- `POST /computer/terminal/environment` - Set environment variable
- `GET /computer/terminal/history` - Get command history
- `GET /computer/terminal/running` - Get running commands

### Browser Automation Endpoints

- `POST /computer/browser/open` - Open browser
- `POST /computer/browser/navigate` - Navigate to URL
- `POST /computer/browser/click` - Click element
- `POST /computer/browser/fill` - Fill form field
- `POST /computer/browser/extract` - Extract content
- `POST /computer/browser/download` - Download file
- `POST /computer/browser/upload` - Upload file
- `POST /computer/browser/screenshot` - Take screenshot
- `POST /computer/browser/close` - Close browser/page
- `GET /computer/browser/pages` - Get active pages

### Desktop Endpoints

- `POST /computer/desktop/launch` - Launch application
- `POST /computer/desktop/close` - Close application
- `POST /computer/desktop/window` - Manage window
- `GET /computer/desktop/clipboard` - Get clipboard content
- `POST /computer/desktop/clipboard` - Set clipboard content
- `POST /computer/desktop/notification` - Send notification
- `POST /computer/desktop/capture` - Capture screen
- `GET /computer/desktop/applications` - Get running applications
- `GET /computer/desktop/platform` - Get platform

### Workflow Endpoints

- `POST /computer/workflows` - Create workflow
- `GET /computer/workflows` - List workflows
- `GET /computer/workflows/{workflow_id}` - Get workflow
- `POST /computer/workflows/execute` - Execute workflow
- `POST /computer/workflows/cancel` - Cancel execution
- `GET /computer/workflows/executions/{execution_id}` - Get execution
- `GET /computer/workflows/history` - Get execution history

### Permission Endpoints

- `GET /computer/permissions/pending` - Get pending permissions
- `GET /computer/permissions/approved` - Get approved permissions
- `GET /computer/permissions/denied` - Get denied permissions
- `POST /computer/permissions/approve` - Approve permission
- `POST /computer/permissions/deny` - Deny permission
- `POST /computer/permissions/revoke` - Revoke permission
- `POST /computer/permissions/clear-expired` - Clear expired permissions

### History Endpoints

- `GET /computer/history` - Get computer action history

## Frontend Integration

### React Hooks (`services/computer-hooks.ts`)

Comprehensive React Query hooks for all computer use APIs:
- File system hooks: `useBrowseDirectory`, `useReadFile`, `useWriteFile`, etc.
- Terminal hooks: `useExecuteCommand`, `useCancelCommand`, `useWorkingDirectory`, etc.
- Browser hooks: `useOpenBrowser`, `useNavigateBrowser`, `useClickElement`, etc.
- Desktop hooks: `useLaunchApplication`, `useCloseApplication`, `useGetClipboard`, etc.
- Workflow hooks: `useCreateWorkflow`, `useWorkflows`, `useExecuteWorkflow`, etc.
- Permission hooks: `usePendingPermissions`, `useApprovePermission`, `useDenyPermission`, etc.
- History hooks: `useComputerHistory`

### Computer Page (`pages/ComputerPage.tsx`)

Main dashboard with tabbed interface:
- **Terminal**: Shell command execution with streaming output
- **File Browser**: Directory navigation and file operations
- **Browser**: Browser automation with page management
- **Workflows**: Workflow builder and execution
- **Permissions**: Permission management interface
- **History**: Execution timeline and audit log

### Components

- **TerminalConsole**: Terminal interface with command input, output display, and command history
- **FileBrowser**: File system browser with directory navigation, file operations, and search
- **BrowserSessions**: Browser automation interface with page tabs and action controls
- **WorkflowBuilder**: Visual workflow builder with step management and execution
- **PermissionManager**: Permission approval/deny interface with risk indicators
- **ExecutionTimeline**: Timeline view of action history with filtering and details

## Desktop Integration

### Electron IPC Bridge

The desktop application uses Electron's IPC (Inter-Process Communication) to bridge the renderer process (React frontend) with the main process (Node.js backend). This enables:

- Native file system access
- System-level command execution
- Desktop application control
- Native notifications
- Clipboard operations

### Permission Dialogs

Permission requests trigger native dialog boxes in the Electron main process:
- Shows action type, target path/command, and risk level
- Provides Approve/Deny/Approve Session options
- Remembers user preferences for session approvals

### Native Notifications

Desktop notifications are sent using Electron's notification API:
- Action completion notifications
- Permission request notifications
- Error notifications
- Workflow status updates

## Security Model

### Permission-Based Execution

All computer actions require explicit user approval:
1. Action requested by AI or user
2. Permission request created with risk assessment
3. User prompted for approval
4. If approved, action executes
5. If denied, action blocked
6. All actions logged for audit

### Sandbox Mode

When sandbox mode is enabled:
- File system operations restricted to allowed paths
- Working directory validated against allowed paths
- Commands executed in restricted environment
- Browser operations limited to safe actions

### Risk Assessment

Each action type assigned a risk level:
- **Low**: Read-only operations, navigation
- **Medium**: Write operations, modifications
- **High**: Destructive operations, command execution

Low-risk actions can be auto-approved if configured.

### Audit Logging

All computer actions are logged:
- Action type and parameters
- User who approved
- Execution result
- Duration and timestamps
- Success/failure status

## Supported Platforms

### Windows

Full support for all features:
- File system operations
- Terminal command execution (PowerShell/CMD)
- Browser automation (Chromium)
- Desktop automation
- Application launch/close
- Clipboard operations
- Notifications

### macOS

Full support for all features:
- File system operations
- Terminal command execution (zsh/bash)
- Browser automation (Chromium)
- Desktop automation
- Application launch/close
- Clipboard operations
- Notifications

### Linux

Basic support with some limitations:
- File system operations
- Terminal command execution (bash)
- Browser automation (Chromium)
- Desktop automation (limited - requires additional libraries)
- Application launch/close (via xdg-open)
- Clipboard operations (requires pyperclip)
- Notifications (requires plyer)

## Deployment Guide

### Prerequisites

**System Dependencies**:
- Python 3.9+
- Node.js 18+
- Electron (for desktop app)

**Python Packages**:
```
playwright
pyperclip
plyer
mss
psutil
```

**Node.js Packages**:
```
electron
electron-builder
```

### Installation

1. **Install Python dependencies**:
   ```bash
   pip install playwright pyperclip plyer mss psutil
   playwright install chromium
   ```

2. **Install Node.js dependencies**:
   ```bash
   cd desktop-app
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   ENABLE_COMPUTER_USE=true
   COMPUTER_USE_SANDBOXED=true
   COMPUTER_USE_ALLOWED_PATHS=./data/computer
   PLAYWRIGHT_HEADLESS=true
   PLAYWRIGHT_BROWSER=chromium
   ```

4. **Run database migrations**:
   ```bash
   alembic revision --autogenerate -m "Add computer use tables"
   alembic upgrade head
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright
RUN pip install playwright
RUN playwright install chromium

# Set environment variables
ENV ENABLE_COMPUTER_USE=true
ENV PLAYWRIGHT_HEADLESS=true
ENV PLAYWRIGHT_BROWSER=chromium

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

**Permission denied errors**:
- Check if sandbox mode is restricting paths
- Verify user has approved the action
- Check if permission has expired

**Browser automation not working**:
- Verify Playwright is installed: `pip show playwright`
- Install browser: `playwright install chromium`
- Check headless mode setting

**Terminal command timeout**:
- Increase `COMPUTER_USE_COMMAND_TIMEOUT`
- Check if command is hanging
- Verify working directory is accessible

**Desktop automation not working**:
- Install required libraries: `pip install pyperclip plyer mss psutil`
- Check platform support for specific features
- Verify Electron IPC is configured

**File operations failing**:
- Check if path is in allowed paths (sandbox mode)
- Verify file permissions
- Check if file size exceeds limit

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("app.computer").setLevel(logging.DEBUG)
```

## Testing

### Unit Tests
```bash
pytest tests/test_file_system_agent.py
pytest tests/test_terminal_agent.py
pytest tests/test_browser_agent.py
pytest tests/test_desktop_agent.py
pytest tests/test_permission_system.py
pytest tests/test_workflow_engine.py
```

### Integration Tests
```bash
pytest tests/test_computer_integration.py
```

### Permission Tests
```bash
pytest tests/test_computer_permissions.py
```

### Workflow Tests
```bash
pytest tests/test_computer_workflows.py
```

### Browser Automation Tests
```bash
pytest tests/test_computer_browser.py
```

## Performance Considerations

### Latency Targets

- Permission check: < 100ms
- File system operations: < 1s (local), < 5s (network)
- Terminal commands: User-configurable timeout (default: 5 min)
- Browser operations: < 5s per action
- Workflow execution: Configurable timeout (default: 10 min)

### Optimization Tips

- Use sandbox mode for security with minimal overhead
- Cache approved permissions for session
- Use parallel workflow execution for independent steps
- Set appropriate timeouts for long-running operations
- Use streaming for terminal output

### Resource Usage

- File system agent: < 50MB RAM
- Terminal agent: < 20MB RAM per command
- Browser agent: ~200MB RAM per browser instance
- Desktop agent: < 30MB RAM
- Total idle usage: < 100MB RAM

## Future Enhancements

### Planned Features
- GPT-4 Computer Use integration for advanced automation
- Real-time voice command execution
- Visual workflow editor with drag-and-drop
- Workflow templates library
- Scheduled workflow execution
- Remote computer control via web interface
- Advanced file operations (sync, diff, merge)
- Multi-browser session management
- Desktop UI automation (beyond basic window management)
- System monitoring and resource management

### Optimization Opportunities
- GPU acceleration for browser automation
- Model quantization for AI-driven automation
- Distributed workflow execution
- Result caching with Redis
- Progressive file loading for large files

## Backward Compatibility

The Computer Use & Automation System maintains backward compatibility:
- Existing Jarvis AI features unchanged
- Computer use features opt-in via feature flag
- No breaking changes to existing APIs
- Database migrations additive only
- Frontend routes added without modifying existing navigation

## Contributing

### Adding New Computer Capabilities

1. Extend agent with new functionality
2. Add API endpoint if needed
3. Update database schema if required
4. Add frontend UI components
5. Write tests
6. Update documentation

### Adding New Workflow Steps

1. Define step parameters in WorkflowStep schema
2. Implement agent action routing
3. Add UI controls in WorkflowBuilder
4. Test workflow execution
5. Document new step type

## License

This Computer Use & Automation System is part of Jarvis AI v1.2 and follows the same license terms.

## Contact

For questions or issues related to the Computer Use & Automation System, please refer to the main project documentation or contact the development team.
