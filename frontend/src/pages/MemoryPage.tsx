import { Plus, Search, MoreVertical, Brain, Pin } from 'lucide-react'
import { useState } from 'react'

export default function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const memories = [
    { id: 1, content: 'User prefers Python for backend development', summary: 'Python preference', type: 'episodic', importance: 0.8, pinned: true, createdAt: '2 days ago' },
    { id: 2, content: 'Project uses PostgreSQL as the database', summary: 'Database choice', type: 'semantic', importance: 0.9, pinned: false, createdAt: '3 days ago' },
    { id: 3, content: 'Meeting with team scheduled for Friday at 2 PM', summary: 'Team meeting', type: 'episodic', importance: 0.6, pinned: true, createdAt: '1 day ago' },
    { id: 4, content: 'API endpoint structure follows REST principles', summary: 'API design', type: 'semantic', importance: 0.7, pinned: false, createdAt: '5 days ago' },
  ]

  const filteredMemories = memories.filter(memory =>
    memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    memory.summary.toLowerCase().includes(searchQuery.toLowerCase())
  )

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
        {filteredMemories.map((memory) => (
          <div key={memory.id} className="p-4 bg-card border border-border rounded-lg">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Brain className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{memory.summary}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="px-2 py-0.5 text-xs bg-muted rounded">{memory.type}</span>
                    {memory.pinned && <Pin className="h-3 w-3 text-primary" />}
                  </div>
                </div>
              </div>
              <button className="p-1 hover:bg-accent rounded-md transition-colors">
                <MoreVertical className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>

            <p className="text-sm text-muted-foreground mb-3">{memory.content}</p>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-full bg-muted rounded-full h-1.5 w-24">
                  <div
                    className="bg-primary h-1.5 rounded-full"
                    style={{ width: `${memory.importance * 100}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">{Math.round(memory.importance * 100)}%</span>
              </div>
              <span className="text-xs text-muted-foreground">{memory.createdAt}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredMemories.length === 0 && (
        <div className="text-center py-12">
          <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Brain className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium text-foreground mb-2">No memories found</h3>
          <p className="text-muted-foreground mb-4">Add your first memory entry</p>
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
            <Plus className="h-4 w-4" />
            Add Memory
          </button>
        </div>
      )}
    </div>
  )
}
