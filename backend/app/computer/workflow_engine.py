"""
Workflow Engine - Multi-step task execution with conditional logic and retry policies.
"""
from typing import Dict, List, Optional, Callable, Any
import asyncio
import time
import uuid
from loguru import logger
from datetime import datetime

from app.computer.base import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    ExecutionResult,
    ExecutionStatus,
    ComputerActionType
)
from app.computer.permission_system import permission_system
from app.computer.file_system_agent import file_system_agent
from app.computer.terminal_agent import terminal_agent
from app.computer.browser_agent import browser_agent
from app.computer.desktop_agent import desktop_agent


class WorkflowEngine:
    """Engine for executing multi-step workflows."""
    
    def __init__(self) -> None:
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.agent_map = {
            ComputerActionType.FILE_READ: file_system_agent,
            ComputerActionType.FILE_WRITE: file_system_agent,
            ComputerActionType.FILE_DELETE: file_system_agent,
            ComputerActionType.FILE_RENAME: file_system_agent,
            ComputerActionType.FILE_MOVE: file_system_agent,
            ComputerActionType.FILE_COPY: file_system_agent,
            ComputerActionType.DIRECTORY_BROWSE: file_system_agent,
            ComputerActionType.DIRECTORY_CREATE: file_system_agent,
            ComputerActionType.DIRECTORY_DELETE: file_system_agent,
            ComputerActionType.FILE_SEARCH: file_system_agent,
            ComputerActionType.FILE_ARCHIVE: file_system_agent,
            ComputerActionType.FILE_EXTRACT: file_system_agent,
            
            ComputerActionType.TERMINAL_EXECUTE: terminal_agent,
            ComputerActionType.TERMINAL_CANCEL: terminal_agent,
            ComputerActionType.TERMINAL_STREAM: terminal_agent,
            
            ComputerActionType.BROWSER_OPEN: browser_agent,
            ComputerActionType.BROWSER_NAVIGATE: browser_agent,
            ComputerActionType.BROWSER_CLICK: browser_agent,
            ComputerActionType.BROWSER_FILL: browser_agent,
            ComputerActionType.BROWSER_EXTRACT: browser_agent,
            ComputerActionType.BROWSER_DOWNLOAD: browser_agent,
            ComputerActionType.BROWSER_UPLOAD: browser_agent,
            ComputerActionType.BROWSER_SCREENSHOT: browser_agent,
            ComputerActionType.BROWSER_CLOSE: browser_agent,
            
            ComputerActionType.DESKTOP_LAUNCH: desktop_agent,
            ComputerActionType.DESKTOP_CLOSE: desktop_agent,
            ComputerActionType.DESKTOP_WINDOW: desktop_agent,
            ComputerActionType.DESKTOP_CLIPBOARD: desktop_agent,
            ComputerActionType.DESKTOP_NOTIFICATION: desktop_agent,
            ComputerActionType.DESKTOP_CAPTURE: desktop_agent,
        }
        
        logger.info("WorkflowEngine initialized")
    
    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition."""
        if workflow.workflow_id in self.workflows:
            raise ValueError(f"Workflow already registered: {workflow.workflow_id}")
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Workflow registered: {workflow.workflow_id}")
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID."""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all registered workflows."""
        return list(self.workflows.values())
    
    async def execute_workflow(
        self,
        workflow_id: str,
        user_id: int = 0,
        parameters: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        # Create execution instance
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.PENDING,
            current_step=None,
            completed_steps=[],
            failed_steps=[],
            started_at=datetime.utcnow(),
            results={}
        )
        
        self.executions[execution_id] = execution
        
        # Check if workflow requires approval
        if workflow.requires_approval:
            # In production, this would trigger a user approval dialog
            # For now, we'll auto-approve
            logger.info(f"Workflow {workflow_id} requires approval - auto-approving for demo")
        
        execution.status = ExecutionStatus.RUNNING
        
        try:
            if workflow.parallel:
                await self._execute_parallel(workflow, execution, user_id, parameters or {})
            else:
                await self._execute_sequential(workflow, execution, user_id, parameters or {})
        
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            logger.error(f"Workflow execution failed: {e}")
        
        finally:
            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
        
        return execution
    
    async def _execute_sequential(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        user_id: int,
        parameters: Dict[str, Any]
    ) -> None:
        """Execute workflow steps sequentially."""
        for step in workflow.steps:
            execution.current_step = step.step_id
            
            # Check dependencies
            if not self._check_dependencies(step, execution.completed_steps):
                execution.failed_steps.append(step.step_id)
                execution.status = ExecutionStatus.FAILED
                raise ValueError(f"Dependencies not met for step {step.step_id}")
            
            # Execute step
            result = await self._execute_step(step, user_id, parameters)
            
            if result.success:
                execution.completed_steps.append(step.step_id)
                execution.results[step.step_id] = result
            else:
                execution.failed_steps.append(step.step_id)
                execution.results[step.step_id] = result
                
                # Try rollback if available
                if step.rollback_action:
                    await self._execute_rollback(step.rollback_action, user_id, parameters)
                
                execution.status = ExecutionStatus.FAILED
                return
    
    async def _execute_parallel(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        user_id: int,
        parameters: Dict[str, Any]
    ) -> None:
        """Execute workflow steps in parallel."""
        # Group steps by dependencies
        execution_groups = self._group_steps_by_dependencies(workflow.steps)
        
        for group in execution_groups:
            # Execute group in parallel
            tasks = [
                self._execute_step(step, user_id, parameters)
                for step in group
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for step, result in zip(group, results):
                if isinstance(result, Exception):
                    execution.failed_steps.append(step.step_id)
                    execution.results[step.step_id] = ExecutionResult(
                        action_id=step.step_id,
                        action_type=step.action_type,
                        status=ExecutionStatus.FAILED,
                        success=False,
                        error=str(result),
                        duration_seconds=0
                    )
                elif hasattr(result, 'success') and result.success:
                    execution.completed_steps.append(step.step_id)
                    execution.results[step.step_id] = result
                elif hasattr(result, 'success'):
                    execution.failed_steps.append(step.step_id)
                    execution.results[step.step_id] = result
            
            # Stop if any step failed
            if execution.failed_steps:
                execution.status = ExecutionStatus.FAILED
                return
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        user_id: int,
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single workflow step with retry policy."""
        max_retries = step.retry_policy.get('max_retries', 0) if step.retry_policy else 0
        retry_delay = step.retry_policy.get('delay', 1) if step.retry_policy else 1
        
        for attempt in range(max_retries + 1):
            try:
                # Get agent for action type
                agent = self.agent_map.get(step.action_type)
                if not agent:
                    return ExecutionResult(
                        action_id=step.step_id,
                        action_type=step.action_type,
                        status=ExecutionStatus.FAILED,
                        success=False,
                        error=f"No agent for action type: {step.action_type}",
                        duration_seconds=0
                    )
                
                # Execute action
                result = await self._execute_agent_action(agent, step, user_id, parameters)
                
                if hasattr(result, 'success') and result.success:
                    return result  # type: ignore[no-any-return]
                elif attempt < max_retries:
                    logger.warning(f"Step {step.step_id} failed, retrying ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                else:
                    return result  # type: ignore[no-any-return]
            
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Step {step.step_id} error, retrying ({attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    return ExecutionResult(
                        action_id=step.step_id,
                        action_type=step.action_type,
                        status=ExecutionStatus.FAILED,
                        success=False,
                        error=str(e),
                        duration_seconds=0
                    )
        
        # This should never be reached, but add a fallback return
        return ExecutionResult(
            action_id=step.step_id,
            action_type=step.action_type,
            status=ExecutionStatus.FAILED,
            success=False,
            error="Unknown error",
            duration_seconds=0
        )
    
    async def _execute_agent_action(
        self,
        agent: Any,
        step: WorkflowStep,
        user_id: int,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute action on appropriate agent."""
        # Map step parameters to agent method
        action_params = {**step.parameters, **parameters}
        
        # Route to appropriate agent method based on action type
        if step.action_type in [ComputerActionType.FILE_READ, ComputerActionType.FILE_WRITE,
                                ComputerActionType.FILE_DELETE, ComputerActionType.FILE_RENAME,
                                ComputerActionType.FILE_MOVE, ComputerActionType.FILE_COPY]:
            if step.action_type == ComputerActionType.FILE_READ:
                return await agent.read_file(action_params.get('path'), user_id)
            elif step.action_type == ComputerActionType.FILE_WRITE:
                return await agent.write_file(action_params.get('path'), action_params.get('content'), 
                                              action_params.get('overwrite', False), user_id)
            elif step.action_type == ComputerActionType.FILE_DELETE:
                return await agent.delete_file(action_params.get('path'), user_id)
            elif step.action_type == ComputerActionType.FILE_RENAME:
                return await agent.rename_file(action_params.get('source'), action_params.get('target'), user_id)
            elif step.action_type == ComputerActionType.FILE_MOVE:
                return await agent.move_file(action_params.get('source'), action_params.get('target'), user_id)
            elif step.action_type == ComputerActionType.FILE_COPY:
                return await agent.copy_file(action_params.get('source'), action_params.get('target'), user_id)
        
        elif step.action_type == ComputerActionType.TERMINAL_EXECUTE:
            return await agent.execute_command(
                action_params.get('command'),
                action_params.get('working_directory'),
                action_params.get('environment'),
                action_params.get('timeout'),
                action_params.get('stream_output', False),
                user_id
            )
        
        elif step.action_type in [ComputerActionType.BROWSER_OPEN, ComputerActionType.BROWSER_NAVIGATE,
                                  ComputerActionType.BROWSER_CLICK, ComputerActionType.BROWSER_FILL]:
            if step.action_type == ComputerActionType.BROWSER_OPEN:
                return await agent.open_browser(action_params.get('url'), user_id)
            elif step.action_type == ComputerActionType.BROWSER_NAVIGATE:
                return await agent.navigate(action_params.get('page_id'), action_params.get('url'), user_id)
            elif step.action_type == ComputerActionType.BROWSER_CLICK:
                return await agent.click_element(action_params.get('page_id'), action_params.get('selector'), user_id)
            elif step.action_type == ComputerActionType.BROWSER_FILL:
                return await agent.fill_form(action_params.get('page_id'), action_params.get('selector'), 
                                            action_params.get('value'), user_id)
        
        elif step.action_type == ComputerActionType.DESKTOP_LAUNCH:
            return await agent.launch_application(action_params.get('application'), user_id)
        
        # Default error
        return ExecutionResult(
            action_id=step.step_id,
            action_type=step.action_type,
            status=ExecutionStatus.FAILED,
            success=False,
            error=f"Action type not implemented: {step.action_type}",
            duration_seconds=0
        )
    
    async def _execute_rollback(
        self,
        rollback_action: Dict[str, Any],
        user_id: int,
        parameters: Dict[str, Any]
    ) -> None:
        """Execute rollback action."""
        try:
            # Create a temporary step for rollback
            rollback_step = WorkflowStep(
                step_id="rollback",
                action_type=ComputerActionType(rollback_action.get('action_type')),
                parameters=rollback_action.get('parameters', {}),
                depends_on=[],
                retry_policy=None,
                rollback_action=None
            )
            
            await self._execute_step(rollback_step, user_id, parameters)
            logger.info("Rollback executed successfully")
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
    
    def _check_dependencies(self, step: WorkflowStep, completed_steps: List[str]) -> bool:
        """Check if step dependencies are met."""
        for dep in step.depends_on:
            if dep not in completed_steps:
                return False
        return True
    
    def _group_steps_by_dependencies(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Group steps by dependencies for parallel execution."""
        groups: List[List[WorkflowStep]] = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Find steps with no unmet dependencies
            ready_steps = [
                step for step in remaining_steps
                if all(dep in [s for group in groups for s in group] for dep in step.depends_on)
            ]
            
            if not ready_steps:
                # Circular dependency or missing dependency
                groups.append(remaining_steps)
                break
            
            groups.append(ready_steps)
            remaining_steps = [s for s in remaining_steps if s not in ready_steps]
        
        return groups
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        return self.executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        if execution_id not in self.executions:
            return False
        
        execution = self.executions[execution_id]
        if execution.status != ExecutionStatus.RUNNING:
            return False
        
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        
        logger.info(f"Execution {execution_id} cancelled")
        return True
    
    def get_execution_history(self, limit: int = 50) -> List[WorkflowExecution]:
        """Get workflow execution history."""
        executions = list(self.executions.values())
        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]


# Global workflow engine instance
workflow_engine = WorkflowEngine()
