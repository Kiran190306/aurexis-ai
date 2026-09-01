/**
 * File Browser Component
 * File system browser with directory navigation, file operations, and search.
 */
import React, { useState } from 'react'
import { 
  ChevronRight, 
  ChevronDown, 
  File, 
  Folder, 
  FolderOpen, 
  Search, 
  Plus, 
  Upload,
  Download,
  Trash2,
  Copy,
  Scissors,
  RefreshCw
} from 'lucide-react'
import { 
  useBrowseDirectory, 
  useReadFile, 
  useWriteFile, 
  useDeleteFile, 
  useRenameFile,
  useMoveFile,
  useCopyFile,
  useSearchFiles,
  useCreateArchive,
  useExtractArchive
} from '../../services/computer-hooks'

interface FileItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size: number
}

const FileBrowser: React.FC = () => {
  const [currentPath, setCurrentPath] = useState('./data/computer')
  const [files, setFiles] = useState<FileItem[]>([])
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [fileContent, setFileContent] = useState('')
  const [showFileContent, setShowFileContent] = useState(false)

  const browseDirectory = useBrowseDirectory()
  const readFile = useReadFile()
  const writeFile = useWriteFile()
  const deleteFile = useDeleteFile()
  const renameFile = useRenameFile()
  const moveFile = useMoveFile()
  const copyFile = useCopyFile()
  const searchFiles = useSearchFiles()

  const handleBrowse = async (path: string) => {
    try {
      const result = await browseDirectory.mutateAsync({ path, depth: 1 })
      if (result.success && result.output) {
        const parsed = JSON.parse(result.output)
        setFiles(parsed)
        setCurrentPath(path)
      }
    } catch (error) {
      console.error('Failed to browse directory:', error)
    }
  }

  const handleFileClick = async (file: FileItem) => {
    if (file.type === 'directory') {
      handleBrowse(file.path)
    } else {
      setSelectedFile(file)
      try {
        const result = await readFile.mutateAsync({ path: file.path })
        if (result.success && result.output) {
          setFileContent(result.output)
          setShowFileContent(true)
        }
      } catch (error) {
        console.error('Failed to read file:', error)
      }
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    try {
      const result = await searchFiles.mutateAsync({
        path: currentPath,
        pattern: searchQuery
      })
      if (result.success && result.output) {
        const parsed = JSON.parse(result.output)
        setFiles(parsed)
      }
    } catch (error) {
      console.error('Failed to search files:', error)
    }
  }

  const handleDelete = async () => {
    if (!selectedFile) return
    try {
      const result = await deleteFile.mutateAsync({ path: selectedFile.path })
      if (result.success) {
        handleBrowse(currentPath)
        setSelectedFile(null)
      }
    } catch (error) {
      console.error('Failed to delete file:', error)
    }
  }

  const handleRefresh = () => {
    handleBrowse(currentPath)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <span className="text-sm text-gray-300 truncate max-w-md">
            {currentPath}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {showSearch ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search files..."
                className="px-3 py-1 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleSearch}
                className="p-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
              >
                <Search className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setShowSearch(false)
                  setSearchQuery('')
                }}
                className="p-2 hover:bg-gray-700 rounded transition-colors"
              >
                ×
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowSearch(true)}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
              title="Search"
            >
              <Search className="w-4 h-4" />
            </button>
          )}
          <button
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="New File"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Upload"
          >
            <Upload className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-800 sticky top-0">
            <tr>
              <th className="px-4 py-2 text-left text-gray-400 font-medium">Name</th>
              <th className="px-4 py-2 text-left text-gray-400 font-medium">Type</th>
              <th className="px-4 py-2 text-right text-gray-400 font-medium">Size</th>
              <th className="px-4 py-2 text-right text-gray-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file, index) => (
              <tr
                key={index}
                onClick={() => handleFileClick(file)}
                className={`border-b border-gray-800 hover:bg-gray-800 cursor-pointer ${
                  selectedFile?.path === file.path ? 'bg-blue-900/30' : ''
                }`}
              >
                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    {file.type === 'directory' ? (
                      <Folder className="w-4 h-4 text-yellow-400" />
                    ) : (
                      <File className="w-4 h-4 text-gray-400" />
                    )}
                    <span className="truncate">{file.name}</span>
                  </div>
                </td>
                <td className="px-4 py-2 text-gray-400 capitalize">{file.type}</td>
                <td className="px-4 py-2 text-right text-gray-400">
                  {file.type === 'file' ? formatFileSize(file.size) : '-'}
                </td>
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-1">
                    {file.type === 'file' && (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            // Copy functionality
                          }}
                          className="p-1 hover:bg-gray-700 rounded transition-colors"
                          title="Copy"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            // Move functionality
                          }}
                          className="p-1 hover:bg-gray-700 rounded transition-colors"
                          title="Move"
                        >
                          <Scissors className="w-3 h-3" />
                        </button>
                      </>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFile(file)
                        handleDelete()
                      }}
                      className="p-1 hover:bg-red-900/50 rounded transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-3 h-3 text-red-400" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {files.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                  No files in this directory
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* File Content Modal */}
      {showFileContent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg shadow-xl w-3/4 h-3/4 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <h3 className="font-medium">{selectedFile?.name}</h3>
              <button
                onClick={() => {
                  setShowFileContent(false)
                  setFileContent('')
                }}
                className="p-1 hover:bg-gray-700 rounded transition-colors"
              >
                ×
              </button>
            </div>
            <pre className="flex-1 overflow-auto p-4 text-sm text-gray-300 font-mono whitespace-pre-wrap">
              {fileContent}
            </pre>
          </div>
        </div>
      )}

      {/* Status Bar */}
      <div className="px-4 py-2 border-t border-gray-700 bg-gray-800 text-xs text-gray-400">
        {files.length} item(s) • {selectedFile ? `Selected: ${selectedFile.name}` : 'No selection'}
      </div>
    </div>
  )
}

export default FileBrowser
