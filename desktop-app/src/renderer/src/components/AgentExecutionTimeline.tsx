/**
 * Agent Execution Timeline Component
 * Visualizes the execution flow of agents in a plan.
 */
import { useExecutionLogs } from '../services/agent-hooks'
import { Clock, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface AgentExecutionTimelineProps {
  planUuid: string
}

export default function AgentExecutionTimeline({ planUuid }: AgentExecutionTimelineProps) {
  const { data: logs, isLoading } = useExecutionLogs(planUuid)

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

  const getAgentColor = (agentRole: string) => {
    switch (agentRole) {
      case 'planner':
        return 'bg-purple-500'
      case 'orchestrator':
        return 'bg-blue-500'
      case 'research':
        return 'bg-green-500'
      case 'coding':
        return 'bg-orange-500'
      case 'memory':
        return 'bg-cyan-500'
      case 'tool':
        return 'bg-pink-500'
      case 'reflection':
        return 'bg-indigo-500'
      default:
        return 'bg-gray-500'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!logs || logs.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No execution logs available
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-foreground">Execution Timeline</h3>
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
        
        {/* Timeline items */}
        <div className="space-y-4">
          {logs.map((log, index) => (
            <div key={log.uuid} className="relative pl-10">
              {/* Timeline dot */}
              <div className={`absolute left-2.5 top-1.5 w-3 h-3 rounded-full ${getAgentColor(log.agent_role)} border-2 border-background`} />
              
              {/* Timeline content */}
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(log.status)}
                    <div>
                      <h4 className="font-medium text-foreground">{log.task_type}</h4>
                      <p className="text-sm text-muted-foreground capitalize">{log.agent_role} agent</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                    </p>
                    {log.execution_time_seconds && (
                      <p className="text-xs text-muted-foreground">
                        {log.execution_time_seconds.toFixed(2)}s
                      </p>
                    )}
                  </div>
                </div>
                
                {log.error_message && (
                  <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                    <p className="text-sm text-destructive">{log.error_message}</p>
                  </div>
                )}
                
                {log.retry_count > 0 && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="h-3 w-3" />
                    <span>Retried {log.retry_count} times</span>
                  </div>
                )}
                
                {log.depends_on && log.depends_on.length > 0 && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Dependencies:</span>
                    {log.depends_on.map((dep, i) => (
                      <span key={dep} className="px-2 py-0.5 bg-muted rounded">
                        {dep}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Arrow to next item */}
              {index < logs.length - 1 && (
                <div className="flex justify-center -my-2 relative z-10">
                  <div className="bg-background p-1">
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Summary */}
      <div className="bg-muted/30 rounded-lg p-4 border border-border">
        <h4 className="font-medium text-foreground mb-2">Execution Summary</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Total Tasks</p>
            <p className="text-foreground font-medium">{logs.length}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Completed</p>
            <p className="text-foreground font-medium text-green-500">
              {logs.filter(l => l.status === 'completed').length}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Failed</p>
            <p className="text-foreground font-medium text-red-500">
              {logs.filter(l => l.status === 'failed').length}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Total Time</p>
            <p className="text-foreground font-medium">
              {logs.reduce((sum, log) => sum + (log.execution_time_seconds || 0), 0).toFixed(2)}s
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
