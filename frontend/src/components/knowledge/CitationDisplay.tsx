import { FileText } from 'lucide-react'

interface Citation {
  document_uuid: string
  document_title: string
  chunk_index: number
  page_number?: number
  text: string
}

interface CitationDisplayProps {
  citations: Citation[]
}

export function CitationDisplay({ citations }: CitationDisplayProps) {
  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="space-y-2">
      {citations.map((citation, index) => (
        <div
          key={`${citation.document_uuid}-${citation.chunk_index}-${index}`}
          className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <div className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
            {index + 1}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
              <span className="font-medium text-sm truncate">{citation.document_title}</span>
            </div>
            
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
              <span>Chunk {citation.chunk_index}</span>
              {citation.page_number && (
                <>
                  <span>•</span>
                  <span>Page {citation.page_number}</span>
                </>
              )}
            </div>
            
            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
              {truncateText(citation.text, 150)}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
