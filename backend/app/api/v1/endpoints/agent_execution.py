"""
API endpoints for multi-agent execution.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Any
from loguru import logger
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.agent_execution import AgentExecutionPlan, AgentExecutionLog, ExecutionStatus
from app.schemas.agent_execution import (
    ExecutionPlanCreate,
    ExecutionPlanResponse,
    ExecutionPlanStatus,
    ExecutionLogResponse,
    ExecutionRequest,
    ExecutionResponse
)
from app.agents import (
    PlannerAgent,
    OrchestratorAgent,
    ResearchAgent,
    CodingAgent,
    MemoryAgent,
    ToolAgent,
    ReflectionAgent,
    event_bus,
    Task,
    AgentRole
)

router = APIRouter()

# Lazy-loaded agent instances
_planner: Optional[PlannerAgent] = None
_orchestrator: Optional[OrchestratorAgent] = None
_research_agent: Optional[ResearchAgent] = None
_coding_agent: Optional[CodingAgent] = None
_memory_agent: Optional[MemoryAgent] = None
_tool_agent: Optional[ToolAgent] = None
_reflection_agent: Optional[ReflectionAgent] = None
_agents_initialized = False


def _initialize_agents() -> None:
    """Initialize agents lazily on first access."""
    global _planner, _orchestrator, _research_agent, _coding_agent
    global _memory_agent, _tool_agent, _reflection_agent, _agents_initialized

    if _agents_initialized:
        return
    _planner = PlannerAgent()
    _orchestrator = OrchestratorAgent()
    _research_agent = ResearchAgent()
    _coding_agent = CodingAgent()
    _memory_agent = MemoryAgent()
    _tool_agent = ToolAgent()
    _reflection_agent = ReflectionAgent()

    # Register agents with orchestrator
    _orchestrator.register_agent(AgentRole.RESEARCH, _research_agent.agent_id)
    _orchestrator.register_agent(AgentRole.CODING, _coding_agent.agent_id)
    _orchestrator.register_agent(AgentRole.MEMORY, _memory_agent.agent_id)
    _orchestrator.register_agent(AgentRole.TOOL, _tool_agent.agent_id)

    _agents_initialized = True


def get_planner() -> PlannerAgent:
    """Get or create planner agent."""
    _initialize_agents()
    assert _planner is not None
    return _planner


def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator agent."""
    _initialize_agents()
    assert _orchestrator is not None
    return _orchestrator


def get_research_agent() -> ResearchAgent:
    """Get or create research agent."""
    _initialize_agents()
    assert _research_agent is not None
    return _research_agent


def get_coding_agent() -> CodingAgent:
    """Get or create coding agent."""
    _initialize_agents()
    assert _coding_agent is not None
    return _coding_agent


def get_memory_agent() -> MemoryAgent:
    """Get or create memory agent."""
    _initialize_agents()
    assert _memory_agent is not None
    return _memory_agent


def get_tool_agent() -> ToolAgent:
    """Get or create tool agent."""
    _initialize_agents()
    assert _tool_agent is not None
    return _tool_agent


def get_reflection_agent() -> ReflectionAgent:
    """Get or create reflection agent."""
    _initialize_agents()
    assert _reflection_agent is not None
    return _reflection_agent


@router.post("/execute", response_model=ExecutionResponse)
async def execute_agent_request(
    request: ExecutionRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ExecutionResponse:
    """Execute a multi-agent request."""
    logger.info(f"Executing agent request for user {current_user_id}: {request.request}")
    
    try:
        # Step 1: Create execution plan
        planner_task = Task(
            task_type="planning",
            description="Create execution plan",
            input_data={
                "request": request.request,
                "context": request.context or {}
            },
            agent_role=AgentRole.PLANNER
        )
        
        planner_response = await get_planner().execute(planner_task)
        
        if not planner_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Planning failed: {planner_response.error}"
            )
        
        if planner_response.data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Planning failed: no data returned"
            )
        
        execution_plan_data = planner_response.data.get("execution_plan")
        if execution_plan_data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Planning failed: no execution plan returned"
            )
        
        # Step 2: Save execution plan to database
        execution_plan = AgentExecutionPlan(
            user_id=current_user_id,
            conversation_id=request.conversation_id,
            user_request=request.request,
            context=request.context,
            plan_data=execution_plan_data,
            task_count=execution_plan_data["task_count"],
            estimated_duration_seconds=execution_plan_data["estimated_duration"],
            status=ExecutionStatus.PENDING,
            started_at=None  # Will be set by Celery task
        )
        
        db.add(execution_plan)
        await db.commit()
        await db.refresh(execution_plan)
        
        # Step 3: Queue Celery task for execution
        from app.worker import get_celery_app
        task = get_celery_app().send_task(
            'app.tasks.agent_tasks.execute_agent_plan',
            args=[str(execution_plan.uuid)],
            queue='agents'
        )
        
        # Step 4: Queue reflection task if enabled
        if request.enable_reflection:
            reflection_task = get_celery_app().send_task(
                'app.tasks.agent_tasks.run_reflection',
                args=[str(execution_plan.uuid)],
                queue='agents'
            )
        
        return ExecutionResponse(
            execution_plan_id=str(execution_plan.uuid),
            status=execution_plan.status.value,
            result=None,  # Will be available after task completes
            summary=None,  # Will be available after task completes
            execution_time_seconds=None,  # Will be available after task completes
            metadata={
                "task_id": task.id,
                "enable_reflection": request.enable_reflection,
                "reflection_task_id": reflection_task.id if request.enable_reflection else None
            } if request.enable_reflection else {"task_id": task.id}
        )
    
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )


@router.get("/plans", response_model=List[ExecutionPlanResponse])
async def list_execution_plans(
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[ExecutionPlanResponse]:
    """List execution plans for current user."""
    result = await db.execute(
        select(AgentExecutionPlan)
        .where(AgentExecutionPlan.user_id == current_user_id)
        .order_by(AgentExecutionPlan.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    plans = result.scalars().all()
    return [
        ExecutionPlanResponse(
            id=int(plan.id),
            uuid=str(plan.uuid),
            user_id=int(plan.user_id),
            conversation_id=int(plan.conversation_id) if plan.conversation_id is not None else None,
            user_request=str(plan.user_request),
            context=plan.context,  # type: ignore[arg-type]
            plan_data=plan.plan_data,  # type: ignore[arg-type]
            task_count=int(plan.task_count),
            estimated_duration_seconds=int(plan.estimated_duration_seconds),
            status=plan.status.value,
            started_at=plan.started_at,  # type: ignore[arg-type]
            completed_at=plan.completed_at,  # type: ignore[arg-type]
            execution_time_seconds=plan.execution_time_seconds,  # type: ignore[arg-type]
            final_output=plan.final_output,  # type: ignore[arg-type]
            result_summary=plan.result_summary,  # type: ignore[arg-type]
            error_message=plan.error_message,  # type: ignore[arg-type]
            metadata_json=plan.metadata_json,  # type: ignore[arg-type]
            created_at=plan.created_at,  # type: ignore[arg-type]
            updated_at=plan.updated_at  # type: ignore[arg-type]
        )
        for plan in plans
    ]


@router.get("/plans/{plan_uuid}", response_model=ExecutionPlanResponse)
async def get_execution_plan(
    plan_uuid: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ExecutionPlanResponse:
    """Get a specific execution plan."""
    result = await db.execute(
        select(AgentExecutionPlan)
        .where(
            and_(
                AgentExecutionPlan.uuid == plan_uuid,
                AgentExecutionPlan.user_id == current_user_id
            )
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution plan not found"
        )
    
    return plan  # type: ignore[no-any-return]


@router.get("/plans/{plan_uuid}/logs", response_model=List[ExecutionLogResponse])
async def get_execution_logs(
    plan_uuid: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[ExecutionLogResponse]:
    """Get execution logs for a plan."""
    # First get the plan
    plan_result = await db.execute(
        select(AgentExecutionPlan)
        .where(
            and_(
                AgentExecutionPlan.uuid == plan_uuid,
                AgentExecutionPlan.user_id == current_user_id
            )
        )
    )
    plan = plan_result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution plan not found"
        )
    
    # Get logs
    result = await db.execute(
        select(AgentExecutionLog)
        .where(AgentExecutionLog.execution_plan_id == plan.id)
        .order_by(AgentExecutionLog.created_at)
    )
    logs = result.scalars().all()
    return [
        ExecutionLogResponse(
            id=int(log.id),
            uuid=str(log.uuid),
            execution_plan_id=int(log.execution_plan_id),
            agent_id=int(log.agent_id) if log.agent_id is not None else None,
            task_id=str(log.task_id),
            task_type=str(log.task_type),
            agent_role=log.agent_role.value,
            input_data=log.input_data,  # type: ignore[arg-type]
            output_data=log.output_data,  # type: ignore[arg-type]
            status=log.status.value,
            started_at=log.started_at,  # type: ignore[arg-type]
            completed_at=log.completed_at,  # type: ignore[arg-type]
            execution_time_seconds=log.execution_time_seconds,  # type: ignore[arg-type]
            retry_count=int(log.retry_count),
            timeout_seconds=int(log.timeout_seconds) if log.timeout_seconds is not None else None,
            error_message=log.error_message,  # type: ignore[arg-type]
            error_code=log.error_code,  # type: ignore[arg-type]
            depends_on=log.depends_on,  # type: ignore[arg-type]
            metadata_json=log.metadata_json,  # type: ignore[arg-type]
            created_at=log.created_at,  # type: ignore[arg-type]
            updated_at=log.updated_at  # type: ignore[arg-type]
        )
        for log in logs
    ]


@router.post("/plans/{plan_uuid}/cancel", response_model=ExecutionPlanStatus)
async def cancel_execution_plan(
    plan_uuid: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ExecutionPlanStatus:
    """Cancel a running execution plan."""
    result = await db.execute(
        select(AgentExecutionPlan)
        .where(
            and_(
                AgentExecutionPlan.uuid == plan_uuid,
                AgentExecutionPlan.user_id == current_user_id
            )
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution plan not found"
        )
    
    if plan.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel plan in status: {plan.status}"
        )
    
    plan.status = ExecutionStatus.CANCELLED  # type: ignore[assignment]
    plan.completed_at = datetime.now(timezone.utc)  # type: ignore[assignment]
    
    await db.commit()
    await db.refresh(plan)
    
    return ExecutionPlanStatus(status=plan.status.value)


@router.get("/agents/status")
async def get_agents_status() -> dict[str, Any]:
    """Get status of all agents."""
    return {
        "planner": get_planner().get_status(),
        "orchestrator": get_orchestrator().get_status(),
        "research": get_research_agent().get_status(),
        "coding": get_coding_agent().get_status(),
        "memory": get_memory_agent().get_status(),
        "tool": get_tool_agent().get_status(),
        "reflection": get_reflection_agent().get_status(),
        "event_bus": event_bus.get_stats()
    }


@router.get("/agents/capabilities")
async def get_agents_capabilities() -> dict[str, Any]:
    """Get capabilities of all agents."""
    return {
        "planner": get_planner().get_capabilities(),
        "orchestrator": get_orchestrator().get_capabilities(),
        "research": get_research_agent().get_capabilities(),
        "coding": get_coding_agent().get_capabilities(),
        "memory": get_memory_agent().get_capabilities(),
        "tool": get_tool_agent().get_capabilities(),
        "reflection": get_reflection_agent().get_capabilities()
    }
