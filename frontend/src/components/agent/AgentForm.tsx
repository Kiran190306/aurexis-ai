import { useState } from 'react'
import { Save, X } from 'lucide-react'
import { AgentService, Agent, AgentCreate, AgentUpdate, AgentType } from '../../services/agent'
import toast from 'react-hot-toast'

interface AgentFormProps {
  existingAgent?: Agent
  onSave?: (agent: Agent) => void
  onCancel?: () => void
}

export function AgentForm({ existingAgent, onSave, onCancel }: AgentFormProps) {
  const [name, setName] = useState(existingAgent?.name || '')
  const [description, setDescription] = useState(existingAgent?.description || '')
  const [agentType, setAgentType] = useState(existingAgent?.agent_type || AgentType.GENERAL)
  const [systemPrompt, setSystemPrompt] = useState(existingAgent?.system_prompt || '')
  const [model, setModel] = useState(existingAgent?.model || 'gpt-4-turbo-preview')
  const [temperature, setTemperature] = useState(existingAgent?.temperature || 70)
  const [maxTokens, setMaxTokens] = useState(existingAgent?.max_tokens || 4096)
  const [memoryEnabled, setMemoryEnabled] = useState(existingAgent?.memory_enabled ?? true)
  const [memoryType, setMemoryType] = useState(existingAgent?.memory_type || 'episodic')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!name || !description || !systemPrompt) {
      toast.error('Please fill in all required fields')
      return
    }

    try {
      setSaving(true)
      if (existingAgent) {
        const updateData: AgentUpdate = {
          name,
          description,
          system_prompt: systemPrompt,
          model,
          temperature,
          max_tokens: maxTokens,
          memory_enabled: memoryEnabled,
          memory_type: memoryType,
        }
        const updatedAgent = await AgentService.updateAgent(existingAgent.id, updateData)
        toast.success('Agent updated successfully')
        onSave?.(updatedAgent)
      } else {
        const createData: AgentCreate = {
          name,
          description,
          agent_type: agentType,
          system_prompt: systemPrompt,
          model,
          temperature,
          max_tokens: maxTokens,
          memory_enabled: memoryEnabled,
          memory_type: memoryType,
        }
        const newAgent = await AgentService.createAgent(createData)
        toast.success('Agent created successfully')
        onSave?.(newAgent)
      }
    } catch (error) {
      console.error('Failed to save agent:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to save agent')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          {existingAgent ? 'Edit Agent' : 'Create Agent'}
        </h2>
        <button
          onClick={onCancel}
          className="p-2 hover:bg-accent rounded-md transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Form */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="My Agent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description *</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder="Describe what this agent does..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Agent Type</label>
          <select
            value={agentType}
            onChange={(e) => setAgentType(e.target.value as AgentType)}
            disabled={!!existingAgent}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
          >
            <option value={AgentType.GENERAL}>General</option>
            <option value={AgentType.SPECIALIST}>Specialist</option>
            <option value={AgentType.ORCHESTRATOR}>Orchestrator</option>
            <option value={AgentType.WORKER}>Worker</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">System Prompt *</label>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={6}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none font-mono text-sm"
            placeholder="You are a helpful AI assistant..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Model</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Temperature (0-100)</label>
            <input
              type="number"
              value={temperature}
              onChange={(e) => setTemperature(parseInt(e.target.value) || 70)}
              min={0}
              max={100}
              className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Max Tokens</label>
          <input
            type="number"
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value) || 4096)}
            min={1}
            max={128000}
            className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Memory Enabled</label>
            <select
              value={memoryEnabled ? 'true' : 'false'}
              onChange={(e) => setMemoryEnabled(e.target.value === 'true')}
              className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Memory Type</label>
            <select
              value={memoryType}
              onChange={(e) => setMemoryType(e.target.value)}
              disabled={!memoryEnabled}
              className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            >
              <option value="episodic">Episodic</option>
              <option value="semantic">Semantic</option>
              <option value="working">Working</option>
            </select>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-4 border-t border-border">
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
          {saving ? 'Saving...' : existingAgent ? 'Update' : 'Create'}
        </button>
      </div>
    </div>
  )
}
