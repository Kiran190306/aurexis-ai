/**
 * Browser Sessions Component
 * Browser automation interface with page management and action controls.
 */
import React, { useState } from 'react'
import { 
  Globe, 
  Plus, 
  X, 
  Navigation, 
  MousePointerClick, 
  Type, 
  Download, 
  Upload,
  Camera,
  RefreshCw,
  ExternalLink
} from 'lucide-react'
import { 
  useOpenBrowser, 
  useNavigateBrowser, 
  useClickElement, 
  useFillForm,
  useExtractContent,
  useDownloadFile,
  useUploadFile,
  useTakeScreenshot,
  useCloseBrowser,
  useActivePages
} from '../../services/computer-hooks'

const BrowserSessions: React.FC = () => {
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null)
  const [url, setUrl] = useState('')
  const [selector, setSelector] = useState('')
  const [value, setValue] = useState('')
  const [extractedContent, setExtractedContent] = useState('')

  const openBrowser = useOpenBrowser()
  const navigateBrowser = useNavigateBrowser()
  const clickElement = useClickElement()
  const fillForm = useFillForm()
  const extractContent = useExtractContent()
  const downloadFile = useDownloadFile()
  const uploadFile = useUploadFile()
  const takeScreenshot = useTakeScreenshot()
  const closeBrowser = useCloseBrowser()
  const { data: activePages } = useActivePages()

  const handleOpenBrowser = async () => {
    try {
      const result = await openBrowser.mutateAsync({ url: url || undefined })
      if (result.success && result.metadata?.page_id) {
        setSelectedPageId(result.metadata.page_id)
        setUrl('')
      }
    } catch (error) {
      console.error('Failed to open browser:', error)
    }
  }

  const handleNavigate = async () => {
    if (!selectedPageId || !url) return
    try {
      await navigateBrowser.mutateAsync({ page_id: selectedPageId, url })
      setUrl('')
    } catch (error) {
      console.error('Failed to navigate:', error)
    }
  }

  const handleClick = async () => {
    if (!selectedPageId || !selector) return
    try {
      await clickElement.mutateAsync({ page_id: selectedPageId, selector })
      setSelector('')
    } catch (error) {
      console.error('Failed to click:', error)
    }
  }

  const handleFill = async () => {
    if (!selectedPageId || !selector || !value) return
    try {
      await fillForm.mutateAsync({ page_id: selectedPageId, selector, value })
      setSelector('')
      setValue('')
    } catch (error) {
      console.error('Failed to fill form:', error)
    }
  }

  const handleExtract = async () => {
    if (!selectedPageId) return
    try {
      const result = await extractContent.mutateAsync({ 
        page_id: selectedPageId, 
        selector: selector || undefined 
      })
      if (result.success && result.output) {
        setExtractedContent(result.output)
      }
    } catch (error) {
      console.error('Failed to extract content:', error)
    }
  }

  const handleScreenshot = async () => {
    if (!selectedPageId) return
    try {
      await takeScreenshot.mutateAsync({ page_id: selectedPageId })
    } catch (error) {
      console.error('Failed to take screenshot:', error)
    }
  }

  const handleClosePage = async (pageId: string) => {
    try {
      await closeBrowser.mutateAsync({ page_id })
      if (selectedPageId === pageId) {
        setSelectedPageId(null)
      }
    } catch (error) {
      console.error('Failed to close page:', error)
    }
  }

  const handleCloseAll = async () => {
    try {
      await closeBrowser.mutateAsync({})
      setSelectedPageId(null)
    } catch (error) {
      console.error('Failed to close browser:', error)
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Page List */}
      <div className="border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between px-4 py-2">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium">Browser Sessions</span>
            <span className="text-xs text-gray-400">
              ({activePages?.pages?.length || 0} active)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenBrowser}
              className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded transition-colors"
            >
              <Plus className="w-3 h-3" />
              New Tab
            </button>
            <button
              onClick={handleCloseAll}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
              title="Close All"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Page Tabs */}
        <div className="flex gap-1 px-2 pb-2 overflow-x-auto">
          {activePages?.pages?.map((pageId: string) => (
            <button
              key={pageId}
              onClick={() => setSelectedPageId(pageId)}
              className={`flex items-center gap-2 px-3 py-1.5 text-xs rounded transition-colors ${
                selectedPageId === pageId
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <span className="truncate max-w-32">Page {pageId.slice(-4)}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleClosePage(pageId)
                }}
                className="hover:bg-gray-500 rounded p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </button>
          ))}
          {(!activePages?.pages || activePages.pages.length === 0) && (
            <div className="px-3 py-1.5 text-xs text-gray-500">
              No active pages
            </div>
          )}
        </div>
      </div>

      {/* Actions Panel */}
      <div className="flex-1 overflow-auto p-4">
        {!selectedPageId ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Globe className="w-12 h-12 mb-4" />
            <p className="text-sm">No page selected</p>
            <p className="text-xs mt-1">Open a new tab to begin browser automation</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Navigation */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Navigation className="w-4 h-4 text-blue-400" />
                Navigation
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Enter URL..."
                  className="flex-1 px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleNavigate}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors text-sm"
                >
                  Go
                </button>
              </div>
            </div>

            {/* Element Actions */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <MousePointerClick className="w-4 h-4 text-green-400" />
                Element Actions
              </h3>
              <div className="space-y-3">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={selector}
                    onChange={(e) => setSelector(e.target.value)}
                    placeholder="CSS selector..."
                    className="flex-1 px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={handleClick}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors text-sm"
                  >
                    Click
                  </button>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    placeholder="Value to fill..."
                    className="flex-1 px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={handleFill}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded transition-colors text-sm"
                  >
                    Fill
                  </button>
                </div>
              </div>
            </div>

            {/* Content Extraction */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Type className="w-4 h-4 text-yellow-400" />
                Content Extraction
              </h3>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={selector}
                  onChange={(e) => setSelector(e.target.value)}
                  placeholder="CSS selector (optional for full page)..."
                  className="flex-1 px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleExtract}
                  className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded transition-colors text-sm"
                >
                  Extract
                </button>
              </div>
              {extractedContent && (
                <div className="bg-gray-900 rounded p-3 text-xs font-mono max-h-40 overflow-auto">
                  {extractedContent}
                </div>
              )}
            </div>

            {/* File Operations */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Download className="w-4 h-4 text-orange-400" />
                File Operations
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={handleScreenshot}
                  className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded transition-colors text-sm"
                >
                  <Camera className="w-4 h-4" />
                  Screenshot
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions Bar */}
      <div className="border-t border-gray-700 px-4 py-2 bg-gray-800 flex items-center justify-between">
        <div className="text-xs text-gray-400">
          Selected: {selectedPageId ? `Page ${selectedPageId.slice(-4)}` : 'None'}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (selectedPageId) {
                window.open('about:blank', '_blank')
              }
            }}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Open in External Browser"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default BrowserSessions
