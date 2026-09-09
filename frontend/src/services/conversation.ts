import { apiRequest } from './api'

export interface Message {
  id: number
  uuid: string
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Conversation {
  id: number
  uuid: string
  user_id: number
  title: string
  description: string | null
  agent_id: number | null
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

export interface MessageCreate {
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: Record<string, unknown>
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

  static async getMessages(conversationId: number): Promise<Message[]> {
    return apiRequest<Message[]>(`${this.BASE_PATH}/${conversationId}/messages`)
  }

  static async createMessage(conversationId: number, request: Omit<MessageCreate, 'conversation_id'>): Promise<Message> {
    return apiRequest<Message>(`${this.BASE_PATH}/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ ...request, conversation_id: conversationId }),
    })
  }
}
