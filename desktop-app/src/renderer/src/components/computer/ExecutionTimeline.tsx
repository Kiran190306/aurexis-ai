/**
 * Execution Timeline Component
 * Timeline view of computer action history with filtering and details.
 */
import React, { useState } from 'react'
import { 
  History, 
  Filter, 
  Search, 
  Calendar, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  ChevronDown,
  ChevronRight
} from 'lucide-react'
import { useComputerHistory } from '../../services/computer-hooks'

const ExecutionTimeline: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'completed' | 'failed'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set())
  const [page, setPage] = useState(0)
  const pageSize = 50

  const { data: history } = useComputerHistory(page * pageSize, pageSize)

  const toggleExpand = (id: number) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedItems(newExpanded)
  }

  const filteredHistory = history?.filter((item: any) => {
    const matchesFilter = filter === 'all' || 
      (filter === 'completed' && item.success) ||
      (filter === 'failed' && !item.success)
    
    const matchesSearch = !searchQuery || 
      item.action_type.toLowerCase().includes(searchQuery.toLowerCase())
    
    return matchesFilter && matchesSearch
  }) || []

  const getStatusIcon = (status: string, success: boolean) => {
    if (status === 'running') return <Clock className="w-4 h-4 text-yellow-400" />
    if (success) return <CheckCircle className="w-4 h-4 text-green-400" />
    if (status === 'failed' || !success) return <XCircle className="w-4 h-4 text-red-400" />
    return <AlertCircle className="w-4 h-4 text-gray-400" />
  }

  const getStatusColor = (status: string, success: boolean) => {
    if (status === 'running') return 'border-yellow-500'
    if (success) return 'border-green-500'
    if (status === 'failed' || !success) return 'border-red-500'
    return 'border-gray-500'
  }

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-'
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`
    if (seconds < 60) return `${Math.round(seconds * 10) / 10}s`
    return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`
  }

  const getActionTypeLabel = (actionType: string) => {
    return actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-700 px-4 py-3 bg-gray-800">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <History className="w-5 h-5 text-blue-400" />
            Execution Timeline
          </h2>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="pl-9 pr-4 py-1.5 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500 w-48"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="border-b border-gray-700 px-4 py-2 bg-gray-800 flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-400" />
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            filter === 'all' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('completed')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            filter === 'completed' ? 'bg-green-600' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          Completed
        </button>
        <button
          onClick={() => setFilter('failed')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            filter === 'failed' ? 'bg-red-600' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          Failed
        </button>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-auto p-4">
        {filteredHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <History className="w-12 h-12 mb-4" />
            <p className="text-sm">No execution history</p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-700" />

            <div className="space-y-4">
              {filteredHistory.map((item: any, index: number) => (
                <div key={item.id} className="relative pl-10">
                  {/* Timeline dot */}
                  <div className={`absolute left-2.5 top-4 w-3 h-3 rounded-full border-2 bg-gray-900 ${getStatusColor(item.status, item.success)}`} />

                  {/* Timeline item */}
                  <div
                    className={`bg-gray-800 rounded-lg p-4 border-l-4 ${getStatusColor(item.status, item.success)}`}
                  >
                    <div
                      className="flex items-start justify-between cursor-pointer"
                      onClick={() => toggleExpand(item.id)}
                    >
                      <div className="flex items-center gap-3">
                        {getStatusIcon(item.status, item.success)}
                        <div>
                          <p className="text-sm font-medium">
                            {getActionTypeLabel(item.action_type)}
                          </p>
                          <p className="text-xs text-gray-400 flex items-center gap-2">
                            <Calendar className="w-3 h-3" />
                            {new Date(item.started_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-400">
                          {formatDuration(item.duration_seconds)}
                        </span>
                        {expandedItems.has(item.id) ? (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                    </div>

                    {expandedItems.has(item.id) && (
                      <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-gray-400">Status:</span>
                            <span className="ml-2 capitalize">{item.status}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Success:</span>
                            <span className="ml-2">{item.success ? 'Yes' : 'No'}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Duration:</span>
                            <span className="ml-2">{formatDuration(item.duration_seconds)}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">UUID:</span>
                            <span className="ml-2 font-mono">{item.uuid.slice(0, 8)}...</span>
                          </div>
                        </div>
                        {item.completed_at && (
                          <div className="text-xs">
                            <span className="text-gray-400">Completed:</span>
                            <span className="ml-2">{new Date(item.completed_at).toLocaleString()}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="border-t border-gray-700 px-4 py-2 bg-gray-800 flex items-center justify-between">
        <div className="text-xs text-gray-400">
          Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, filteredHistory.length)} of {filteredHistory.length}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed rounded transition-colors"
          >
            Previous
          </button>
          <span className="text-xs text-gray-400">Page {page + 1}</span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={filteredHistory.length < pageSize}
            className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed rounded transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}

export default ExecutionTimeline
