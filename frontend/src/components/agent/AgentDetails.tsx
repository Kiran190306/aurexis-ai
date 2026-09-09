import { useState, useEffect } from 'react'
import { Edit, Play, Clock, Zap, Cpu, Settings, History, Activity } from 'lucide-react'
import { AgentService, Agent, ExecutionPlan, AgentStatus, ExecutionStatus } from '../../services/agent'
import toast from 'react-hot-toast'

interface AgentDetailsProps {
  agentId: number
  onEdit?: (agent: Agent) => void
  onExecute?: (agent: Agent) => void
  onClose?: () => void
}

export function AgentDetails({ agentId, onEdit, onExecute, onClose }: AgentDetailsProps) {
  const [agent, setAgent] = useState<Agent | null>(null)
  const [executions, setExecutions] = useState<ExecutionPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'configuration' | 'executions'>('overview')

  const loadData = async () => {
    try {
      setLoading(true)
      const [agentData, executionsData] = await Promise.all([
        AgentService.getAgent(agentId),
        AgentService.listExecutionPlans(0, 20),
      ])
      setAgent(agentData)
      setExecutions(executionsData.filter(e => e.user_request.includes(agentData.name)))
    } catch (error) {
      console.error('Failed to load agent details:', error)
      toast.error('Failed to load agent details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
   loadData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId])

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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Agent not found</p>
      </div>
    )
  }

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: Activity },
    { id: 'configuration' as const, label: 'Configuration', icon: Settings },
    { id: 'executions' as const, label: 'Executions', icon: History },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/10 rounded-lg">
            <Cpu className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">{agent.name}</h2>
            <p className="text-sm text-muted-foreground">{agent.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onExecute?.(agent)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Play className="w-4 h-4" />
            Execute
          </button>
          <button
            onClick={() => onEdit?.(agent)}
            className="flex items-center gap-2 px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors"
          >
            <Edit className="w-4 h-4" />
            Edit
          </button>
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

      {/* Status Badge */}
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${getStatusColor(agent.status)}`}>
        <Zap className="w-4 h-4" />
        <span className="text-sm font-medium capitalize">{agent.status}</span>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-card border border-border rounded-lg">
                <p className="text-sm text-muted-foreground">Total Tasks</p>
                <p className="text-2xl font-bold">{agent.task_count}</p>
              </div>
              <div className="p-4 bg-card border border-border rounded-lg">
                <p className="text-sm text-muted-foreground">Successful</p>
                <p className="text-2xl font-bold text-green-500">{agent.success_count}</p>
              </div>
              <div className="p-4 bg-card border border-border rounded-lg">
                <p className="text-sm text-muted-foreground">Errors</p>
                <p className="text-2xl font-bold text-red-500">{agent.error_count}</p>
              </div>
              <div className="p-4 bg-card border border-border rounded-lg">
                <p className="text-sm text-muted-foreground">Avg Response</p>
                <p className="text-2xl font-bold">{agent.avg_response_time}ms</p>
              </div>
            </div>

            {/* Capabilities */}
            {agent.capabilities && agent.capabilities.length > 0 && (
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Capabilities</h3>
                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((cap) => (
                    <span key={cap} className="px-2 py-1 bg-primary/10 text-primary rounded text-sm">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Specializations */}
            {agent.specializations && agent.specializations.length > 0 && (
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Specializations</h3>
                <div className="flex flex-wrap gap-2">
                  {agent.specializations.map((spec) => (
                    <span key={spec} className="px-2 py-1 bg-blue-500/10 text-blue-500 rounded text-sm">
                      {spec}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Memory */}
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="font-semibold mb-3">Memory Configuration</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Enabled</span>
                  <span className="text-sm font-medium">{agent.memory_enabled ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Type</span>
                  <span className="text-sm font-medium capitalize">{agent.memory_type}</span>
                </div>
              </div>
            </div>

            {/* Tools */}
            {agent.tool_ids && agent.tool_ids.length > 0 && (
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Tools ({agent.tool_ids.length})</h3>
                <div className="flex flex-wrap gap-2">
                  {agent.tool_ids.map((toolId) => (
                    <span key={toolId} className="px-2 py-1 bg-purple-500/10 text-purple-500 rounded text-sm">
                      Tool #{toolId}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'configuration' && (
          <div className="space-y-4">
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="font-semibold mb-3">Model Configuration</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Model</span>
                  <span className="text-sm font-medium">{agent.model}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Temperature</span>
                  <span className="text-sm font-medium">{agent.temperature}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Max Tokens</span>
                  <span className="text-sm font-medium">{agent.max_tokens}</span>
                </div>
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="font-semibold mb-3">System Prompt</h3>
              <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
                {agent.system_prompt}
              </pre>
            </div>

            {agent.personality && (
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Personality</h3>
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                  {JSON.stringify(agent.personality, null, 2)}
                </pre>
              </div>
            )}

            {agent.behavior_rules && (
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Behavior Rules</h3>
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                  {JSON.stringify(agent.behavior_rules, null, 2)}
                </pre>
              </div>
            )}

            {agent.constraints && (
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="font-semibold mb-3">Constraints</h3>
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                  {JSON.stringify(agent.constraints, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {activeTab === 'executions' && (
          <div className="space-y-4">
            {executions.length > 0 ? (
              <div className="divide-y divide-border">
                {executions.map((execution) => (
                  <div key={execution.uuid} className="p-4 bg-card border border-border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium line-clamp-1">{execution.user_request}</p>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${getStatusColor(execution.status)}`}>
                        {execution.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span>{new Date(execution.created_at).toLocaleString()}</span>
                      <span>{execution.task_count} tasks</span>
                    </div>
                    {execution.execution_time_seconds && (
                      <div className="mt-2 text-sm text-muted-foreground">
                        Duration: {execution.execution_time_seconds.toFixed(2)}s
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No executions yet</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
