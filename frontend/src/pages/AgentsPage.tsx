import { useState } from 'react'
import { Activity, Plus, Cpu } from 'lucide-react'
import { AgentDashboard } from '../components/agent/AgentDashboard'
import { AgentForm } from '../components/agent/AgentForm'
import { AgentList } from '../components/agent/AgentList'
import { AgentDetails } from '../components/agent/AgentDetails'
import { AgentExecution } from '../components/agent/AgentExecution'
import { Agent } from '../services/agent'
import toast from 'react-hot-toast'

type Tab = 'dashboard' | 'list' | 'create' | 'details' | 'execution'

export default function AgentsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [selectedExecutionUuid, setSelectedExecutionUuid] = useState<string | null>(null)

  const handleAgentSaved = (agent: Agent) => {
    setSelectedAgent(agent)
    setActiveTab('list')
  }

  const handleAgentDeleted = (agent: Agent) => {
    toast.success(`Agent "${agent.name}" deleted`)
  }

  const handleViewAgent = (agent: Agent) => {
    setSelectedAgent(agent)
    setActiveTab('details')
  }

  const handleEditAgent = (agent: Agent) => {
    setSelectedAgent(agent)
    setActiveTab('create')
  }

  const handleExecuteAgent = (agent: Agent) => {
    setSelectedAgent(agent)
    setActiveTab('execution')
  }

  const handleViewExecution = (planUuid: string) => {
    setSelectedExecutionUuid(planUuid)
    setActiveTab('execution')
  }

  const tabs = [
    { id: 'dashboard' as Tab, label: 'Dashboard', icon: Activity },
    { id: 'list' as Tab, label: 'All Agents', icon: Cpu },
    { id: 'create' as Tab, label: 'Create Agent', icon: Plus },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Agents</h1>
        <p className="mt-2 text-muted-foreground">Manage your AI agents and their capabilities</p>
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
          <AgentDashboard
            onExecuteAgent={() => setActiveTab('execution')}
            onViewExecution={handleViewExecution}
          />
        )}

        {activeTab === 'list' && (
          <AgentList
            onSelectAgent={handleViewAgent}
            onEditAgent={handleEditAgent}
            onDeleteAgent={handleAgentDeleted}
            onExecuteAgent={handleExecuteAgent}
          />
        )}

        {activeTab === 'create' && (
          <AgentForm
            existingAgent={selectedAgent || undefined}
            onSave={handleAgentSaved}
            onCancel={() => {
              setSelectedAgent(null)
              setActiveTab('list')
            }}
          />
        )}

        {activeTab === 'details' && selectedAgent && (
          <AgentDetails
            agentId={selectedAgent.id}
            onEdit={handleEditAgent}
            onExecute={handleExecuteAgent}
            onClose={() => {
              setSelectedAgent(null)
              setActiveTab('list')
            }}
          />
        )}

        {activeTab === 'execution' && (
          <AgentExecution
            planUuid={selectedExecutionUuid || undefined}
            onClose={() => {
              setSelectedExecutionUuid(null)
              setActiveTab('dashboard')
            }}
          />
        )}
      </div>
    </div>
  )
}
