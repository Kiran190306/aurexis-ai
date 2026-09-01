import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from './api'

// Types
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  avatar_url?: string
  bio?: string
  timezone?: string
  language?: string
  theme?: string
  is_active: boolean
  is_verified: boolean
  role: string
  created_at: string
  updated_at: string
  last_login?: string
}

export interface Conversation {
  id: number
  user_id: number
  title: string
  description?: string
  model: string
  temperature: number
  max_tokens: number
  system_prompt?: string
  tags: string[]
  status: string
  message_count: number
  last_message_at?: string
  created_at: string
  updated_at: string
  deleted_at?: string
}

export interface Message {
  id: number
  conversation_id: number
  user_id: number
  role: string
  content: string
  message_type: string
  code_language?: string
  code_content?: string
  image_url?: string
  image_alt?: string
  file_id?: number
  tool_calls?: any[]
  tool_response?: any
  metadata?: any
  parent_message_id?: number
  is_edited: boolean
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface Agent {
  id: number
  user_id: number
  name: string
  description: string
  agent_type: string
  capabilities?: string[]
  specializations?: string[]
  system_prompt: string
  model: string
  temperature: number
  max_tokens: number
  tool_ids?: number[]
  plugin_ids?: number[]
  personality?: any
  behavior_rules?: any
  constraints?: any
  memory_enabled: boolean
  memory_type: string
  parent_agent_id?: number
  status: string
  created_at: string
  updated_at: string
  deleted_at?: string
}

export interface Memory {
  id: number
  user_id: number
  content: string
  summary?: string
  memory_type: string
  embedding?: any
  embedding_model: string
  tags?: string[]
  entities?: any
  metadata?: any
  importance_score: number
  conversation_id?: number
  message_id?: number
  status: string
  is_pinned: boolean
  access_count: number
  last_accessed?: string
  created_at: string
  updated_at: string
  deleted_at?: string
}

export interface Document {
  id: number
  user_id: number
  title: string
  description?: string
  document_type: string
  file_id?: number
  raw_content?: string
  processed_content?: string
  content_hash?: string
  metadata?: any
  author?: string
  language?: string
  chunk_size: number
  chunk_overlap: number
  embedding_model: string
  status: string
  is_public: boolean
  access_count: number
  indexed_at?: string
  created_at: string
  updated_at: string
  deleted_at?: string
}

export interface Tool {
  id: number
  user_id: number
  name: string
  display_name: string
  description: string
  tool_type: string
  config_schema?: any
  config?: any
  parameters?: any
  execution_type: string
  endpoint?: string
  method: string
  headers?: any
  authentication?: any
  code?: string
  language?: string
  plugin_id?: number
  required_permissions?: string[]
  sandbox_enabled: boolean
  status: string
  created_at: string
  updated_at: string
  deleted_at?: string
}

export interface UserSettings {
  id: number
  user_id: number
  default_model?: string
  default_temperature?: number
  default_max_tokens?: number
  enable_streaming?: boolean
  memory_retention_days?: number
  enable_long_term_memory?: boolean
  enable_short_term_memory?: boolean
  enable_browse?: boolean
  enable_terminal?: boolean
  enable_github?: boolean
  enable_voice?: boolean
  enable_image?: boolean
  enable_document?: boolean
  enable_calendar?: boolean
  email_notifications?: boolean
  push_notifications?: boolean
  sms_notifications?: boolean
  notification_frequency?: string
  data_sharing_enabled?: boolean
  analytics_enabled?: boolean
  created_at: string
  updated_at: string
}

// Auth Hooks
export function useLogin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const data = await apiRequest<{ access_token: string; refresh_token: string }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      return data
    },
    onSuccess: (data) => {
      // Store tokens
      localStorage.setItem('jarvis-access-token', data.access_token)
      localStorage.setItem('jarvis-refresh-token', data.refresh_token)
      // Invalidate user queries
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: async ({ email, username, password, full_name }: { 
      email: string
      username: string
      password: string
      full_name?: string
    }) => {
      const data = await apiRequest<User>('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, username, password, full_name }),
      })
      return data
    },
  })
}

export function useRefreshToken() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (refreshToken: string) => {
      const data = await apiRequest<{ access_token: string; refresh_token: string }>('/api/v1/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token }),
      })
      return data
    },
    onSuccess: (data) => {
      localStorage.setItem('jarvis-access-token', data.access_token)
      localStorage.setItem('jarvis-refresh-token', data.refresh_token)
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      await apiRequest('/api/v1/auth/logout', { method: 'POST' })
    },
    onSuccess: () => {
      localStorage.removeItem('jarvis-access-token')
      localStorage.removeItem('jarvis-refresh-token')
      sessionStorage.removeItem('jarvis-auth-user')
      queryClient.clear()
    },
  })
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const data = await apiRequest<User>('/api/v1/auth/me')
      return data
    },
    retry: false,
  })
}

// Conversation Hooks
export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const data = await apiRequest<Conversation[]>('/api/v1/conversations')
      return data
    },
  })
}

export function useConversation(id: number) {
  return useQuery({
    queryKey: ['conversation', id],
    queryFn: async () => {
      const data = await apiRequest<Conversation>(`/api/v1/conversations/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateConversation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: {
      title: string
      description?: string
      model?: string
      temperature?: number
      max_tokens?: number
      system_prompt?: string
      tags?: string[]
    }) => {
      const result = await apiRequest<Conversation>('/api/v1/conversations', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
}

export function useUpdateConversation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Conversation> }) => {
      const result = await apiRequest<Conversation>(`/api/v1/conversations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['conversation', variables.id] })
    },
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      await apiRequest(`/api/v1/conversations/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
}

// Message Hooks
export function useMessages(conversationId: number) {
  return useQuery({
    queryKey: ['messages', conversationId],
    queryFn: async () => {
      const data = await apiRequest<Message[]>(`/api/v1/messages/conversation/${conversationId}`)
      return data
    },
    enabled: !!conversationId,
  })
}

export function useCreateMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: {
      conversation_id: number
      role: string
      content: string
      message_type?: string
      code_language?: string
      code_content?: string
      image_url?: string
      image_alt?: string
      file_id?: number
      tool_calls?: any[]
      tool_response?: any
      metadata?: any
      parent_message_id?: number
    }) => {
      const result = await apiRequest<Message>('/api/v1/messages', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['messages', variables.conversation_id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
}

// Agent Hooks
export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const data = await apiRequest<Agent[]>('/api/v1/agents')
      return data
    },
  })
}

export function useAgent(id: number) {
  return useQuery({
    queryKey: ['agent', id],
    queryFn: async () => {
      const data = await apiRequest<Agent>(`/api/v1/agents/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateAgent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: {
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
      personality?: any
      behavior_rules?: any
      constraints?: any
      memory_enabled?: boolean
      memory_type?: string
      parent_agent_id?: number
    }) => {
      const result = await apiRequest<Agent>('/api/v1/agents', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}

export function useUpdateAgent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Agent> }) => {
      const result = await apiRequest<Agent>(`/api/v1/agents/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      queryClient.invalidateQueries({ queryKey: ['agent', variables.id] })
    },
  })
}

export function useDeleteAgent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      await apiRequest(`/api/v1/agents/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}

// Memory Hooks
export function useMemories() {
  return useQuery({
    queryKey: ['memories'],
    queryFn: async () => {
      const data = await apiRequest<Memory[]>('/api/v1/memory')
      return data
    },
  })
}

export function useMemory(id: number) {
  return useQuery({
    queryKey: ['memory', id],
    queryFn: async () => {
      const data = await apiRequest<Memory>(`/api/v1/memory/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useSearchMemories(query: string) {
  return useQuery({
    queryKey: ['memories', 'search', query],
    queryFn: async () => {
      const data = await apiRequest<Memory[]>(`/api/v1/memory/search/${encodeURIComponent(query)}`)
      return data
    },
    enabled: !!query && query.length >
 2,
  })
}

export function useCreateMemory() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: {
      content: string
      summary?: string
      memory_type?: string
      embedding?: any
      embedding_model?: string
      tags?: string[]
      entities?: any
      metadata?: any
      importance_score?: number
      conversation_id?: number
      message_id?: number
    }) => {
      const result = await apiRequest<Memory>('/api/v1/memory', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
    },
  })
}

export function useUpdateMemory() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Memory> }) => {
      const result = await apiRequest<Memory>(`/api/v1/memory/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
      queryClient.invalidateQueries({ queryKey: ['memory', variables.id] })
    },
  })
}

export function useDeleteMemory() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      await apiRequest(`/api/v1/memory/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
    },
  })
}

// Document Hooks
export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const data = await apiRequest<Document[]>('/api/v1/documents')
      return data
    },
  })
}

export function useDocument(id: number) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const data = await apiRequest<Document>(`/api/v1/documents/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: {
      title: string
      description?: string
      document_type: string
      file_id?: number
      raw_content?: string
      processed_content?: string
      content_hash?: string
      metadata?: any
      author?: string
      language?: string
      chunk_size?: number
      chunk_overlap?: number
      embedding_model?: string
    }) => {
      const result = await apiRequest<Document>('/api/v1/documents', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useUpdateDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Document> }) => {
      const result = await apiRequest<Document>(`/api/v1/documents/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['document', variables.id] })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      await apiRequest(`/api/v1/documents/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useIndexDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      await apiRequest(`/api/v1/documents/${id}/index`, { method: 'POST' })
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['document', variables.id] })
    },
  })
}

// Tool Hooks
export function useTools() {
  return useQuery({
    queryKey: ['tools'],
    queryFn: async () => {
      const data = await apiRequest<Tool[]>('/api/v1/tools')
      return data
    },
  })
}

export function useTool(id: number) {
  return useQuery({
    queryKey: ['tool', id],
    queryFn: async () => {
      const data = await apiRequest<Tool>(`/api/v1/tools/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateTool() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: {
      name: string
      display_name: string
      description: string
      tool_type?: string
      config_schema?: any
      config?: any
      parameters?: any
      execution_type?: string
      endpoint?: string
      method?: string
      headers?: any
      authentication?: any
      code?: string
      language?: string
      plugin_id?: number
      required_permissions?: string[]
      sandbox_enabled?: boolean
    }) => {
      const result = await apiRequest<Tool>('/api/v1/tools', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}

export function useUpdateTool() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Tool> }) => {
      const result = await apiRequest<Tool>(`/api/v1/tools/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tools'] })
      queryClient.invalidateQueries({ queryKey: ['tool', variables.id] })
    },
  })
}

export function useDeleteTool() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      await apiRequest(`/api/v1/tools/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}

// User Settings Hooks
export function useUserSettings() {
  return useQuery({
    queryKey: ['user-settings'],
    queryFn: async () => {
      const data = await apiRequest<UserSettings>('/api/v1/users/me/settings')
      return data
    },
  })
}

export function useUpdateUserSettings() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: Partial<UserSettings>) => {
      const result = await apiRequest<UserSettings>('/api/v1/users/me/settings', {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-settings'] })
    },
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: {
      full_name?: string
      bio?: string
      avatar_url?: string
      timezone?: string
      language?: string
      theme?: string
    }) => {
      const result = await apiRequest<User>('/api/v1/users/me', {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })
}
