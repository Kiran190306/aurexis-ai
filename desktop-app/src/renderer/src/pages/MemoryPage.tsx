import { Plus, Search, MoreVertical, Brain, Pin, Loader2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useMemories, useDeleteMemory } from '../services/api-hooks'
import { formatDistanceToNow } from 'date-fns'

export default function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const { data: memories, isLoading, error } = useMemories()
  const deleteMemory = useDeleteMemory()

  const filteredMemories = memories?.filter(memory =>
    memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (memory.summary && memory.summary.toLowerCase().includes(searchQuery.toLowerCase()))
  ) || []

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this memory?')) {
      await deleteMemory.mutateAsync(id)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Memory</h1>
          <p className="mt-2 text-muted-foreground">Manage your AI memory and knowledge base</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
          <Plus className="h-4 w-4" />
          Add Memory
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search memories..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Memory Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="col-span-full text-sm text-destructive text-center py-12">
            Failed to load memories: {error.message}
          </div>
        ) : filteredMemories.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Brain className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              {searchQuery ? 'No memories found' : 'No memories yet'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery ? 'Try adjusting your search query' : 'Add your first memory entry'}
            </p>
          </div>
        ) : (
          filteredMemories.map((memory) => (
            <div key={memory.id} className="p-4 bg-card border border-border rounded-lg">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Brain className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">{memory.summary || 'No summary'}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="px-2 py-0.5 text-xs bg-muted rounded capitalize">{memory.memory_type}</span>
                      {memory.is_pinned && <Pin className="h-3 w-3 text-primary" />}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleDelete(memory.id)}
                    className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button className="p-1 hover:bg-accent rounded-md transition-colors">
                    <MoreVertical className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-3 line-clamp-3">{memory.content}</p>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-muted rounded-full h-1.5">
                    <div
                      className="bg-primary h-1.5 rounded-full"
                      style={{ width: `${memory.importance_score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">{Math.round(memory.importance_score * 100)}%</span>
                </div>
                <span className="text-xs text-muted-foreground">{formatDistanceToNow(new Date(memory.created_at), { addSuffix: true })}</span>
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  )
}
