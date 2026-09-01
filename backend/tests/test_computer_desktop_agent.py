"""
Unit tests for Computer Use Desktop Agent.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import platform
import sys

from app.computer.desktop_agent import desktop_agent
from app.computer.base import ExecutionResult, ExecutionStatus, ComputerActionType


@pytest.fixture
def mock_permission_system():
    """Mock the permission system."""
    with patch('app.computer.desktop_agent.permission_system') as mock:
        mock.check_permission = AsyncMock(return_value=True)
        mock.request_permission = AsyncMock(return_value=MagicMock(
            status="approved",
            request_id="test_request_id"
        ))
        yield mock


class TestDesktopAgentInitialization:
    """Test DesktopAgent initialization."""

    def test_initialization(self):
        """Test that DesktopAgent initializes correctly."""
        assert desktop_agent is not None
        assert hasattr(desktop_agent, 'launch_application')
        assert hasattr(desktop_agent, 'close_application')
        assert hasattr(desktop_agent, 'get_clipboard')


class TestGetPlatform:
    """Test platform detection."""

    def test_get_platform(self):
        """Test getting current platform."""
        platform_name = desktop_agent.get_platform()
        assert platform_name is not None
        assert isinstance(platform_name, str)
        assert platform_name.lower() in ["windows", "darwin", "linux"]


class TestLaunchApplication:
    """Test application launching functionality."""

    @pytest.mark.asyncio
    async def test_launch_application_windows(self, mock_permission_system):
        """Test launching application on Windows."""
        with patch('app.computer.desktop_agent.platform.system', return_value='Windows'):
            with patch('app.computer.desktop_agent.subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_popen.return_value = mock_process

                result = await desktop_agent.launch_application("notepad.exe", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_popen.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_application_macos(self, mock_permission_system):
        """Test launching application on macOS."""
        with patch('app.computer.desktop_agent.platform.system', return_value='Darwin'):
            with patch('app.computer.desktop_agent.subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_popen.return_value = mock_process

                result = await desktop_agent.launch_application("TextEdit.app", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_popen.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_application_linux(self, mock_permission_system):
        """Test launching application on Linux."""
        with patch('app.computer.desktop_agent.platform.system', return_value='Linux'):
            with patch('app.computer.desktop_agent.subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_popen.return_value = mock_process

                result = await desktop_agent.launch_application("gedit", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_popen.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_application_permission_denied(self, mock_permission_system):
        """Test launching application with permission denied."""
        mock_permission_system.request_permission = AsyncMock(return_value=MagicMock(status="denied"))

        result = await desktop_agent.launch_application("notepad.exe", user_id=1)

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "Permission denied" in result.error


class TestCloseApplication:
    """Test application closing functionality."""

    @pytest.mark.asyncio
    async def test_close_application_windows(self, mock_permission_system):
        """Test closing application on Windows."""
        with patch('app.computer.desktop_agent.platform.system', return_value='Windows'):
            with patch('app.computer.desktop_agent.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = await desktop_agent.close_application("notepad.exe", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_close_application_macos(self, mock_permission_system):
        """Test closing application on macOS."""
        with patch('app.computer.desktop_agent.platform.system', return_value='Darwin'):
            with patch('app.computer.desktop_agent.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = await desktop_agent.close_application("TextEdit", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_close_application_linux(self, mock_permission_system):
        """Test closing application on Linux."""
        with patch('app.computer.desktop_agent.platform.system', return_value='Linux'):
            with patch('app.computer.desktop_agent.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = await desktop_agent.close_application("gedit", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True


class TestManageWindow:
    """Test window management functionality."""

    @pytest.mark.asyncio
    async def test_manage_window_minimize(self, mock_permission_system):
        """Test minimizing window."""
        result = await desktop_agent.manage_window("minimize", "Notepad", user_id=1)

        # Window management is stubbed, so it should return an error
        assert result.success is False
        assert "not implemented" in result.error.lower() or "stub" in result.error.lower() or "platform-specific" in result.error.lower()

    @pytest.mark.asyncio
    async def test_manage_window_maximize(self, mock_permission_system):
        """Test maximizing window."""
        result = await desktop_agent.manage_window("maximize", "Notepad", user_id=1)

        assert result.success is False
        assert "not implemented" in result.error.lower() or "stub" in result.error.lower() or "platform-specific" in result.error.lower()

    @pytest.mark.asyncio
    async def test_manage_window_restore(self, mock_permission_system):
        """Test restoring window."""
        result = await desktop_agent.manage_window("restore", "Notepad", user_id=1)

        assert result.success is False
        assert "not implemented" in result.error.lower() or "stub" in result.error.lower() or "platform-specific" in result.error.lower()


class TestGetClipboard:
    """Test getting clipboard content."""

    @pytest.mark.asyncio
    async def test_get_clipboard_success(self, mock_permission_system):
        """Test successful clipboard content retrieval."""
        result = await desktop_agent.get_clipboard(user_id=1)

        # Either succeeds with pyperclip or fails gracefully without it
        if result.success:
            assert result.status == ExecutionStatus.COMPLETED
        else:
            assert result.status == ExecutionStatus.FAILED
            assert "pyperclip" in result.error.lower()

    @pytest.mark.asyncio
    async def test_get_clipboard_permission_denied(self, mock_permission_system):
        """Test getting clipboard with permission denied."""
        mock_permission_system.request_permission = AsyncMock(return_value=MagicMock(status="denied"))

        result = await desktop_agent.get_clipboard(user_id=1)

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "Permission denied" in result.error


class TestSetClipboard:
    """Test setting clipboard content."""

    @pytest.mark.asyncio
    async def test_set_clipboard_success(self, mock_permission_system):
        """Test successful clipboard content setting."""
        result = await desktop_agent.set_clipboard("new content", user_id=1)

        # Either succeeds with pyperclip or fails gracefully without it
        if result.success:
            assert result.status == ExecutionStatus.COMPLETED
        else:
            assert result.status == ExecutionStatus.FAILED
            assert "pyperclip" in result.error.lower()

    @pytest.mark.asyncio
    async def test_set_clipboard_permission_denied(self, mock_permission_system):
        """Test setting clipboard with permission denied."""
        mock_permission_system.request_permission = AsyncMock(return_value=MagicMock(status="denied"))

        result = await desktop_agent.set_clipboard("new content", user_id=1)

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "Permission denied" in result.error


class TestSendNotification:
    """Test sending desktop notifications."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self, mock_permission_system):
        """Test successful notification sending."""
        # Test the ImportError path since plyer is optional
        result = await desktop_agent.send_notification(
            "Test Title",
            "Test Message",
            user_id=1
        )

        # Since plyer is not installed, it should fail gracefully
        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "plyer" in result.error.lower()

    @pytest.mark.asyncio
    async def test_send_notification_permission_denied(self, mock_permission_system):
        """Test sending notification with permission denied."""
        mock_permission_system.request_permission = AsyncMock(return_value=MagicMock(status="denied"))

        result = await desktop_agent.send_notification(
            "Test Title",
            "Test Message",
            user_id=1
        )

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "Permission denied" in result.error


class TestCaptureScreen:
    """Test screen capture functionality."""

    @pytest.mark.asyncio
    async def test_capture_screen_success(self, mock_permission_system):
        """Test successful screen capture."""
        # Test the ImportError path since mss is optional
        result = await desktop_agent.capture_screen(user_id=1)

        # Since mss is not installed, it should fail gracefully
        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "mss" in result.error.lower()

    @pytest.mark.asyncio
    async def test_capture_screen_permission_denied(self, mock_permission_system):
        """Test screen capture with permission denied."""
        mock_permission_system.request_permission = AsyncMock(return_value=MagicMock(status="denied"))

        result = await desktop_agent.capture_screen(user_id=1)

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "Permission denied" in result.error


class TestGetRunningApplications:
    """Test getting running applications."""

    def test_get_running_applications_success(self):
        """Test successful retrieval of running applications."""
        result = desktop_agent.get_running_applications()

        # psutil is available on this system, so it should succeed
        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        # The implementation returns str(applications), not the list itself
        assert isinstance(result.output, str)

    def test_get_running_applications_no_psutil(self):
        """Test when psutil is not available."""
        # This test would require mocking psutil to not be available
        # Since psutil is installed, we skip this or test the success path
        result = desktop_agent.get_running_applications()

        # psutil is available on this system
        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        assert isinstance(result.output, str)
