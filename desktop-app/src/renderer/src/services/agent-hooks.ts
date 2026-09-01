/**
 * React Query hooks for multi-agent execution API.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from './api'

export interface ExecutionRequest {
  request: string
  context?: Record<string, any>
  conversation_id?: number
  enable_reflection?: boolean
}

export interface ExecutionResponse {
  execution_plan_id: string
  status: string
  result?: Record<string, any>
  summary?: string
  execution_time_seconds?: number
  metadata?:_RECORD<string, any>
}

export interface ExecutionPlan {
  id: number
  uuid: string
  user_id: number
  conversation_id?: number
  user_request: string
  context?: Record<string, any>
  plan_data: Record<string, any>
  task_count: number
  estimated_duration_seconds: number
  status: string
  started_at?: string
  completed_at?: string
  execution_time_seconds?: number
  final_output?: Record<string, any>
  result_summary?: string
  error_message?: string
  metadata_json?: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface ExecutionLog {
  id: number
  uuid: string
  execution_plan_id: number
  agent_id?: number
  task_id: string
  task_type: string
  agent_role: string
  input_data?: Record<string, any>
  output_data?: Record<string, any>
  status: string
  started_at?: string
  completed_at?: string
  execution_time_seconds?: number
  retry_count: number
  timeout_seconds?: number
  error_message?: string
  error_code?: string
  depends_on?: string[]
  metadata_json?: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface AgentStatus {
  agent_id: string
  role: string
  config: Record<string, any>
  active_tasks?: number
  completed_tasks?: number
  failed_tasks?: number
  registered_agents?: number
}

export interface AgentCapabilities {
  capabilities: string[]
}

export interface EventBusStats {
  subscribers: number
  queue_size: number
  running: boolean
}

// Execute agent request
export function useExecuteAgent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (request: ExecutionRequest) => {
      const data = await apiRequest<ExecutionResponse>('/api/v1/agent-execution/execute', {
        method: 'POST',
        body: JSON.stringify(request),
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-plans'] })
    },
  })
}

// List execution plans
export function useExecutionPlans() {
  return useQuery({
    queryKey: ['execution-plans'],
    queryFn: async () => {
      const data = await apiRequest<ExecutionPlan[]>('/api/v1/agent-execution/plans')
      return data
    },
  })
}

// Get execution plan by UUID
export function useExecutionPlan(planUuid: string) {
  return useQuery({
    queryKey: ['execution-plan', planUuid],
    queryFn: async () => {
      const data = await apiRequest<ExecutionPlan>(`/api/v1/agent-execution/plans/${planUuid}`)
      return data
    },
    enabled: !!planUuid,
  })
}

// Get execution logs for a plan
export function useExecutionLogs(planUuid: string) {
  return useQuery({
    queryKey: ['execution-logs', planUuid],
    queryFn: async () => {
      const data = await apiRequest<ExecutionLog[]>(`/api/v1/agent-execution/plans/${planUuid}/logs`)
      return data
    },
    enabled: !!planUuid,
  })
}

// Cancel execution plan
export function useCancelExecutionPlan() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (planUuid: string) => {
      const data = await apiRequest<{ status: string }>(`/api/v1/agent-execution/plans/${planUuid}/cancel`, {
        method: 'POST',
      })
      return data
    },
    onSuccess: (_, planUuid) => {
      queryClient.invalidateQueries({ queryKey: ['execution-plan', planUuid] })
      queryClient.invalidateQueries({ queryKey: ['execution-plans'] })
    },
  })
}

// Get agent status
export function useAgentStatus() {
  return useQuery({
    queryKey: ['agent-status'],
    queryFn: async () => {
      const data = await apiRequest<Record<string, AgentStatus>>('/api/v1/agent-execution/agents/status')
      return data
    },
    refetchInterval: 5000, // Poll every 5 seconds
  })
}

// Get agent capabilities
export function useAgentCapabilities() {
  return useQuery({
    queryKey: ['agent-capabilities'],
    queryFn: async () => {
      const data = await apiRequest<Record<string, AgentCapabilities>>('/api/v1/agent-execution/agents/capabilities')
      return data
    },
  })
}
