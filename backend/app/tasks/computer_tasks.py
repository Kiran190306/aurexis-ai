"""
Computer Automation Tasks
Celery tasks for asynchronous computer automation, workflow execution, and long-running operations
"""
from celery import Task
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.worker import get_celery_app
from app.core.database import AsyncSessionLocal
from app.models.computer import WorkflowExecution, WorkflowDefinition, ExecutionStatus


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


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.computer_tasks.execute_workflow')
def execute_workflow(self, execution_id: int) -> dict:
    """
    Execute a computer automation workflow asynchronously
    
    Args:
        execution_id: Workflow execution ID to execute
        
    Returns:
        Execution result
    """
    import asyncio
    from app.computer.workflow_engine import workflow_engine
    from app.computer.base import WorkflowDefinition as WorkflowDef
    
    async def _execute():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            
            if not execution:
                logger.error(f"Workflow execution {execution_id} not found")
                return {"status": "error", "message": "Workflow execution not found"}
            
            # Check if already completed
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                logger.info(f"Workflow execution {execution_id} already in terminal state: {execution.status}")
                return {"status": "success", "execution_id": execution_id, "already_completed": True}
            
            # Update status to running
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = func.now()
            await db.commit()
            
            try:
                # Get workflow definition
                workflow_def_result = await db.execute(
                    select(WorkflowDefinition).where(WorkflowDefinition.id == execution.workflow_id)
                )
                workflow_def_db = workflow_def_result.scalar_one_or_none()
                
                if not workflow_def_db:
                    raise ValueError(f"Workflow definition not found for execution {execution_id}")
                
                # Create workflow definition object
                from app.computer.base import WorkflowStep
                workflow_def = WorkflowDef(
                    workflow_id=workflow_def_db.workflow_id,
                    name=workflow_def_db.name,
                    description=workflow_def_db.description,
                    steps=[WorkflowStep(**step) for step in workflow_def_db.steps_json] if workflow_def_db.steps_json else [],
                    parallel=workflow_def_db.parallel,
                    requires_approval=workflow_def_db.requires_approval,
                    timeout=workflow_def_db.timeout
                )
                
                # Execute workflow via workflow engine
                execution_result = await workflow_engine.execute_workflow(
                    workflow_def,
                    execution.parameters or {},
                    execution_id
                )
                
                # Update execution status
                if execution_result.get("success"):
                    execution.status = ExecutionStatus.COMPLETED
                    execution.result_json = execution_result
                else:
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = execution_result.get("error", "Unknown error")
                
                execution.completed_at = func.now()
                execution.execution_time_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds() if execution.started_at else None
                await db.commit()
                
                logger.info(f"Workflow execution {execution_id} completed with status: {execution.status}")
                return {
                    "status": "success",
                    "execution_id": execution_id,
                    "execution_status": execution.status.value,
                    "execution_time_seconds": execution.execution_time_seconds
                }
            except Exception as e:
                logger.error(f"Failed to execute workflow {execution_id}: {e}", exc_info=True)
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = func.now()
                await db.commit()
                return {"status": "error", "message": str(e), "execution_id": execution_id}
    
    return asyncio.run(_execute())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.computer_tasks.execute_long_running_action')
def execute_long_running_action(self, action_type: str, parameters: dict) -> dict:
    """
    Execute a long-running computer action asynchronously
    
    Args:
        action_type: Type of action to execute
        parameters: Action parameters
        
    Returns:
        Execution result
    """
    import asyncio
    
    async def _execute():
        # Execute long-running computer action based on type
        from app.computer.file_system_agent import file_system_agent
        from app.computer.terminal_agent import terminal_agent
        from app.computer.browser_agent import browser_agent
        from app.computer.desktop_agent import desktop_agent
        
        result = None
        
        if action_type == "file_operation":
            # Execute file system operation
            path = parameters.get("path")
            operation = parameters.get("operation")
            if operation == "browse":
                result = await file_system_agent.browse_directory(path, 1, 1)
            elif operation == "read":
                result = await file_system_agent.read_file(path, 1)
        elif action_type == "terminal_command":
            # Execute terminal command
            command = parameters.get("command")
            result = await terminal_agent.execute_command(command, 1, 300)
        elif action_type == "browser_action":
            # Execute browser action
            url = parameters.get("url")
            action = parameters.get("action")
            if action == "navigate":
                result = await browser_agent.navigate(url, 1)
        elif action_type == "desktop_action":
            # Execute desktop action
            app_name = parameters.get("app_name")
            action = parameters.get("action")
            if action == "launch":
                result = await desktop_agent.launch_application(app_name, 1)
        
        logger.info(f"Long-running action {action_type} completed")
        return {"status": "success", "action_type": action_type, "result": result}
    
    return asyncio.run(_execute())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.computer_tasks.cleanup_old_workflows')
def cleanup_old_workflows(self) -> dict:
    """
    Cleanup old workflow executions (scheduled task)
    
    Returns:
        Cleanup result
    """
    import asyncio
    from datetime import datetime, timedelta, timezone
    
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            # Delete workflow executions older than 7 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            
            result = await db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.created_at < cutoff_date,
                    WorkflowExecution.status.in_([ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED])
                )
            )
            executions = result.scalars().all()
            
            count = len(executions)
            
            logger.info(f"Cleaned up {count} old workflow executions")
            return {"status": "success", "cleaned_count": count}
    
    return asyncio.run(_cleanup())
