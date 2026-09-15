import { Link } from 'react-router-dom'
import { Plus, Search, MoreVertical, Loader2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useConversations, useDeleteConversation, useCreateConversation } from '../services/api-hooks'
import { formatDistanceToNow } from 'date-fns'

export default function ConversationsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const { data: conversations, isLoading, error } = useConversations()
  const deleteConversation = useDeleteConversation()
  const createConversation = useCreateConversation()
  const [isCreating, setIsCreating] = useState(false)

  const filteredConversations = conversations?.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (conv.description && conv.description.toLowerCase().includes(searchQuery.toLowerCase()))
  ) || []

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this conversation?')) {
      await deleteConversation.mutateAsync(id)
    }
  }

  const handleCreate = async () => {
    setIsCreating(true)
    try {
      const result = await createConversation.mutateAsync({
        title: 'New Conversation',
        description: '',
        model: 'gpt-4o-mini',
      })
      // Navigate to the new conversation
      window.location.href = `/conversations/${result.id}`
    } catch (error) {
      console.error('Failed to create conversation:', error)
      setIsCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Conversations</h1>
          <p className="mt-2 text-muted-foreground">Manage your AI conversations</p>
        </div>
        <button
          onClick={handleCreate}
          disabled={isCreating}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          {isCreating ? 'Creating...' : 'New Conversation'}
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Conversations List */}
      <div className="bg-card border border-border rounded-lg divide-y divide-border">
        {isLoading ? (
          <div className="p-6 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="p-6 text-sm text-destructive">
            Failed to load conversations: {error.message}
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="text-center py-12">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              {searchQuery ? 'No conversations found' : 'No conversations yet'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery ? 'Try adjusting your search query' : 'Start your first conversation with Jarvis AI'}
            </p>
            {!searchQuery && (
              <button
                onClick={handleCreate}
                disabled={isCreating}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                {isCreating ? 'Creating...' : 'New Conversation'}
              </button>
            )}
          </div>
        ) : (
          filteredConversations.map((conv) => (
            <Link
              key={conv.id}
              to={`/conversations/${conv.id}`}
              className="block p-6 hover:bg-accent transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-foreground">{conv.title}</h3>
                    {conv.status !== 'active' && (
                      <span className="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded-full capitalize">
                        {conv.status}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
                    {conv.description || 'No description'}
                  </p>
                  <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{conv.message_count} messages</span>
                    <span>•</span>
                    <span>{formatDistanceToNow(new Date(conv.updated_at), { addSuffix: true })}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleDelete(conv.id, e)}
                    className="p-2 hover:bg-destructive hover:text-destructive-foreground rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button className="p-2 hover:bg-accent rounded-md transition-colors">
                    <MoreVertical className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
