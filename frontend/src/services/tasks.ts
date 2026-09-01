import { apiRequest } from './api'

export interface TaskStatus {
  task_id: string
  status: string
  state: string
  result: unknown
  traceback?: string
  ready: boolean
  successful?: boolean
  failed?: boolean
}

export interface TaskResult {
  task_id: string
  status: string
  result: unknown
}

export class TaskService {
  private static readonly BASE_PATH = '/api/v1/tasks'

  static async getTaskStatus(taskId: string): Promise<TaskStatus> {
    return apiRequest<TaskStatus>(`${this.BASE_PATH}/${taskId}/status`)
  }

  static async getTaskResult(taskId: string): Promise<TaskResult> {
    return apiRequest<TaskResult>(`${this.BASE_PATH}/${taskId}/result`)
  }

  static async cancelTask(taskId: string): Promise<{ task_id: string; status: string; message: string }> {
    return apiRequest<{ task_id: string; status: string; message: string }>(
      `${this.BASE_PATH}/${taskId}/cancel`,
      { method: 'POST' }
    )
  }

  static async getWorkerStats(): Promise<{
    workers: Record<string, unknown>
    active_tasks: Record<string, unknown>
    registered_tasks: Record<string, unknown>
    worker_count: number
  }> {
    return apiRequest<{
      workers: Record<string, unknown>
      active_tasks: Record<string, unknown>
      registered_tasks: Record<string, unknown>
      worker_count: number
    }>(`${this.BASE_PATH}/stats`)
  }
}
