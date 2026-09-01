import { Link } from 'react-router-dom'
import { Plus, Search, MoreVertical } from 'lucide-react'

export default function ConversationsPage() {
  const conversations = [
    { id: 1, title: 'Project Planning', messageCount: 24, lastMessage: 'Let me help you plan the architecture...', updatedAt: '2 hours ago', status: 'active' },
    { id: 2, title: 'Code Review', messageCount: 15, lastMessage: 'The code looks good overall...', updatedAt: '5 hours ago', status: 'active' },
    { id: 3, title: 'Research Task', messageCount: 8, lastMessage: 'I found several relevant papers...', updatedAt: '1 day ago', status: 'archived' },
    { id: 4, title: 'Debug Session', messageCount: 32, lastMessage: 'Let me check the error logs...', updatedAt: '2 days ago', status: 'active' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Conversations</h1>
          <p className="mt-2 text-muted-foreground">Manage your AI conversations</p>
        </div>
        <Link
          to="/conversations/new"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Conversation
        </Link>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search conversations..."
          className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Conversations List */}
      <div className="bg-card border border-border rounded-lg divide-y divide-border">
        {conversations.map((conv) => (
          <Link
            key={conv.id}
            to={`/conversations/${conv.id}`}
            className="block p-6 hover:bg-accent transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-foreground">{conv.title}</h3>
                  {conv.status === 'archived' && (
                    <span className="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded-full">
                      Archived
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-muted-foreground line-clamp-1">{conv.lastMessage}</p>
                <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{conv.messageCount} messages</span>
                  <span>•</span>
                  <span>{conv.updatedAt}</span>
                </div>
              </div>
              <button className="p-2 hover:bg-accent rounded-md transition-colors">
                <MoreVertical className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          </Link>
        ))}
      </div>

      {/* Empty State */}
      {conversations.length === 0 && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No conversations yet</h3>
          <p className="text-muted-foreground mb-4">Start your first conversation with Jarvis AI</p>
          <Link
            to="/conversations/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Conversation
          </Link>
        </div>
      )}
    </div>
  )
}
