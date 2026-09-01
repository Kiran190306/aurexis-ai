/**
 * Workflow Builder Component
 * Visual workflow builder for creating multi-step automation workflows.
 */
import React, { useState } from 'react'
import { 
  Plus, 
  Play, 
  Trash2, 
  Copy, 
  Save, 
  ChevronRight, 
  ChevronDown,
  Settings,
  Clock,
  Shield
} from 'lucide-react'
import { 
  useCreateWorkflow, 
  useWorkflows, 
  useExecuteWorkflow, 
  useCancelWorkflow,
  useWorkflowExecution
} from '../../services/computer-hooks'

interface WorkflowStep {
  step_id: string
  action_type: string
  parameters: Record<string, any>
  depends_on: string[]
  retry_policy?: { max_retries: number; delay: number }
  rollback_action?: Record<string, any>
}

const WorkflowBuilder: React.FC = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null)
  const [workflowName, setWorkflowName] = useState('')
  const [workflowDescription, setWorkflowDescription] = useState('')
  const [steps, setSteps] = useState<WorkflowStep[]>([])
  const [parallel, setParallel] = useState(false)
  const [requiresApproval, setRequiresApproval] = useState(true)
  const [timeout, setTimeout] = useState(600)
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())

  const createWorkflow = useCreateWorkflow()
  const { data: workflows } = useWorkflows()
  const executeWorkflow = useExecuteWorkflow()
  const cancelWorkflow = useCancelWorkflow()
  const [activeExecution, setActiveExecution] = useState<string | null>(null)
  const { data: execution } = useWorkflowExecution(activeExecution || '')

  const actionTypes = [
    'file_read', 'file_write', 'file_delete', 'file_move', 'file_copy',
    'terminal_execute', 'browser_open', 'browser_navigate', 'browser_click',
    'browser_fill', 'desktop_launch', 'desktop_capture'
  ]

  const addStep = () => {
    const newStep: WorkflowStep = {
      step_id: `step_${Date.now()}`,
      action_type: 'file_read',
      parameters: {},
      depends_on: [],
      retry_policy: { max_retries: 0, delay: 1 }
    }
    setSteps([...steps, newStep])
    setExpandedSteps(new Set([...expandedSteps, newStep.step_id]))
  }

  const removeStep = (stepId: string) => {
    setSteps(steps.filter(s => s.step_id !== stepId))
    setExpandedSteps(new Set([...expandedSteps].filter(id => id !== stepId)))
  }

  const updateStep = (stepId: string, updates: Partial<WorkflowStep>) => {
    setSteps(steps.map(s => s.step_id === stepId ? { ...s, ...updates } : s))
  }

  const toggleExpand = (stepId: string) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId)
    } else {
      newExpanded.add(stepId)
    }
    setExpandedSteps(newExpanded)
  }

  const handleSave = async () => {
    if (!workflowName.trim()) return
    
    try {
      await createWorkflow.mutateAsync({
        workflow_id: workflowName.toLowerCase().replace(/\s+/g, '_'),
        name: workflowName,
        description: workflowDescription,
        steps,
        parallel,
        requires_approval,
        timeout
      })
      
      // Reset form
      setWorkflowName('')
      setWorkflowDescription('')
      setSteps([])
    } catch (error) {
      console.error('Failed to create workflow:', error)
    }
  }

  const handleExecute = async (workflowId: string) => {
    try {
      const result = await executeWorkflow.mutateAsync({ workflow_id })
      setActiveExecution(result.execution_id)
    } catch (error) {
      console.error('Failed to execute workflow:', error)
    }
  }

  const handleCancel = async () => {
    if (activeExecution) {
      try {
        await cancelWorkflow.mutateAsync({ execution_id: activeExecution })
        setActiveExecution(null)
      } catch (error) {
        console.error('Failed to cancel workflow:', error)
      }
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-700 px-4 py-3 bg-gray-800">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-400" />
            Workflow Builder
          </h2>
          <button
            onClick={addStep}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Step
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Workflow List */}
        <div className="w-64 border-r border-gray-700 bg-gray-800 overflow-auto">
          <div className="p-3">
            <h3 className="text-xs font-medium text-gray-400 mb-2">Saved Workflows</h3>
            <div className="space-y-1">
              {workflows?.map((workflow: any) => (
                <button
                  key={workflow.id}
                  onClick={() => handleExecute(workflow.workflow_id)}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                >
                  <span className="truncate">{workflow.name}</span>
                  <Play className="w-3 h-3 text-green-400" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Workflow Editor */}
        <div className="flex-1 overflow-auto p-4">
          {/* Workflow Settings */}
          <div className="bg-gray-800 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-medium mb-3">Workflow Settings</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Name</label>
                <input
                  type="text"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  placeholder="Workflow name..."
                  className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Timeout (seconds)</label>
                <input
                  type="number"
                  value={timeout}
                  onChange={(e) => setTimeout(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-xs text-gray-400 mb-1">Description</label>
                <textarea
                  value={workflowDescription}
                  onChange={(e) => setWorkflowDescription(e.target.value)}
                  placeholder="Describe what this workflow does..."
                  rows={2}
                  className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>
            </div>
            <div className="flex items-center gap-4 mt-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={parallel}
                  onChange={(e) => setParallel(e.target.checked)}
                  className="rounded"
                />
                <span>Parallel Execution</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={requiresApproval}
                  onChange={(e) => setRequiresApproval(e.target.checked)}
                  className="rounded"
                />
                <span>Require Approval</span>
              </label>
            </div>
            <button
              onClick={handleSave}
              className="mt-3 flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors text-sm"
            >
              <Save className="w-4 h-4" />
              Save Workflow
            </button>
          </div>

          {/* Steps */}
          <div className="space-y-2">
            {steps.map((step, index) => (
              <div key={step.step_id} className="bg-gray-800 rounded-lg overflow-hidden">
                <div
                  className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-700"
                  onClick={() => toggleExpand(step.step_id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-gray-400 text-sm">{index + 1}</span>
                    <ChevronRight 
                      className={`w-4 h-4 transition-transform ${
                        expandedSteps.has(step.step_id) ? 'rotate-90' : ''
                      }`} 
                    />
                    <select
                      value={step.action_type}
                      onChange={(e) => updateStep(step.step_id, { action_type: e.target.value })}
                      className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm focus:outline-none"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {actionTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      removeStep(step.step_id)
                    }}
                    className="p-1 hover:bg-red-900/50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>

                {expandedSteps.has(step.step_id) && (
                  <div className="px-4 py-3 border-t border-gray-700 space-y-3">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Parameters (JSON)</label>
                      <textarea
                        value={JSON.stringify(step.parameters, null, 2)}
                        onChange={(e) => {
                          try {
                            updateStep(step.step_id, { parameters: JSON.parse(e.target.value) })
                          } catch {
                            // Invalid JSON, ignore
                          }
                        }}
                        rows={3}
                        className="w-full px-3 py-2 text-xs bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500 font-mono resize-none"
                      />
                    </div>
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <label className="block text-xs text-gray-400 mb-1">Max Retries</label>
                        <input
                          type="number"
                          value={step.retry_policy?.max_retries || 0}
                          onChange={(e) => updateStep(step.step_id, {
                            retry_policy: { 
                              ...step.retry_policy, 
                              max_retries: Number(e.target.value),
                              delay: step.retry_policy?.delay || 1
                            }
                          })}
                          className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs text-gray-400 mb-1">Retry Delay (s)</label>
                        <input
                          type="number"
                          value={step.retry_policy?.delay || 1}
                          onChange={(e) => updateStep(step.step_id, {
                            retry_policy: { 
                              ...step.retry_policy,
                              max_retries: step.retry_policy?.max_retries || 0,
                              delay: Number(e.target.value)
                            }
                          })}
                          className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Execution Status */}
      {activeExecution && execution && (
        <div className="border-t border-gray-700 px-4 py-3 bg-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${
                execution.status === 'running' ? 'bg-green-400 animate-pulse' :
                execution.status === 'completed' ? 'bg-blue-400' :
                execution.status === 'failed' ? 'bg-red-400' : 'bg-yellow-400'
              }`} />
              <span className="text-sm">
                {execution.status.charAt(0).toUpperCase() + execution.status.slice(1)}
              </span>
              <span className="text-xs text-gray-400">
                {execution.completed_steps.length} / {steps.length} steps
              </span>
            </div>
            {execution.status === 'running' && (
              <button
                onClick={handleCancel}
                className="flex items-center gap-2 px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded transition-colors text-sm"
              >
                <Clock className="w-4 h-4" />
                Cancel
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default WorkflowBuilder
