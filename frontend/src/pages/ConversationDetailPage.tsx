import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Send, Paperclip, Mic, MoreVertical } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { ConversationService, Conversation } from '../services/conversation'
import { MessageService, Message, MessageRole } from '../services/message'

export default function ConversationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [message, setMessage] = useState('')
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMessages, setIsLoadingMessages] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const conversationId = id ? parseInt(id) : 0

  useEffect(() => {
    const loadConversation = async () => {
      if (!conversationId) {
        setError('Invalid conversation ID')
        setIsLoading(false)
        return
      }

      try {
        const convData = await ConversationService.getConversation(conversationId)
        setConversation(convData)
      } catch (err) {
        setError('Failed to load conversation')
      } finally {
        setIsLoading(false)
      }
    }
    loadConversation()
  }, [conversationId])

  useEffect(() => {
    const loadMessages = async () => {
      if (!conversationId) return

      setIsLoadingMessages(true)
      try {
        const messagesData = await MessageService.listConversationMessages(conversationId)
        setMessages(messagesData)
      } catch (err) {
        setError('Failed to load messages')
      } finally {
        setIsLoadingMessages(false)
      }
    }
    loadMessages()
  }, [conversationId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!message.trim() || !conversationId || isSending) {
      return
    }

    setIsSending(true)
    const userMessage = message.trim()
    setMessage('')

    try {
      // Create user message with AI trigger
      const createdMessage = await MessageService.createMessage({
        conversation_id: conversationId,
        role: MessageRole.USER,
        content: userMessage,
        message_type: 'text' as any,
        trigger_ai: true,
      })

      // Add user message to list
      setMessages(prev => [...prev, createdMessage])

      // Reload messages after a short delay to get the assistant response
      // The backend creates the assistant message synchronously
      setTimeout(async () => {
        try {
          const updatedMessages = await MessageService.listConversationMessages(conversationId)
          setMessages(updatedMessages)
        } catch (err) {
          console.error('Failed to reload messages:', err)
        }
      }, 1000)

    } catch (err) {
      setError('Failed to send message')
      setMessage(userMessage) // Restore message on error
    } finally {
      setIsSending(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Link to="/conversations" className="text-primary hover:underline">
            Back to Conversations
          </Link>
        </div>
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Conversation not found</p>
          <Link to="/conversations" className="text-primary hover:underline">
            Back to Conversations
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
            <p className="text-sm text-muted-foreground">
              {conversation.model} • {messages.length} messages
            </p>
          </div>
        </div>
        <button className="p-2 hover:bg-accent rounded-md transition-colors">
          <MoreVertical className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoadingMessages ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === MessageRole.USER ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] p-4 rounded-lg ${
                  msg.role === MessageRole.USER
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card border border-border'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className="text-xs mt-2 opacity-70">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
        {/* AI processing indicator */}
        {isSending && (
          <div className="flex justify-start">
            <div className="bg-card border border-border p-4 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                <p className="text-sm text-muted-foreground">AI is thinking...</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card">
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-accent rounded-md transition-colors" disabled={isSending}>
            <Paperclip className="h-5 w-5 text-muted-foreground" />
          </button>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            disabled={isSending}
          />
          <button className="p-2 hover:bg-accent rounded-md transition-colors" disabled={isSending}>
            <Mic className="h-5 w-5 text-muted-foreground" />
          </button>
          <button
            onClick={handleSend}
            disabled={!message.trim() || isSending}
            className="p-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
