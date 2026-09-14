"""
Orchestrator Agent - Manages task execution and agent coordination.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from app.ai.engine import ai_engine
from app.ai.base import Message
from .base import BaseAgent, AgentRole, Task, TaskStatus, ExecutionPlan, AgentResponse, AgentMessage
from .event_bus import event_bus


class OrchestratorAgent(BaseAgent):
    """Agent responsible for orchestrating task execution across specialized agents."""
    
    def __init__(self, agent_id: str = "orchestrator", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.ORCHESTRATOR
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        self.agent_registry: Dict[AgentRole, str] = {}
        self.system_prompt = """You are an Orchestrator Agent for Jarvis AI. Your role is to:
1. Receive execution plans from the Planner
2. Assign tasks to appropriate specialized agents
3. Monitor task progress and handle failures
4. Aggregate results from multiple agents
5. Coordinate dependencies between tasks
6. Retry failed tasks when appropriate"""
    
    async def initialize(self) -> None:
        """Initialize the orchestrator agent."""
        logger.info(f"Initializing Orchestrator Agent: {self.agent_id}")
        
        # Register message handlers
        await event_bus.subscribe(
            self.agent_id,
            "task_completed",
            self._handle_task_completed
        )
        await event_bus.subscribe(
            self.agent_id,
            "task_failed",
            self._handle_task_failed
        )
        await event_bus.subscribe(
            self.agent_id,
            "task_progress",
            self._handle_task_progress
        )
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator agent."""
        logger.info(f"Shutting down Orchestrator Agent: {self.agent_id}")
        
        # Unsubscribe from event bus
        await event_bus.unsubscribe(self.agent_id)
    
    def register_agent(self, role: AgentRole, agent_id: str) -> None:
        """Register a specialized agent."""
        self.agent_registry[role] = agent_id
        logger.info(f"Registered agent {agent_id} for role {role}")
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute an orchestration task."""
        logger.info(f"Orchestrator Agent executing task: {task.id}")
        
        try:
            execution_plan_data = task.input_data.get("execution_plan")
            if not execution_plan_data:
                return AgentResponse(
                    success=False,
                    error="No execution plan provided"
                )
            
            execution_plan = ExecutionPlan(**execution_plan_data)
            results = await self._execute_plan(execution_plan)
            
            return AgentResponse(
                success=True,
                data={
                    "results": results,
                    "total_tasks": len(execution_plan.tasks),
                    "completed_tasks": len(self.completed_tasks),
                    "failed_tasks": len(self.failed_tasks)
                }
            )
        
        except Exception as e:
            logger.error(f"Orchestrator Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _execute_plan(self, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute an execution plan by coordinating agents."""
        logger.info(f"Executing plan with {len(execution_plan.tasks)} tasks")
        
        # Build dependency graph
        task_graph = self._build_dependency_graph(execution_plan.tasks)
        
        # Execute tasks in dependency order
        results: Dict[str, Any] = {}
        for task in execution_plan.tasks:
            # Check if dependencies are satisfied
            if not self._are_dependencies_satisfied(task, results):
                logger.warning(f"Task {task.id} dependencies not satisfied, skipping")
                continue
            
            # Assign to appropriate agent
            agent_id = self.agent_registry.get(task.agent_role)
            if not agent_id:
                logger.error(f"No agent registered for role {task.agent_role}")
                self.failed_tasks[task.id] = task
                continue
            
            # Execute task
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            self.active_tasks[task.id] = task
            
            try:
                message = AgentMessage(
                    sender=self.agent_id,
                    receiver=agent_id,
                    message_type="execute_task",
                    content={"task": task.dict()}
                )
                
                response = await event_bus.publish_and_wait(message, timeout=task.timeout_seconds)
                
                if response.content.get("success"):
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    task.output_data = response.content.get("data")
                    self.completed_tasks[task.id] = task
                    results[task.id] = task.output_data
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = response.content.get("error")
                    self.failed_tasks[task.id] = task
                    
                    # Retry if possible
                    if task.retry_count < task.max_retries:
                        await self._retry_task(task)
            
            except Exception as e:
                logger.error(f"Task {task.id} execution failed: {e}", exc_info=True)
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                self.failed_tasks[task.id] = task
            
            finally:
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]
        
        # Aggregate final results
        aggregated_results = await self._aggregate_results(execution_plan, results)
        
        return aggregated_results
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """Build a dependency graph from tasks."""
        graph = {}
        for task in tasks:
            graph[task.id] = task.dependencies
        return graph
    
    def _are_dependencies_satisfied(self, task: Task, completed_results: Dict[str, Any]) -> bool:
        """Check if all task dependencies are satisfied."""
        for dep_id in task.dependencies:
            if dep_id not in completed_results:
                return False
        return True
    
    async def _retry_task(self, task: Task) -> None:
        """Retry a failed task."""
        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        logger.info(f"Retrying task {task.id} (attempt {task.retry_count}/{task.max_retries})")
        
        # Re-queue the task for execution
        # In a real implementation, this would use a proper queue
        await self._execute_single_task(task)
    
    async def _execute_single_task(self, task: Task) -> AgentResponse:
        """Execute a single task."""
        agent_id = self.agent_registry.get(task.agent_role)
        if not agent_id:
            return AgentResponse(success=False, error=f"No agent for role {task.agent_role}")
        
        message = AgentMessage(
            sender=self.agent_id,
            receiver=agent_id,
            message_type="execute_task",
            content={"task": task.dict()}
        )
        
        response = await event_bus.publish_and_wait(message, timeout=task.timeout_seconds)
        
        if response.content.get("success"):
            return AgentResponse(
                success=True,
                data=response.content.get("data")
            )
        else:
            return AgentResponse(
                success=False,
                error=response.content.get("error")
            )
    
    async def _aggregate_results(self, execution_plan: ExecutionPlan, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all tasks."""
        logger.info("Aggregating results from completed tasks")
        
        # Use AI to synthesize final response
        messages = [
            Message(
                role="system",
                content="You are an Orchestrator Agent responsible for synthesizing results from multiple specialized agents. Combine the results into a coherent final response."
            ),
            Message(
                role="user",
                content=f"""Original Request: {execution_plan.user_request}

Task Results:
{self._format_results(results)}

Please synthesize these results into a comprehensive response addressing the original request."""
            )
        ]
        
        try:
            response = await ai_engine.generate(
                messages=messages,
                temperature=0.5,
                max_tokens=2000
            )

            # Safely access response content - handle both dict and object
            if hasattr(response, 'content'):
                response_content = response.content
            elif isinstance(response, dict):
                response_content = response.get('content', '')
            else:
                response_content = str(response)

            return {
                "synthesized_response": response_content,
                "task_results": results,
                "metadata": {
                    "total_tasks": len(execution_plan.tasks),
                    "completed_tasks": len(self.completed_tasks),
                    "failed_tasks": len(self.failed_tasks)
                }
            }
        except Exception as e:
            logger.error(f"Failed to synthesize results with AI: {e}", exc_info=True)
            # Return unsynthesized results if AI synthesis fails
            return {
                "synthesized_response": "AI synthesis failed. Here are the raw task results:",
                "task_results": results,
                "metadata": {
                    "total_tasks": len(execution_plan.tasks),
                    "completed_tasks": len(self.completed_tasks),
                    "failed_tasks": len(self.failed_tasks),
                    "synthesis_error": str(e)
                }
            }
    
    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format results for AI synthesis."""
        formatted = []
        for task_id, result in results.items():
            formatted.append(f"Task {task_id}: {result}")
        return "\n".join(formatted)
    
    async def _handle_task_completed(self, message: AgentMessage) -> None:
        """Handle task completion message."""
        task_id = message.content.get("task_id")
        logger.info(f"Task {task_id} completed")
    
    async def _handle_task_failed(self, message: AgentMessage) -> None:
        """Handle task failure message."""
        task_id = message.content.get("task_id")
        error = message.content.get("error")
        logger.error(f"Task {task_id} failed: {error}")
    
    async def _handle_task_progress(self, message: AgentMessage) -> None:
        """Handle task progress message."""
        task_id = message.content.get("task_id")
        progress = message.content.get("progress")
        logger.info(f"Task {task_id} progress: {progress}%")
    
    def get_capabilities(self) -> List[str]:
        """Return orchestrator agent capabilities."""
        return [
            "task_assignment",
            "progress_monitoring",
            "failure_handling",
            "result_aggregation",
            "dependency_management"
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Return current orchestrator status."""
        return {
            **super().get_status(),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "registered_agents": len(self.agent_registry)
        }
