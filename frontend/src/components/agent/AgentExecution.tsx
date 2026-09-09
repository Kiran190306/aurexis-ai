import { useState, useEffect } from 'react'
import { XCircle, Clock, CheckCircle, AlertCircle, RefreshCw, Copy, Send } from 'lucide-react'
import { AgentService, ExecutionPlan, ExecutionLog, ExecutionStatus } from '../../services/agent'
import { TaskService } from '../../services/tasks'
import { useTaskPolling } from '../../hooks/useTaskPolling'
import toast from 'react-hot-toast'

interface AgentExecutionProps {
  planUuid?: string
  onClose?: () => void
}

export function AgentExecution({ planUuid, onClose }: AgentExecutionProps) {
  const [plan, setPlan] = useState<ExecutionPlan | null>(null)
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [request, setRequest] = useState('')
  const [executing, setExecuting] = useState(false)
  const [currentPlanUuid, setCurrentPlanUuid] = useState(planUuid || null)
  const [taskId, setTaskId] = useState<string | null>(null)

  const { startPolling, stopPolling } = useTaskPolling({
    onSuccess: () => {
      toast.success('Agent execution completed')
      setExecuting(false)
      setTaskId(null)
      if (currentPlanUuid) {
        loadExecution()
      }
    },
    onFailure: (error) => {
      toast.error(`Agent execution failed: ${error}`)
      setExecuting(false)
      setTaskId(null)
      if (currentPlanUuid) {
        loadExecution()
      }
    }
  })

  const loadExecution = async () => {
    if (!currentPlanUuid) return
    try {
      setLoading(true)
      const [planData, logsData] = await Promise.all([
        AgentService.getExecutionPlan(currentPlanUuid),
        AgentService.getExecutionLogs(currentPlanUuid),
      ])
      setPlan(planData)
      setLogs(logsData)
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

  const handleExecute = async () => {
    if (!request.trim()) {
      toast.error('Please enter a request')
      return
    }
    try {
      setExecuting(true)
      const response = await AgentService.executeAgent({
        request,
        enable_reflection: true,
      })
      
      // Check if response contains task_id (async response)
      const responseAny = response as unknown
      if (responseAny && typeof responseAny === 'object' && 'metadata' in responseAny) {
        const metadata = (responseAny as { metadata: { task_id?: string } }).metadata
        if (metadata && metadata.task_id) {
          setTaskId(metadata.task_id)
          startPolling(metadata.task_id)
          toast.success('Execution queued')
          setCurrentPlanUuid(response.execution_plan_id)
          setRequest('')
          return
        }
      }
      
      // Fallback for synchronous response
      toast.success('Execution started')
      setCurrentPlanUuid(response.execution_plan_id)
      setRequest('')
      await loadExecution()
    } catch (error) {
      console.error('Failed to execute agent:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to execute agent')
      setExecuting(false)
    }
  }

  const handleCancel = async () => {
    if (taskId) {
      try {
        await TaskService.cancelTask(taskId)
        stopPolling()
        setExecuting(false)
        setTaskId(null)
        toast.success('Task cancelled')
        return
      } catch (error) {
        toast.error('Failed to cancel task')
      }
    }
    
    if (!currentPlanUuid) return
    try {
      await AgentService.cancelExecutionPlan(currentPlanUuid)
      toast.success('Execution cancelled')
      await loadExecution()
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
    if (currentPlanUuid && !taskId) {
      loadExecution()
      const interval = setInterval(() => {
        if (plan?.status === ExecutionStatus.RUNNING) {
          loadExecution()
        }
      }, 2000)
      return () => clearInterval(interval)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPlanUuid, plan?.status, taskId])

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
      case ExecutionStatus.PAUSED:
        return 'text-gray-500 bg-gray-500/10'
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
      case ExecutionStatus.PAUSED:
        return <Clock className="w-5 h-5" />
      default:
        return <Clock className="w-5 h-5" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Agent Execution</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors"
          >
            Close
          </button>
        )}
      </div>

      {/* New Execution */}
      {!currentPlanUuid && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="font-semibold mb-4">Execute Agent</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              placeholder="Enter your request..."
              className="flex-1 px-4 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
            />
            <button
              onClick={handleExecute}
              disabled={executing || !request.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {executing ? 'Executing...' : 'Execute'}
            </button>
          </div>
        </div>
      )}

      {/* Execution Details */}
      {plan && (
        <>
          {/* Status Card */}
          <div className="bg-card border border-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-lg ${getStatusColor(plan.status)}`}>
                  {getStatusIcon(plan.status)}
                </div>
                <div>
                  <h3 className="font-semibold">Execution Plan</h3>
                  <p className="text-sm text-muted-foreground">ID: {plan.uuid}</p>
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
                {plan.status === ExecutionStatus.RUNNING && (
                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                    Cancel
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <p className={`font-semibold ${getStatusColor(plan.status).split(' ')[0]}`}>
                  {plan.status}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Tasks</p>
                <p className="font-semibold">{plan.task_count}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="font-semibold">
                  {plan.execution_time_seconds ? `${plan.execution_time_seconds.toFixed(2)}s` : '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Started</p>
                <p className="font-semibold">
                  {plan.started_at ? new Date(plan.started_at).toLocaleString() : '-'}
                </p>
              </div>
            </div>

            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-1">Request</p>
              <p className="font-medium">{plan.user_request}</p>
            </div>
          </div>

          {/* Result */}
          {plan.final_output && (
            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Result</h3>
                <button
                  onClick={() => handleCopy(JSON.stringify(plan.final_output, null, 2))}
                  className="p-1.5 hover:bg-accent rounded-md transition-colors"
                  title="Copy Result"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm max-h-64 overflow-y-auto">
                {JSON.stringify(plan.final_output, null, 2)}
              </pre>
            </div>
          )}

          {/* Summary */}
          {plan.result_summary && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="font-semibold mb-2">Summary</h3>
              <p className="text-sm">{plan.result_summary}</p>
            </div>
          )}

          {/* Error */}
          {plan.error_message && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-500">Execution Failed</h3>
                  <p className="text-sm text-red-400 mt-1">{plan.error_message}</p>
                </div>
              </div>
            </div>
          )}

          {/* Execution Logs */}
          {logs.length > 0 && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="font-semibold mb-4">Execution Logs ({logs.length})</h3>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {logs.map((log) => (
                  <div key={log.uuid} className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{log.agent_role}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${getStatusColor(log.status)}`}>
                          {log.status}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {log.execution_time_seconds ? `${log.execution_time_seconds.toFixed(2)}s` : '-'}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{log.task_type}</p>
                    {log.error_message && (
                      <p className="text-sm text-red-500 mt-1">{log.error_message}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {loading && !plan && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      )}
    </div>
  )
}
