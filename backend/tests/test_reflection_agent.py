"""
Unit tests for Reflection Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.reflection_agent import ReflectionAgent
from app.agents.base import Task, AgentRole, TaskPriority


@pytest.fixture
def reflection_agent():
    """Create a Reflection Agent instance for testing."""
    return ReflectionAgent(agent_id="test_reflection")


@pytest.fixture
def sample_evaluate_task():
    """Create a sample evaluate task."""
    return Task(
        task_type="reflection",
        description="Evaluate response task",
        input_data={
            "task_type": "evaluate",
            "original_request": "Test request",
            "generated_response": "Test response",
            "context": {}
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.REFLECTION
    )


@pytest.fixture
def sample_hallucination_task():
    """Create a sample hallucination detection task."""
    return Task(
        task_type="reflection",
        description="Detect hallucination task",
        input_data={
            "task_type": "detect_hallucination",
            "generated_response": "Test response",
            "knowledge_base": []
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.REFLECTION
    )


@pytest.mark.asyncio
async def test_reflection_initialization(reflection_agent):
    """Test reflection agent initialization."""
    await reflection_agent.initialize()
    assert reflection_agent.agent_id == "test_reflection"
    assert reflection_agent.role == AgentRole.REFLECTION


@pytest.mark.asyncio
async def test_reflection_shutdown(reflection_agent):
    """Test reflection agent shutdown."""
    await reflection_agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
@patch('app.agents.reflection_agent.ai_engine')
async def test_reflection_evaluate(mock_ai_engine, reflection_agent, sample_evaluate_task):
    """Test response evaluation."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = '''{
        "overall_score": 0.85,
        "relevance": 0.9,
        "accuracy": 0.8,
        "completeness": 0.85,
        "feedback": "Good response"
    }'''
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await reflection_agent.execute(sample_evaluate_task)
    
    assert response.success is True
    assert "evaluation" in response.data
    assert response.data["overall_score"] == 0.85
    assert response.data["quality_pass"] is True


@pytest.mark.asyncio
@patch('app.agents.reflection_agent.ai_engine')
async def test_reflection_detect_hallucination(mock_ai_engine, reflection_agent, sample_hallucination_task):
    """Test hallucination detection."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = '''{
        "hallucination_probability": 0.2,
        "analysis": "Low hallucination risk"
    }'''
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await reflection_agent.execute(sample_hallucination_task)
    
    assert response.success is True
    assert "analysis" in response.data
    assert response.data["hallucination_score"] == 0.2
    assert response.data["has_hallucination"] is False


@pytest.mark.asyncio
@patch('app.agents.reflection_agent.ai_engine')
async def test_reflection_quality_check(mock_ai_engine, reflection_agent):
    """Test comprehensive quality check."""
    # Mock AI engine responses
    mock_eval_response = MagicMock()
    mock_eval_response.content = '{"overall_score": 0.8, "quality_pass": true}'
    
    mock_hallucination_response = MagicMock()
    mock_hallucination_response.content = '{"hallucination_probability": 0.1, "has_hallucination": false}'
    
    mock_ai_engine.generate = AsyncMock(side_effect=[mock_eval_response, mock_hallucination_response])
    
    task = Task(
        task_type="reflection",
        description="Quality check task",
        input_data={
            "task_type": "quality_check",
            "generated_response": "Test response",
            "original_request": "Test request"
        },
        agent_role=AgentRole.REFLECTION
    )
    
    response = await reflection_agent.execute(task)
    
    assert response.success is True
    assert "evaluation" in response.data
    assert "hallucination_check" in response.data
    assert response.data["overall_quality_pass"] is True


@pytest.mark.asyncio
async def test_reflection_unknown_type(reflection_agent):
    """Test reflection with unknown type."""
    task = Task(
        task_type="reflection",
        description="Test task",
        input_data={"task_type": "unknown"},
        agent_role=AgentRole.REFLECTION
    )
    
    response = await reflection_agent.execute(task)
    
    assert response.success is False
    assert "Unknown reflection task type" in response.error


def test_reflection_get_capabilities(reflection_agent):
    """Test getting reflection capabilities."""
    capabilities = reflection_agent.get_capabilities()
    
    assert isinstance(capabilities, list)
    assert "response_evaluation" in capabilities
    assert "hallucination_detection" in capabilities
    assert "reasoning_verification" in capabilities
    assert "quality_assurance" in capabilities


def test_reflection_get_status(reflection_agent):
    """Test getting reflection status."""
    status = reflection_agent.get_status()
    
    assert status["agent_id"] == "test_reflection"
    assert status["role"] == "reflection"
