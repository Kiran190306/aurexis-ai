# Multi-Agent Architecture Documentation

## Overview

Jarvis AI v1.1 implements a production-grade autonomous multi-agent system that transforms the platform from a single AI assistant into a coordinated network of specialized agents. This architecture enables complex task decomposition, parallel execution, and intelligent coordination between agents with different capabilities.

## Architecture Principles

- **Async Architecture**: All agent operations are asynchronous for non-blocking execution
- **Event-Driven Communication**: Agents communicate via an async event bus using pub/sub pattern
- **Dependency Injection**: Agent dependencies are injected through the orchestrator
- **Structured Logging**: All operations are logged with structured JSON format
- **Retry Policies**: Configurable retry logic with exponential backoff
- **Timeout Handling**: Comprehensive timeout management for all operations
- **Metrics Collection**: Prometheus metrics for monitoring and observability
- **Backward Compatibility**: Maintains compatibility with existing single-agent mode

## Agent Roles

### 1. Planner Agent
**Purpose**: Breaks complex user requests into executable tasks

**Responsibilities**:
- Analyze user requests and understand intent
- Decompose complex requests into atomic tasks
- Identify dependencies between tasks
- Prioritize tasks based on importance and dependencies
- Estimate task duration and complexity
- Generate structured execution plans

**Capabilities**:
- `task_decomposition`
- `dependency_analysis`
- `priority_estimation`
- `duration_estimation`
- `execution_planning`

### 2. Orchestrator Agent
**Purpose**: Manages task execution and agent coordination

**Responsibilities**:
- Receive execution plans from Planner
- Assign tasks to appropriate specialized agents
- Monitor task progress in real-time
- Handle task failures and implement retries
- Aggregate results from multiple agents
- Coordinate dependencies between tasks
- Manage agent registry and availability

**Capabilities**:
- `task_assignment`
- `progress_monitoring`
- `failure_handling`
- `result_aggregation`
- `dependency_management`

### 3. Research Agent
**Purpose**: Handles web research, document analysis, and knowledge extraction

**Responsibilities**:
- Conduct web research on given topics
- Analyze documents and extract key information
- Rank sources by credibility and relevance
- Provide citations and references
- Synthesize research findings
- Identify knowledge gaps

**Capabilities**:
- `web_search`
- `document_analysis`
- `source_ranking`
- `knowledge_extraction`
- `citation_generation`
- `research_synthesis`

### 4. Coding Agent
**Purpose**: Handles code generation, refactoring, debugging, and testing

**Responsibilities**:
- Generate clean, efficient, well-documented code
- Refactor existing code for performance and readability
- Debug code issues and provide fixes
- Generate comprehensive unit and integration tests
- Review code for best practices and security
- Generate documentation and comments

**Capabilities**:
- `code_generation`
- `code_refactoring`
- `debugging`
- `test_generation`
- `code_review`
- `documentation_generation`
- `security_analysis`

### 5. Memory Agent
**Purpose**: Manages long-term memory, short-term memory, and context retrieval

**Responsibilities**:
- Store and retrieve information from long-term memory
- Manage short-term working memory for current context
- Compress and summarize old memories to save space
- Retrieve relevant context based on queries
- Identify important information to remember long-term
- Synthesize related memories for context

**Capabilities**:
- `memory_storage`
- `memory_retrieval`
- `memory_search`
- `memory_compression`
- `memory_summarization`
- `context_retrieval`
- `short_term_memory`
- `long_term_memory`

### 6. Tool Agent
**Purpose**: Handles dynamic tool selection, execution, and permission validation

**Responsibilities**:
- Select appropriate tools for given tasks
- Execute tools with proper parameters
- Validate permissions before tool execution
- Handle tool errors and implement recovery
- Chain multiple tools for complex operations
- Monitor tool performance and reliability
- Maintain tool usage statistics

**Capabilities**:
- `tool_selection`
- `tool_execution`
- `permission_validation`
- `tool_chaining`
- `error_recovery`
- `tool_registration`
- `performance_monitoring`

### 7. Reflection Agent
**Purpose**: Evaluates responses, detects hallucinations, and verifies reasoning

**Responsibilities**:
- Evaluate generated responses for quality and accuracy
- Detect potential hallucinations or factual errors
- Verify reasoning logic and coherence
- Identify areas for improvement
- Suggest corrections or refinements
- Trigger retries when quality is insufficient
- Provide detailed feedback for agent improvement

**Capabilities**:
- `response_evaluation`
- `hallucination_detection`
- `reasoning_verification`
- `improvement_suggestion`
- `quality_assurance`
- `feedback_generation`

## Execution Flow

```
User Request
    ↓
Planner Agent (decompose request into tasks)
    ↓
Execution Plan (structured task list with dependencies)
    ↓
Orchestrator Agent (assign tasks to specialized agents)
    ↓
Specialized Agents (execute tasks in parallel/sequence)
    ├─ Research Agent
    ├─ Coding Agent
    ├─ Memory Agent
    └─ Tool Agent
    ↓
Reflection Agent (evaluate quality and detect issues)
    ↓
Memory Agent (update memory with new information)
    ↓
Final Response (aggregated and synthesized)
```

## Data Models

### Task
```python
class Task(BaseModel):
    id: str
    task_type: str
    description: str
    input_data: Dict[str, Any]
    priority: TaskPriority  # critical, high, medium, low
    status: TaskStatus  # pending, running, completed, failed, cancelled, retrying
    agent_role: AgentRole
    dependencies: List[str]
    retry_count: int
    max_retries: int
    timeout_seconds: int
    metadata: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    output_data: Optional[Dict[str, Any]]
```

### ExecutionPlan
```python
class ExecutionPlan(BaseModel):
    id: str
    user_request: str
    tasks: List[Task]
    estimated_duration_seconds: int
    metadata: Dict[str, Any]
    created_at: datetime
```

### AgentMessage
```python
class AgentMessage(BaseModel):
    id: str
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str]
```

## Database Schema

### AgentExecutionPlan
Stores execution plans generated by the Planner agent.

**Fields**:
- `id`, `uuid`, `user_id`, `conversation_id`
- `user_request`, `context`, `plan_data`
- `task_count`, `estimated_duration_seconds`
- `status`, `started_at`, `completed_at`, `execution_time_seconds`
- `final_output`, `result_summary`
- `error_message`, `error_code`
- `metadata_json`, `created_at`, `updated_at`

### AgentExecutionLog
Stores execution logs for tracking agent operations.

**Fields**:
- `id`, `uuid`, `execution_plan_id`, `agent_id`
- `task_id`, `task_type`, `agent_role`
- `input_data`, `output_data`
- `status`, `started_at`, `completed_at`, `execution_time_seconds`
- `retry_count`, `timeout_seconds`
- `error_message`, `error_code`
- `depends_on`, `metadata_json`
- `created_at`, `updated_at`

### AgentMetrics
Stores performance metrics for agents.

**Fields**:
- `id`, `agent_id`, `user_id`
- `total_executions`, `successful_executions`, `failed_executions`, `success_rate`
- `avg_execution_time_seconds`, `min_execution_time_seconds`, `max_execution_time_seconds`
- `avg_quality_score`, `hallucination_count`
- `avg_token_usage`, `total_token_usage`
- `period_start`, `period_end`
- `created_at`, `updated_at`

### AgentEvent
Stores event log for agent communication and state changes.

**Fields**:
- `id`, `uuid`, `execution_plan_id`, `execution_log_id`, `agent_id`
- `event_type`, `event_source`, `event_target`
- `event_data`, `message_type`, `message_content`, `correlation_id`
- `created_at`

## API Endpoints

### Agent Execution

#### POST /api/v1/agent-execution/execute
Execute a multi-agent request.

**Request Body**:
```json
{
  "request": "User request text",
  "context": {},
  "conversation_id": 123,
  "enable_reflection": true
}
```

**Response**:
```json
{
  "execution_plan_id": "uuid",
  "status": "completed",
  "result": {},
  "summary": "Synthesized response",
  "execution_time_seconds": 45.2,
  "metadata": {}
}
```

#### GET /api/v1/agent-execution/plans
List execution plans for current user.

**Query Parameters**: `skip`, `limit`

#### GET /api/v1/agent-execution/plans/{plan_uuid}
Get a specific execution plan.

#### GET /api/v1/agent-execution/plans/{plan_uuid}/logs
Get execution logs for a plan.

#### POST /api/v1/agent-execution/plans/{plan_uuid}/cancel
Cancel a running execution plan.

#### GET /api/v1/agent-execution/agents/status
Get status of all agents.

**Response**:
```json
{
  "planner": { "agent_id": "planner", "role": "planner", "config": {} },
  "orchestrator": { "agent_id": "orchestrator", "role": "orchestrator", "config": {} },
  ...
}
```

#### GET /api/v1/agent-execution/agents/capabilities
Get capabilities of all agents.

**Response**:
```json
{
  "planner": { "capabilities": ["task_decomposition", "dependency_analysis"] },
  "orchestrator": { "capabilities": ["task_assignment", "progress_monitoring"] },
  ...
}
```

## Event Bus

The event bus provides async pub/sub communication between agents.

### Features
- **Async message passing**: Non-blocking message delivery
- **Type-based routing**: Messages routed by type
- **Request-response pattern**: Support for synchronous-style async calls
- **Automatic cleanup**: Unsubscribe on agent shutdown

### Usage
```python
# Subscribe to messages
await event_bus.subscribe(agent_id, "task_completed", handler)

# Publish message
message = AgentMessage(
    sender=sender_id,
    receiver=receiver_id,
    message_type="execute_task",
    content={"task": task_data}
)
await event_bus.publish(message)

# Publish and wait for response
response = await event_bus.publish_and_wait(message, timeout=30.0)
```

## Retry Policies

### Configuration
```python
class RetryConfig:
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: tuple = (Exception,)
```

### Predefined Configs
- `DEFAULT_RETRY_CONFIG`: 3 attempts, 1s initial delay, 60s max
- `CRITICAL_RETRY_CONFIG`: 5 attempts, 0.5s initial delay, 60s max
- `QUICK_RETRY_CONFIG`: 2 attempts, 0.5s initial delay, 5s max

### Usage
```python
@with_retry(DEFAULT_RETRY_CONFIG)
async def execute_task():
    # Task logic
    pass
```

## Timeout Handling

### TimeoutHandler
Manages timeouts for agent operations.

```python
handler = TimeoutHandler(default_timeout_seconds=300)

# Execute with timeout
result = await handler.execute_with_timeout(coro, timeout_seconds=60)

# Execute with deadline
result = await handler.execute_with_deadline(coro, deadline=datetime)
```

### Circuit Breaker
Prevents cascading failures by stopping calls to failing services.

```python
breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout_seconds=60,
    expected_exception=Exception
)

result = await breaker.call(func, *args, **kwargs)
```

## Structured Logging

### AgentLogger
Provides structured logging for agent operations.

```python
logger = AgentLogger(agent_id="research", agent_role="research")

logger.log_task_start(task_id, task_type, input_data)
logger.log_task_complete(task_id, task_type, output_data, execution_time)
logger.log_task_error(task_id, task_type, error, error_code)
logger.log_task_retry(task_id, task_type, retry_count, max_retries)
logger.log_message_sent(message_id, receiver, message_type)
logger.log_message_received(message_id, sender, message_type)
logger.log_agent_state(state, details)
logger.log_metric(metric_name, metric_value, labels)
```

### ExecutionLogger
Logs execution plan tracking.

```python
logger = ExecutionLogger(execution_plan_id="uuid")

logger.log_plan_created(user_request, task_count)
logger.log_plan_started()
logger.log_plan_completed(total_time, success_count, failure_count)
logger.log_plan_failed(error)
logger.log_plan_cancelled()
```

## Metrics Collection

### Prometheus Metrics
- `agent_task_executions_total`: Total task executions by agent role and status
- `agent_task_execution_duration_seconds`: Task execution duration histogram
- `agent_active_tasks`: Current active tasks by agent role
- `agent_task_retries_total`: Total task retries by agent role
- `agent_messages_sent_total`: Total messages sent
- `agent_messages_received_total`: Total messages received
- `agent_quality_score`: Quality score gauge
- `agent_hallucinations_total`: Total hallucinations detected

### Usage
```python
from app.agents.metrics import agent_metrics

agent_metrics.task_started(task_id, agent_role, task_type)
agent_metrics.task_completed(task_id, agent_role, task_type, status)
agent_metrics.task_retried(task_id, agent_role, task_type)
agent_metrics.message_sent(sender_role, receiver_role, message_type)
agent_metrics.quality_score_recorded(agent_role, score)
agent_metrics.hallucination_detected(agent_role)

# Get stats
stats = agent_metrics.get_agent_stats("research", time_window_minutes=60)
all_stats = agent_metrics.get_all_stats(time_window_minutes=60)
```

## Frontend Integration

### React Hooks
```typescript
import { useExecuteAgent, useExecutionPlans, useAgentStatus } from './services/agent-hooks'

// Execute request
const executeAgent = useExecuteAgent()
await executeAgent.mutateAsync({ request: "User request" })

// List plans
const { data: plans } = useExecutionPlans()

// Get agent status
const { data: status } = useAgentStatus()
```

### Agent Dashboard
Located at `/agent-dashboard`, provides:
- Real-time agent status monitoring
- Execution request input
- Execution plan history
- Agent capabilities display
- Plan cancellation

### Execution Timeline Component
Visualizes execution flow with:
- Timeline view of task execution
- Status indicators for each task
- Agent role color coding
- Dependency visualization
- Execution time tracking
- Error display

## Configuration

### Environment Variables
```bash
# Multi-Agent System
AGENT_MAX_CONCURRENT_TASKS=10
AGENT_DEFAULT_TIMEOUT_SECONDS=300
AGENT_RETRY_MAX_ATTEMPTS=3
AGENT_RETRY_INITIAL_DELAY_SECONDS=1.0
AGENT_RETRY_MAX_DELAY_SECONDS=60.0

# Event Bus
EVENT_BUS_QUEUE_SIZE=1000
EVENT_BUS_WORKER_COUNT=4

# Metrics
AGENT_METRICS_ENABLED=true
AGENT_METRICS_PORT=9091
```

## Testing

### Unit Tests
Test individual agent modules in isolation.

```python
# tests/test_planner_agent.py
async def test_planner_decompose_request():
    planner = PlannerAgent()
    task = Task(task_type="planning", input_data={"request": "test"})
    response = await planner.execute(task)
    assert response.success
    assert "execution_plan" in response.data
```

### Integration Tests
Test full execution flow with multiple agents.

```python
# tests/test_agent_execution.py
async def test_full_execution_flow():
    # Create execution plan
    planner = PlannerAgent()
    plan = await planner.create_execution_plan("test request", {})
    
    # Execute via orchestrator
    orchestrator = OrchestratorAgent()
    result = await orchestrator.execute_plan(plan)
    
    assert result.success
    assert "synthesized_response" in result
```

## Deployment

### Database Migration
```bash
alembic revision --autogenerate -m "Add agent execution tables"
alembic upgrade head
```

### Service Dependencies
- PostgreSQL (for execution tracking)
- Redis (for event bus queue)
- Prometheus (for metrics)

### Scaling Considerations
- Run orchestrator as a separate service for high load
- Use Redis cluster for event bus scaling
- Implement agent pooling for horizontal scaling
- Consider Kubernetes deployment for auto-scaling

## Backward Compatibility

The multi-agent system maintains backward compatibility with the existing single-agent mode:

- Existing conversation endpoints remain unchanged
- Single-agent mode available via direct LLM calls
- Agent execution is opt-in via new endpoints
- Existing agent models extended, not replaced
- No breaking changes to existing APIs

## Security

### Permission Validation
- Tool Agent validates user permissions before tool execution
- Agent-to-agent communication authenticated
- Execution plans scoped to user context
- Sensitive data sanitized from logs

### Rate Limiting
- Per-user execution rate limits
- Per-agent task rate limits
- Event bus message rate limiting

## Monitoring

### Health Checks
- `/health/live`: Liveness check
- `/health/ready`: Readiness check (includes agent status)
- `/metrics`: Prometheus metrics endpoint

### Alerts
- High agent failure rate
- Long-running tasks
- Event bus queue buildup
- Quality score degradation

## Future Enhancements

### Planned Features
- WebSocket support for real-time execution updates
- Agent marketplace for custom agents
- Distributed execution across multiple servers
- Advanced dependency resolution with DAGs
- Agent learning and adaptation
- Multi-modal agent capabilities (vision, audio)

### Optimization Opportunities
- Agent result caching
- Predictive task scheduling
- Dynamic agent scaling
- Execution plan optimization
- Memory compression algorithms

## Troubleshooting

### Common Issues

**Agent not responding**
- Check event bus status
- Verify agent registration with orchestrator
- Review agent logs for errors
- Check timeout configurations

**Execution plan stuck**
- Verify task dependencies are resolvable
- Check for circular dependencies
- Review agent availability
- Check timeout settings

**High failure rate**
- Review retry policy configuration
- Check LLM provider status
- Verify tool permissions
- Review error logs for patterns

### Debug Mode
Enable debug logging:
```python
import logging
logging.getLogger("app.agents").setLevel(logging.DEBUG)
```

## Performance

### Benchmarks
- Planner Agent: ~2s for complex request decomposition
- Orchestrator Agent: ~0.5s overhead for coordination
- Research Agent: ~5-10s for web search
- Coding Agent: ~3-8s for code generation
- Memory Agent: ~0.5s for context retrieval
- Tool Agent: ~1-5s depending on tool
- Reflection Agent: ~2-3s for quality check

### Optimization Tips
- Use appropriate timeout values
- Enable result caching for repeated queries
- Batch similar tasks when possible
- Monitor and adjust retry policies
- Use quality thresholds to avoid unnecessary retries

## Contributing

### Adding New Agents
1. Extend `BaseAgent` class
2. Implement required methods: `execute`, `initialize`, `shutdown`
3. Register with orchestrator
4. Add database schema if needed
5. Create tests
6. Update documentation

### Adding New Capabilities
1. Update agent's `get_capabilities()` method
2. Implement capability logic in `execute()` method
3. Add metrics for the capability
4. Update API schemas if needed
5. Add UI support if applicable

## License

This multi-agent system is part of Jarvis AI v1.1 and follows the same license terms.

## Contact

For questions or issues related to the multi-agent architecture, please refer to the main project documentation or contact the development team.
