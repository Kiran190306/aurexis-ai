import { useState, useEffect } from 'react'
import { XCircle, Clock, CheckCircle, AlertCircle, RefreshCw, Copy } from 'lucide-react'
import { ComputerService, WorkflowExecution, ExecutionStatus } from '../../services/computer'
import { TaskService } from '../../services/tasks'
import { useTaskPolling } from '../../hooks/useTaskPolling'
import toast from 'react-hot-toast'

interface ExecutionViewProps {
  executionId: string
  onClose?: () => void
}

export function ExecutionView({ executionId, onClose }: ExecutionViewProps) {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)

  const { startPolling, stopPolling } = useTaskPolling({
    onSuccess: () => {
      toast.success('Workflow execution completed')
      setTaskId(null)
      loadExecution()
    },
    onFailure: (error) => {
      toast.error(`Workflow execution failed: ${error}`)
      setTaskId(null)
      loadExecution()
    }
  })

  const loadExecution = async () => {
    try {
      setLoading(true)
      const data = await ComputerService.getWorkflowExecution(executionId)
      setExecution(data)
      
      // Check if execution has task_id in results (async response)
      const resultsAny = data.results as unknown
      if (resultsAny && typeof resultsAny === 'object' && 'task_id' in resultsAny) {
        const task_id = (resultsAny as { task_id: string }).task_id
        if (task_id && !taskId) {
          setTaskId(task_id)
          startPolling(task_id)
        }
      }
    } catch (error) {
      console.error('Failed to load execution:', error)
      toast.error('Failed to load execution details')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadExecution()
    setRefreshing(false)
  }

  const handleCancel = async () => {
    if (taskId) {
      try {
        await TaskService.cancelTask(taskId)
        stopPolling()
        setTaskId(null)
        toast.success('Task cancelled')
        loadExecution()
        return
      } catch (error) {
        toast.error('Failed to cancel task')
      }
    }
    
    if (!confirm('Are you sure you want to cancel this execution?')) {
      return
    }
    try {
      await ComputerService.cancelWorkflow({ execution_id: executionId })
      toast.success('Execution cancelled')
      loadExecution()
    } catch (error) {
      console.error('Failed to cancel execution:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to cancel execution')
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  useEffect(() => {
    loadExecution()
    // Poll for running executions every 2 seconds (only if not using task polling)
    const interval = setInterval(() => {
      if (execution?.status === ExecutionStatus.RUNNING && !taskId) {
        loadExecution()
      }
    }, 2000)

    return () => {
      clearInterval(interval)
      stopPolling()
    }
  }, [executionId, taskId])

  const getStatusColor = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.RUNNING:
        return 'text-blue-500 bg-blue-500/10'
      case ExecutionStatus.COMPLETED:
        return 'text-green-500 bg-green-500/10'
      case ExecutionStatus.FAILED:
        return 'text-red-500 bg-red-500/10'
      case ExecutionStatus.CANCELLED:
        return 'text-yellow-500 bg-yellow-500/10'
      default:
        return 'text-gray-500 bg-gray-500/10'
    }
  }

  const getStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.RUNNING:
        return <RefreshCw className="w-5 h-5 animate-spin" />
      case ExecutionStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5" />
      case ExecutionStatus.FAILED:
        return <XCircle className="w-5 h-5" />
      case ExecutionStatus.CANCELLED:
        return <Clock className="w-5 h-5" />
      default:
        return <Clock className="w-5 h-5" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!execution) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-muted-foreground">Execution not found</p>
      </div>
    )
  }

  const duration = execution.completed_at
    ? Math.round((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000)
    : Math.round((Date.now() - new Date(execution.started_at).getTime()) / 1000)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${getStatusColor(execution.status)}`}>
            {getStatusIcon(execution.status)}
          </div>
          <div>
            <h2 className="text-2xl font-bold">{execution.workflow_id}</h2>
            <p className="text-sm text-muted-foreground">Execution ID: {execution.execution_id}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 border border-border rounded-md hover:bg-accent transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          {execution.status === ExecutionStatus.RUNNING && (
            <button
              onClick={handleCancel}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
            >
              <XCircle className="w-4 h-4" />
              Cancel
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Status Card */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Status</p>
            <p className={`font-semibold ${getStatusColor(execution.status).split(' ')[0]}`}>
              {execution.status}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Duration</p>
            <p className="font-semibold">{duration}s</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Started</p>
            <p className="font-semibold">{new Date(execution.started_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Completed</p>
            <p className="font-semibold">
              {execution.completed_at ? new Date(execution.completed_at).toLocaleString() : '-'}
            </p>
          </div>
        </div>
      </div>

      {/* Steps Progress */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="font-semibold mb-4">Execution Progress</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Current Step</span>
            <span className="font-medium">{execution.current_step || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Completed Steps</span>
            <span className="font-medium text-green-500">{execution.completed_steps.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Failed Steps</span>
            <span className="font-medium text-red-500">{execution.failed_steps.length}</span>
          </div>
        </div>

        {execution.completed_steps.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-medium mb-2">Completed Steps</p>
            <div className="flex flex-wrap gap-2">
              {execution.completed_steps.map((step) => (
                <span
                  key={step}
                  className="px-2 py-1 bg-green-500/10 text-green-500 rounded text-xs"
                >
                  {step}
                </span>
              ))}
            </div>
          </div>
        )}

        {execution.failed_steps.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-medium mb-2 text-red-500">Failed Steps</p>
            <div className="flex flex-wrap gap-2">
              {execution.failed_steps.map((step) => (
                <span
                  key={step}
                  className="px-2 py-1 bg-red-500/10 text-red-500 rounded text-xs"
                >
                  {step}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {Object.keys(execution.results).length > 0 && (
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Results</h3>
            <button
              onClick={() => handleCopy(JSON.stringify(execution.results, null, 2))}
              className="p-1.5 hover:bg-accent rounded-md transition-colors"
              title="Copy Results"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
          <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
            {JSON.stringify(execution.results, null, 2)}
          </pre>
        </div>
      )}

      {/* Error Display */}
      {execution.status === ExecutionStatus.FAILED && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-500">Execution Failed</h3>
              <p className="text-sm text-red-400 mt-1">
                Check the failed steps and results above for more details.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Success Display */}
      {execution.status === ExecutionStatus.COMPLETED && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-green-500">Execution Completed Successfully</h3>
              <p className="text-sm text-green-400 mt-1">
                All steps completed without errors.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
