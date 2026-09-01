"""
Permission System - Core module for managing computer use permissions.
"""
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from loguru import logger
import uuid

from app.core.config import settings
from app.computer.base import (
    PermissionRequest,
    PermissionResponse,
    PermissionStatus,
    ComputerActionType
)


class PermissionSystem:
    """Central permission management system for computer use."""
    
    def __init__(self) -> None:
        self.pending_requests: Dict[str, PermissionRequest] = {}
        self.approved_permissions: Dict[str, PermissionResponse] = {}
        self.denied_permissions: Dict[str, PermissionResponse] = {}
        
        # Permission policies
        self.risk_levels = {
            ComputerActionType.FILE_READ: "low",
            ComputerActionType.FILE_WRITE: "medium",
            ComputerActionType.FILE_DELETE: "high",
            ComputerActionType.FILE_RENAME: "medium",
            ComputerActionType.FILE_MOVE: "medium",
            ComputerActionType.FILE_COPY: "medium",
            ComputerActionType.DIRECTORY_BROWSE: "low",
            ComputerActionType.DIRECTORY_CREATE: "medium",
            ComputerActionType.DIRECTORY_DELETE: "high",
            ComputerActionType.FILE_SEARCH: "low",
            ComputerActionType.FILE_ARCHIVE: "medium",
            ComputerActionType.FILE_EXTRACT: "medium",
            
            ComputerActionType.TERMINAL_EXECUTE: "high",
            ComputerActionType.TERMINAL_CANCEL: "medium",
            ComputerActionType.TERMINAL_STREAM: "medium",
            
            ComputerActionType.BROWSER_OPEN: "low",
            ComputerActionType.BROWSER_NAVIGATE: "low",
            ComputerActionType.BROWSER_CLICK: "low",
            ComputerActionType.BROWSER_FILL: "medium",
            ComputerActionType.BROWSER_EXTRACT: "low",
            ComputerActionType.BROWSER_DOWNLOAD: "medium",
            ComputerActionType.BROWSER_UPLOAD: "medium",
            ComputerActionType.BROWSER_SCREENSHOT: "low",
            ComputerActionType.BROWSER_CLOSE: "low",
            
            ComputerActionType.DESKTOP_LAUNCH: "medium",
            ComputerActionType.DESKTOP_CLOSE: "medium",
            ComputerActionType.DESKTOP_WINDOW: "low",
            ComputerActionType.DESKTOP_CLIPBOARD: "medium",
            ComputerActionType.DESKTOP_NOTIFICATION: "low",
            ComputerActionType.DESKTOP_CAPTURE: "low",
        }
        
        # Session approvals cache
        self.session_approvals: Dict[str, datetime] = {}
        
        logger.info("PermissionSystem initialized")
    
    async def request_permission(
        self,
        request: Any,
        user_id: int
    ) -> PermissionResponse:
        """Request permission for an action."""
        from app.computer.base import PermissionRequest
        
        # If request is a ComputerActionType, create a PermissionRequest
        if isinstance(request, ComputerActionType):
            request = PermissionRequest(
                action_type=request,
                description=f"Request to perform {request.value}",
                risk_level="medium"
            )
        
        request_id = str(uuid.uuid4())
        
        # Check if already approved in session
        session_key = self._get_session_key(request, user_id)
        if session_key in self.session_approvals:
            if datetime.utcnow() < self.session_approvals[session_key]:
                logger.info(f"Permission already approved for session: {session_key}")
                return PermissionResponse(
                    request_id=request_id,
                    status=PermissionStatus.APPROVED,
                    approved_by="session",
                    approved_at=self.session_approvals[session_key],
                    expires_at=self.session_approvals[session_key]
                )
        
        # Determine risk level if not provided
        if request.risk_level == "medium":
            request.risk_level = self.risk_levels.get(request.action_type, "medium")
        
        # Store pending request
        self.pending_requests[request_id] = request
        
        logger.info(f"Permission request {request_id} pending: {request.action_type.value}")
        
        # In production, this would trigger a user approval dialog
        # For now, auto-approve low-risk actions
        if request.risk_level == "low" and not settings.COMPUTER_USE_SANDBOXED:
            return await self._auto_approve(request_id, user_id)
        
        # Return pending status
        return PermissionResponse(
            request_id=request_id,
            status=PermissionStatus.PENDING
        )
    
    async def approve_permission(
        self,
        request_id: str,
        user_id: int,
        approve_for_session: bool = False
    ) -> PermissionResponse:
        """Approve a pending permission request."""
        if request_id not in self.pending_requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.pending_requests[request_id]
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=settings.COMPUTER_USE_PERMISSION_DURATION)
        
        response = PermissionResponse(
            request_id=request_id,
            status=PermissionStatus.APPROVED,
            approved_by=str(user_id),
            approved_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        # Store approved permission
        self.approved_permissions[request_id] = response
        
        # Add to session approvals if requested
        if approve_for_session:
            session_key = self._get_session_key(request, user_id)
            self.session_approvals[session_key] = expires_at
        
        # Remove from pending
        del self.pending_requests[request_id]
        
        logger.info(f"Permission {request_id} approved by user {user_id}")
        
        return response
    
    async def deny_permission(
        self,
        request_id: str,
        user_id: int,
        reason: Optional[str] = None
    ) -> PermissionResponse:
        """Deny a pending permission request."""
        if request_id not in self.pending_requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.pending_requests[request_id]
        
        response = PermissionResponse(
            request_id=request_id,
            status=PermissionStatus.DENIED,
            approved_by=str(user_id),
            approved_at=datetime.utcnow(),
            reason=reason or "Denied by user"
        )
        
        # Store denied permission
        self.denied_permissions[request_id] = response
        
        # Remove from pending
        del self.pending_requests[request_id]
        
        logger.warning(f"Permission {request_id} denied by user {user_id}")
        
        return response
    
    def check_permission(
        self,
        request_id: str
    ) -> Optional[PermissionResponse]:
        """Check if a permission is approved and not expired."""
        if request_id in self.approved_permissions:
            response = self.approved_permissions[request_id]
            
            # Check expiration
            if response.expires_at and datetime.utcnow() > response.expires_at:
                response.status = PermissionStatus.EXPIRED
                logger.info(f"Permission {request_id} expired")
                return response
            
            return response
        
        return None
    
    def revoke_permission(self, request_id: str) -> None:
        """Revoke an approved permission."""
        if request_id in self.approved_permissions:
            self.approved_permissions[request_id].status = PermissionStatus.REVOKED
            logger.warning(f"Permission {request_id} revoked")
    
    def get_pending_requests(self) -> List[PermissionRequest]:
        """Get all pending permission requests."""
        return list(self.pending_requests.values())
    
    def get_approved_permissions(self, user_id: Optional[int] = None) -> List[PermissionResponse]:
        """Get approved permissions."""
        permissions = list(self.approved_permissions.values())
        
        # Filter by user if specified
        if user_id is not None:
            permissions = [p for p in permissions if p.approved_by == str(user_id)]
        
        return permissions
    
    def get_denied_permissions(self, user_id: Optional[int] = None) -> List[PermissionResponse]:
        """Get denied permissions."""
        permissions = list(self.denied_permissions.values())
        
        # Filter by user if specified
        if user_id is not None:
            permissions = [p for p in permissions if p.approved_by == str(user_id)]
        
        return permissions
    
    def clear_expired_permissions(self) -> int:
        """Clear expired permissions."""
        now = datetime.utcnow()
        expired_count = 0
        
        # Clear expired approved permissions
        expired = [
            rid for rid, resp in self.approved_permissions.items()
            if resp.expires_at and resp.expires_at < now
        ]
        
        for rid in expired:
            self.approved_permissions[rid].status = PermissionStatus.EXPIRED
            expired_count += 1
        
        # Clear expired session approvals
        expired_sessions = [
            key for key, expires in self.session_approvals.items()
            if expires < now
        ]
        
        for key in expired_sessions:
            del self.session_approvals[key]
        
        logger.info(f"Cleared {expired_count} expired permissions")
        
        return expired_count
    
    def _get_session_key(self, request: PermissionRequest, user_id: int) -> str:
        """Generate session key for permission caching."""
        return f"{user_id}:{request.action_type.value}:{request.target_path or request.url or request.command}"
    
    async def _auto_approve(self, request_id: str, user_id: int) -> PermissionResponse:
        """Auto-approve low-risk actions."""
        expires_at = datetime.utcnow() + timedelta(seconds=settings.COMPUTER_USE_PERMISSION_DURATION)
        
        response = PermissionResponse(
            request_id=request_id,
            status=PermissionStatus.APPROVED,
            approved_by="auto",
            approved_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        self.approved_permissions[request_id] = response
        del self.pending_requests[request_id]
        
        logger.info(f"Permission {request_id} auto-approved (low risk)")
        
        return response
    
    def get_risk_level(self, action_type: ComputerActionType) -> str:
        """Get risk level for an action type."""
        return self.risk_levels.get(action_type, "medium")
    
    def is_action_allowed(
        self,
        action_type: ComputerActionType,
        target_path: Optional[str] = None
    ) -> bool:
        """Check if action is allowed based on sandbox settings."""
        if not settings.COMPUTER_USE_SANDBOXED:
            return True
        
        # Check if target path is in allowed paths
        if target_path:
            for allowed_path in settings.COMPUTER_USE_ALLOWED_PATHS:
                if target_path.startswith(allowed_path):
                    return True
            return False
        
        return True


# Global permission system instance
permission_system = PermissionSystem()
