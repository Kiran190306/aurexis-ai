"""
Agent Execution Tasks
Celery tasks for asynchronous agent execution, planning, and reflection
"""
from celery import Task
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.worker import celery_app
from app.core.database import AsyncSessionLocal
from app.models.agent_execution import AgentExecutionPlan, ExecutionStatus


class DatabaseTask(Task):
    """Base task with database session management"""
    _db: Optional[AsyncSession] = None

    @property
    def db(self) -> AsyncSession:
        if self._db is None:
            self._db = AsyncSessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            import asyncio
            asyncio.run(self._db.close())
        super().after_return(*args, **kwargs)


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.agent_tasks.execute_agent_plan')
def execute_agent_plan(self, plan_uuid: str) -> dict:
    """
    Execute an agent execution plan asynchronously
    
    Args:
        plan_uuid: Execution plan UUID to execute
        
    Returns:
        Execution result
    """
    import asyncio
    from app.agents import (
        OrchestratorAgent,
        PlannerAgent,
        ResearchAgent,
        CodingAgent,
        MemoryAgent,
        ToolAgent,
        ReflectionAgent,
        Task,
        AgentRole
    )
    
    async def _execute():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentExecutionPlan).where(AgentExecutionPlan.uuid == plan_uuid)
            )
            plan = result.scalar_one_or_none()
            
            if not plan:
                logger.error(f"Execution plan {plan_uuid} not found")
                return {"status": "error", "message": "Execution plan not found"}
            
            # Check if already completed
            if plan.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                logger.info(f"Execution plan {plan_uuid} already in terminal state: {plan.status}")
                return {"status": "success", "plan_uuid": plan_uuid, "already_completed": True}
            
            # Update status to running
            plan.status = ExecutionStatus.RUNNING
            plan.started_at = datetime.now(timezone.utc)
            await db.commit()
            
            try:
                # Initialize agents
                orchestrator = OrchestratorAgent()
                research_agent = ResearchAgent()
                coding_agent = CodingAgent()
                memory_agent = MemoryAgent()
                tool_agent = ToolAgent()
                reflection_agent = ReflectionAgent()
                
                # Register agents with orchestrator
                orchestrator.register_agent(AgentRole.RESEARCH, research_agent.agent_id)
                orchestrator.register_agent(AgentRole.CODING, coding_agent.agent_id)
                orchestrator.register_agent(AgentRole.MEMORY, memory_agent.agent_id)
                orchestrator.register_agent(AgentRole.TOOL, tool_agent.agent_id)
                
                # Execute plan via orchestrator
                orchestrator_task = Task(
                    task_type="orchestration",
                    description="Execute execution plan",
                    input_data={
                        "execution_plan": plan.plan_data
                    },
                    agent_role=AgentRole.ORCHESTRATOR
                )
                
                orchestrator_response = await orchestrator.execute(orchestrator_task)
                
                # Update execution plan with results
                if orchestrator_response.success:
                    plan.status = ExecutionStatus.COMPLETED
                    plan.final_output = orchestrator_response.data
                    plan.result_summary = orchestrator_response.data.get("synthesized_response") if orchestrator_response.data else None
                    plan.completed_at = datetime.now(timezone.utc)
                    plan.execution_time_seconds = (
                        plan.completed_at - plan.started_at
                    ).total_seconds()
                else:
                    plan.status = ExecutionStatus.FAILED
                    plan.error_message = orchestrator_response.error
                    plan.completed_at = datetime.now(timezone.utc)
                
                await db.commit()
                
                logger.info(f"Agent execution plan {plan_uuid} completed with status: {plan.status}")
                return {
                    "status": "success",
                    "plan_uuid": plan_uuid,
                    "execution_status": plan.status.value,
                    "execution_time_seconds": plan.execution_time_seconds
                }
            except Exception as e:
                logger.error(f"Failed to execute agent plan {plan_uuid}: {e}", exc_info=True)
                plan.status = ExecutionStatus.FAILED
                plan.error_message = str(e)
                plan.completed_at = datetime.utcnow()
                await db.commit()
                return {"status": "error", "message": str(e), "plan_uuid": plan_uuid}
    
    return asyncio.run(_execute())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.agent_tasks.run_reflection')
def run_reflection(self, plan_uuid: str) -> dict:
    """
    Run reflection agent on execution result
    
    Args:
        plan_uuid: Execution plan UUID to reflect on
        
    Returns:
        Reflection result
    """
    import asyncio
    
    async def _reflect():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentExecutionPlan).where(AgentExecutionPlan.uuid == plan_uuid)
            )
            plan = result.scalar_one_or_none()
            
            if not plan:
                logger.error(f"Execution plan {plan_uuid} not found")
                return {"status": "error", "message": "Execution plan not found"}
            
            # Run reflection agent on execution result
            from app.agents import ReflectionAgent, Task, AgentRole
            
            reflection_agent = ReflectionAgent()
            
            reflection_task = Task(
                task_type="reflection",
                description="Reflect on execution result",
                input_data={
                    "execution_plan": plan.plan_data,
                    "final_output": plan.final_output
                },
                agent_role=AgentRole.REFLECTION
            )
            
            reflection_response = await reflection_agent.execute(reflection_task)
            
            if reflection_response.success:
                # Store reflection results
                plan.metadata_json = plan.metadata_json or {}
                plan.metadata_json["reflection"] = reflection_response.data
                await db.commit()
            
            logger.info(f"Reflection completed for plan {plan_uuid}")
            return {"status": "success", "plan_uuid": plan_uuid, "reflection_data": reflection_response.data if reflection_response.success else None}
    
    return asyncio.run(_reflect())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.agent_tasks.cleanup_old_executions')
def cleanup_old_executions(self) -> dict:
    """
    Cleanup old execution plans (scheduled task)
    
    Returns:
        Cleanup result
    """
    import asyncio
    
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            # Delete execution plans older than 30 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            result = await db.execute(
                select(AgentExecutionPlan).where(
                    AgentExecutionPlan.created_at < cutoff_date,
                    AgentExecutionPlan.status.in_([ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED])
                )
            )
            plans = result.scalars().all()
            
            count = len(plans)
            
            logger.info(f"Cleaned up {count} old execution plans")
            return {"status": "success", "cleaned_count": count}
    
    return asyncio.run(_cleanup())
