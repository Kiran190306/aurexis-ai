"""
Unit tests for Computer Use Terminal Agent.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from app.computer.terminal_agent import terminal_agent
from app.computer.base import ExecutionResult, ExecutionStatus, ComputerActionType


@pytest.fixture
def mock_permission_system():
    """Mock the permission system."""
    with patch('app.computer.terminal_agent.permission_system') as mock:
        mock.check_permission = AsyncMock(return_value=True)
        mock.request_permission = AsyncMock(return_value=MagicMock(
            status="approved",
            request_id="test_request_id"
        ))
        yield mock


class TestTerminalAgentInitialization:
    """Test TerminalAgent initialization."""

    def test_initialization(self):
        """Test that TerminalAgent initializes correctly."""
        assert terminal_agent is not None
        assert hasattr(terminal_agent, 'execute_command')
        assert hasattr(terminal_agent, 'cancel_command')
        assert hasattr(terminal_agent, 'get_working_directory')


class TestExecuteCommand:
    """Test command execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_command_success(self, mock_permission_system):
        """Test successful command execution."""
        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_COMMAND_TIMEOUT = 300

            result = await terminal_agent.execute_command(
                "echo 'hello world'",
                working_directory=None,
                environment={},
                timeout=30,
                stream_output=False,
                user_id=1
            )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        assert "hello world" in result.output

    @pytest.mark.asyncio
    async def test_execute_command_with_timeout(self, mock_permission_system):
        """Test command execution with timeout."""
        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_COMMAND_TIMEOUT = 300

            result = await terminal_agent.execute_command(
                "echo 'test'",
                working_directory=None,
                environment={},
                timeout=5,
                stream_output=False,
                user_id=1
            )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_command_with_environment(self, mock_permission_system):
        """Test command execution with environment variables."""
        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_COMMAND_TIMEOUT = 300

            result = await terminal_agent.execute_command(
                "echo $TEST_VAR",
                working_directory=None,
                environment={"TEST_VAR": "test_value"},
                timeout=30,
                stream_output=False,
                user_id=1
            )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_command_permission_denied(self, mock_permission_system):
        """Test command execution with permission denied."""
        mock_permission_system.request_permission = AsyncMock(return_value=MagicMock(status="denied"))

        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_COMMAND_TIMEOUT = 300

            result = await terminal_agent.execute_command(
                "echo 'test'",
                working_directory=None,
                environment={},
                timeout=30,
                stream_output=False,
                user_id=1
            )

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "Permission denied" in result.error

    @pytest.mark.asyncio
    async def test_execute_command_invalid_command(self, mock_permission_system):
        """Test execution of invalid command."""
        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_COMMAND_TIMEOUT = 300

            result = await terminal_agent.execute_command(
                "nonexistent_command_12345",
                working_directory=None,
                environment={},
                timeout=30,
                stream_output=False,
                user_id=1
            )

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False


class TestCancelCommand:
    """Test command cancellation functionality."""

    @pytest.mark.asyncio
    async def test_cancel_command_success(self, mock_permission_system):
        """Test successful command cancellation."""
        # First start a long-running command
        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_COMMAND_TIMEOUT = 300

            # Start command in background
            execute_task = asyncio.create_task(
                terminal_agent.execute_command(
                    "sleep 100",
                    working_directory=None,
                    environment={},
                    timeout=300,
                    stream_output=False,
                    user_id=1
                )
            )

            # Wait a bit for it to start
            await asyncio.sleep(0.1)

            # Get the action ID from the running commands
            running = terminal_agent.get_running_commands()
            if running:
                action_id = running[0]['action_id']
                
                result = terminal_agent.cancel_command(action_id, user_id=1)
                
                assert result.success is True
                assert result.status == ExecutionStatus.CANCELLED

            # Clean up
            execute_task.cancel()
            try:
                await execute_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_command(self, mock_permission_system):
        """Test cancelling a non-existent command."""
        with patch('app.computer.terminal_agent.permission_system') as mock_ps:
            mock_ps.request_permission = AsyncMock(return_value=MagicMock(status="approved"))
            result = await terminal_agent.cancel_command("nonexistent_id", user_id=1)
            assert result.success is False
            assert "not found" in result.error.lower()


class TestWorkingDirectory:
    """Test working directory management."""

    def test_get_working_directory(self):
        """Test getting current working directory."""
        wd = terminal_agent.get_working_directory()
        assert wd is not None
        assert isinstance(wd, str)

    def test_set_working_directory(self, mock_permission_system):
        """Test setting working directory."""
        import tempfile
        temp_dir = tempfile.mkdtemp()

        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_SANDBOXED = False
            result = terminal_agent.set_working_directory(temp_dir, user_id=1)

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED

        # Verify it was set
        wd = terminal_agent.get_working_directory()
        assert wd == temp_dir

    def test_set_working_directory_invalid(self, mock_permission_system):
        """Test setting invalid working directory."""
        result = terminal_agent.set_working_directory("/nonexistent/path/12345", user_id=1)

        assert result.success is False
        assert result.status == ExecutionStatus.FAILED


class TestEnvironmentVariables:
    """Test environment variable management."""

    def test_get_environment_variables(self):
        """Test getting environment variables."""
        env = terminal_agent.get_environment_variables()
        assert env is not None
        assert isinstance(env, dict)
        assert "PATH" in env or "Path" in env  # PATH should exist on most systems

    def test_set_environment_variable(self, mock_permission_system):
        """Test setting environment variable."""
        result = terminal_agent.set_environment_variable("TEST_VAR", "test_value", user_id=1)

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED

        # Verify it was set
        env = terminal_agent.get_environment_variables()
        assert env.get("TEST_VAR") == "test_value"


class TestCommandHistory:
    """Test command history functionality."""

    def test_get_command_history(self):
        """Test getting command history."""
        history = terminal_agent.get_command_history(limit=10)
        assert history is not None
        assert isinstance(history, list)
        assert len(history) <= 10

    def test_get_command_history_with_limit(self):
        """Test getting command history with custom limit."""
        history = terminal_agent.get_command_history(limit=5)
        assert len(history) <= 5


class TestRunningCommands:
    """Test running commands tracking."""

    def test_get_running_commands(self):
        """Test getting running commands."""
        running = terminal_agent.get_running_commands()
        assert running is not None
        assert isinstance(running, list)


class TestExecuteCommandStream:
    """Test streaming command execution."""

    @pytest.mark.asyncio
    async def test_execute_command_stream_success(self, mock_permission_system):
        """Test successful streaming command execution."""
        with patch('app.computer.terminal_agent.settings') as mock_settings:
            mock_settings.COMPUTER_USE_COMMAND_TIMEOUT = 300

            result = await terminal_agent.execute_command(
                "echo 'line1'; echo 'line2'; echo 'line3'",
                working_directory=None,
                environment={},
                timeout=30,
                stream_output=True,
                user_id=1
            )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
