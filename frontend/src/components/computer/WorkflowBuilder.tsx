import { useState } from 'react'
import { Plus, Trash2, GripVertical, Save, Play, ArrowUp, ArrowDown, Settings } from 'lucide-react'
import { ComputerService, WorkflowStep, ComputerActionType, CreateWorkflowRequest, WorkflowDefinition } from '../../services/computer'
import toast from 'react-hot-toast'

interface WorkflowBuilderProps {
  onSave?: (workflow: WorkflowDefinition) => void
  onExecute?: (workflowId: string) => void
  onCancel?: () => void
  existingWorkflow?: WorkflowDefinition
}

const ACTION_LABELS: Record<ComputerActionType, string> = {
  [ComputerActionType.FILE_READ]: 'Read File',
  [ComputerActionType.FILE_WRITE]: 'Write File',
  [ComputerActionType.FILE_DELETE]: 'Delete File',
  [ComputerActionType.FILE_RENAME]: 'Rename File',
  [ComputerActionType.FILE_MOVE]: 'Move File',
  [ComputerActionType.FILE_COPY]: 'Copy File',
  [ComputerActionType.DIRECTORY_BROWSE]: 'Browse Directory',
  [ComputerActionType.DIRECTORY_CREATE]: 'Create Directory',
  [ComputerActionType.DIRECTORY_DELETE]: 'Delete Directory',
  [ComputerActionType.FILE_SEARCH]: 'Search Files',
  [ComputerActionType.FILE_ARCHIVE]: 'Create Archive',
  [ComputerActionType.FILE_EXTRACT]: 'Extract Archive',
  [ComputerActionType.TERMINAL_EXECUTE]: 'Execute Command',
  [ComputerActionType.TERMINAL_CANCEL]: 'Cancel Command',
  [ComputerActionType.TERMINAL_STREAM]: 'Stream Terminal',
  [ComputerActionType.BROWSER_OPEN]: 'Open Browser',
  [ComputerActionType.BROWSER_NAVIGATE]: 'Navigate',
  [ComputerActionType.BROWSER_CLICK]: 'Click Element',
  [ComputerActionType.BROWSER_FILL]: 'Fill Form',
  [ComputerActionType.BROWSER_EXTRACT]: 'Extract Content',
  [ComputerActionType.BROWSER_DOWNLOAD]: 'Download File',
  [ComputerActionType.BROWSER_UPLOAD]: 'Upload File',
  [ComputerActionType.BROWSER_SCREENSHOT]: 'Take Screenshot',
  [ComputerActionType.BROWSER_CLOSE]: 'Close Browser',
  [ComputerActionType.DESKTOP_LAUNCH]: 'Launch Application',
  [ComputerActionType.DESKTOP_CLOSE]: 'Close Application',
  [ComputerActionType.DESKTOP_WINDOW]: 'Manage Window',
  [ComputerActionType.DESKTOP_CLIPBOARD]: 'Set Clipboard',
  [ComputerActionType.DESKTOP_NOTIFICATION]: 'Send Notification',
  [ComputerActionType.DESKTOP_CAPTURE]: 'Capture Screen',
}

export function WorkflowBuilder({ onSave, onExecute, onCancel, existingWorkflow }: WorkflowBuilderProps) {
  const [workflowId, setWorkflowId] = useState(existingWorkflow?.workflow_id || '')
  const [name, setName] = useState(existingWorkflow?.name || '')
  const [description, setDescription] = useState(existingWorkflow?.description || '')
  const [steps, setSteps] = useState<WorkflowStep[]>(existingWorkflow?.steps || [])
  const [parallel, setParallel] = useState(existingWorkflow?.parallel || false)
  const [requiresApproval, setRequiresApproval] = useState(existingWorkflow?.requires_approval ?? true)
  const [timeout, setTimeout] = useState(existingWorkflow?.timeout || 600)
  const [saving, setSaving] = useState(false)
  const [showStepEditor, setShowStepEditor] = useState(false)
  const [editingStepIndex, setEditingStepIndex] = useState<number | null>(null)

  const addStep = () => {
    const newStep: WorkflowStep = {
      step_id: `step_${Date.now()}`,
      action_type: ComputerActionType.FILE_READ,
      parameters: {},
      depends_on: [],
      retry_policy: null,
      rollback_action: null,
    }
    setSteps([...steps, newStep])
    setEditingStepIndex(steps.length)
    setShowStepEditor(true)
  }

  const removeStep = (index: number) => {
    if (!confirm('Are you sure you want to remove this step?')) {
      return
    }
    const newSteps = steps.filter((_, i) => i !== index)
    setSteps(newSteps)
  }

  const moveStepUp = (index: number) => {
    if (index === 0) return
    const newSteps = [...steps]
    ;[newSteps[index - 1], newSteps[index]] = [newSteps[index], newSteps[index - 1]]
    setSteps(newSteps)
  }

  const moveStepDown = (index: number) => {
    if (index === steps.length - 1) return
    const newSteps = [...steps]
    ;[newSteps[index], newSteps[index + 1]] = [newSteps[index + 1], newSteps[index]]
    setSteps(newSteps)
  }

  const updateStep = (index: number, updatedStep: WorkflowStep) => {
    const newSteps = [...steps]
    newSteps[index] = updatedStep
    setSteps(newSteps)
  }

  const handleSave = async () => {
    if (!workflowId || !name || !description) {
      toast.error('Please fill in all required fields')
      return
    }

    if (steps.length === 0) {
      toast.error('Please add at least one step')
      return
    }

    try {
      setSaving(true)
      const request: CreateWorkflowRequest = {
        workflow_id: workflowId,
        name,
        description,
        steps,
        parallel,
        requires_approval: requiresApproval,
        timeout,
      }

      const workflow = await ComputerService.createWorkflow(request)
      toast.success('Workflow saved successfully')
      onSave?.(workflow)
    } catch (error) {
      console.error('Failed to save workflow:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to save workflow')
    } finally {
      setSaving(false)
    }
  }

  const handleExecute = async () => {
    if (!workflowId) {
      toast.error('Please save the workflow first')
      return
    }
    onExecute?.(workflowId)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          {existingWorkflow ? 'Edit Workflow' : 'Create Workflow'}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Workflow Details */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Workflow ID *</label>
          <input
            type="text"
            value={workflowId}
            onChange={(e) => setWorkflowId(e.target.value)}
            disabled={!!existingWorkflow}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            placeholder="unique-workflow-id"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="My Workflow"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description *</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder="Describe what this workflow does..."
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Timeout (seconds)</label>
            <input
              type="number"
              value={timeout}
              onChange={(e) => setTimeout(parseInt(e.target.value) || 600)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              min={1}
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="parallel"
              checked={parallel}
              onChange={(e) => setParallel(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="parallel" className="text-sm">Parallel Execution</label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="approval"
              checked={requiresApproval}
              onChange={(e) => setRequiresApproval(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="approval" className="text-sm">Requires Approval</label>
          </div>
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Workflow Steps ({steps.length})</h3>
          <button
            onClick={addStep}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Step
          </button>
        </div>

        {steps.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-border rounded-lg">
            <p className="text-muted-foreground">No steps added yet</p>
            <button
              onClick={addStep}
              className="mt-2 text-primary hover:underline"
            >
              Add your first step
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {steps.map((step, index) => (
              <div
                key={step.step_id}
                className="p-4 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="flex flex-col gap-1 pt-1">
                    <button
                      onClick={() => moveStepUp(index)}
                      disabled={index === 0}
                      className="p-1 hover:bg-accent rounded disabled:opacity-30"
                    >
                      <ArrowUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => moveStepDown(index)}
                      disabled={index === steps.length - 1}
                      className="p-1 hover:bg-accent rounded disabled:opacity-30"
                    >
                      <ArrowDown className="w-4 h-4" />
                    </button>
                  </div>

                  <GripVertical className="w-5 h-5 text-muted-foreground mt-1" />

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{ACTION_LABELS[step.action_type]}</p>
                        <p className="text-sm text-muted-foreground">Step ID: {step.step_id}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setEditingStepIndex(index)
                            setShowStepEditor(true)
                          }}
                          className="p-1.5 hover:bg-accent rounded-md transition-colors"
                          title="Edit Step"
                        >
                          <Settings className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => removeStep(index)}
                          className="p-1.5 hover:bg-accent rounded-md transition-colors text-red-500"
                          title="Remove Step"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {Object.keys(step.parameters).length > 0 && (
                      <div className="mt-2 p-2 bg-muted rounded text-xs">
                        <p className="font-medium mb-1">Parameters:</p>
                        {Object.entries(step.parameters).map(([key, value]) => (
                          <div key={key} className="flex gap-2">
                            <span className="text-muted-foreground">{key}:</span>
                            <span className="font-mono">{String(value).substring(0, 50)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Execute Button */}
      {existingWorkflow && (
        <div className="pt-4 border-t border-border">
          <button
            onClick={handleExecute}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
          >
            <Play className="w-4 h-4" />
            Execute Workflow
          </button>
        </div>
      )}

      {/* Step Editor Modal */}
      {showStepEditor && editingStepIndex !== null && (
        <StepEditor
          step={steps[editingStepIndex]}
          onSave={(updatedStep) => {
            updateStep(editingStepIndex, updatedStep)
            setShowStepEditor(false)
            setEditingStepIndex(null)
          }}
          onCancel={() => {
            setShowStepEditor(false)
            setEditingStepIndex(null)
          }}
        />
      )}
    </div>
  )
}

interface StepEditorProps {
  step: WorkflowStep
  onSave: (step: WorkflowStep) => void
  onCancel: () => void
}

function StepEditor({ step, onSave, onCancel }: StepEditorProps) {
  const [actionType, setActionType] = useState(step.action_type)
  const [parameters, setParameters] = useState<Record<string, unknown>>(step.parameters)

  const handleParameterChange = (key: string, value: string) => {
    setParameters({ ...parameters, [key]: value })
  }

  const addParameter = () => {
    const key = prompt('Enter parameter name:')
    if (key) {
      setParameters({ ...parameters, [key]: '' })
    }
  }

  const removeParameter = (key: string) => {
    const newParams = { ...parameters }
    delete newParams[key]
    setParameters(newParams)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">Edit Step</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Action Type</label>
            <select
              value={actionType}
              onChange={(e) => setActionType(e.target.value as ComputerActionType)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {Object.entries(ACTION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium">Parameters</label>
              <button
                onClick={addParameter}
                className="text-sm text-primary hover:underline"
              >
                + Add Parameter
              </button>
            </div>
            <div className="space-y-2">
              {Object.entries(parameters).map(([key, value]) => (
                <div key={key} className="flex gap-2">
                  <input
                    type="text"
                    value={key}
                    disabled
                    className="w-1/3 px-3 py-2 border border-border rounded-md bg-muted opacity-50"
                  />
                  <input
                    type="text"
                    value={String(value)}
                    onChange={(e) => handleParameterChange(key, e.target.value)}
                    className="flex-1 px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <button
                    onClick={() => removeParameter(key)}
                    className="p-2 text-red-500 hover:bg-accent rounded-md"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave({ ...step, action_type: actionType, parameters })}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Save Step
          </button>
        </div>
      </div>
    </div>
  )
}
