import { useState, useEffect } from 'react'
import { Activity, CheckCircle, XCircle, Clock, Plus, RefreshCw, Zap } from 'lucide-react'
import { AgentService, Agent, ExecutionPlan, AgentStatus, ExecutionStatus } from '../../services/agent'
import toast from 'react-hot-toast'

interface AgentDashboardProps {
  onExecuteAgent?: () => void
  onViewExecution?: (planUuid: string) => void
}

export function AgentDashboard({ onViewExecution }: AgentDashboardProps) {
  const [agents, setAgents] = useState<Agent[]>([])
  const [executions, setExecutions] = useState<ExecutionPlan[]>([])
  const [agentStatus, setAgentStatus] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async () => {
    try {
      setLoading(true)
      const [agentsData, executionsData, statusData] = await Promise.all([
        AgentService.listAgents(),
        AgentService.listExecutionPlans(0, 10),
        AgentService.getAgentsStatus().catch(() => null),
      ])
      setAgents(agentsData)
      setExecutions(executionsData)
      setAgentStatus(statusData)
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
    totalAgents: agents.length,
    activeAgents: agents.filter(a => a.status === AgentStatus.ACTIVE).length,
    inactiveAgents: agents.filter(a => a.status === AgentStatus.INACTIVE).length,
    busyAgents: agents.filter(a => a.status === AgentStatus.BUSY).length,
    errorAgents: agents.filter(a => a.status === AgentStatus.ERROR).length,
    runningExecutions: executions.filter(e => e.status === ExecutionStatus.RUNNING).length,
    completedExecutions: executions.filter(e => e.status === ExecutionStatus.COMPLETED).length,
    failedExecutions: executions.filter(e => e.status === ExecutionStatus.FAILED).length,
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case AgentStatus.ACTIVE:
      case ExecutionStatus.RUNNING:
        return 'text-green-500 bg-green-500/10'
      case AgentStatus.INACTIVE:
      case ExecutionStatus.PAUSED:
        return 'text-gray-500 bg-gray-500/10'
      case AgentStatus.BUSY:
        return 'text-blue-500 bg-blue-500/10'
      case AgentStatus.ERROR:
      case ExecutionStatus.FAILED:
        return 'text-red-500 bg-red-500/10'
      case ExecutionStatus.COMPLETED:
        return 'text-green-500 bg-green-500/10'
      case ExecutionStatus.CANCELLED:
        return 'text-yellow-500 bg-yellow-500/10'
      default:
        return 'text-gray-500 bg-gray-500/10'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case AgentStatus.ACTIVE:
      case ExecutionStatus.RUNNING:
        return <Activity className="w-4 h-4" />
      case AgentStatus.INACTIVE:
      case ExecutionStatus.PAUSED:
        return <Clock className="w-4 h-4" />
      case AgentStatus.BUSY:
        return <Zap className="w-4 h-4" />
      case AgentStatus.ERROR:
      case ExecutionStatus.FAILED:
        return <XCircle className="w-4 h-4" />
      case ExecutionStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4" />
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
        <h2 className="text-2xl font-bold">Agent Dashboard</h2>
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
              <p className="text-sm text-muted-foreground">Total Agents</p>
              <p className="text-2xl font-bold">{stats.totalAgents}</p>
            </div>
            <div className="p-2 bg-primary/10 rounded-lg">
              <Activity className="w-5 h-5 text-primary" />
            </div>
          </div>
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active</p>
              <p className="text-2xl font-bold text-green-500">{stats.activeAgents}</p>
            </div>
            <div className="p-2 bg-green-500/10 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-500" />
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
              <Zap className="w-5 h-5 text-blue-500" />
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

      {/* Agent Status */}
      {agentStatus && (
        <div className="bg-card border border-border rounded-lg">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold">Agent System Status</h3>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(agentStatus).map(([key, value]) => (
                <div key={key} className="p-3 bg-muted rounded">
                  <p className="text-xs text-muted-foreground capitalize">{key}</p>
                  <p className="text-sm font-medium truncate">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recent Executions */}
      <div className="bg-card border border-border rounded-lg">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold">Recent Executions</h3>
        </div>
        {executions.length > 0 ? (
          <div className="divide-y divide-border">
            {executions.slice(0, 5).map((execution) => (
              <div
                key={execution.uuid}
                className="p-4 hover:bg-accent transition-colors cursor-pointer"
                onClick={() => onViewExecution?.(execution.uuid)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${getStatusColor(execution.status)}`}>
                      {getStatusIcon(execution.status)}
                    </div>
                    <div>
                      <p className="font-medium line-clamp-1">{execution.user_request}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(execution.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${getStatusColor(execution.status).split(' ')[0]}`}>
                      {execution.status}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {execution.task_count} tasks
                    </p>
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

      {/* Agents List */}
      <div className="bg-card border border-border rounded-lg">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold">Agents ({stats.totalAgents})</h3>
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
            <Plus className="w-4 h-4" />
            Create Agent
          </button>
        </div>
        {agents.length > 0 ? (
          <div className="divide-y divide-border">
            {agents.slice(0, 5).map((agent) => (
              <div key={agent.id} className="p-4 hover:bg-accent transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{agent.name}</p>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${getStatusColor(agent.status)}`}>
                        {agent.status}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-1">{agent.description}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-muted-foreground">
                        {agent.model}
                      </span>
                      {agent.memory_enabled && (
                        <span className="text-xs px-2 py-0.5 bg-blue-500/10 text-blue-500 rounded">
                          Memory: {agent.memory_type}
                        </span>
                      )}
                      {agent.tool_ids && agent.tool_ids.length > 0 && (
                        <span className="text-xs text-muted-foreground">
                          {agent.tool_ids.length} tools
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      {agent.task_count} tasks
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {agent.success_count} successful
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">
            <p>No agents configured</p>
            <button className="mt-2 text-primary hover:underline">
              Create your first agent
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
