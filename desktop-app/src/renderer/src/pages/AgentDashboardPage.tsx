/**
 * Agent Monitoring Dashboard
 * Displays real-time status of all agents and execution plans.
 */
import { useState } from 'react'
import { useAgentStatus, useAgentCapabilities, useExecutionPlans, useExecuteAgent, useCancelExecutionPlan } from '../services/agent-hooks'
import { Activity, Cpu, Brain, Code, Database, Wrench, Eye, Loader2, Play, X, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

export default function AgentDashboardPage() {
  const [requestInput, setRequestInput] = useState('')
  const { data: agentStatus, isLoading: statusLoading } = useAgentStatus()
  const { data: agentCapabilities, isLoading: capabilitiesLoading } = useAgentCapabilities()
  const { data: executionPlans, isLoading: plansLoading, refetch: refetchPlans } = useExecutionPlans()
  const executeAgent = useExecuteAgent()
  const cancelExecution = useCancelExecutionPlan()
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  const handleExecute = async () => {
    if (!requestInput.trim()) return
    
    await executeAgent.mutateAsync({
      request: requestInput,
      enable_reflection: true,
    })
    
    setRequestInput('')
    refetchPlans()
  }

  const handleCancel = async (planUuid: string) => {
    await cancelExecution.mutateAsync(planUuid)
    refetchPlans()
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  const getAgentIcon = (role: string) => {
    switch (role) {
      case 'planner':
        return <Activity className="h-5 w-5" />
      case 'orchestrator':
        return <Cpu className="h-5 w-5" />
      case 'research':
        return <Brain className="h-5 w-5" />
      case 'coding':
        return <Code className="h-5 w-5" />
      case 'memory':
        return <Database className="h-5 w-5" />
      case 'tool':
        return <Wrench className="h-5 w-5" />
      case 'reflection':
        return <Eye className="h-5 w-5" />
      default:
        return <Activity className="h-5 w-5" />
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Agent Dashboard</h1>
        <p className="mt-2 text-muted-foreground">Monitor and control multi-agent execution</p>
      </div>

      {/* Execute Request */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Execute Agent Request</h2>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Enter your request..."
            value={requestInput}
            onChange={(e) => setRequestInput(e.target.value)}
            className="flex-1 px-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
          />
          <button
            onClick={handleExecute}
            disabled={executeAgent.isPending || !requestInput.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {executeAgent.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Execute
          </button>
        </div>
      </div>

      {/* Agent Status */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Agent Status</h2>
        {statusLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {agentStatus && Object.entries(agentStatus).map(([role, status]) => (
              <div key={role} className="p-4 bg-muted/50 rounded-lg border border-border">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    {getAgentIcon(role)}
                  </div>
                  <div>
                    <h3 className="font-medium text-foreground capitalize">{role}</h3>
                    <p className="text-xs text-muted-foreground">{status.agent_id}</p>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  {status.active_tasks !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Active Tasks</span>
                      <span className="text-foreground">{status.active_tasks}</span>
                    </div>
                  )}
                  {status.completed_tasks !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Completed</span>
                      <span className="text-foreground">{status.completed_tasks}</span>
                    </div>
                  )}
                  {status.failed_tasks !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Failed</span>
                      <span className="text-foreground">{status.failed_tasks}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Execution Plans */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Execution Plans</h2>
        {plansLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !executionPlans || executionPlans.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No execution plans yet
          </div>
        ) : (
          <div className="space-y-3">
            {executionPlans.map((plan) => (
              <div
                key={plan.uuid}
                className="p-4 bg-muted/30 rounded-lg border border-border hover:bg-muted/50 transition-colors cursor-pointer"
                onClick={() => setSelectedPlan(plan.uuid)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {getStatusIcon(plan.status)}
                      <h3 className="font-medium text-foreground line-clamp-1">
                        {plan.user_request}
                      </h3>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{plan.task_count} tasks</span>
                      <span>•</span>
                      <span>{plan.estimated_duration_seconds}s estimated</span>
                      {plan.execution_time_seconds && (
                        <>
                          <span>•</span>
                          <span>{plan.execution_time_seconds.toFixed(2)}s actual</span>
                        </>
                      )}
                    </div>
                  </div>
                  {plan.status === 'running' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleCancel(plan.uuid)
                      }}
                      className="p-2 hover:bg-destructive hover:text-destructive-foreground rounded-md transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Agent Capabilities */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Agent Capabilities</h2>
        {capabilitiesLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agentCapabilities && Object.entries(agentCapabilities).map(([role, caps]) => (
              <div key={role} className="p-4 bg-muted/30 rounded-lg border border-border">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    {getAgentIcon(role)}
                  </div>
                  <h3 className="font-medium text-foreground capitalize">{role}</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {caps.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="px-2 py-1 text-xs bg-primary/10 text-primary rounded"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
