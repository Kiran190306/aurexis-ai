/**
 * Terminal Console Component
 * Terminal interface for executing shell commands with streaming output.
 */
import React, { useState, useRef, useEffect } from 'react'
import { Play, Square, Folder, Settings, History as HistoryIcon } from 'lucide-react'
import { 
  useExecuteCommand, 
  useCancelCommand, 
  useWorkingDirectory,
  useSetWorkingDirectory,
  useCommandHistory,
  useRunningCommands
} from '../../services/computer-hooks'

const TerminalConsole: React.FC = () => {
  const [command, setCommand] = useState('')
  const [output, setOutput] = useState<string[]>([])
  const [isExecuting, setIsExecuting] = useState(false)
  const [currentActionId, setCurrentActionId] = useState<string | null>(null)
  const outputRef = useRef<HTMLDivElement>(null)

  const executeCommand = useExecuteCommand()
  const cancelCommand = useCancelCommand()
  const { data: workingDir } = useWorkingDirectory()
  const setWorkingDir = useSetWorkingDirectory()
  const { data: history } = useCommandHistory()
  const { data: running } = useRunningCommands()

  // Auto-scroll to bottom
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [output])

  const handleExecute = async () => {
    if (!command.trim()) return

    setIsExecuting(true)
    setOutput(prev => [...prev, `$ ${command}`])

    try {
      const result = await executeCommand.mutateAsync({
        command,
        working_directory: workingDir?.working_directory,
        stream_output: true,
      })

      setCurrentActionId(result.action_id)

      if (result.output) {
        setOutput(prev => [...prev, result.output])
      }

      if (result.error) {
        setOutput(prev => [...prev, `Error: ${result.error}`])
      }
    } catch (error) {
      setOutput(prev => [...prev, `Error: ${String(error)}`])
    } finally {
      setIsExecuting(false)
      setCommand('')
      setCurrentActionId(null)
    }
  }

  const handleCancel = async () => {
    if (currentActionId) {
      await cancelCommand.mutateAsync({ action_id: currentActionId })
      setIsExecuting(false)
      setOutput(prev => [...prev, 'Command cancelled'])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleExecute()
    }
  }

  const clearOutput = () => {
    setOutput([])
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-green-400 font-mono text-sm">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center gap-2">
          <Folder className="w-4 h-4 text-gray-400" />
          <span className="text-gray-300 text-xs">
            {workingDir?.working_directory || '~'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearOutput}
            className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
          >
            Clear
          </button>
          <button
            onClick={() => setWorkingDir.mutateAsync({ path: '~' })}
            className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Output Area */}
      <div
        ref={outputRef}
        className="flex-1 overflow-auto p-4 space-y-1"
      >
        {output.length === 0 && (
          <div className="text-gray-500">
            Jarvis AI Terminal v1.0
            Type 'help' for available commands or enter any shell command.
          </div>
        )}
        {output.map((line, index) => (
          <div key={index} className="whitespace-pre-wrap break-words">
            {line}
          </div>
        ))}
        {isExecuting && (
          <div className="animate-pulse">
            <span className="text-blue-400">●</span> Executing...
          </div>
        )}
      </div>

      {/* Command Input */}
      <div className="border-t border-gray-700 p-4 bg-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-green-400">$</span>
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isExecuting}
            placeholder="Enter command..."
            className="flex-1 bg-transparent border-none outline-none text-green-400 placeholder-gray-500"
            autoFocus
          />
          {isExecuting ? (
            <button
              onClick={handleCancel}
              className="p-2 bg-red-600 hover:bg-red-700 rounded transition-colors"
              title="Cancel"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleExecute}
              disabled={!command.trim()}
              className="p-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded transition-colors"
              title="Execute"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Running Commands Indicator */}
      {running?.running && running.running.length > 0 && (
        <div className="px-4 py-2 bg-yellow-900/30 border-t border-yellow-700">
          <div className="flex items-center gap-2 text-yellow-400 text-xs">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
            {running.running.length} command(s) running
          </div>
        </div>
      )}
    </div>
  )
}

export default TerminalConsole
