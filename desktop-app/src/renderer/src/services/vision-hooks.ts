/**
 * React Query hooks for Vision Intelligence System API.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from './api'

export interface VisionAnalyzeRequest {
  task_types: string[]
  target_size?: [number, number]
  options?: Record<string, any>
}

export interface OCRRequest {
  language?: string
  preserve_layout?: boolean
  config?: string
}

export interface ScreenshotAnalysisRequest {
  detect_ui_elements?: boolean
  detect_errors?: boolean
  options?: Record<string, any>
}

export interface DocumentVisionRequest {
  perform_ocr?: boolean
  ocr_language?: string
  extract_images?: boolean
  extract_tables?: boolean
  page_numbers?: number[]
  options?: Record<string, any>
}

export interface VisionAnalysisResponse {
  uuid: string
  analysis_type: string
  status: string
  caption?: string
  objects_detected?: any[]
  scene_description?: string
  ocr_text?: string
  ocr_confidence?: number
  ocr_blocks?: any[]
  screenshot_analysis?: any
  tables_extracted?: any[]
  forms_extracted?: any[]
  reasoning?: string
  processing_time_seconds?: number
  model_used?: string
  overall_confidence?: number
  error_message?: string
  created_at: string
  completed_at?: string
}

export interface OCRResponse {
  text: string
  confidence: number
  blocks: any[]
  language?: string
  layout?: any
}

export interface ScreenshotAnalysisResponse {
  window_title?: string
  application_type?: string
  ui_elements: any[]
  error_dialogs: any[]
  description: string
}

export interface DocumentVisionResponse {
  uuid: string
  status: string
  page_count: number
  pages: any[]
  tables: any[]
  forms: any[]
  images: any[]
  processing_time_seconds?: number
  error_message?: string
  created_at: string
  completed_at?: string
}

export interface VisionHistoryResponse {
  id: number
  uuid: string
  analysis_type: string
  status: string
  image_metadata?: any
  caption?: string
  processing_time_seconds?: number
  overall_confidence?: number
  error_message?: string
  created_at: string
  completed_at?: string
}

// Analyze image
export function useAnalyzeImage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: { file: File; request: VisionAnalyzeRequest }) => {
      const formData = new FormData()
      formData.append('file', data.file)
      formData.append('task_types', JSON.stringify(data.request.task_types))
      if (data.request.options) {
        formData.append('options', JSON.stringify(data.request.options))
      }
      
      const response = await apiRequest<VisionAnalysisResponse>('/api/v1/vision/analyze', {
        method: 'POST',
        body: formData,
      })
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vision-history'] })
    },
  })
}

// Perform OCR
export function usePerformOCR() {
  return useMutation({
    mutationFn: async (data: { file: File; request: OCRRequest }) => {
      const formData = new FormData()
      formData.append('file', data.file)
      if (data.request.language) formData.append('language', data.request.language)
      formData.append('preserve_layout', String(data.request.preserve_layout ?? true))
      if (data.request.config) formData.append('config', data.request.config)
      
      const response = await apiRequest<OCRResponse>('/api/v1/vision/ocr', {
        method: 'POST',
        body: formData,
      })
      return response
    },
  })
}

// Analyze screenshot
export function useAnalyzeScreenshot() {
  return useMutation({
    mutationFn: async (data: { file: File; request: ScreenshotAnalysisRequest }) => {
      const formData = new FormData()
      formData.append('file', data.file)
      formData.append('detect_ui_elements', String(data.request.detect_ui_elements ?? true))
      formData.append('detect_errors', String(data.request.detect_errors ?? true))
      if (data.request.options) {
        formData.append('options', JSON.stringify(data.request.options))
      }
      
      const response = await apiRequest<ScreenshotAnalysisResponse>('/api/v1/vision/screenshot', {
        method: 'POST',
        body: formData,
      })
      return response
    },
  })
}

// Process document
export function useProcessDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: { file: File; request: DocumentVisionRequest }) => {
      const formData = new FormData()
      formData.append('file', data.file)
      formData.append('perform_ocr', String(data.request.perform_ocr ?? false))
      if (data.request.ocr_language) formData.append('ocr_language', data.request.ocr_language)
      formData.append('extract_images', String(data.request.extract_images ?? false))
      formData.append('extract_tables', String(data.request.extract_tables ?? false))
      if (data.request.page_numbers) {
        formData.append('page_numbers', JSON.stringify(data.request.page_numbers))
      }
      if (data.request.options) {
        formData.append('options', JSON.stringify(data.request.options))
      }
      
      const response = await apiRequest<DocumentVisionResponse>('/api/v1/vision/document', {
        method: 'POST',
        body: formData,
      })
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vision-history'] })
    },
  })
}

// Get vision history
export function useVisionHistory(analysisType?: string) {
  return useQuery({
    queryKey: ['vision-history', analysisType],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (analysisType) params.append('analysis_type', analysisType)
      
      const data = await apiRequest<VisionHistoryResponse[]>(`/api/v1/vision/history?${params}`)
      return data
    },
  })
}

// Get specific vision analysis
export function useVisionAnalysis(analysisUuid: string) {
  return useQuery({
    queryKey: ['vision-analysis', analysisUuid],
    queryFn: async () => {
      const data = await apiRequest<VisionAnalysisResponse>(`/api/v1/vision/history/${analysisUuid}`)
      return data
    },
    enabled: !!analysisUuid,
  })
}
