/**
 * React Query hooks for Voice Intelligence System API.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from './api'

export interface TranscriptionRequest {
  language?: string
  detect_language?: boolean
  stream?: boolean
}

export interface TranscriptionResponse {
  text: string
  language?: string
  confidence: number
  duration: number
  segments: any[]
  partial: boolean
}

export interface SynthesisRequest {
  text: string
  voice?: string
  speed?: number
  pitch?: number
  format?: string
}

export interface SynthesisResponse {
  audio_data: string
  format: string
  sample_rate: number
  duration: number
  voice: string
}

export interface ChatRequest {
  conversation_id?: string
  text?: string
  voice?: string
  mode?: string
}

export interface ChatResponse {
  conversation_id: string
  user_text: string
  assistant_text: string
  audio_data?: string
  transcription_confidence?: number
  processing_time: number
}

export interface VoiceConversationResponse {
  id: number
  uuid: string
  mode: string
  status: string
  message_count: number
  total_audio_duration: number
  started_at: string
  ended_at?: string
}

export interface VoiceSettingsResponse {
  voice_profile: string
  speed: number
  pitch: number
  language: string
  detect_language: boolean
  wake_word_enabled: boolean
  wake_word_phrase: string
  wake_word_sensitivity: number
  input_device_id?: string
  output_device_id?: string
  default_mode: string
  save_recordings: boolean
  auto_transcribe: boolean
}

// Transcribe audio
export function useTranscribe() {
  return useMutation({
    mutationFn: async (data: { file: File; request: TranscriptionRequest }) => {
      const formData = new FormData()
      formData.append('file', data.file)
      if (data.request.language) formData.append('language', data.request.language)
      formData.append('detect_language', String(data.request.detect_language ?? true))
      formData.append('stream', String(data.request.stream ?? false))
      
      const response = await apiRequest<TranscriptionResponse>('/api/v1/voice/transcribe', {
        method: 'POST',
        body: formData,
      })
      return response
    },
  })
}

// Synthesize speech
export function useSynthesize() {
  return useMutation({
    mutationFn: async (request: SynthesisRequest) => {
      const params = new URLSearchParams()
      params.append('text', request.text)
      if (request.voice) params.append('voice', request.voice)
      if (request.speed) params.append('speed', String(request.speed))
      if (request.pitch) params.append('pitch', String(request.pitch))
      if (request.format) params.append('format', request.format)
      
      const response = await apiRequest<SynthesisResponse>(`/api/v1/voice/speak?${params}`, {
        method: 'POST',
      })
      return response
    },
  })
}

// Voice chat
export function useVoiceChat() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: { file?: File; request: ChatRequest }) => {
      const formData = new FormData()
      if (data.file) formData.append('file', data.file)
      if (data.request.text) formData.append('text', data.request.text)
      if (data.request.conversation_id) formData.append('conversation_id', data.request.conversation_id)
      if (data.request.voice) formData.append('voice', data.request.voice)
      formData.append('mode', data.request.mode || 'push_to_talk')
      
      const response = await apiRequest<ChatResponse>('/api/v1/voice/chat', {
        method: 'POST',
        body: formData,
      })
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['voice-history'] })
    },
  })
}

// Get voice history
export function useVoiceHistory() {
  return useQuery({
    queryKey: ['voice-history'],
    queryFn: async () => {
      const data = await apiRequest<VoiceConversationResponse[]>('/api/v1/voice/history')
      return data
    },
  })
}

// Get voice settings
export function useVoiceSettings() {
  return useQuery({
    queryKey: ['voice-settings'],
    queryFn: async () => {
      const data = await apiRequest<VoiceSettingsResponse>('/api/v1/voice/settings')
      return data
    },
  })
}

// Update voice settings
export function useUpdateVoiceSettings() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (settings: Partial<VoiceSettingsResponse>) => {
      const params = new URLSearchParams()
      Object.entries(settings).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, String(value))
        }
      })
      
      const data = await apiRequest<VoiceSettingsResponse>(`/api/v1/voice/settings?${params}`, {
        method: 'PATCH',
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['voice-settings'] })
    },
  })
}
