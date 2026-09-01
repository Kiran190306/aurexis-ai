import { useAuth } from '../components/providers/AuthProvider'
import { useConversations } from '../services/api-hooks'
import { MessageSquare, Plus, Clock, TrendingUp, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: conversations, isLoading: conversationsLoading, error: conversationsError } = useConversations()

  const stats = [
    { label: 'Total Conversations', value: conversations?.length || 0, icon: MessageSquare, color: 'text-blue-500' },
    { label: 'Total Messages', value: conversations?.reduce((acc, conv) => acc + conv.message_count, 0) || 0, icon: TrendingUp, color: 'text-green-500' },
    { label: 'Active Sessions', value: conversations?.filter(c => c.status === 'active').length || 0, icon: Clock, color: 'text-purple-500' },
  ]

  const recentConversations = conversations?.slice(0, 5) || []

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Welcome back, {user?.username}</h1>
          <p className="mt-2 text-muted-foreground">Here's what's happening with your Jarvis AI</p>
        </div>
        <Link
          to="/conversations"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Conversation
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => (
          <div key={stat.label} className="p-6 bg-card border border-border rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                <p className="text-3xl font-bold text-foreground mt-2">{stat.value}</p>
              </div>
              <stat.icon className={`h-8 w-8 ${stat.color}`} />
            </div>
          </div>
        ))}
      </div>

      {/* Recent Conversations */}
      <div className="bg-card border border-border rounded-lg">
        <div className="p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground">Recent Conversations</h2>
        </div>
        <div className="divide-y divide-border">
          {conversationsLoading ? (
            <div className="p-6 flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : conversationsError ? (
            <div className="p-6 text-sm text-destructive">
              Failed to load conversations: {conversationsError.message}
            </div>
          ) : recentConversations.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground">
              No conversations yet. Start your first conversation!
            </div>
          ) : (
            recentConversations.map((conv) => (
              <Link
                key={conv.id}
                to={`/conversations/${conv.id}`}
                className="block p-6 hover:bg-accent transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-foreground">{conv.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground line-clamp-1">{conv.description || 'No description'}</p>
                  </div>
                  <span className="text-xs text-muted-foreground ml-4 whitespace-nowrap">
                    {conv.last_message_at ? formatDistanceToNow(new Date(conv.last_message_at), { addSuffix: true }) : formatDistanceToNow(new Date(conv.updated_at), { addSuffix: true })}
                  </span>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-card border border-border rounded-lg">
          <h3 className="font-semibold text-foreground mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link
              to="/conversations"
              className="block px-4 py-2 text-sm text-foreground hover:bg-accent rounded-md transition-colors"
            >
              View All Conversations
            </Link>
            <Link
              to="/settings"
              className="block px-4 py-2 text-sm text-foreground hover:bg-accent rounded-md transition-colors"
            >
              Configure AI Model
            </Link>
            <Link
              to="/tools"
              className="block px-4 py-2 text-sm text-foreground hover:bg-accent rounded-md transition-colors"
            >
              Manage Tools
            </Link>
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-lg">
          <h3 className="font-semibold text-foreground mb-4">System Status</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">API Status</span>
              <span className="text-sm text-green-500">Online</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Database</span>
              <span className="text-sm text-green-500">Connected</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">AI Engine</span>
              <span className="text-sm text-green-500">Ready</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
