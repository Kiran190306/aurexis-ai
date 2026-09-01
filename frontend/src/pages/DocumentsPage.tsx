import { FileText, Upload, Search, MessageSquare } from 'lucide-react'
import { useState } from 'react'
import { DocumentUpload } from '../components/knowledge/DocumentUpload'
import { DocumentList } from '../components/knowledge/DocumentList'
import { SearchInterface } from '../components/knowledge/SearchInterface'
import { RAGQueryInterface } from '../components/knowledge/RAGQueryInterface'

type Tab = 'upload' | 'list' | 'search' | 'query'

export default function DocumentsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('list')
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleUploadComplete = () => {
    setActiveTab('list')
    setRefreshTrigger(prev => prev + 1)
  }

  const tabs = [
    { id: 'upload' as Tab, label: 'Upload', icon: Upload },
    { id: 'list' as Tab, label: 'Documents', icon: FileText },
    { id: 'search' as Tab, label: 'Search', icon: Search },
    { id: 'query' as Tab, label: 'Ask', icon: MessageSquare },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Knowledge Base</h1>
        <p className="mt-2 text-muted-foreground">Upload documents, search, and ask questions about your knowledge</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'upload' && (
          <DocumentUpload
            onUploadComplete={handleUploadComplete}
            onCancel={() => setActiveTab('list')}
          />
        )}

        {activeTab === 'list' && (
          <DocumentList refreshTrigger={refreshTrigger} />
        )}

        {activeTab === 'search' && (
          <SearchInterface />
        )}

        {activeTab === 'query' && (
          <RAGQueryInterface />
        )}
      </div>
    </div>
  )
}
