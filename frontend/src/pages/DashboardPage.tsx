import { useAuth } from '../components/providers/AuthProvider'
import { MessageSquare, Plus, Clock, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function DashboardPage() {
  const { user } = useAuth()

  const stats = [
    { label: 'Total Conversations', value: '12', icon: MessageSquare, color: 'text-blue-500' },
    { label: 'Messages Today', value: '45', icon: TrendingUp, color: 'text-green-500' },
    { label: 'Active Sessions', value: '3', icon: Clock, color: 'text-purple-500' },
  ]

  const recentConversations = [
    { id: 1, title: 'Project Planning', lastMessage: 'Let me help you plan the architecture...', time: '2 hours ago' },
    { id: 2, title: 'Code Review', lastMessage: 'The code looks good overall...', time: '5 hours ago' },
    { id: 3, title: 'Research Task', lastMessage: 'I found several relevant papers...', time: '1 day ago' },
  ]

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Welcome back, {user?.username}</h1>
          <p className="mt-2 text-muted-foreground">Here's what's happening with your Aurexis AI</p>
        </div>
        <Link
          to="/conversations/new"
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
          {recentConversations.map((conv) => (
            <Link
              key={conv.id}
              to={`/conversations/${conv.id}`}
              className="block p-6 hover:bg-accent transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-foreground">{conv.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-1">{conv.lastMessage}</p>
                </div>
                <span className="text-xs text-muted-foreground">{conv.time}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-card border border-border rounded-lg">
          <h3 className="font-semibold text-foreground mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link
              to="/conversations/new"
              className="block px-4 py-2 text-sm text-foreground hover:bg-accent rounded-md transition-colors"
            >
              Start New Conversation
            </Link>
            <Link
              to="/settings"
              className="block px-4 py-2 text-sm text-foreground hover:bg-accent rounded-md transition-colors"
            >
              Configure AI Model
            </Link>
            <Link
              to="/settings"
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
