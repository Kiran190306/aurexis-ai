"""
Unit tests for Research Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.research_agent import ResearchAgent
from app.agents.base import Task, AgentRole, TaskPriority


@pytest.fixture
def research_agent():
    """Create a Research Agent instance for testing."""
    return ResearchAgent(agent_id="test_research")


@pytest.fixture
def sample_web_search_task():
    """Create a sample web search task."""
    return Task(
        task_type="research",
        description="Web search task",
        input_data={
            "research_type": "web_search",
            "query": "AI developments 2024",
            "max_results": 10
        },
        priority=TaskPriority.HIGH,
        agent_role=AgentRole.RESEARCH
    )


@pytest.fixture
def sample_document_analysis_task():
    """Create a sample document analysis task."""
    return Task(
        task_type="research",
        description="Document analysis task",
        input_data={
            "research_type": "document_analysis",
            "document_ids": ["doc1", "doc2"],
            "analysis_type": "summary"
        },
        priority=TaskPriority.MEDIUM,
        agent_role=AgentRole.RESEARCH
    )


@pytest.mark.asyncio
async def test_research_initialization(research_agent):
    """Test research agent initialization."""
    await research_agent.initialize()
    assert research_agent.agent_id == "test_research"
    assert research_agent.role == AgentRole.RESEARCH


@pytest.mark.asyncio
async def test_research_shutdown(research_agent):
    """Test research agent shutdown."""
    await research_agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
@patch('app.agents.research_agent.ai_engine')
async def test_research_web_search(mock_ai_engine, research_agent, sample_web_search_task):
    """Test web search research."""
    # Mock AI engine response
    mock_response = MagicMock()
    mock_response.content = '{"strategy": "test strategy"}'
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    response = await research_agent.execute(sample_web_search_task)
    
    assert response.success is True
    assert "query" in response.data
    assert "results" in response.data


@pytest.mark.asyncio
async def test_research_document_analysis(research_agent, sample_document_analysis_task):
    """Test document analysis research."""
    response = await research_agent.execute(sample_document_analysis_task)
    
    assert response.success is True
    assert "document_ids" in response.data
    assert "analysis_type" in response.data


@pytest.mark.asyncio
@patch('app.agents.research_agent.ai_engine')
async def test_research_unknown_type(mock_ai_engine, research_agent):
    """Test research with unknown type - falls back to general research."""
    task = Task(
        task_type="research",
        description="Test task",
        input_data={"research_type": "unknown"},
        agent_role=AgentRole.RESEARCH
    )
    
    # Mock AI engine for general research fallback
    mock_ai_response = MagicMock()
    mock_ai_response.content = "General research result"
    mock_ai_engine.generate = AsyncMock(return_value=mock_ai_response)
    
    response = await research_agent.execute(task)
    
    # Unknown types fall back to general research, so should succeed
    assert response.success is True
    assert "research_summary" in response.data


def test_research_get_capabilities(research_agent):
    """Test getting research capabilities."""
    capabilities = research_agent.get_capabilities()
    
    assert isinstance(capabilities, list)
    assert "web_search" in capabilities
    assert "document_analysis" in capabilities
    assert "source_ranking" in capabilities
    assert "knowledge_extraction" in capabilities


def test_research_get_status(research_agent):
    """Test getting research status."""
    status = research_agent.get_status()
    
    assert status["agent_id"] == "test_research"
    assert status["role"] == "research"
