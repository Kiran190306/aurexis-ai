import { apiRequest } from './api'

// Enums
export enum ComputerActionType {
  FILE_READ = 'file_read',
  FILE_WRITE = 'file_write',
  FILE_DELETE = 'file_delete',
  FILE_RENAME = 'file_rename',
  FILE_MOVE = 'file_move',
  FILE_COPY = 'file_copy',
  DIRECTORY_BROWSE = 'directory_browse',
  DIRECTORY_CREATE = 'directory_create',
  DIRECTORY_DELETE = 'directory_delete',
  FILE_SEARCH = 'file_search',
  FILE_ARCHIVE = 'file_archive',
  FILE_EXTRACT = 'file_extract',
  TERMINAL_EXECUTE = 'terminal_execute',
  TERMINAL_CANCEL = 'terminal_cancel',
  TERMINAL_STREAM = 'terminal_stream',
  BROWSER_OPEN = 'browser_open',
  BROWSER_NAVIGATE = 'browser_navigate',
  BROWSER_CLICK = 'browser_click',
  BROWSER_FILL = 'browser_fill',
  BROWSER_EXTRACT = 'browser_extract',
  BROWSER_DOWNLOAD = 'browser_download',
  BROWSER_UPLOAD = 'browser_upload',
  BROWSER_SCREENSHOT = 'browser_screenshot',
  BROWSER_CLOSE = 'browser_close',
  DESKTOP_LAUNCH = 'desktop_launch',
  DESKTOP_CLOSE = 'desktop_close',
  DESKTOP_WINDOW = 'desktop_window',
  DESKTOP_CLIPBOARD = 'desktop_clipboard',
  DESKTOP_NOTIFICATION = 'desktop_notification',
  DESKTOP_CAPTURE = 'desktop_capture',
}

export enum PermissionStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  DENIED = 'denied',
  EXPIRED = 'expired',
  REVOKED = 'revoked',
}

export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// Base Types
export interface ExecutionResult {
  action_id: string
  action_type: ComputerActionType
  status: ExecutionStatus
  success: boolean
  output: string | null
  error: string | null
  duration_seconds: number
  metadata: Record<string, unknown>
}

export interface WorkflowStep {
  step_id: string
  action_type: ComputerActionType
  parameters: Record<string, unknown>
  depends_on: string[]
  retry_policy: Record<string, unknown> | null
  rollback_action: Record<string, unknown> | null
}

export interface WorkflowDefinition {
  id: number
  uuid: string
  workflow_id: string
  name: string
  description: string
  steps: WorkflowStep[]
  parallel: boolean
  requires_approval: boolean
  timeout: number
  is_active: boolean
  created_at: string
}

export interface WorkflowExecution {
  execution_id: string
  workflow_id: string
  status: ExecutionStatus
  current_step: string | null
  completed_steps: string[]
  failed_steps: string[]
  started_at: string
  completed_at: string | null
  results: Record<string, unknown>
}

export interface ComputerHistory {
  id: number
  uuid: string
  action_type: ComputerActionType
  status: ExecutionStatus
  success: boolean
  duration_seconds: number | null
  started_at: string
  completed_at: string | null
}

export interface PermissionRequest {
  request_id: string
  action_type: ComputerActionType
  target_path: string | null
  command: string | null
  url: string | null
  description: string
  risk_level: string
  metadata: Record<string, unknown>
}

export interface PermissionResponse {
  request_id: string
  status: PermissionStatus
  approved_by: string | null
  approved_at: string | null
  expires_at: string | null
  reason: string | null
}

// Request Types
export interface BrowseDirectoryRequest {
  path: string
  depth?: number
}

export interface ReadFileRequest {
  path: string
}

export interface WriteFileRequest {
  path: string
  content: string
  overwrite?: boolean
}

export interface DeleteFileRequest {
  path: string
}

export interface RenameFileRequest {
  source: string
  target: string
}

export interface MoveFileRequest {
  source: string
  target: string
}

export interface CopyFileRequest {
  source: string
  target: string
}

export interface SearchFilesRequest {
  path: string
  pattern: string
}

export interface ArchiveRequest {
  source: string
  target: string
}

export interface ExtractRequest {
  source: string
  target: string
}

export interface ExecuteCommandRequest {
  command: string
  working_directory?: string
  environment?: Record<string, string>
  timeout?: number
  stream_output?: boolean
}

export interface CancelCommandRequest {
  action_id: string
}

export interface SetWorkingDirectoryRequest {
  path: string
}

export interface SetEnvironmentVariableRequest {
  name: string
  value: string
}

export interface OpenBrowserRequest {
  url?: string
}

export interface NavigateRequest {
  page_id: string
  url: string
}

export interface ClickElementRequest {
  page_id: string
  selector: string
}

export interface FillFormRequest {
  page_id: string
  selector: string
  value: string
}

export interface ExtractContentRequest {
  page_id: string
  selector?: string
}

export interface DownloadFileRequest {
  page_id: string
  url: string
}

export interface UploadFileRequest {
  page_id: string
  selector: string
  file_path: string
}

export interface TakeScreenshotRequest {
  page_id: string
}

export interface CloseBrowserRequest {
  page_id?: string
}

export interface LaunchApplicationRequest {
  application: string
}

export interface CloseApplicationRequest {
  application: string
}

export interface ManageWindowRequest {
  action: string
  window_title?: string
}

export interface SetClipboardRequest {
  content: string
}

export interface SendNotificationRequest {
  title: string
  message: string
}

export interface CreateWorkflowRequest {
  workflow_id: string
  name: string
  description: string
  steps: WorkflowStep[]
  parallel?: boolean
  requires_approval?: boolean
  timeout?: number
}

export interface ExecuteWorkflowRequest {
  workflow_id: string
  parameters?: Record<string, unknown>
}

export interface CancelWorkflowRequest {
  execution_id: string
}

export interface ApprovePermissionRequest {
  request_id: string
  approve_for_session?: boolean
}

export interface DenyPermissionRequest {
  request_id: string
  reason?: string
}

export class ComputerService {
  private static readonly BASE_PATH = '/api/v1/computer'

  // ============================================================================
  // File System Endpoints
  // ============================================================================

  static async browseDirectory(request: BrowseDirectoryRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/browse`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async readFile(request: ReadFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/read`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async writeFile(request: WriteFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/write`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async deleteFile(request: DeleteFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/delete`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async renameFile(request: RenameFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/rename`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async moveFile(request: MoveFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/move`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async copyFile(request: CopyFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/copy`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async searchFiles(request: SearchFilesRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/search`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async createArchive(request: ArchiveRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/archive`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async extractArchive(request: ExtractRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/files/extract`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // ============================================================================
  // Terminal Endpoints
  // ============================================================================

  static async executeCommand(request: ExecuteCommandRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/terminal/execute`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async cancelCommand(request: CancelCommandRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/terminal/cancel`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getWorkingDirectory(): Promise<{ working_directory: string }> {
    return apiRequest<{ working_directory: string }>(`${this.BASE_PATH}/terminal/working-directory`)
  }

  static async setWorkingDirectory(request: SetWorkingDirectoryRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/terminal/working-directory`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getEnvironmentVariables(): Promise<{ environment: Record<string, string> }> {
    return apiRequest<{ environment: Record<string, string> }>(`${this.BASE_PATH}/terminal/environment`)
  }

  static async setEnvironmentVariable(request: SetEnvironmentVariableRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/terminal/environment`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getCommandHistory(limit: number = 50): Promise<{ history: string[] }> {
    return apiRequest<{ history: string[] }>(`${this.BASE_PATH}/terminal/history?limit=${limit}`)
  }

  static async getRunningCommands(): Promise<{ running: string[] }> {
    return apiRequest<{ running: string[] }>(`${this.BASE_PATH}/terminal/running`)
  }

  // ============================================================================
  // Browser Endpoints
  // ============================================================================

  static async openBrowser(request: OpenBrowserRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/open`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async navigate(request: NavigateRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/navigate`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async clickElement(request: ClickElementRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/click`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async fillForm(request: FillFormRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/fill`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async extractContent(request: ExtractContentRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/extract`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async downloadFile(request: DownloadFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/download`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async uploadFile(request: UploadFileRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/upload`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async takeScreenshot(request: TakeScreenshotRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/screenshot`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async closeBrowser(request: CloseBrowserRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/browser/close`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getActivePages(): Promise<{ pages: string[] }> {
    return apiRequest<{ pages: string[] }>(`${this.BASE_PATH}/browser/pages`)
  }

  // ============================================================================
  // Desktop Endpoints
  // ============================================================================

  static async launchApplication(request: LaunchApplicationRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/launch`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async closeApplication(request: CloseApplicationRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/close`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async manageWindow(request: ManageWindowRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/window`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getClipboard(): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/clipboard`)
  }

  static async setClipboard(request: SetClipboardRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/clipboard`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async sendNotification(request: SendNotificationRequest): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/notification`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async captureScreen(): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/capture`)
  }

  static async getRunningApplications(): Promise<ExecutionResult> {
    return apiRequest<ExecutionResult>(`${this.BASE_PATH}/desktop/applications`)
  }

  static async getPlatform(): Promise<{ platform: string }> {
    return apiRequest<{ platform: string }>(`${this.BASE_PATH}/desktop/platform`)
  }

  // ============================================================================
  // Workflow Endpoints
  // ============================================================================

  static async createWorkflow(request: CreateWorkflowRequest): Promise<WorkflowDefinition> {
    return apiRequest<WorkflowDefinition>(`${this.BASE_PATH}/workflows`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async listWorkflows(): Promise<WorkflowDefinition[]> {
    return apiRequest<WorkflowDefinition[]>(`${this.BASE_PATH}/workflows`)
  }

  static async getWorkflow(workflowId: string): Promise<WorkflowDefinition> {
    return apiRequest<WorkflowDefinition>(`${this.BASE_PATH}/workflows/${workflowId}`)
  }

  static async executeWorkflow(request: ExecuteWorkflowRequest): Promise<WorkflowExecution> {
    return apiRequest<WorkflowExecution>(`${this.BASE_PATH}/workflows/execute`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async cancelWorkflow(request: CancelWorkflowRequest): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`${this.BASE_PATH}/workflows/cancel`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
    return apiRequest<WorkflowExecution>(`${this.BASE_PATH}/workflows/executions/${executionId}`)
  }

  static async getWorkflowHistory(limit: number = 50): Promise<{ history: WorkflowExecution[] }> {
    return apiRequest<{ history: WorkflowExecution[] }>(`${this.BASE_PATH}/workflows/history?limit=${limit}`)
  }

  // ============================================================================
  // Permission Endpoints
  // ============================================================================

  static async getPendingPermissions(): Promise<{ pending: PermissionRequest[] }> {
    return apiRequest<{ pending: PermissionRequest[] }>(`${this.BASE_PATH}/permissions/pending`)
  }

  static async getApprovedPermissions(): Promise<{ approved: PermissionResponse[] }> {
    return apiRequest<{ approved: PermissionResponse[] }>(`${this.BASE_PATH}/permissions/approved`)
  }

  static async getDeniedPermissions(): Promise<{ denied: PermissionResponse[] }> {
    return apiRequest<{ denied: PermissionResponse[] }>(`${this.BASE_PATH}/permissions/denied`)
  }

  static async approvePermission(request: ApprovePermissionRequest): Promise<PermissionResponse> {
    return apiRequest<PermissionResponse>(`${this.BASE_PATH}/permissions/approve`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async denyPermission(request: DenyPermissionRequest): Promise<PermissionResponse> {
    return apiRequest<PermissionResponse>(`${this.BASE_PATH}/permissions/deny`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async revokePermission(requestId: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`${this.BASE_PATH}/permissions/revoke?request_id=${requestId}`, {
      method: 'POST',
    })
  }

  static async clearExpiredPermissions(): Promise<{ cleared: number }> {
    return apiRequest<{ cleared: number }>(`${this.BASE_PATH}/permissions/clear-expired`, {
      method: 'POST',
    })
  }

  // ============================================================================
  // History Endpoints
  // ============================================================================

  static async getComputerHistory(skip: number = 0, limit: number = 100): Promise<ComputerHistory[]> {
    return apiRequest<ComputerHistory[]>(`${this.BASE_PATH}/history?skip=${skip}&limit=${limit}`)
  }
}
