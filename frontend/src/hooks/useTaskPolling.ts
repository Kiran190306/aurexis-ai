import { useState, useEffect, useCallback, useRef } from 'react'
import { TaskService, TaskStatus } from '../services/tasks'

interface UseTaskPollingOptions {
  pollInterval?: number // milliseconds, default 2000
  onSuccess?: (result: unknown) => void
  onFailure?: (error: string) => void
}

interface UseTaskPollingReturn {
  taskStatus: TaskStatus | null
  isLoading: boolean
  error: string | null
  startPolling: (taskId: string) => void
  stopPolling: () => void
  isPolling: boolean
}

export function useTaskPolling(options: UseTaskPollingOptions = {}): UseTaskPollingReturn {
  const {
    pollInterval = 2000,
    onSuccess,
    onFailure
  } = options

  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)

  const pollIntervalRef = useRef<number | null>(null)
  const isMountedRef = useRef(true)

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
    setIsPolling(false)
  }, [])

  const pollTaskStatus = useCallback(async (taskId: string) => {
    if (!isMountedRef.current) return

    try {
      const status = await TaskService.getTaskStatus(taskId)
      
      if (!isMountedRef.current) return

      setTaskStatus(status)
      setError(null)

      // Check if task is complete
      if (status.ready) {
        stopPolling()
        setIsLoading(false)

        if (status.successful) {
          onSuccess?.(status.result)
        } else if (status.failed) {
          onFailure?.(status.traceback || 'Task failed')
        }
      }
    } catch (err) {
      if (!isMountedRef.current) return

      const errorMessage = err instanceof Error ? err.message : 'Failed to poll task status'
      setError(errorMessage)
      stopPolling()
      setIsLoading(false)
      onFailure?.(errorMessage)
    }
  }, [stopPolling, onSuccess, onFailure])

  const startPolling = useCallback((taskId: string) => {
    // Stop any existing polling
    stopPolling()

    setIsPolling(true)
    setIsLoading(true)
    setError(null)

    // Initial poll
    pollTaskStatus(taskId)

    // Set up interval polling
    pollIntervalRef.current = window.setInterval(() => {
      pollTaskStatus(taskId)
    }, pollInterval)
  }, [stopPolling, pollTaskStatus, pollInterval])

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false
      stopPolling()
    }
  }, [stopPolling])

  return {
    taskStatus,
    isLoading,
    error,
    startPolling,
    stopPolling,
    isPolling
  }
}
