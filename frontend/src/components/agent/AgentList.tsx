import { useState, useEffect } from 'react'
import { Search, MoreVertical, Edit, Trash2, Play, Eye } from 'lucide-react'
import { AgentService, Agent, AgentStatus } from '../../services/agent'
import toast from 'react-hot-toast'

interface AgentListProps {
  onSelectAgent?: (agent: Agent) => void
  onEditAgent?: (agent: Agent) => void
  onDeleteAgent?: (agent: Agent) => void
  onExecuteAgent?: (agent: Agent) => void
}

export function AgentList({ onSelectAgent, onEditAgent, onDeleteAgent, onExecuteAgent }: AgentListProps) {
  const [agents, setAgents] = useState<Agent[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)

  const loadAgents = async () => {
    try {
      setLoading(true)
      const data = await AgentService.listAgents()
      setAgents(data)
    } catch (error) {
      console.error('Failed to load agents:', error)
      toast.error('Failed to load agents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAgents()
  }, [])

  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleDelete = async (agent: Agent) => {
    if (!confirm(`Are you sure you want to delete agent "${agent.name}"?`)) {
      return
    }
    try {
      await AgentService.deleteAgent(agent.id)
      toast.success('Agent deleted successfully')
      loadAgents()
      onDeleteAgent?.(agent)
    } catch (error) {
      console.error('Failed to delete agent:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to delete agent')
    }
  }

  const getStatusColor = (status: AgentStatus) => {
    switch (status) {
      case AgentStatus.ACTIVE:
        return 'text-green-500 bg-green-500/10'
      case AgentStatus.INACTIVE:
        return 'text-gray-500 bg-gray-500/10'
      case AgentStatus.BUSY:
        return 'text-blue-500 bg-blue-500/10'
      case AgentStatus.ERROR:
        return 'text-red-500 bg-red-500/10'
      default:
        return 'text-gray-500 bg-gray-500/10'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search agents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAgents.map((agent) => (
          <div key={agent.id} className="p-4 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-foreground">{agent.name}</h3>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${getStatusColor(agent.status)}`}>
                    {agent.status}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{agent.description}</p>
              </div>
              <button className="p-1 hover:bg-accent rounded-md transition-colors">
                <MoreVertical className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Model</span>
                <span className="font-medium text-foreground">{agent.model}</span>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Type</span>
                <span className="font-medium text-foreground capitalize">{agent.agent_type}</span>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Tasks</span>
                <span className="font-medium text-foreground">{agent.task_count}</span>
              </div>
              {agent.tool_ids && agent.tool_ids.length > 0 && (
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Tools</span>
                  <span className="font-medium text-foreground">{agent.tool_ids.length}</span>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => onSelectAgent?.(agent)}
                  className="p-1.5 hover:bg-accent rounded-md transition-colors"
                  title="View"
                >
                  <Eye className="h-4 w-4 text-muted-foreground" />
                </button>
                <button
                  onClick={() => onEditAgent?.(agent)}
                  className="p-1.5 hover:bg-accent rounded-md transition-colors"
                  title="Edit"
                >
                  <Edit className="h-4 w-4 text-muted-foreground" />
                </button>
                <button
                  onClick={() => onExecuteAgent?.(agent)}
                  className="p-1.5 hover:bg-accent rounded-md transition-colors"
                  title="Execute"
                >
                  <Play className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
              <button
                onClick={() => handleDelete(agent)}
                className="p-1.5 hover:bg-accent hover:text-red-500 rounded-md transition-colors"
                title="Delete"
              >
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredAgents.length === 0 && (
        <div className="text-center py-12">
          <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium text-foreground mb-2">No agents found</h3>
          <p className="text-muted-foreground">
            {searchQuery ? 'Try adjusting your search query' : 'Create your first agent'}
          </p>
        </div>
      )}
    </div>
  )
}
