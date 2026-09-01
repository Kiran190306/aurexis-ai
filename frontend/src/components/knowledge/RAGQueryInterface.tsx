import { useState } from 'react'
import { MessageSquare, Send, Loader2, AlertCircle, CheckCircle, Copy, Settings } from 'lucide-react'
import { KnowledgeService, RAGQueryRequest, RAGQueryResponse } from '../../services/knowledge'
import { CitationDisplay } from './CitationDisplay'
import toast from 'react-hot-toast'

interface RAGQueryInterfaceProps {
  onAnswerGenerated?: (response: RAGQueryResponse) => void
}

export function RAGQueryInterface({ onAnswerGenerated }: RAGQueryInterfaceProps) {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [useHybrid, setUseHybrid] = useState(true)
  const [useReranking, setUseReranking] = useState(true)
  const [generateAnswer, setGenerateAnswer] = useState(true)
  const [isQuerying, setIsQuerying] = useState(false)
  const [response, setResponse] = useState<RAGQueryResponse | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleQuery = async () => {
    if (!query.trim()) {
      toast.error('Please enter a question')
      return
    }

    setIsQuerying(true)
    setResponse(null)

    try {
      const request: RAGQueryRequest = {
        query: query.trim(),
        top_k: topK,
        use_hybrid: useHybrid,
        use_reranking: useReranking,
        generate_answer: generateAnswer,
      }

      const result = await KnowledgeService.ragQuery(request)
      setResponse(result)
      onAnswerGenerated?.(result)

      if (result.answer_generated) {
        toast.success('Answer generated successfully')
      } else {
        toast('Context retrieved (answer generation disabled or unavailable)')
      }
    } catch (error) {
      console.error('Query failed:', error)
      toast.error(error instanceof Error ? error.message : 'Query failed')
    } finally {
      setIsQuerying(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleQuery()
    }
  }

  const handleCopyAnswer = () => {
    if (response?.answer) {
      navigator.clipboard.writeText(response.answer)
      setCopied(true)
      toast.success('Answer copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleCopyContext = () => {
    if (response?.context) {
      navigator.clipboard.writeText(response.context)
      toast.success('Context copied to clipboard')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Ask Your Knowledge</h2>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          title="Advanced options"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Query Input */}
      <div className="relative">
        <MessageSquare className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your documents..."
          className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 resize-none"
          rows={3}
        />
        <button
          onClick={handleQuery}
          disabled={!query.trim() || isQuerying}
          className="absolute right-2 top-2 p-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white rounded-lg transition-colors"
        >
          {isQuerying ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Advanced Options */}
      {showAdvanced && (
        <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-4">
          <h3 className="font-semibold text-sm">Advanced Options</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Top K Results</label>
              <input
                type="number"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800"
                min={1}
                max={20}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="generateAnswer"
                checked={generateAnswer}
                onChange={(e) => setGenerateAnswer(e.target.checked)}
                className="w-4 h-4 text-blue-500 rounded focus:ring-blue-500"
              />
              <label htmlFor="generateAnswer" className="text-sm">Generate AI Answer</label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="useHybrid"
                checked={useHybrid}
                onChange={(e) => setUseHybrid(e.target.checked)}
                className="w-4 h-4 text-blue-500 rounded focus:ring-blue-500"
              />
              <label htmlFor="useHybrid" className="text-sm">Hybrid Search</label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="useReranking"
                checked={useReranking}
                onChange={(e) => setUseReranking(e.target.checked)}
                className="w-4 h-4 text-blue-500 rounded focus:ring-blue-500"
              />
              <label htmlFor="useReranking" className="text-sm">Reranking</label>
            </div>
          </div>
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="space-y-4">
          {/* Answer */}
          {response.answer_generated && response.answer && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <h3 className="font-semibold">AI Answer</h3>
                </div>
                <button
                  onClick={handleCopyAnswer}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="Copy answer"
                >
                  {copied ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <div className="prose dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{response.answer}</p>
              </div>
              {response.model_used && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
                  <span>Model: {response.model_used}</span>
                  {response.tokens_used && (
                    <>
                      <span> • </span>
                      <span>Tokens: {response.tokens_used}</span>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Context */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-500" />
                <h3 className="font-semibold">Retrieved Context</h3>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  ({response.sources.length} sources)
                </span>
              </div>
              <button
                onClick={handleCopyContext}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Copy context"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800 rounded p-3 max-h-64 overflow-y-auto">
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {response.context}
              </p>
            </div>
          </div>

          {/* Citations */}
          {response.citations && response.citations.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">Citations</h3>
              <CitationDisplay citations={response.citations} />
            </div>
          )}

          {/* Sources */}
          {response.sources && response.sources.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">Source Chunks</h3>
              <div className="space-y-2">
                {response.sources.map((source, index) => (
                  <div
                    key={`${source.chunk_id}-${index}`}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">{source.document_title}</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        Score: {(source.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {source.chunk_text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warning if answer not generated */}
          {!response.answer_generated && generateAnswer && (
            <div className="flex items-start gap-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-yellow-800 dark:text-yellow-200">Answer Not Generated</p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  The AI answer could not be generated. This may be due to an external service issue (e.g., OpenAI quota). 
                  However, the context and sources were successfully retrieved from your knowledge base.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!isQuerying && !response && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Ask a question to get answers from your knowledge base</p>
        </div>
      )}
    </div>
  )
}
