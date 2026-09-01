import { Plus, Search, MoreVertical, Edit, Trash2, Power } from 'lucide-react'
import { useState } from 'react'

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const tools = [
    { id: 1, name: 'Web Search', description: 'Search the web for information', category: 'Search', status: 'active', version: '1.0.0' },
    { id: 2, name: 'Code Executor', description: 'Execute code in a sandboxed environment', category: 'Development', status: 'active', version: '2.1.0' },
    { id: 3, name: 'File Manager', description: 'Manage files and directories', category: 'File System', status: 'inactive', version: '1.5.0' },
    { id: 4, name: 'Database Query', description: 'Query SQL databases', category: 'Database', status: 'active', version: '1.2.0' },
    { id: 5, name: 'API Client', description: 'Make HTTP requests to external APIs', category: 'Network', status: 'active', version: '1.0.0' },
  ]

  const filteredTools = tools.filter(tool =>
    tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tool.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Tools</h1>
          <p className="mt-2 text-muted-foreground">Manage your AI tools and integrations</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
          <Plus className="h-4 w-4" />
          Add Tool
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search tools..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTools.map((tool) => (
          <div key={tool.id} className="p-4 bg-card border border-border rounded-lg">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-foreground">{tool.name}</h3>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${
                    tool.status === 'active' ? 'bg-green-500/10 text-green-500' : 'bg-gray-500/10 text-gray-500'
                  }`}>
                    {tool.status}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">{tool.description}</p>
              </div>
              <button className="p-1 hover:bg-accent rounded-md transition-colors">
                <MoreVertical className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="px-2 py-0.5 bg-muted rounded">{tool.category}</span>
                <span>v{tool.version}</span>
              </div>
              <div className="flex items-center gap-1">
                <button className="p-1.5 hover:bg-accent rounded-md transition-colors" title="Edit">
                  <Edit className="h-4 w-4 text-muted-foreground" />
                </button>
                <button className="p-1.5 hover:bg-accent rounded-md transition-colors" title="Toggle">
                  <Power className="h-4 w-4 text-muted-foreground" />
                </button>
                <button className="p-1.5 hover:bg-accent rounded-md transition-colors" title="Delete">
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredTools.length === 0 && (
        <div className="text-center py-12">
          <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium text-foreground mb-2">No tools found</h3>
          <p className="text-muted-foreground">Try adjusting your search query</p>
        </div>
      )}
    </div>
  )
}
