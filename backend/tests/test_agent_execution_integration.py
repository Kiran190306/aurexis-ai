"""
Integration tests for multi-agent execution flow.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.planner_agent import PlannerAgent
from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.research_agent import ResearchAgent
from app.agents.coding_agent import CodingAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.tool_agent import ToolAgent
from app.agents.reflection_agent import ReflectionAgent
from app.agents.base import Task, AgentRole, TaskPriority, ExecutionPlan
from app.agents.event_bus import event_bus


@pytest.fixture
async def agent_system():
    """Set up the full agent system for integration testing."""
    # Initialize agents
    planner = PlannerAgent()
    orchestrator = OrchestratorAgent()
    research = ResearchAgent()
    coding = CodingAgent()
    memory = MemoryAgent()
    tool = ToolAgent()
    reflection = ReflectionAgent()
    
    # Initialize all agents
    await planner.initialize()
    await orchestrator.initialize()
    await research.initialize()
    await coding.initialize()
    await memory.initialize()
    await tool.initialize()
    await reflection.initialize()
    
    # Register agents with orchestrator
    orchestrator.register_agent(AgentRole.RESEARCH, research.agent_id)
    orchestrator.register_agent(AgentRole.CODING, coding.agent_id)
    orchestrator.register_agent(AgentRole.MEMORY, memory.agent_id)
    orchestrator.register_agent(AgentRole.TOOL, tool.agent_id)
    
    # Start event bus
    await event_bus.start()
    
    yield {
        "planner": planner,
        "orchestrator": orchestrator,
        "research": research,
        "coding": coding,
        "memory": memory,
        "tool": tool,
        "reflection": reflection
    }
    
    # Cleanup
    await event_bus.stop()
    await planner.shutdown()
    await orchestrator.shutdown()
    await research.shutdown()
    await coding.shutdown()
    await memory.shutdown()
    await tool.shutdown()
    await reflection.shutdown()


@pytest.mark.asyncio
@patch('app.agents.planner_agent.ai_engine')
@patch('app.agents.orchestrator_agent.ai_engine')
@patch('app.agents.orchestrator_agent.event_bus')
async def test_full_execution_flow(mock_event_bus, mock_orchestrator_ai_engine, mock_planner_ai_engine, agent_system):
    """Test the complete execution flow from request to response."""
    # Mock AI engine for planner
    mock_plan_response = MagicMock()
    mock_plan_response.content = '''{
        "tasks": [
            {
                "task_type": "research",
                "description": "Research task",
                "priority": "high",
                "dependencies": [],
                "agent_role": "research",
                "input_data": {},
                "estimated_duration": 30
            }
        ],
        "estimated_duration": 30,
        "metadata": {}
    }'''
    
    # Mock AI engine for orchestrator (for result aggregation)
    mock_synthesis_response = MagicMock()
    mock_synthesis_response.content = "Synthesized test response"
    
    # Mock event bus for orchestrator
    mock_agent_message = MagicMock()
    mock_agent_message.content = {"success": True, "data": {"result": "test result"}}
    mock_event_bus.publish_and_wait = AsyncMock(return_value=mock_agent_message)
    
    mock_planner_ai_engine.generate = AsyncMock(return_value=mock_plan_response)
    mock_orchestrator_ai_engine.generate = AsyncMock(return_value=mock_synthesis_response)
    
    planner = agent_system["planner"]
    orchestrator = agent_system["orchestrator"]
    
    # Step 1: Create execution plan
    planner_task = Task(
        task_type="planning",
        description="Create plan",
        input_data={"request": "Test request", "context": {}},
        agent_role=AgentRole.PLANNER
    )
    
    planner_response = await planner.execute(planner_task)
    assert planner_response.success is True
    assert "execution_plan" in planner_response.data
    
    # Step 2: Execute plan via orchestrator
    execution_plan_data = planner_response.data["execution_plan"]
    orchestrator_task = Task(
        task_type="orchestration",
        description="Execute plan",
        input_data={"execution_plan": execution_plan_data},
        agent_role=AgentRole.ORCHESTRATOR
    )
    
    orchestrator_response = await orchestrator.execute(orchestrator_task)
    assert orchestrator_response.success is True
    assert "results" in orchestrator_response.data


@pytest.mark.asyncio
@patch('app.agents.planner_agent.ai_engine')
@patch('app.agents.planner_agent.KnowledgeAgent')
async def test_planner_to_orchestrator_integration(mock_knowledge_agent, mock_ai_engine, agent_system):
    """Test integration between planner and orchestrator."""
    planner = agent_system["planner"]
    orchestrator = agent_system["orchestrator"]
    
    # Mock planner response
    mock_response = MagicMock()
    mock_response.content = '''{
        "tasks": [],
        "estimated_duration": 0,
        "metadata": {}
    }'''
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    # Mock KnowledgeAgent to prevent RAG calls
    mock_knowledge_instance = AsyncMock()
    mock_knowledge_instance.query = AsyncMock(return_value=MagicMock(
        context=MagicMock(context_text=""),
        sources=[]
    ))
    mock_knowledge_agent.return_value = mock_knowledge_instance
    
    # Create plan
    task = Task(
        task_type="planning",
        description="Test",
        input_data={"request": "Test", "context": {}},
        agent_role=AgentRole.PLANNER
    )
    
    response = await planner.execute(task)
    assert response.success is True
    
    # Verify plan can be used by orchestrator
    execution_plan = ExecutionPlan(**response.data["execution_plan"])
    assert execution_plan.user_request == "Test"


@pytest.mark.asyncio
async def test_agent_communication_via_event_bus(agent_system):
    """Test agent communication through event bus."""
    from app.agents.base import AgentMessage
    
    research = agent_system["research"]
    
    # Subscribe to messages
    received_messages = []
    
    async def message_handler(message: AgentMessage):
        received_messages.append(message)
    
    await event_bus.subscribe(research.agent_id, "test_message", message_handler)
    
    # Send message
    message = AgentMessage(
        sender="test_sender",
        receiver=research.agent_id,
        message_type="test_message",
        content={"test": "data"}
    )
    
    await event_bus.publish(message)
    
    # Wait for message to be processed
    import asyncio
    await asyncio.sleep(0.1)
    
    assert len(received_messages) == 1
    assert received_messages[0].message_type == "test_message"


@pytest.mark.asyncio
async def test_orchestrator_agent_registration(agent_system):
    """Test orchestrator agent registration."""
    orchestrator = agent_system["orchestrator"]
    
    # Verify agents are registered
    assert AgentRole.RESEARCH in orchestrator.agent_registry
    assert AgentRole.CODING in orchestrator.agent_registry
    assert AgentRole.MEMORY in orchestrator.agent_registry
    assert AgentRole.TOOL in orchestrator.agent_registry


@pytest.mark.asyncio
@patch('app.agents.reflection_agent.ai_engine')
async def test_reflection_quality_check_integration(mock_ai_engine, agent_system):
    """Test reflection agent quality check integration."""
    reflection = agent_system["reflection"]
    
    # Mock AI response
    mock_response = MagicMock()
    mock_response.content = '{"overall_score": 0.8, "quality_pass": true}'
    mock_ai_engine.generate = AsyncMock(return_value=mock_response)
    
    task = Task(
        task_type="reflection",
        description="Quality check",
        input_data={
            "task_type": "quality_check",
            "generated_response": "Test response",
            "original_request": "Test request"
        },
        agent_role=AgentRole.REFLECTION
    )
    
    response = await reflection.execute(task)
    assert response.success is True
    assert response.data["overall_quality_pass"] is True


@pytest.mark.asyncio
async def test_memory_agent_integration(agent_system):
    """Test memory agent integration with storage and retrieval."""
    memory = agent_system["memory"]
    
    # Store memory
    store_task = Task(
        task_type="memory",
        description="Store memory",
        input_data={
            "task_type": "store",
            "content": "Test content",
            "memory_type": "episodic",
            "importance": 0.5,
            "tags": []
        },
        agent_role=AgentRole.MEMORY
    )
    
    store_response = await memory.execute(store_task)
    assert store_response.success is True
    memory_id = store_response.data["memory_id"]
    
    # Retrieve memory
    retrieve_task = Task(
        task_type="memory",
        description="Retrieve memory",
        input_data={
            "task_type": "retrieve",
            "memory_id": memory_id
        },
        agent_role=AgentRole.MEMORY
    )
    
    retrieve_response = await memory.execute(retrieve_task)
    assert retrieve_response.success is True


@pytest.mark.asyncio
async def test_tool_agent_tool_registration(agent_system):
    """Test tool agent tool registration."""
    tool = agent_system["tool"]
    
    # Verify default tools are registered
    assert "web_search" in tool.tool_registry
    assert "file_read" in tool.tool_registry
    assert "file_write" in tool.tool_registry


@pytest.mark.asyncio
async def test_event_bus_stats(agent_system):
    """Test event bus statistics."""
    stats = event_bus.get_stats()
    
    assert "subscribers" in stats
    assert "queue_size" in stats
    assert "running" in stats
    assert stats["running"] is True


@pytest.mark.asyncio
async def test_agent_capabilities(agent_system):
    """Test all agents have capabilities."""
    for agent_name, agent in agent_system.items():
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0


@pytest.mark.asyncio
async def test_agent_status(agent_system):
    """Test all agents can report status."""
    for agent_name, agent in agent_system.items():
        status = agent.get_status()
        assert "agent_id" in status
        assert "role" in status
