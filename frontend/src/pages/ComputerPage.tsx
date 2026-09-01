import { useState } from 'react'
import { Monitor, Plus, Activity } from 'lucide-react'
import { AutomationDashboard } from '../components/computer/AutomationDashboard'
import { WorkflowBuilder } from '../components/computer/WorkflowBuilder'
import { ExecutionView } from '../components/computer/ExecutionView'
import { ComputerService, WorkflowDefinition } from '../services/computer'
import toast from 'react-hot-toast'

type Tab = 'dashboard' | 'create' | 'execution'

export default function ComputerPage() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null)
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowDefinition | null>(null)

  const handleExecuteWorkflow = async (workflowId: string) => {
    try {
      await ComputerService.executeWorkflow({ workflow_id: workflowId })
      toast.success('Workflow execution started')
    } catch (error) {
      console.error('Failed to execute workflow:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to execute workflow')
    }
  }

  const handleViewExecution = (executionId: string) => {
    setSelectedExecutionId(executionId)
    setActiveTab('execution')
  }

  const handleWorkflowSaved = (workflow: WorkflowDefinition) => {
    setSelectedWorkflow(workflow)
    setActiveTab('dashboard')
  }


  const tabs = [
    { id: 'dashboard' as Tab, label: 'Dashboard', icon: Activity },
    { id: 'create' as Tab, label: 'Create Workflow', icon: Plus },
    { id: 'execution' as Tab, label: 'Execution View', icon: Monitor },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Computer Automation</h1>
        <p className="mt-2 text-muted-foreground">Automate file system, terminal, browser, and desktop operations</p>
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
        {activeTab === 'dashboard' && (
          <AutomationDashboard
            onExecuteWorkflow={handleExecuteWorkflow}
            onViewExecution={handleViewExecution}
          />
        )}

        {activeTab === 'create' && (
          <WorkflowBuilder
            existingWorkflow={selectedWorkflow || undefined}
            onSave={handleWorkflowSaved}
            onExecute={handleExecuteWorkflow}
            onCancel={() => setActiveTab('dashboard')}
          />
        )}

        {activeTab === 'execution' && selectedExecutionId && (
          <ExecutionView
            executionId={selectedExecutionId}
            onClose={() => setActiveTab('dashboard')}
          />
        )}
      </div>
    </div>
  )
}
