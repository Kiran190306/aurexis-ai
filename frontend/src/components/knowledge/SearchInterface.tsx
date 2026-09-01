import { useState } from 'react'
import { Search, Settings, Loader2, FileText } from 'lucide-react'
import { KnowledgeService, SearchRequest, SearchResult } from '../../services/knowledge'
import toast from 'react-hot-toast'

interface SearchInterfaceProps {
  onResultSelect?: (result: SearchResult) => void
}

export function SearchInterface({ onResultSelect }: SearchInterfaceProps) {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [useHybrid, setUseHybrid] = useState(true)
  const [useReranking, setUseReranking] = useState(true)
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.error('Please enter a search query')
      return
    }

    setIsSearching(true)
    try {
      const request: SearchRequest = {
        query: query.trim(),
        top_k: topK,
        use_hybrid: useHybrid,
        use_reranking: useReranking,
      }

      const searchResults = await KnowledgeService.search(request)
      setResults(searchResults)

      if (searchResults.length === 0) {
        toast('No results found')
      } else {
        toast.success(`Found ${searchResults.length} results`)
      }
    } catch (error) {
      console.error('Search failed:', error)
      toast.error(error instanceof Error ? error.message : 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400'
    if (score >= 0.6) return 'text-blue-600 dark:text-blue-400'
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Search Knowledge</h2>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          title="Advanced options"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Enter your search query..."
          className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 resize-none"
          rows={2}
        />
      </div>

      {/* Advanced Options */}
      {showAdvanced && (
        <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-4">
          <h3 className="font-semibold text-sm">Advanced Options</h3>
          
          <div className="grid grid-cols-3 gap-4">
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

      {/* Search Button */}
      <button
        onClick={handleSearch}
        disabled={!query.trim() || isSearching}
        className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
      >
        {isSearching ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Searching...
          </>
        ) : (
          <>
            <Search className="w-5 h-5" />
            Search
          </>
        )}
      </button>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Results ({results.length})</h3>
          </div>

          <div className="space-y-3">
            {results.map((result, index) => (
              <div
                key={`${result.chunk_id}-${index}`}
                onClick={() => onResultSelect?.(result)}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-500" />
                    <span className="font-medium">{result.document_title}</span>
                  </div>
                  <span className={`text-sm font-medium ${getScoreColor(result.score)}`}>
                    {(result.score * 100).toFixed(1)}%
                  </span>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-3">
                  {truncateText(result.chunk_text, 300)}
                </p>

                {result.citation && (
                  <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>Chunk {result.citation.chunk_index}</span>
                    {result.citation.page_number && (
                      <>
                        <span>•</span>
                        <span>Page {result.citation.page_number}</span>
                      </>
                    )}
                  </div>
                )}

                {result.metadata && Object.keys(result.metadata).length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(result.metadata).slice(0, 3).map(([key, value]) => (
                        <span
                          key={key}
                          className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs"
                        >
                          {key}: {String(value).substring(0, 20)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isSearching && results.length === 0 && query && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Enter a query above to search your knowledge base</p>
        </div>
      )}
    </div>
  )
}
