import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Send, Paperclip, Mic, MoreVertical, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useMessages, useCreateMessage, useConversation } from '../services/api-hooks'
import { formatDistanceToNow } from 'date-fns'

export default function ConversationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const conversationId = parseInt(id || '0')
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)

  const { data: conversation, isLoading: conversationLoading } = useConversation(conversationId)
  const { data: messages, isLoading: messagesLoading, error: messagesError } = useMessages(conversationId)
  const createMessage = useCreateMessage()

  const handleSend = async () => {
    if (!message.trim() || !conversationId) return

    setIsSending(true)
    try {
      await createMessage.mutateAsync({
        conversation_id: conversationId,
        role: 'user',
        content: message,
        message_type: 'text',
      })
      setMessage('')
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (conversationLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Conversation not found</p>
          <Link to="/conversations" className="text-primary hover:underline">
            Back to conversations
          </Link>
        </div>
      </div>
    )
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
            <h1 className="text-lg font-semibold text-foreground">{conversation.title}</h1>
            <p className="text-sm text-muted-foreground">{conversation.model} • {conversation.message_count} messages</p>
          </div>
        </div>
        <button className="p-2 hover:bg-accent rounded-md transition-colors">
          <MoreVertical className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messagesLoading ? (
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : messagesError ? (
          <div className="text-sm text-destructive text-center">
            Failed to load messages: {messagesError.message}
          </div>
        ) : messages && messages.length > 0 ? (
          messages.map((msg) => (
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
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className="text-xs mt-2 opacity-70">
                  {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}
                </p>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center text-muted-foreground py-8">
            No messages yet. Start the conversation!
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card">
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-accent rounded-md transition-colors" title="Attach file">
            <Paperclip className="h-5 w-5 text-muted-foreground" />
          </button>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isSending}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
          />
          <button className="p-2 hover:bg-accent rounded-md transition-colors" title="Voice input">
            <Mic className="h-5 w-5 text-muted-foreground" />
          </button>
          <button
            onClick={handleSend}
            disabled={!message.trim() || isSending}
            className="p-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isSending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </div>
  )
}
