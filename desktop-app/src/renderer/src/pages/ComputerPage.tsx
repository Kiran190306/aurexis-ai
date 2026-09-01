/**
 * Computer Use & Automation Page
 * Main dashboard for computer control with tabs for terminal, file browser, browser automation, workflows, permissions, and history.
 */
import React, { useState } from 'react'
import { 
  Terminal, 
  FolderOpen, 
  Globe, 
  Workflow, 
  Shield, 
  History,
  Monitor
} from 'lucide-react'

// Components (will be implemented as sub-components)
import TerminalConsole from '../components/computer/TerminalConsole'
import FileBrowser from '../components/computer/FileBrowser'
import BrowserSessions from '../components/computer/BrowserSessions'
import WorkflowBuilder from '../components/computer/WorkflowBuilder'
import PermissionManager from '../components/computer/PermissionManager'
import ExecutionTimeline from '../components/computer/ExecutionTimeline'

const ComputerPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('terminal')

  const tabs = [
    { id: 'terminal', label: 'Terminal', icon: Terminal },
    { id: 'files', label: 'File Browser', icon: FolderOpen },
    { id: 'browser', label: 'Browser', icon: Globe },
    { id: 'workflows', label: 'Workflows', icon: Workflow },
    { id: 'permissions', label: 'Permissions', icon: Shield },
    { id: 'history', label: 'History', icon: History },
  ]

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-700 px-6 py-4">
        <div className="flex items-center gap-3">
          <Monitor className="w-6 h-6 text-blue-400" />
          <h1 className="text-2xl font-bold">Computer Control</h1>
        </div>
        <p className="text-gray-400 text-sm mt-1">
          Safe computer automation with permission-based execution
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-700 px-6">
        <div className="flex gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400 bg-gray-800'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:bg-gray-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'terminal' && <TerminalConsole />}
        {activeTab === 'files' && <FileBrowser />}
        {activeTab === 'browser' && <BrowserSessions />}
        {activeTab === 'workflows' && <WorkflowBuilder />}
        {activeTab === 'permissions' && <PermissionManager />}
        {activeTab === 'history' && <ExecutionTimeline />}
      </div>
    </div>
  )
}

export default ComputerPage
