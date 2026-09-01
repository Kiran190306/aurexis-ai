"""
Unit tests for Memory Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.memory_agent import MemoryAgent
from app.agents.base import Task, AgentRole, TaskPriority


@pytest.fixture
def memory_agent():
    """Create a Memory Agent instance for testing."""
    return MemoryAgent(agent_id="test_memory")


@pytest.fixture
def sample_store_task():
    """Create a sample store memory task."""
    return Task(
        task_type="memory",
        description="Store memory task",
        input_data={
            "task_type": "store",
            "content": "Important information to remember",
            "memory_type": "episodic",
            "importance": 0.8,
            "tags": ["important", "user_data"]
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.MEMORY
    )


@pytest.fixture
def sample_retrieve_task():
    """Create a sample retrieve memory task."""
    return Task(
        task_type="memory",
        description="Retrieve memory task",
        input_data={
            "task_type": "retrieve",
            "memory_id": "test_memory_id"
        },
        priority=TaskPriority.MEDIUM,
        agent_role=AgentRole.MEMORY
    )


@pytest.fixture
def sample_search_task():
    """Create a sample search memory task."""
    return Task(
        task_type="memory",
        description="Search memory task",
        input_data={
            "task_type": "search",
            "query": "important information",
            "memory_type": None,
            "limit": 10
        },
        priority=TaskPriority.MEDIUM,
        agent_role=AgentRole.MEMORY
    )


@pytest.mark.asyncio
async def test_memory_initialization(memory_agent):
    """Test memory agent initialization."""
    await memory_agent.initialize()
    assert memory_agent.agent_id == "test_memory"
    assert memory_agent.role == AgentRole.MEMORY


@pytest.mark.asyncio
async def test_memory_shutdown(memory_agent):
    """Test memory agent shutdown."""
    await memory_agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
async def test_memory_store(memory_agent, sample_store_task):
    """Test storing memory."""
    response = await memory_agent.execute(sample_store_task)
    
    assert response.success is True
    assert "memory_id" in response.data
    assert response.data["memory_type"] == "episodic"


@pytest.mark.asyncio
async def test_memory_retrieve(memory_agent, sample_retrieve_task):
    """Test retrieving memory."""
    # First store a memory
    store_task = Task(
        task_type="memory",
        description="Store task",
        input_data={
            "task_type": "store",
            "content": "Test content",
            "memory_type": "episodic",
            "importance": 0.5,
            "tags": []
        },
        agent_role=AgentRole.MEMORY
    )
    store_response = await memory_agent.execute(store_task)
    memory_id = store_response.data["memory_id"]
    
    # Now retrieve it
    retrieve_task = Task(
        task_type="memory",
        description="Retrieve task",
        input_data={
            "task_type": "retrieve",
            "memory_id": memory_id
        },
        agent_role=AgentRole.MEMORY
    )
    
    response = await memory_agent.execute(retrieve_task)
    
    assert response.success is True
    assert "memory" in response.data


@pytest.mark.asyncio
@patch('app.agents.memory_agent.ai_engine')
async def test_memory_search(mock_ai_engine, memory_agent, sample_search_task):
    """Test searching memory."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = '["important", "information"]'
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await memory_agent.execute(sample_search_task)
    
    assert response.success is True
    assert "query" in response.data
    assert "results" in response.data


@pytest.mark.asyncio
async def test_memory_unknown_type(memory_agent):
    """Test memory with unknown type."""
    task = Task(
        task_type="memory",
        description="Test task",
        input_data={"task_type": "unknown"},
        agent_role=AgentRole.MEMORY
    )
    
    response = await memory_agent.execute(task)
    
    assert response.success is False
    assert "Unknown memory task type" in response.error


def test_memory_get_capabilities(memory_agent):
    """Test getting memory capabilities."""
    capabilities = memory_agent.get_capabilities()
    
    assert isinstance(capabilities, list)
    assert "memory_storage" in capabilities
    assert "memory_retrieval" in capabilities
    assert "memory_search" in capabilities
    assert "context_retrieval" in capabilities


def test_memory_get_status(memory_agent):
    """Test getting memory status."""
    status = memory_agent.get_status()
    
    assert status["agent_id"] == "test_memory"
    assert status["role"] == "memory"
