import { apiRequest } from './api'

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
  TOOL = 'tool',
}

export enum MessageType {
  TEXT = 'text',
  CODE = 'code',
  IMAGE = 'image',
  FILE = 'file',
  SYSTEM = 'system',
  TOOL_CALL = 'tool_call',
  TOOL_RESPONSE = 'tool_response',
}

export interface Message {
  id: number
  uuid: string
  conversation_id: number
  user_id: number
  role: MessageRole
  content: string
  message_type: MessageType
  code_language: string | null
  code_content: string | null
  image_url: string | null
  image_alt: string | null
  file_id: number | null
  tool_calls: Record<string, unknown>[] | null
  tool_response: Record<string, unknown> | null
  metadata_json: Record<string, unknown> | null
  parent_message_id: number | null
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  is_edited: boolean
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface MessageCreate {
  conversation_id: number
  role: MessageRole
  content: string
  message_type?: MessageType
  code_language?: string | null
  code_content?: string | null
  image_url?: string | null
  image_alt?: string | null
  file_id?: number | null
  tool_calls?: Record<string, unknown>[] | null
  tool_response?: Record<string, unknown> | null
  metadata?: Record<string, unknown> | null
  parent_message_id?: number | null
}

export interface MessageUpdate {
  content?: string
  is_edited?: boolean
  is_deleted?: boolean
}

export class MessageService {
  private static readonly BASE_PATH = '/api/v1/messages'

  static async listConversationMessages(conversationId: number): Promise<Message[]> {
    return apiRequest<Message[]>(`${this.BASE_PATH}/conversation/${conversationId}`)
  }

  static async createMessage(messageData: MessageCreate): Promise<Message> {
    return apiRequest<Message>(this.BASE_PATH, {
      method: 'POST',
      body: JSON.stringify(messageData),
    })
  }

  static async getMessage(messageId: number): Promise<Message> {
    return apiRequest<Message>(`${this.BASE_PATH}/${messageId}`)
  }

  static async updateMessage(messageId: number, messageData: MessageUpdate): Promise<Message> {
    return apiRequest<Message>(`${this.BASE_PATH}/${messageId}`, {
      method: 'PATCH',
      body: JSON.stringify(messageData),
    })
  }

  static async deleteMessage(messageId: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`${this.BASE_PATH}/${messageId}`, {
      method: 'DELETE',
    })
  }
}
