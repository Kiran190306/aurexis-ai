import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, Loader2 } from 'lucide-react'
import { KnowledgeService, DocumentUploadRequest, KnowledgeDocument } from '../../services/knowledge'
import { TaskService } from '../../services/tasks'
import { useTaskPolling } from '../../hooks/useTaskPolling'
import toast from 'react-hot-toast'

interface DocumentUploadProps {
  onUploadComplete?: (document: KnowledgeDocument) => void
  onCancel?: () => void
}

export function DocumentUpload({ onUploadComplete, onCancel }: DocumentUploadProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [chunkingStrategy, setChunkingStrategy] = useState('semantic')
  const [chunkSize, setChunkSize] = useState(500)
  const [chunkOverlap, setChunkOverlap] = useState(50)
  const [embeddingProvider, setEmbeddingProvider] = useState('BAAI_BGE')
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)

  const { startPolling, stopPolling, isLoading: isTaskProcessing } = useTaskPolling({
    onSuccess: (result) => {
      toast.success('Document processing completed')
      setIsUploading(false)
      setTaskId(null)
      onUploadComplete?.(result as KnowledgeDocument)
    },
    onFailure: (error) => {
      toast.error(`Document processing failed: ${error}`)
      setIsUploading(false)
      setTaskId(null)
    }
  })

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/markdown': ['.md'],
      'text/plain': ['.txt'],
      'text/html': ['.html'],
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'application/xml': ['.xml'],
      'application/zip': ['.zip'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0])
        if (!title) {
          setTitle(acceptedFiles[0].name.replace(/\.[^/.]+$/, ''))
        }
      }
    },
  })

  const handleUpload = async () => {
    if (!file || !title) {
      toast.error('Please select a file and enter a title')
      return
    }

    setIsUploading(true)

    try {
      const request: DocumentUploadRequest = {
        file,
        title,
        description: description || undefined,
        chunking_strategy: chunkingStrategy,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
        embedding_provider: embeddingProvider,
      }

      const response = await KnowledgeService.uploadDocument(request)
      
      // Check if response contains task_id (async response)
      const responseAny = response as unknown
      if (responseAny && typeof responseAny === 'object' && 'task_id' in responseAny) {
        const asyncResponse = responseAny as { document_id: string; task_id: string; status: string; message: string }
        setTaskId(asyncResponse.task_id)
        startPolling(asyncResponse.task_id)
        toast.success(asyncResponse.message)
      } else {
        // Synchronous response (fallback)
        toast.success('Document uploaded successfully')
        onUploadComplete?.(response)
        setIsUploading(false)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to upload document')
      setIsUploading(false)
    }
  }

  const handleCancelTask = async () => {
    if (taskId) {
      try {
        await TaskService.cancelTask(taskId)
        stopPolling()
        setIsUploading(false)
        setTaskId(null)
        toast.success('Task cancelled')
      } catch (error) {
        toast.error('Failed to cancel task')
      }
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Upload Document</h2>
        {onCancel && (
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* File Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="space-y-2">
            <FileText className="w-12 h-12 mx-auto text-blue-500" />
            <p className="font-medium">{file.name}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(file.size)}</p>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-12 h-12 mx-auto text-gray-400" />
            <p className="text-gray-600 dark:text-gray-400">
              Drag and drop a file here, or click to select
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500">
              PDF, DOCX, PPTX, MD, TXT, HTML, JSON, CSV, XML, ZIP
            </p>
          </div>
        )}
      </div>

      {/* Form Fields */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Title *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800"
            placeholder="Enter document title"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800"
            rows={3}
            placeholder="Enter document description (optional)"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Chunking Strategy</label>
            <select
              value={chunkingStrategy}
              onChange={(e) => setChunkingStrategy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800"
            >
              <option value="semantic">Semantic</option>
              <option value="recursive">Recursive</option>
              <option value="sliding_window">Sliding Window</option>
              <option value="parent_child">Parent/Child</option>
              <option value="adaptive">Adaptive</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Embedding Provider</label>
            <select
              value={embeddingProvider}
              onChange={(e) => setEmbeddingProvider(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800"
            >
              <option value="BAAI_BGE">BAAI BGE</option>
              <option value="MULTILINGUAL_E5">Multilingual E5</option>
              <option value="OPENAI">OpenAI</option>
              <option value="JINA">Jina</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Chunk Size</label>
            <input
              type="number"
              value={chunkSize}
              onChange={(e) => setChunkSize(parseInt(e.target.value) || 500)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800"
              min={100}
              max={2000}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Chunk Overlap</label>
            <input
              type="number"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(parseInt(e.target.value) || 50)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800"
              min={0}
              max={500}
            />
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      {isUploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              {isTaskProcessing ? 'Processing...' : 'Uploading...'}
            </span>
            {taskId && (
              <button
                onClick={handleCancelTask}
                className="text-red-500 hover:text-red-600 text-xs"
              >
                Cancel
              </button>
            )}
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300 animate-pulse"
              style={{ width: isTaskProcessing ? '75%' : '25%' }}
            />
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleUpload}
          disabled={!file || !title || isUploading}
          className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Upload Document
            </>
          )}
        </button>
        {onCancel && (
          <button
            onClick={onCancel}
            disabled={isUploading}
            className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}
