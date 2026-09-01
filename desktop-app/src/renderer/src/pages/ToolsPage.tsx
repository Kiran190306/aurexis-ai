import { Plus, Search, MoreVertical, Edit, Trash2, Power, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useTools, useDeleteTool } from '../services/api-hooks'
import { formatDistanceToNow } from 'date-fns'

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const { data: tools, isLoading, error } = useTools()
  const deleteTool = useDeleteTool()

  const filteredTools = tools?.filter(tool =>
    tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (tool.description && tool.description.toLowerCase().includes(searchQuery.toLowerCase()))
  ) || []

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this tool?')) {
      await deleteTool.mutateAsync(id)
    }
  }

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
        {isLoading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="col-span-full text-sm text-destructive text-center py-12">
            Failed to load tools: {error.message}
          </div>
        ) : filteredTools.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              {searchQuery ? 'No tools found' : 'No tools yet'}
            </h3>
            <p className="text-muted-foreground">
              {searchQuery ? 'Try adjusting your search query' : 'Add your first tool'}
            </p>
          </div>
        ) : (
          filteredTools.map((tool) => (
            <div key={tool.id} className="p-4 bg-card border border-border rounded-lg">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-foreground">{tool.display_name || tool.name}</h3>
                    <span className={`px-2 py-0.5 text-xs rounded-full capitalize ${
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
                  <span className="px-2 py-0.5 bg-muted rounded capitalize">{tool.tool_type}</span>
                  <span>{formatDistanceToNow(new Date(tool.created_at), { addSuffix: true })}</span>
                </div>
                <div className="flex items-center gap-1">
                  <button className="p-1.5 hover:bg-accent rounded-md transition-colors" title="Edit">
                    <Edit className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button className="p-1.5 hover:bg-accent rounded-md transition-colors" title="Toggle">
                    <Power className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button
                    onClick={() => handleDelete(tool.id)}
                    className="p-1.5 hover:bg-destructive hover:text-destructive-foreground rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  )
}
