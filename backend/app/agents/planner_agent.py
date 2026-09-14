"""
Planner Agent - Breaks complex user requests into executable tasks.
Integrates with Knowledge Agent for RAG-enhanced planning.
"""
from typing import Dict, List, Any, Optional
from loguru import logger
from app.ai.engine import ai_engine
from app.ai.base import Message
from .base import BaseAgent, AgentRole, Task, TaskStatus, TaskPriority, ExecutionPlan, AgentResponse
from app.knowledge.agent import KnowledgeAgent, RAGQuery, RAGResult


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and task decomposition."""
    
    def __init__(self, agent_id: str = "planner", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.PLANNER
        self.knowledge_agent = KnowledgeAgent()
        self.system_prompt = """You are a Planner Agent for Jarvis AI. Your role is to:
1. Analyze user requests and understand the intent
2. Break down complex requests into executable tasks
3. Identify dependencies between tasks
4. Prioritize tasks based on importance and dependencies
5. Estimate task duration and complexity
6. Use knowledge base to inform planning when relevant

You should output a structured execution plan in JSON format with:
- tasks: list of tasks with type, description, priority, dependencies
- estimated_duration: total estimated time in seconds
- metadata: additional context and requirements"""
    
    async def initialize(self) -> None:
        """Initialize the planner agent."""
        logger.info(f"Initializing Planner Agent: {self.agent_id}")
    
    async def shutdown(self) -> None:
        """Shutdown the planner agent."""
        logger.info(f"Shutting down Planner Agent: {self.agent_id}")
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute a planning task."""
        logger.info(f"Planner Agent executing task: {task.id}")
        
        try:
            user_request = task.input_data.get("request", "")
            context = task.input_data.get("context", {})
            user_id = task.input_data.get("user_id")
            
            if not user_request:
                return AgentResponse(
                    success=False,
                    error="No user request provided"
                )
            
            # Use RAG to enhance planning if user_id is provided
            rag_context = ""
            if user_id:
                try:
                    rag_query = RAGQuery(
                        query=user_request,
                        user_id=user_id,
                        top_k=5,
                        use_hybrid=True,
                        max_tokens=1000
                    )
                    rag_result = await self.knowledge_agent.query(rag_query)
                    if rag_result.context.context_text:
                        rag_context = f"\n\nRelevant Knowledge Base Context:\n{rag_result.context.context_text}"
                        logger.info(f"RAG-enhanced planning with {len(rag_result.sources)} sources")
                except Exception as e:
                    logger.warning(f"RAG query failed, proceeding without knowledge context: {e}")
            
            execution_plan = await self._create_execution_plan(user_request, context, rag_context)
            
            return AgentResponse(
                success=True,
                data={
                    "execution_plan": execution_plan.dict(),
                    "task_count": len(execution_plan.tasks)
                },
                metadata={
                    "estimated_duration": execution_plan.estimated_duration_seconds,
                    "rag_enhanced": bool(rag_context)
                }
            )
        
        except Exception as e:
            logger.error(f"Planner Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _create_execution_plan(self, user_request: str, context: Dict[str, Any], rag_context: str = "") -> ExecutionPlan:
        """Create an execution plan from a user request."""
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""User Request: {user_request}

Context: {context}{rag_context}

Please analyze this request and create a detailed execution plan. Output valid JSON with the following structure:
{{
    "tasks": [
        {{
            "task_type": "research|coding|memory|tool|knowledge",
            "description": "Clear description of what needs to be done",
            "priority": "critical|high|medium|low",
            "dependencies": ["task_id_1", "task_id_2"],
            "agent_role": "research|coding|memory|tool|knowledge",
            "input_data": {{}},
            "estimated_duration": 60
        }}
    ],
    "estimated_duration": 300,
    "metadata": {{
        "complexity": "low|medium|high",
        "requires_tools": ["tool1", "tool2"],
        "notes": "Additional context"
    }}
}}"""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        import json
        try:
            # Safely access response content
            if hasattr(response, 'content'):
                response_content = response.content
            elif isinstance(response, dict):
                response_content = response.get('content', '')
            else:
                response_content = str(response)

            plan_data = json.loads(response_content)
        except (json.JSONDecodeError, ValueError):
            # Fallback to empty plan if JSON parsing fails
            plan_data = {"tasks": [], "estimated_duration": 300, "metadata": {}}
        
        # Convert to ExecutionPlan
        tasks = []
        for i, task_data in enumerate(plan_data.get("tasks", [])):
            task = Task(
                task_type=task_data.get("task_type", "general"),
                description=task_data.get("description", ""),
                priority=TaskPriority(task_data.get("priority", "medium")),
                agent_role=AgentRole(task_data.get("agent_role", "tool")),
                dependencies=task_data.get("dependencies", []),
                input_data=task_data.get("input_data", {}),
                timeout_seconds=task_data.get("estimated_duration", 300),
                metadata={
                    "estimated_duration": task_data.get("estimated_duration", 60)
                }
            )
            tasks.append(task)
        
        execution_plan = ExecutionPlan(
            user_request=user_request,
            tasks=tasks,
            estimated_duration_seconds=plan_data.get("estimated_duration", 300),
            metadata=plan_data.get("metadata", {})
        )
        
        logger.info(f"Created execution plan with {len(tasks)} tasks")
        return execution_plan
    
    def get_capabilities(self) -> List[str]:
        """Return planner agent capabilities."""
        return [
            "task_decomposition",
            "dependency_analysis",
            "priority_estimation",
            "duration_estimation",
            "execution_planning"
        ]
