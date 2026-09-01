/**
 * Permission Manager Component
 * Interface for managing computer use permissions and approval workflows.
 */
import React, { useState } from 'react'
import { 
  Shield, 
  Check, 
  X, 
  Clock, 
  AlertTriangle, 
  RefreshCw,
  Ban,
  CheckCircle
} from 'lucide-react'
import { 
  usePendingPermissions, 
  useApprovedPermissions, 
  useDeniedPermissions,
  useApprovePermission,
  useDenyPermission,
  useRevokePermission,
  useClearExpiredPermissions
} from '../../services/computer-hooks'

const PermissionManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'pending' | 'approved' | 'denied'>('pending')
  
  const { data: pending } = usePendingPermissions()
  const { data: approved } = useApprovedPermissions()
  const { data: denied } = useDeniedPermissions()
  
  const approvePermission = useApprovePermission()
  const denyPermission = useDenyPermission()
  const revokePermission = useRevokePermission()
  const clearExpired = useClearExpiredPermissions()

  const handleApprove = async (requestId: string, forSession: boolean = false) => {
    try {
      await approvePermission.mutateAsync({ request_id: requestId, approve_for_session: forSession })
    } catch (error) {
      console.error('Failed to approve permission:', error)
    }
  }

  const handleDeny = async (requestId: string, reason?: string) => {
    try {
      await denyPermission.mutateAsync({ request_id: requestId, reason })
    } catch (error) {
      console.error('Failed to deny permission:', error)
    }
  }

  const handleRevoke = async (requestId: string) => {
    try {
      await revokePermission.mutateAsync(requestId)
    } catch (error) {
      console.error('Failed to revoke permission:', error)
    }
  }

  const handleClearExpired = async () => {
    try {
      await clearExpired.mutateAsync()
    } catch (error) {
      console.error('Failed to clear expired permissions:', error)
    }
  }

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'text-green-400 bg-green-900/30'
      case 'medium': return 'text-yellow-400 bg-yellow-900/30'
      case 'high': return 'text-red-400 bg-red-900/30'
      default: return 'text-gray-400 bg-gray-700'
    }
  }

  const getActionTypeLabel = (actionType: string) => {
    return actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-700 px-4 py-3 bg-gray-800">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-400" />
            Permission Manager
          </h2>
          <button
            onClick={handleClearExpired}
            className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded transition-colors text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Clear Expired
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700 px-4 bg-gray-800">
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab('pending')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
              activeTab === 'pending'
                ? 'border-yellow-500 text-yellow-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Pending {pending?.pending?.length ? `(${pending.pending.length})` : ''}
          </button>
          <button
            onClick={() => setActiveTab('approved')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
              activeTab === 'approved'
                ? 'border-green-500 text-green-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Approved {approved?.approved?.length ? `(${approved.approved.length})` : ''}
          </button>
          <button
            onClick={() => setActiveTab('denied')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
              activeTab === 'denied'
                ? 'border-red-500 text-red-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Denied {denied?.denied?.length ? `(${denied.denied.length})` : ''}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'pending' && (
          <div className="space-y-3">
            {pending?.pending?.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <Clock className="w-12 h-12 mb-4" />
                <p className="text-sm">No pending permissions</p>
              </div>
            ) : (
              pending?.pending?.map((request: any) => (
                <div key={request.request_id} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRiskColor(request.risk_level)}`}>
                          {request.risk_level.toUpperCase()}
                        </span>
                        <span className="text-sm font-medium">
                          {getActionTypeLabel(request.action_type)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300 mb-2">{request.description}</p>
                      {request.target_path && (
                        <p className="text-xs text-gray-400 font-mono">
                          Path: {request.target_path}
                        </p>
                      )}
                      {request.command && (
                        <p className="text-xs text-gray-400 font-mono">
                          Command: {request.command}
                        </p>
                      )}
                      {request.url && (
                        <p className="text-xs text-gray-400">
                          URL: {request.url}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleApprove(request.request_id, false)}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors text-sm"
                    >
                      <Check className="w-4 h-4" />
                      Approve Once
                    </button>
                    <button
                      onClick={() => handleApprove(request.request_id, true)}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors text-sm"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Approve Session
                    </button>
                    <button
                      onClick={() => handleDeny(request.request_id)}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors text-sm"
                    >
                      <X className="w-4 h-4" />
                      Deny
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'approved' && (
          <div className="space-y-3">
            {approved?.approved?.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <CheckCircle className="w-12 h-12 mb-4" />
                <p className="text-sm">No approved permissions</p>
              </div>
            ) : (
              approved?.approved?.map((permission: any) => (
                <div key={permission.request_id} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium">
                          {getActionTypeLabel(permission.action_type)}
                        </span>
                        <span className="text-xs text-gray-400">
                          by {permission.approved_by}
                        </span>
                      </div>
                      {permission.expires_at && (
                        <p className="text-xs text-gray-400">
                          Expires: {new Date(permission.expires_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => handleRevoke(permission.request_id)}
                      className="p-2 hover:bg-red-900/50 rounded transition-colors"
                      title="Revoke"
                    >
                      <Ban className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'denied' && (
          <div className="space-y-3">
            {denied?.denied?.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <X className="w-12 h-12 mb-4" />
                <p className="text-sm">No denied permissions</p>
              </div>
            ) : (
              denied?.denied?.map((permission: any) => (
                <div key={permission.request_id} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium">
                          {getActionTypeLabel(permission.action_type)}
                        </span>
                        <span className="text-xs text-gray-400">
                          by {permission.approved_by}
                        </span>
                      </div>
                      {permission.reason && (
                        <p className="text-xs text-gray-400">
                          Reason: {permission.reason}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="border-t border-gray-700 px-4 py-2 bg-gray-800 text-xs text-gray-400 flex items-center justify-between">
        <div>
          {pending?.pending?.length || 0} pending • {approved?.approved?.length || 0} approved • {denied?.denied?.length || 0} denied
        </div>
        <div className="flex items-center gap-1">
          <Shield className="w-3 h-3" />
          Permission-based execution
        </div>
      </div>
    </div>
  )
}

export default PermissionManager
