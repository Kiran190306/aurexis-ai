"""
Unit tests for Planner Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.planner_agent import PlannerAgent
from app.agents.base import Task, AgentRole, TaskPriority


@pytest.fixture
def planner_agent():
    """Create a Planner Agent instance for testing."""
    return PlannerAgent(agent_id="test_planner")


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        task_type="planning",
        description="Test planning task",
        input_data={
            "request": "Research the latest AI developments",
            "context": {"user_id": 1}
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.PLANNER
    )


@pytest.mark.asyncio
async def test_planner_initialization(planner_agent):
    """Test planner agent initialization."""
    await planner_agent.initialize()
    assert planner_agent.agent_id == "test_planner"
    assert planner_agent.role == AgentRole.PLANNER


@pytest.mark.asyncio
async def test_planner_shutdown(planner_agent):
    """Test planner agent shutdown."""
    await planner_agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
@patch('app.agents.planner_agent.ai_engine')
async def test_planner_execute_success(mock_ai_engine, planner_agent, sample_task):
    """Test successful execution of planning task."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = '''{
        "tasks": [
            {
                "task_type": "research",
                "description": "Search for AI developments",
                "priority": "high",
                "dependencies": [],
                "agent_role": "research",
                "input_data": {},
                "estimated_duration": 60
            }
        ],
        "estimated_duration": 60,
        "metadata": {
            "complexity": "medium"
        }
    }'''
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await planner_agent.execute(sample_task)
    
    assert response.success is True
    assert "execution_plan" in response.data
    assert response.data["task_count"] == 1


@pytest.mark.asyncio
async def test_planner_execute_no_request(planner_agent):
    """Test planner execution with no request."""
    task = Task(
        task_type="planning",
        description="Test task",
        input_data={},
        agent_role=AgentRole.PLANNER
    )
    
    response = await planner_agent.execute(task)
    
    assert response.success is False
    assert "No user request provided" in response.error


@pytest.mark.asyncio
@patch('app.agents.planner_agent.ai_engine')
async def test_planner_execute_ai_error(mock_ai_engine, planner_agent, sample_task):
    """Test planner execution with AI engine error."""
    mock_ai_engine.generate = AsyncMock(side_effect=Exception("AI Engine error"))
    
    response = await planner_agent.execute(sample_task)
    
    assert response.success is False
    assert "AI Engine error" in response.error


def test_planner_get_capabilities(planner_agent):
    """Test getting planner capabilities."""
    capabilities = planner_agent.get_capabilities()
    
    assert isinstance(capabilities, list)
    assert "task_decomposition" in capabilities
    assert "dependency_analysis" in capabilities
    assert "priority_estimation" in capabilities


def test_planner_get_status(planner_agent):
    """Test getting planner status."""
    status = planner_agent.get_status()
    
    assert status["agent_id"] == "test_planner"
    assert status["role"] == "planner"
    assert "config" in status
