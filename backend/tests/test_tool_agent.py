"""
Unit tests for Tool Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.tool_agent import ToolAgent
from app.agents.base import Task, AgentRole, TaskPriority


@pytest.fixture
def tool_agent():
    """Create a Tool Agent instance for testing."""
    return ToolAgent(agent_id="test_tool")


@pytest.fixture
def sample_execute_task():
    """Create a sample tool execution task."""
    return Task(
        task_type="tool",
        description="Execute tool task",
        input_data={
            "task_type": "execute",
            "tool_name": "web_search",
            "parameters": {"query": "test"},
            "user_id": "test_user"
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.TOOL
    )


@pytest.fixture
def sample_select_task():
    """Create a sample tool selection task."""
    return Task(
        task_type="tool",
        description="Select tool task",
        input_data={
            "task_type": "select",
            "task_description": "Search the web for information"
        },
        priority=TaskPriority.MEDIUM,
        agent_role=AgentRole.TOOL
    )


@pytest.mark.asyncio
async def test_tool_initialization(tool_agent):
    """Test tool agent initialization."""
    await tool_agent.initialize()
    assert tool_agent.agent_id == "test_tool"
    assert tool_agent.role == AgentRole.TOOL
    assert len(tool_agent.tool_registry) > 0  # Should have default tools


@pytest.mark.asyncio
async def test_tool_shutdown(tool_agent):
    """Test tool agent shutdown."""
    await tool_agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
async def test_tool_execute_not_found(tool_agent, sample_execute_task):
    """Test tool execution with non-existent tool."""
    task = Task(
        task_type="tool",
        description="Test task",
        input_data={
            "task_type": "execute",
            "tool_name": "non_existent_tool",
            "parameters": {},
            "user_id": "test"
        },
        agent_role=AgentRole.TOOL
    )
    
    response = await tool_agent.execute(task)
    
    assert response.success is False
    assert "Tool not found" in response.error


@pytest.mark.asyncio
@patch('app.agents.tool_agent.ai_engine')
async def test_tool_select(mock_ai_engine, tool_agent, sample_select_task):
    """Test tool selection."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = '{"tool": "web_search", "reasoning": "Best for web search"}'
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await tool_agent.execute(sample_select_task)
    
    assert response.success is True
    assert "selection" in response.data
    assert "available_tools" in response.data


@pytest.mark.asyncio
async def test_tool_validate_permissions(tool_agent):
    """Test permission validation."""
    task = Task(
        task_type="tool",
        description="Validate permissions task",
        input_data={
            "task_type": "validate_permissions",
            "tool_name": "web_search",
            "user_id": "test_user"
        },
        agent_role=AgentRole.TOOL
    )
    
    response = await tool_agent.execute(task)
    
    assert response.success is True
    assert "has_permission" in response.data
    assert "required_permissions" in response.data


@pytest.mark.asyncio
async def test_tool_unknown_type(tool_agent):
    """Test tool with unknown type."""
    task = Task(
        task_type="tool",
        description="Test task",
        input_data={"task_type": "unknown"},
        agent_role=AgentRole.TOOL
    )
    
    response = await tool_agent.execute(task)
    
    assert response.success is False
    assert "Unknown tool task type" in response.error


def test_tool_get_capabilities(tool_agent):
    """Test getting tool capabilities."""
    capabilities = tool_agent.get_capabilities()
    
    assert isinstance(capabilities, list)
    assert "tool_selection" in capabilities
    assert "tool_execution" in capabilities
    assert "permission_validation" in capabilities
    assert "error_recovery" in capabilities


def test_tool_get_status(tool_agent):
    """Test getting tool status."""
    status = tool_agent.get_status()
    
    assert status["agent_id"] == "test_tool"
    assert status["role"] == "tool"
