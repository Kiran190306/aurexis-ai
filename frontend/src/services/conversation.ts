import { apiRequest } from './api'

export interface Conversation {
  id: number
  uuid: string
  user_id: number
  title: string
  description: string | null
  agent_id: number | null
  model: string
  temperature: number
  max_tokens: number
  system_prompt: string | null
  tags: string[]
  is_active: boolean
  created_at: string
  updated_at: string
  message_count?: number
  last_message?: string
}

export interface ConversationCreate {
  title: string
  description?: string
  agent_id?: number
}

export class ConversationService {
  private static readonly BASE_PATH = '/api/v1/conversations'

  static async listConversations(): Promise<Conversation[]> {
    return apiRequest<Conversation[]>(this.BASE_PATH)
  }

  static async getConversation(conversationId: number): Promise<Conversation> {
    return apiRequest<Conversation>(`${this.BASE_PATH}/${conversationId}`)
  }

  static async createConversation(request: ConversationCreate): Promise<Conversation> {
    return apiRequest<Conversation>(this.BASE_PATH, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async updateConversation(conversationId: number, request: Partial<ConversationCreate>): Promise<Conversation> {
    return apiRequest<Conversation>(`${this.BASE_PATH}/${conversationId}`, {
      method: 'PATCH',
      body: JSON.stringify(request),
    })
  }

  static async deleteConversation(conversationId: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`${this.BASE_PATH}/${conversationId}`, {
      method: 'DELETE',
    })
  }
}
