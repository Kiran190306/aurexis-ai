"""
Unit tests for Orchestrator Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.base import Task, AgentRole, TaskPriority, ExecutionPlan


@pytest.fixture
def orchestrator_agent():
    """Create an Orchestrator Agent instance for testing."""
    return OrchestratorAgent(agent_id="test_orchestrator")


@pytest.fixture
def sample_execution_plan():
    """Create a sample execution plan for testing."""
    return ExecutionPlan(
        user_request="Test request",
        tasks=[
            Task(
                task_type="research",
                description="Research task",
                input_data={},
                priority=TaskPriority.HIGH,
                agent_role=AgentRole.RESEARCH,
                dependencies=[]
            )
        ],
        estimated_duration_seconds=60
    )


@pytest.fixture
def sample_orchestration_task(sample_execution_plan):
    """Create a sample orchestration task."""
    return Task(
        task_type="orchestration",
        description="Orchestrate execution",
        input_data={
            "execution_plan": sample_execution_plan.model_dump()
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.ORCHESTRATOR
    )


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator_agent):
    """Test orchestrator agent initialization."""
    await orchestrator_agent.initialize()
    assert orchestrator_agent.agent_id == "test_orchestrator"
    assert orchestrator_agent.role == AgentRole.ORCHESTRATOR


@pytest.mark.asyncio
async def test_orchestrator_shutdown(orchestrator_agent):
    """Test orchestrator agent shutdown."""
    await orchestrator_agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
async def test_orchestrator_register_agent(orchestrator_agent):
    """Test registering an agent with orchestrator."""
    orchestrator_agent.register_agent(AgentRole.RESEARCH, "research_agent")
    
    assert AgentRole.RESEARCH in orchestrator_agent.agent_registry
    assert orchestrator_agent.agent_registry[AgentRole.RESEARCH] == "research_agent"


@pytest.mark.asyncio
async def test_orchestrator_execute_no_plan(orchestrator_agent):
    """Test orchestrator execution with no execution plan."""
    task = Task(
        task_type="orchestration",
        description="Test task",
        input_data={},
        agent_role=AgentRole.ORCHESTRATOR
    )
    
    response = await orchestrator_agent.execute(task)
    
    assert response.success is False
    assert "No execution plan provided" in response.error


@pytest.mark.asyncio
@patch('app.agents.orchestrator_agent.ai_engine')
@patch('app.agents.event_bus.event_bus.publish_and_wait', new_callable=AsyncMock)
async def test_orchestrator_execute_success(mock_publish_and_wait, mock_ai_engine, orchestrator_agent, sample_orchestration_task):
    """Test successful execution of orchestration task."""
    # Register agents
    orchestrator_agent.register_agent(AgentRole.RESEARCH, "research_agent")
    
    # Mock event bus response
    mock_response = MagicMock()
    mock_response.content = {"success": True, "data": {"result": "test"}}
    mock_publish_and_wait.return_value = mock_response
    
    # Mock AI engine
    mock_ai_response = MagicMock()
    mock_ai_response.content = "Synthesized response"
    mock_ai_engine.generate = AsyncMock(return_value=mock_ai_response)
    
    response = await orchestrator_agent.execute(sample_orchestration_task)
    
    assert response.success is True
    assert "results" in response.data


def test_orchestrator_get_capabilities(orchestrator_agent):
    """Test getting orchestrator capabilities."""
    capabilities = orchestrator_agent.get_capabilities()
    
    assert isinstance(capabilities, list)
    assert "task_assignment" in capabilities
    assert "progress_monitoring" in capabilities
    assert "result_aggregation" in capabilities


def test_orchestrator_get_status(orchestrator_agent):
    """Test getting orchestrator status."""
    status = orchestrator_agent.get_status()
    
    assert status["agent_id"] == "test_orchestrator"
    assert status["role"] == "orchestrator"
    assert "active_tasks" in status
    assert "completed_tasks" in status
    assert "failed_tasks" in status
    assert "registered_agents" in status
