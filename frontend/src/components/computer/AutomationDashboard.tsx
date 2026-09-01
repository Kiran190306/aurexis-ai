import { useState, useEffect } from 'react'
import { Activity, CheckCircle, XCircle, Clock, Play, Plus, RefreshCw } from 'lucide-react'
import { ComputerService, WorkflowDefinition, WorkflowExecution, ComputerHistory, ExecutionStatus } from '../../services/computer'
import toast from 'react-hot-toast'

interface AutomationDashboardProps {
  onExecuteWorkflow?: (workflowId: string) => void
  onViewExecution?: (executionId: string) => void
}

export function AutomationDashboard({ onExecuteWorkflow, onViewExecution }: AutomationDashboardProps) {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([])
  const [executions, setExecutions] = useState<WorkflowExecution[]>([])
  const [history, setHistory] = useState<ComputerHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async () => {
    try {
      setLoading(true)
      const [workflowsData, executionsData, historyData] = await Promise.all([
        ComputerService.listWorkflows(),
        ComputerService.getWorkflowHistory(10),
        ComputerService.getComputerHistory(0, 20),
      ])
      setWorkflows(workflowsData)
      setExecutions(executionsData.history)
      setHistory(historyData)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadData()
    setRefreshing(false)
    toast.success('Dashboard refreshed')
  }

  useEffect(() => {
    loadData()
  }, [])

  const stats = {
    totalWorkflows: workflows.length,
    runningExecutions: executions.filter(e => e.status === ExecutionStatus.RUNNING).length,
    completedExecutions: executions.filter(e => e.status === ExecutionStatus.COMPLETED).length,
    failedExecutions: executions.filter(e => e.status === ExecutionStatus.FAILED).length,
    totalHistory: history.length,
  }

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
        return <Activity className="w-4 h-4" />
      case ExecutionStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4" />
      case ExecutionStatus.FAILED:
        return <XCircle className="w-4 h-4" />
      case ExecutionStatus.CANCELLED:
        return <Clock className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Automation Dashboard</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-card border border-border rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Workflows</p>
              <p className="text-2xl font-bold">{stats.totalWorkflows}</p>
            </div>
            <div className="p-2 bg-primary/10 rounded-lg">
              <Activity className="w-5 h-5 text-primary" />
            </div>
          </div>
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Running</p>
              <p className="text-2xl font-bold text-blue-500">{stats.runningExecutions}</p>
            </div>
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Activity className="w-5 h-5 text-blue-500" />
            </div>
          </div>
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold text-green-500">{stats.completedExecutions}</p>
            </div>
            <div className="p-2 bg-green-500/10 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
          </div>
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Failed</p>
              <p className="text-2xl font-bold text-red-500">{stats.failedExecutions}</p>
            </div>
            <div className="p-2 bg-red-500/10 rounded-lg">
              <XCircle className="w-5 h-5 text-red-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="bg-card border border-border rounded-lg">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold">Recent Executions</h3>
        </div>
        {executions.length > 0 ? (
          <div className="divide-y divide-border">
            {executions.slice(0, 5).map((execution) => (
              <div
                key={execution.execution_id}
                className="p-4 hover:bg-accent transition-colors cursor-pointer"
                onClick={() => onViewExecution?.(execution.execution_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${getStatusColor(execution.status)}`}>
                      {getStatusIcon(execution.status)}
                    </div>
                    <div>
                      <p className="font-medium">{execution.workflow_id}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(execution.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${getStatusColor(execution.status).split(' ')[0]}`}>
                      {execution.status}
                    </p>
                    {execution.completed_at && (
                      <p className="text-xs text-muted-foreground">
                        {Math.round((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000)}s
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">
            <p>No recent executions</p>
          </div>
        )}
      </div>

      {/* Saved Workflows */}
      <div className="bg-card border border-border rounded-lg">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold">Saved Workflows</h3>
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
            <Plus className="w-4 h-4" />
            Create Workflow
          </button>
        </div>
        {workflows.length > 0 ? (
          <div className="divide-y divide-border">
            {workflows.slice(0, 5).map((workflow) => (
              <div
                key={workflow.uuid}
                className="p-4 hover:bg-accent transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{workflow.name}</p>
                    <p className="text-sm text-muted-foreground">{workflow.description}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-muted-foreground">
                        {workflow.steps.length} steps
                      </span>
                      {workflow.requires_approval && (
                        <span className="text-xs px-2 py-0.5 bg-yellow-500/10 text-yellow-500 rounded">
                          Requires Approval
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => onExecuteWorkflow?.(workflow.workflow_id)}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm border border-border rounded-md hover:bg-accent transition-colors"
                  >
                    <Play className="w-4 h-4" />
                    Execute
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">
            <p>No saved workflows</p>
            <button className="mt-2 text-primary hover:underline">
              Create your first workflow
            </button>
          </div>
        )}
      </div>

      {/* Recent History */}
      <div className="bg-card border border-border rounded-lg">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold">Recent Actions ({stats.totalHistory})</h3>
        </div>
        {history.length > 0 ? (
          <div className="divide-y divide-border max-h-64 overflow-y-auto">
            {history.slice(0, 10).map((item) => (
              <div key={item.uuid} className="p-4 hover:bg-accent transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{item.action_type}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(item.started_at).toLocaleString()}
                    </p>
                  </div>
                  <div className={`flex items-center gap-1 px-2 py-1 rounded ${getStatusColor(item.status)}`}>
                    {getStatusIcon(item.status)}
                    <span className="text-xs">{item.status}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">
            <p>No recent actions</p>
          </div>
        )}
      </div>
    </div>
  )
}
