import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Send, Paperclip, Mic, MoreVertical } from 'lucide-react'
import { useState } from 'react'

export default function ConversationDetailPage() {
  useParams<{ id: string }>()
  const [message, setMessage] = useState('')

  const messages = [
    { id: 1, role: 'user', content: 'Can you help me plan a REST API architecture?', timestamp: '10:30 AM' },
    { id: 2, role: 'assistant', content: 'Of course! Let me help you design a scalable REST API architecture. Here are the key components you should consider...', timestamp: '10:31 AM' },
    { id: 3, role: 'user', content: 'What about authentication?', timestamp: '10:35 AM' },
    { id: 4, role: 'assistant', content: 'For authentication, I recommend using JWT tokens with OAuth2. Here\'s how you can implement it...', timestamp: '10:36 AM' },
  ]

  const handleSend = () => {
    if (message.trim()) {
      // Send message logic here
      setMessage('')
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-card">
        <div className="flex items-center gap-4">
          <Link to="/conversations" className="p-2 hover:bg-accent rounded-md transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-lg font-semibold text-foreground">Project Planning</h1>
            <p className="text-sm text-muted-foreground">GPT-4 Turbo • 4 messages</p>
          </div>
        </div>
        <button className="p-2 hover:bg-accent rounded-md transition-colors">
          <MoreVertical className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] p-4 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-card border border-border'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
              <p className="text-xs mt-2 opacity-70">{msg.timestamp}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card">
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-accent rounded-md transition-colors">
            <Paperclip className="h-5 w-5 text-muted-foreground" />
          </button>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button className="p-2 hover:bg-accent rounded-md transition-colors">
            <Mic className="h-5 w-5 text-muted-foreground" />
          </button>
          <button
            onClick={handleSend}
            className="p-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
