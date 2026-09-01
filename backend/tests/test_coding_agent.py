"""
Unit tests for Coding Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.coding_agent import CodingAgent
from app.agents.base import Task, AgentRole, TaskPriority


@pytest.fixture
def coding_agent():
    """Create a Coding Agent instance for testing."""
    return CodingAgent(agent_id="test_coding")


@pytest.fixture
def sample_code_generation_task():
    """Create a sample code generation task."""
    return Task(
        task_type="coding",
        description="Code generation task",
        input_data={
            "task_type": "generation",
            "requirements": "Create a function to sort an array",
            "language": "python",
            "context": {}
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.CODING
    )


@pytest.fixture
def sample_code_refactoring_task():
    """Create a sample code refactoring task."""
    return Task(
        task_type="coding",
        description="Code refactoring task",
        input_data={
            "task_type": "refactoring",
            "code": "def foo(x): return x+1",
            "goals": ["performance", "readability"]
        },
        priority=TaskPriority.MEDIUM,
        agent_role=AgentRole.CODING
    )


@pytest.mark.asyncio
async def test_coding_initialization(coding_agent):
    """Test coding agent initialization."""
    await coding_agent.initialize()
    assert coding_agent.agent_id == "test_coding"
    assert coding_agent.role == AgentRole.CODING


@pytest.mark.asyncio
async def test_coding_shutdown(coding_agent):
    """Test coding agent shutdown."""
    await coding_agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
@patch('app.agents.coding_agent.ai_engine')
async def test_coding_code_generation(mock_ai_engine, coding_agent, sample_code_generation_task):
    """Test code generation."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = "def sort_array(arr): return sorted(arr)"
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await coding_agent.execute(sample_code_generation_task)
    
    assert response.success is True
    assert "code" in response.data
    assert response.data["language"] == "python"


@pytest.mark.asyncio
@patch('app.agents.coding_agent.ai_engine')
async def test_coding_code_refactoring(mock_ai_engine, coding_agent, sample_code_refactoring_task):
    """Test code refactoring."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = "def increment(x): return x + 1"
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await coding_agent.execute(sample_code_refactoring_task)
    
    assert response.success is True
    assert "refactored_code" in response.data
    assert "original_code" in response.data


@pytest.mark.asyncio
async def test_coding_unknown_type(coding_agent):
    """Test coding with unknown type."""
    task = Task(
        task_type="coding",
        description="Test task",
        input_data={"task_type": "unknown"},
        agent_role=AgentRole.CODING
    )
    
    response = await coding_agent.execute(task)
    
    assert response.success is False
    assert "Unknown coding task type" in response.error


def test_coding_get_capabilities(coding_agent):
    """Test getting coding capabilities."""
    capabilities = coding_agent.get_capabilities()
    
    assert isinstance(capabilities, list)
    assert "code_generation" in capabilities
    assert "code_refactoring" in capabilities
    assert "debugging" in capabilities
    assert "test_generation" in capabilities
    assert "code_review" in capabilities


def test_coding_get_status(coding_agent):
    """Test getting coding status."""
    status = coding_agent.get_status()
    
    assert status["agent_id"] == "test_coding"
    assert status["role"] == "coding"
