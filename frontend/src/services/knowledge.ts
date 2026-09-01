import { apiRequest } from './api'

export interface KnowledgeDocument {
  id: number
  uuid: string
  user_id: number
  file_id?: number
  title: string
  description?: string
  document_type: string
  status: string
  file_name: string
  file_size: number
  file_path?: string
  raw_content?: string
  processed_content?: string
  checksum: string
  metadata_json?: Record<string, unknown>
  author?: string
  language?: string
  version: number
  parent_id?: number
  chunking_strategy: string
  chunk_size: number
  chunk_overlap: number
  embedding_provider: string
  total_chunks: number
  indexed_chunks: number
  created_at: string
  updated_at: string
  indexed_at?: string
}

export interface DocumentUploadRequest {
  file: File
  title: string
  description?: string
  chunking_strategy?: string
  chunk_size?: number
  chunk_overlap?: number
  embedding_provider?: string
}

export interface SearchRequest {
  query: string
  top_k?: number
  use_hybrid?: boolean
  use_reranking?: boolean
  filters?: Record<string, unknown>
}

export interface SearchResult {
  chunk_id: number
  document_uuid: string
  document_title: string
  chunk_text: string
  score: number
  metadata?: Record<string, unknown>
  citation?: {
    chunk_index: number
    page_number?: number
    start_char?: number
    end_char?: number
  }
}

export interface RAGQueryRequest {
  query: string
  top_k?: number
  use_hybrid?: boolean
  use_reranking?: boolean
  generate_answer?: boolean
}

export interface RAGQueryResponse {
  query: string
  context: string
  sources: SearchResult[]
  citations: Array<{
    document_uuid: string
    document_title: string
    chunk_index: number
    page_number?: number
    text: string
  }>
  answer?: string
  answer_generated: boolean
  model_used?: string
  tokens_used?: number
}

export class KnowledgeService {
  private static readonly BASE_PATH = '/api/v1/knowledge'

  static async uploadDocument(request: DocumentUploadRequest): Promise<KnowledgeDocument> {
    const formData = new FormData()
    formData.append('file', request.file)
    formData.append('title', request.title)
    if (request.description) {
      formData.append('description', request.description)
    }
    if (request.chunking_strategy) {
      formData.append('chunking_strategy', request.chunking_strategy)
    }
    if (request.chunk_size) {
      formData.append('chunk_size', request.chunk_size.toString())
    }
    if (request.chunk_overlap) {
      formData.append('chunk_overlap', request.chunk_overlap.toString())
    }
    if (request.embedding_provider) {
      formData.append('embedding_provider', request.embedding_provider)
    }

    return apiRequest<KnowledgeDocument>(`${this.BASE_PATH}/upload`, {
      method: 'POST',
      body: formData,
    })
  }

  static async indexDocument(documentUuid: string): Promise<KnowledgeDocument> {
    return apiRequest<KnowledgeDocument>(`${this.BASE_PATH}/index/${documentUuid}`, {
      method: 'POST',
    })
  }

  static async listDocuments(): Promise<KnowledgeDocument[]> {
    return apiRequest<KnowledgeDocument[]>(`${this.BASE_PATH}/documents`)
  }

  static async getDocument(documentUuid: string): Promise<KnowledgeDocument> {
    return apiRequest<KnowledgeDocument>(`${this.BASE_PATH}/documents/${documentUuid}`)
  }

  static async getDocumentStatus(documentUuid: string): Promise<{ status: string; indexed_chunks: number; total_chunks: number }> {
    return apiRequest<{ status: string; indexed_chunks: number; total_chunks: number }>(
      `${this.BASE_PATH}/documents/${documentUuid}/status`
    )
  }

  static async search(request: SearchRequest): Promise<SearchResult[]> {
    const formData = new FormData()
    formData.append('query', request.query)
    if (request.top_k) {
      formData.append('top_k', request.top_k.toString())
    }
    if (request.use_hybrid !== undefined) {
      formData.append('use_hybrid', request.use_hybrid.toString())
    }
    if (request.use_reranking !== undefined) {
      formData.append('use_reranking', request.use_reranking.toString())
    }
    if (request.filters) {
      formData.append('filters', JSON.stringify(request.filters))
    }

    return apiRequest<SearchResult[]>(`${this.BASE_PATH}/search`, {
      method: 'POST',
      body: formData,
    })
  }

  static async ragQuery(request: RAGQueryRequest): Promise<RAGQueryResponse> {
    const formData = new FormData()
    formData.append('query', request.query)
    if (request.top_k) {
      formData.append('top_k', request.top_k.toString())
    }
    if (request.use_hybrid !== undefined) {
      formData.append('use_hybrid', request.use_hybrid.toString())
    }
    if (request.use_reranking !== undefined) {
      formData.append('use_reranking', request.use_reranking.toString())
    }
    if (request.generate_answer !== undefined) {
      formData.append('generate_answer', request.generate_answer.toString())
    }

    return apiRequest<RAGQueryResponse>(`${this.BASE_PATH}/query`, {
      method: 'POST',
      body: formData,
    })
  }

  static async deleteDocument(documentUuid: string): Promise<void> {
    return apiRequest<void>(`${this.BASE_PATH}/documents/${documentUuid}`, {
      method: 'DELETE',
    })
  }
}
