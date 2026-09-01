import { apiRequest } from './api'

// Enums
export enum AgentType {
  GENERAL = 'general',
  SPECIALIST = 'specialist',
  ORCHESTRATOR = 'orchestrator',
  WORKER = 'worker',
}

export enum AgentStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  BUSY = 'busy',
  ERROR = 'error',
}

export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused',
}

// Base Types
export interface Agent {
  id: number
  uuid: string
  user_id: number
  name: string
  description: string
  avatar_url: string | null
  agent_type: AgentType
  status: AgentStatus
  capabilities: string[] | null
  specializations: string[] | null
  system_prompt: string
  model: string
  temperature: number
  max_tokens: number
  tool_ids: number[] | null
  plugin_ids: number[] | null
  personality: Record<string, unknown> | null
  behavior_rules: Record<string, unknown> | null
  constraints: Record<string, unknown> | null
  memory_enabled: boolean
  memory_type: string
  parent_agent_id: number | null
  task_count: number
  success_count: number
  error_count: number
  avg_response_time: number
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface AgentCreate {
  name: string
  description: string
  agent_type?: string
  capabilities?: string[]
  specializations?: string[]
  system_prompt: string
  model?: string
  temperature?: number
  max_tokens?: number
  tool_ids?: number[]
  plugin_ids?: number[]
  personality?: Record<string, unknown>
  behavior_rules?: Record<string, unknown>
  constraints?: Record<string, unknown>
  memory_enabled?: boolean
  memory_type?: string
  parent_agent_id?: number
}

export interface AgentUpdate {
  name?: string
  description?: string
  status?: string
  capabilities?: string[]
  specializations?: string[]
  system_prompt?: string
  model?: string
  temperature?: number
  max_tokens?: number
  tool_ids?: number[]
  plugin_ids?: number[]
  personality?: Record<string, unknown>
  behavior_rules?: Record<string, unknown>
  constraints?: Record<string, unknown>
  memory_enabled?: boolean
  memory_type?: string
}

export interface ExecutionPlan {
  id: number
  uuid: string
  user_id: number
  conversation_id: number | null
  user_request: string
  context: Record<string, unknown> | null
  plan_data: Record<string, unknown>
  task_count: number
  estimated_duration_seconds: number
  status: ExecutionStatus
  started_at: string | null
  completed_at: string | null
  execution_time_seconds: number | null
  final_output: Record<string, unknown> | null
  result_summary: string | null
  error_message: string | null
  metadata_json: Record<string, unknown> | null
  created_at: string
  updated_at: string | null
}

export interface ExecutionLog {
  id: number
  uuid: string
  execution_plan_id: number
  agent_id: number | null
  task_id: string
  task_type: string
  agent_role: string
  input_data: Record<string, unknown> | null
  output_data: Record<string, unknown> | null
  status: ExecutionStatus
  started_at: string | null
  completed_at: string | null
  execution_time_seconds: number | null
  retry_count: number
  timeout_seconds: number | null
  error_message: string | null
  error_code: string | null
  depends_on: string[] | null
  metadata_json: Record<string, unknown> | null
  created_at: string
  updated_at: string | null
}

export interface ExecutionRequest {
  request: string
  context?: Record<string, unknown>
  conversation_id?: number
  enable_reflection?: boolean
}

export interface ExecutionResponse {
  execution_plan_id: string
  status: string
  result: Record<string, unknown> | null
  summary: string | null
  execution_time_seconds: number | null
  metadata: Record<string, unknown> | null
}

export interface AgentStatusResponse {
  agent_id: string
  role: string
  config: Record<string, unknown>
  active_tasks: number | null
  completed_tasks: number | null
  failed_tasks: number | null
  registered_agents: number | null
}

export interface AgentCapabilitiesResponse {
  capabilities: string[]
}

export class AgentService {
  private static readonly BASE_PATH = '/api/v1/agents'
  private static readonly EXECUTION_BASE_PATH = '/api/v1/agent-execution'

  // ============================================================================
  // Agent CRUD Endpoints
  // ============================================================================

  static async listAgents(): Promise<Agent[]> {
    return apiRequest<Agent[]>(this.BASE_PATH)
  }

  static async createAgent(request: AgentCreate): Promise<Agent> {
    return apiRequest<Agent>(this.BASE_PATH, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getAgent(agentId: number): Promise<Agent> {
    return apiRequest<Agent>(`${this.BASE_PATH}/${agentId}`)
  }

  static async updateAgent(agentId: number, request: AgentUpdate): Promise<Agent> {
    return apiRequest<Agent>(`${this.BASE_PATH}/${agentId}`, {
      method: 'PATCH',
      body: JSON.stringify(request),
    })
  }

  static async deleteAgent(agentId: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`${this.BASE_PATH}/${agentId}`, {
      method: 'DELETE',
    })
  }

  // ============================================================================
  // Agent Execution Endpoints
  // ============================================================================

  static async executeAgent(request: ExecutionRequest): Promise<ExecutionResponse> {
    return apiRequest<ExecutionResponse>(`${this.EXECUTION_BASE_PATH}/execute`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async listExecutionPlans(skip: number = 0, limit: number = 100): Promise<ExecutionPlan[]> {
    return apiRequest<ExecutionPlan[]>(`${this.EXECUTION_BASE_PATH}/plans?skip=${skip}&limit=${limit}`)
  }

  static async getExecutionPlan(planUuid: string): Promise<ExecutionPlan> {
    return apiRequest<ExecutionPlan>(`${this.EXECUTION_BASE_PATH}/plans/${planUuid}`)
  }

  static async getExecutionLogs(planUuid: string): Promise<ExecutionLog[]> {
    return apiRequest<ExecutionLog[]>(`${this.EXECUTION_BASE_PATH}/plans/${planUuid}/logs`)
  }

  static async cancelExecutionPlan(planUuid: string): Promise<{ status: string; completed_at: string | null }> {
    return apiRequest<{ status: string; completed_at: string | null }>(
      `${this.EXECUTION_BASE_PATH}/plans/${planUuid}/cancel`,
      { method: 'POST' }
    )
  }

  static async getAgentsStatus(): Promise<Record<string, unknown>> {
    return apiRequest<Record<string, unknown>>(`${this.EXECUTION_BASE_PATH}/agents/status`)
  }

  static async getAgentsCapabilities(): Promise<Record<string, unknown>> {
    return apiRequest<Record<string, unknown>>(`${this.EXECUTION_BASE_PATH}/agents/capabilities`)
  }
}
