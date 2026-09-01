/**
 * React Query hooks for Computer Use & Automation System API.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from './api'

// ============================================================================
// File System Hooks
// ============================================================================

export const useBrowseDirectory = () => {
  return useMutation({
    mutationFn: (data: { path: string; depth?: number }) =>
      api.post('/computer/files/browse', data),
  })
}

export const useReadFile = () => {
  return useMutation({
    mutationFn: (data: { path: string }) =>
      api.post('/computer/files/read', data),
  })
}

export const useWriteFile = () => {
  return useMutation({
    mutationFn: (data: { path: string; content: string; overwrite?: boolean }) =>
      api.post('/computer/files/write', data),
  })
}

export const useDeleteFile = () => {
  return useMutation({
    mutationFn: (data: { path: string }) =>
      api.post('/computer/files/delete', data),
  })
}

export const useRenameFile = () => {
  return useMutation({
    mutationFn: (data: { source: string; target: string }) =>
      api.post('/computer/files/rename', data),
  })
}

export const useMoveFile = () => {
  return useMutation({
    mutationFn: (data: { source: string; target: string }) =>
      api.post('/computer/files/move', data),
  })
}

export const useCopyFile = () => {
  return useMutation({
    mutationFn: (data: { source: string; target: string }) =>
      api.post('/computer/files/copy', data),
  })
}

export const useSearchFiles = () => {
  return useMutation({
    mutationFn: (data: { path: string; pattern: string }) =>
      api.post('/computer/files/search', data),
  })
}

export const useCreateArchive = () => {
  return useMutation({
    mutationFn: (data: { source: string; target: string }) =>
      api.post('/computer/files/archive', data),
  })
}

export const useExtractArchive = () => {
  return useMutation({
    mutationFn: (data: { source: string; target: string }) =>
      api.post('/computer/files/extract', data),
  })
}

// ============================================================================
// Terminal Hooks
// ============================================================================

export const useExecuteCommand = () => {
  return useMutation({
    mutationFn: (data: { 
      command: string; 
      working_directory?: string; 
      environment?: Record<string, string>;
      timeout?: number;
      stream_output?: boolean;
    }) => api.post('/computer/terminal/execute', data),
  })
}

export const useCancelCommand = () => {
  return useMutation({
    mutationFn: (data: { action_id: string }) =>
      api.post('/computer/terminal/cancel', data),
  })
}

export const useWorkingDirectory = () => {
  return useQuery({
    queryKey: ['terminal', 'working-directory'],
    queryFn: () => api.get('/computer/terminal/working-directory'),
  })
}

export const useSetWorkingDirectory = () => {
  return useMutation({
    mutationFn: (data: { path: string }) =>
      api.post('/computer/terminal/working-directory', data),
  })
}

export const useEnvironmentVariables = () => {
  return useQuery({
    queryKey: ['terminal', 'environment'],
    queryFn: () => api.get('/computer/terminal/environment'),
  })
}

export const useSetEnvironmentVariable = () => {
  return useMutation({
    mutationFn: (data: { name: string; value: string }) =>
      api.post('/computer/terminal/environment', data),
  })
}

export const useCommandHistory = (limit: number = 50) => {
  return useQuery({
    queryKey: ['terminal', 'history', limit],
    queryFn: () => api.get(`/computer/terminal/history?limit=${limit}`),
  })
}

export const useRunningCommands = () => {
  return useQuery({
    queryKey: ['terminal', 'running'],
    queryFn: () => api.get('/computer/terminal/running'),
  })
}

// ============================================================================
// Browser Hooks
// ============================================================================

export const useOpenBrowser = () => {
  return useMutation({
    mutationFn: (data: { url?: string }) =>
      api.post('/computer/browser/open', data),
  })
}

export const useNavigateBrowser = () => {
  return useMutation({
    mutationFn: (data: { page_id: string; url: string }) =>
      api.post('/computer/browser/navigate', data),
  })
}

export const useClickElement = () => {
  return useMutation({
    mutationFn: (data: { page_id: string; selector: string }) =>
      api.post('/computer/browser/click', data),
  })
}

export const useFillForm = () => {
  return useMutation({
    mutationFn: (data: { page_id: string; selector: string; value: string }) =>
      api.post('/computer/browser/fill', data),
  })
}

export const useExtractContent = () => {
  return useMutation({
    mutationFn: (data: { page_id: string; selector?: string }) =>
      api.post('/computer/browser/extract', data),
  })
}

export const useDownloadFile = () => {
  return useMutation({
    mutationFn: (data: { page_id: string; url: string }) =>
      api.post('/computer/browser/download', data),
  })
}

export const useUploadFile = () => {
  return useMutation({
    mutationFn: (data: { page_id: string; selector: string; file_path: string }) =>
      api.post('/computer/browser/upload', data),
  })
}

export const useTakeScreenshot = () => {
  return useMutation({
    mutationFn: (data: { page_id: string }) =>
      api.post('/computer/browser/screenshot', data),
  })
}

export const useCloseBrowser = () => {
  return useMutation({
    mutationFn: (data: { page_id?: string }) =>
      api.post('/computer/browser/close', data),
  })
}

export const useActivePages = () => {
  return useQuery({
    queryKey: ['browser', 'pages'],
    queryFn: () => api.get('/computer/browser/pages'),
  })
}

// ============================================================================
// Desktop Hooks
// ============================================================================

export const useLaunchApplication = () => {
  return useMutation({
    mutationFn: (data: { application: string }) =>
      api.post('/computer/desktop/launch', data),
  })
}

export const useCloseApplication = () => {
  return useMutation({
    mutationFn: (data: { application: string }) =>
      api.post('/computer/desktop/close', data),
  })
}

export const useManageWindow = () => {
  return useMutation({
    mutationFn: (data: { action: string; window_title?: string }) =>
      api.post('/computer/desktop/window', data),
  })
}

export const useGetClipboard = () => {
  return useMutation({
    mutationFn: () => api.get('/computer/desktop/clipboard'),
  })
}

export const useSetClipboard = () => {
  return useMutation({
    mutationFn: (data: { content: string }) =>
      api.post('/computer/desktop/clipboard', data),
  })
}

export const useSendNotification = () => {
  return useMutation({
    mutationFn: (data: { title: string; message: string }) =>
      api.post('/computer/desktop/notification', data),
  })
}

export const useCaptureScreen = () => {
  return useMutation({
    mutationFn: () => api.post('/computer/desktop/capture'),
  })
}

export const useRunningApplications = () => {
  return useQuery({
    queryKey: ['desktop', 'applications'],
    queryFn: () => api.get('/computer/desktop/applications'),
  })
}

export const usePlatform = () => {
  return useQuery({
    queryKey: ['desktop', 'platform'],
    queryFn: () => api.get('/computer/desktop/platform'),
  })
}

// ============================================================================
// Workflow Hooks
// ============================================================================

export const useCreateWorkflow = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: any) => api.post('/computer/workflows', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
    },
  })
}

export const useWorkflows = () => {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () => api.get('/computer/workflows'),
  })
}

export const useWorkflow = (workflowId: string) => {
  return useQuery({
    queryKey: ['workflows', workflowId],
    queryFn: () => api.get(`/computer/workflows/${workflowId}`),
    enabled: !!workflowId,
  })
}

export const useExecuteWorkflow = () => {
  return useMutation({
    mutationFn: (data: { workflow_id: string; parameters?: Record<string, any> }) =>
      api.post('/computer/workflows/execute', data),
  })
}

export const useCancelWorkflow = () => {
  return useMutation({
    mutationFn: (data: { execution_id: string }) =>
      api.post('/computer/workflows/cancel', data),
  })
}

export const useWorkflowExecution = (executionId: string) => {
  return useQuery({
    queryKey: ['workflow-executions', executionId],
    queryFn: () => api.get(`/computer/workflows/executions/${executionId}`),
    enabled: !!executionId,
    refetchInterval: 2000, // Poll every 2 seconds
  })
}

export const useWorkflowHistory = (limit: number = 50) => {
  return useQuery({
    queryKey: ['workflow-history', limit],
    queryFn: () => api.get(`/computer/workflows/history?limit=${limit}`),
  })
}

// ============================================================================
// Permission Hooks
// ============================================================================

export const usePendingPermissions = () => {
  return useQuery({
    queryKey: ['permissions', 'pending'],
    queryFn: () => api.get('/computer/permissions/pending'),
    refetchInterval: 3000, // Poll every 3 seconds
  })
}

export const useApprovedPermissions = () => {
  return useQuery({
    queryKey: ['permissions', 'approved'],
    queryFn: () => api.get('/computer/permissions/approved'),
  })
}

export const useDeniedPermissions = () => {
  return useQuery({
    queryKey: ['permissions', 'denied'],
    queryFn: () => api.get('/computer/permissions/denied'),
  })
}

export const useApprovePermission = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { request_id: string; approve_for_session?: boolean }) =>
      api.post('/computer/permissions/approve', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
    },
  })
}

export const useDenyPermission = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { request_id: string; reason?: string }) =>
      api.post('/computer/permissions/deny', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
    },
  })
}

export const useRevokePermission = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (requestId: string) =>
      api.post(`/computer/permissions/revoke?request_id=${requestId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
    },
  })
}

export const useClearExpiredPermissions = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.post('/computer/permissions/clear-expired'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
    },
  })
}

// ============================================================================
// History Hooks
// ============================================================================

export const useComputerHistory = (skip: number = 0, limit: number = 100) => {
  return useQuery({
    queryKey: ['computer-history', skip, limit],
    queryFn: () => api.get(`/computer/history?skip=${skip}&limit=${limit}`),
  })
}
