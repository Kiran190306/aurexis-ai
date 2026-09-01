import { Search, MoreVertical, FileText, Upload, Download, Trash2, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useDocuments, useDeleteDocument } from '../services/api-hooks'
import { formatDistanceToNow } from 'date-fns'

export default function DocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const { data: documents, isLoading, error } = useDocuments()
  const deleteDocument = useDeleteDocument()

  const filteredDocuments = documents?.filter(doc =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this document?')) {
      await deleteDocument.mutateAsync(id)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'indexed':
        return 'bg-green-500/10 text-green-500'
      case 'processing':
        return 'bg-yellow-500/10 text-yellow-500'
      default:
        return 'bg-gray-500/10 text-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Documents</h1>
          <p className="mt-2 text-muted-foreground">Manage your documents and knowledge base</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
          <Upload className="h-4 w-4" />
          Upload Document
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Documents List */}
      <div className="bg-card border border-border rounded-lg divide-y divide-border">
        {isLoading ? (
          <div className="p-6 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="p-6 text-sm text-destructive text-center">
            Failed to load documents: {error.message}
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              {searchQuery ? 'No documents found' : 'No documents yet'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery ? 'Try adjusting your search query' : 'Upload your first document'}
            </p>
          </div>
        ) : (
          filteredDocuments.map((doc) => (
            <div key={doc.id} className="p-4 hover:bg-accent transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-foreground">{doc.title}</h3>
                      <span className={`px-2 py-0.5 text-xs rounded-full capitalize ${getStatusColor(doc.status)}`}>
                        {doc.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <span className="capitalize">{doc.document_type}</span>
                      <span>•</span>
                      <span>{formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button className="p-1.5 hover:bg-accent rounded-md transition-colors" title="Download">
                    <Download className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-1.5 hover:bg-destructive hover:text-destructive-foreground rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button className="p-1.5 hover:bg-accent rounded-md transition-colors">
                    <MoreVertical className="h-4 w-4 text-muted-foreground" />
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
