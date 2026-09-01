"""
Unit tests for Computer Use Permission System.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.computer.permission_system import PermissionSystem
from app.computer.base import (
    PermissionRequest,
    PermissionResponse,
    PermissionStatus,
    ComputerActionType,
    RiskLevel
)


@pytest.fixture
def permission_system():
    """Create a fresh PermissionSystem instance for each test."""
    return PermissionSystem()


class TestPermissionSystemInitialization:
    """Test PermissionSystem initialization."""

    def test_initialization(self, permission_system):
        """Test that PermissionSystem initializes correctly."""
        assert permission_system is not None
        assert permission_system.pending_requests == {}
        assert permission_system.approved_permissions == {}
        assert permission_system.denied_permissions == {}


class TestRequestPermission:
    """Test permission request functionality."""

    @pytest.mark.asyncio
    async def test_request_permission_low_risk(self, permission_system):
        """Test requesting permission for low-risk action."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        response = await permission_system.request_permission(request, user_id=1)

        assert response.status == PermissionStatus.PENDING
        assert response.request_id in permission_system.pending_requests
        assert permission_system.pending_requests[response.request_id].action_type == ComputerActionType.FILE_READ

    @pytest.mark.asyncio
    async def test_request_permission_high_risk(self, permission_system):
        """Test requesting permission for high-risk action."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_DELETE,
            target_path="./test.txt",
            description="Delete test file",
            risk_level=RiskLevel.HIGH
        )

        response = await permission_system.request_permission(request, user_id=1)

        assert response.status == PermissionStatus.PENDING
        assert permission_system.pending_requests[response.request_id].risk_level == RiskLevel.HIGH

    @pytest.mark.asyncio
    async def test_request_permission_with_command(self, permission_system):
        """Test requesting permission for terminal command."""
        request = PermissionRequest(
            action_type=ComputerActionType.TERMINAL_EXECUTE,
            command="ls -la",
            description="List directory contents",
            risk_level=RiskLevel.HIGH
        )

        response = await permission_system.request_permission(request, user_id=1)

        assert response.status == PermissionStatus.PENDING
        assert permission_system.pending_requests[response.request_id].command == "ls -la"

    @pytest.mark.asyncio
    async def test_request_permission_with_url(self, permission_system):
        """Test requesting permission for browser navigation."""
        request = PermissionRequest(
            action_type=ComputerActionType.BROWSER_NAVIGATE,
            url="https://example.com",
            description="Navigate to example.com",
            risk_level=RiskLevel.LOW
        )

        response = await permission_system.request_permission(request, user_id=1)

        assert response.status == PermissionStatus.PENDING
        assert permission_system.pending_requests[response.request_id].url == "https://example.com"


class TestApprovePermission:
    """Test permission approval functionality."""

    @pytest.mark.asyncio
    async def test_approve_permission_once(self, permission_system):
        """Test approving permission for single use."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        response = await permission_system.approve_permission(
            request_response.request_id,
            user_id=1,
            approve_for_session=False
        )

        assert response.status == PermissionStatus.APPROVED
        assert response.request_id not in permission_system.pending_requests
        assert response.request_id in permission_system.approved_permissions

    @pytest.mark.asyncio
    async def test_approve_permission_for_session(self, permission_system):
        """Test approving permission for session."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        response = await permission_system.approve_permission(
            request_response.request_id,
            user_id=1,
            approve_for_session=True
        )

        assert response.status == PermissionStatus.APPROVED
        assert response.request_id not in permission_system.pending_requests
        assert response.request_id in permission_system.approved_permissions
        assert response.expires_at is not None

    @pytest.mark.asyncio
    async def test_approve_nonexistent_request(self, permission_system):
        """Test approving a non-existent request."""
        with pytest.raises(ValueError):
            await permission_system.approve_permission("nonexistent_id", user_id=1)

    @pytest.mark.asyncio
    async def test_approve_already_approved(self, permission_system):
        """Test approving an already approved request."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.approve_permission(
            request_response.request_id,
            user_id=1,
            approve_for_session=True
        )

        with pytest.raises(ValueError):
            await permission_system.approve_permission(
                request_response.request_id,
                user_id=1,
                approve_for_session=True
            )


class TestDenyPermission:
    """Test permission denial functionality."""

    @pytest.mark.asyncio
    async def test_deny_permission(self, permission_system):
        """Test denying a permission request."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_DELETE,
            target_path="./test.txt",
            description="Delete test file",
            risk_level=RiskLevel.HIGH
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        response = await permission_system.deny_permission(
            request_response.request_id,
            user_id=1,
            reason="Unsafe operation"
        )

        assert response.status == PermissionStatus.DENIED
        assert response.request_id not in permission_system.pending_requests
        assert response.request_id in permission_system.denied_permissions
        assert response.reason == "Unsafe operation"

    @pytest.mark.asyncio
    async def test_deny_nonexistent_request(self, permission_system):
        """Test denying a non-existent request."""
        with pytest.raises(ValueError):
            await permission_system.deny_permission("nonexistent_id", user_id=1)

    @pytest.mark.asyncio
    async def test_deny_without_reason(self, permission_system):
        """Test denying without providing a reason."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_DELETE,
            target_path="./test.txt",
            description="Delete test file",
            risk_level=RiskLevel.HIGH
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        response = await permission_system.deny_permission(
            request_response.request_id,
            user_id=1
        )

        assert response.status == PermissionStatus.DENIED
        assert response.reason == "Denied by user"


class TestCheckPermission:
    """Test permission checking functionality."""

    @pytest.mark.asyncio
    async def test_check_approved_permission(self, permission_system):
        """Test checking an approved permission."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.approve_permission(
            request_response.request_id,
            user_id=1
        )

        response = permission_system.check_permission(request_response.request_id)

        assert response is not None
        assert response.status == PermissionStatus.APPROVED

    @pytest.mark.asyncio
    async def test_check_denied_permission(self, permission_system):
        """Test checking a denied permission."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_DELETE,
            target_path="./test.txt",
            description="Delete test file",
            risk_level=RiskLevel.HIGH
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.deny_permission(
            request_response.request_id,
            user_id=1
        )

        response = permission_system.check_permission(request_response.request_id)

        assert response is None

    @pytest.mark.asyncio
    async def test_check_nonexistent_permission(self, permission_system):
        """Test checking a non-existent permission."""
        response = permission_system.check_permission("nonexistent_id")

        assert response is None


class TestRevokePermission:
    """Test permission revocation functionality."""

    @pytest.mark.asyncio
    async def test_revoke_approved_permission(self, permission_system):
        """Test revoking an approved permission."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.approve_permission(
            request_response.request_id,
            user_id=1
        )

        permission_system.revoke_permission(request_response.request_id)

        response = permission_system.check_permission(request_response.request_id)
        assert response.status == PermissionStatus.REVOKED

    def test_revoke_nonexistent_permission(self, permission_system):
        """Test revoking a non-existent permission."""
        # Should not raise an error
        permission_system.revoke_permission("nonexistent_id")


class TestGetPendingRequests:
    """Test getting pending permission requests."""

    @pytest.mark.asyncio
    async def test_get_pending_requests_empty(self, permission_system):
        """Test getting pending requests when none exist."""
        pending = permission_system.get_pending_requests()
        assert pending == []

    @pytest.mark.asyncio
    async def test_get_pending_requests_with_items(self, permission_system):
        """Test getting pending requests with items."""
        request1 = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test1.txt",
            description="Read test file 1",
            risk_level=RiskLevel.LOW
        )
        request2 = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test2.txt",
            description="Read test file 2",
            risk_level=RiskLevel.LOW
        )

        await permission_system.request_permission(request1, user_id=1)
        await permission_system.request_permission(request2, user_id=1)

        pending = permission_system.get_pending_requests()
        assert len(pending) == 2


class TestGetApprovedPermissions:
    """Test getting approved permissions."""

    @pytest.mark.asyncio
    async def test_get_approved_permissions_empty(self, permission_system):
        """Test getting approved permissions when none exist."""
        approved = permission_system.get_approved_permissions(user_id=1)
        assert approved == []

    @pytest.mark.asyncio
    async def test_get_approved_permissions_with_items(self, permission_system):
        """Test getting approved permissions with items."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.approve_permission(
            request_response.request_id,
            user_id=1,
            approve_for_session=True
        )

        approved = permission_system.get_approved_permissions(user_id=1)
        assert len(approved) == 1
        assert approved[0].request_id == request_response.request_id


class TestGetDeniedPermissions:
    """Test getting denied permissions."""

    @pytest.mark.asyncio
    async def test_get_denied_permissions_empty(self, permission_system):
        """Test getting denied permissions when none exist."""
        denied = permission_system.get_denied_permissions(user_id=1)
        assert denied == []

    @pytest.mark.asyncio
    async def test_get_denied_permissions_with_items(self, permission_system):
        """Test getting denied permissions with items."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_DELETE,
            target_path="./test.txt",
            description="Delete test file",
            risk_level=RiskLevel.HIGH
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.deny_permission(
            request_response.request_id,
            user_id=1
        )

        denied = permission_system.get_denied_permissions(user_id=1)
        assert len(denied) == 1
        assert denied[0].request_id == request_response.request_id


class TestClearExpiredPermissions:
    """Test clearing expired permissions."""

    @pytest.mark.asyncio
    async def test_clear_expired_permissions(self, permission_system):
        """Test clearing expired permissions."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.approve_permission(
            request_response.request_id,
            user_id=1,
            approve_for_session=True
        )

        # Manually set expiration to past
        permission_system.approved_permissions[request_response.request_id].expires_at = (
            datetime.utcnow() - timedelta(seconds=1)
        )

        count = permission_system.clear_expired_permissions()
        assert count == 1
        response = permission_system.check_permission(request_response.request_id)
        assert response.status == PermissionStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_clear_expired_permissions_none_expired(self, permission_system):
        """Test clearing when no permissions are expired."""
        request = PermissionRequest(
            action_type=ComputerActionType.FILE_READ,
            target_path="./test.txt",
            description="Read test file",
            risk_level=RiskLevel.LOW
        )

        request_response = await permission_system.request_permission(request, user_id=1)
        await permission_system.approve_permission(
            request_response.request_id,
            user_id=1,
            approve_for_session=True
        )

        count = permission_system.clear_expired_permissions()
        assert count == 0
        assert request_response.request_id in permission_system.approved_permissions


class TestSandboxPathValidation:
    """Test sandbox path validation."""

    def test_validate_allowed_path(self, permission_system):
        """Test validating an allowed path."""
        with patch('app.computer.permission_system.settings') as mock_settings:
            mock_settings.COMPUTER_USE_SANDBOXED = True
            mock_settings.COMPUTER_USE_ALLOWED_PATHS = ['./data/computer', './data/uploads']

            is_valid = permission_system.is_action_allowed(
                ComputerActionType.FILE_READ,
                './data/computer/test.txt'
            )
            assert is_valid is True

    def test_validate_disallowed_path(self, permission_system):
        """Test validating a disallowed path."""
        with patch('app.computer.permission_system.settings') as mock_settings:
            mock_settings.COMPUTER_USE_SANDBOXED = True
            mock_settings.COMPUTER_USE_ALLOWED_PATHS = ['./data/computer']

            is_valid = permission_system.is_action_allowed(
                ComputerActionType.FILE_READ,
                '/etc/passwd'
            )
            assert is_valid is False

    def test_validate_path_sandbox_disabled(self, permission_system):
        """Test path validation when sandbox is disabled."""
        with patch('app.computer.permission_system.settings') as mock_settings:
            mock_settings.COMPUTER_USE_SANDBOXED = False

            is_valid = permission_system.is_action_allowed(
                ComputerActionType.FILE_READ,
                '/etc/passwd'
            )
            assert is_valid is True


class TestRiskLevelAssessment:
    """Test risk level assessment for action types."""

    def test_assess_risk_level_low(self, permission_system):
        """Test risk assessment for low-risk actions."""
        low_risk_actions = [
            ComputerActionType.FILE_READ,
            ComputerActionType.DIRECTORY_BROWSE,
            ComputerActionType.BROWSER_OPEN,
            ComputerActionType.BROWSER_NAVIGATE,
            ComputerActionType.BROWSER_EXTRACT,
            ComputerActionType.BROWSER_SCREENSHOT,
        ]

        for action in low_risk_actions:
            risk = permission_system.get_risk_level(action)
            assert risk == RiskLevel.LOW

    def test_assess_risk_level_medium(self, permission_system):
        """Test risk assessment for medium-risk actions."""
        medium_risk_actions = [
            ComputerActionType.FILE_WRITE,
            ComputerActionType.FILE_RENAME,
            ComputerActionType.FILE_MOVE,
            ComputerActionType.FILE_COPY,
            ComputerActionType.FILE_ARCHIVE,
            ComputerActionType.FILE_EXTRACT,
            ComputerActionType.TERMINAL_STREAM,
            ComputerActionType.BROWSER_FILL,
            ComputerActionType.BROWSER_DOWNLOAD,
            ComputerActionType.BROWSER_UPLOAD,
            ComputerActionType.DESKTOP_LAUNCH,
            ComputerActionType.DESKTOP_CLOSE,
            ComputerActionType.DESKTOP_CLIPBOARD,
        ]

        for action in medium_risk_actions:
            risk = permission_system.get_risk_level(action)
            assert risk == RiskLevel.MEDIUM

    def test_assess_risk_level_high(self, permission_system):
        """Test risk assessment for high-risk actions."""
        high_risk_actions = [
            ComputerActionType.FILE_DELETE,
            ComputerActionType.DIRECTORY_DELETE,
            ComputerActionType.TERMINAL_EXECUTE,
        ]

        for action in high_risk_actions:
            risk = permission_system.get_risk_level(action)
            assert risk == RiskLevel.HIGH
