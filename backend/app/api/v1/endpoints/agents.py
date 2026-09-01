from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.agent import Agent, AgentStatus
from pydantic import BaseModel

router = APIRouter()


class AgentCreate(BaseModel):
    name: str
    description: str
    agent_type: str = "general"
    capabilities: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    system_prompt: str
    model: str = "gpt-4-turbo-preview"
    temperature: int = 70
    max_tokens: int = 4096
    tool_ids: Optional[List[int]] = None
    plugin_ids: Optional[List[int]] = None
    personality: Optional[dict] = None
    behavior_rules: Optional[dict] = None
    constraints: Optional[dict] = None
    memory_enabled: bool = True
    memory_type: str = "episodic"
    parent_agent_id: Optional[int] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    capabilities: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[int] = None
    max_tokens: Optional[int] = None
    tool_ids: Optional[List[int]] = None
    plugin_ids: Optional[List[int]] = None
    personality: Optional[dict] = None
    behavior_rules: Optional[dict] = None
    constraints: Optional[dict] = None
    memory_enabled: Optional[bool] = None
    memory_type: Optional[str] = None


@router.get("/", response_model=None)
async def list_agents(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[Agent]:
    """List all agents for the current user."""
    result = await db.execute(
        select(Agent)
        .where(Agent.user_id == current_user_id)
        .where(Agent.deleted_at.is_(None))
        .order_by(Agent.created_at.desc())
    )
    agents = result.scalars().all()
    return list(agents)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_agent(
    agent_data: AgentCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """Create a new agent."""
    agent = Agent(
        user_id=current_user_id,
        name=agent_data.name,
        description=agent_data.description,
        agent_type=agent_data.agent_type,
        capabilities=agent_data.capabilities,
        specializations=agent_data.specializations,
        system_prompt=agent_data.system_prompt,
        model=agent_data.model,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,
        tool_ids=agent_data.tool_ids,
        plugin_ids=agent_data.plugin_ids,
        personality=agent_data.personality,
        behavior_rules=agent_data.behavior_rules,
        constraints=agent_data.constraints,
        memory_enabled=agent_data.memory_enabled,
        memory_type=agent_data.memory_type,
        parent_agent_id=agent_data.parent_agent_id,
        status=AgentStatus.ACTIVE,
    )
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    logger.info(f"Agent created: {agent.name}")
    
    return agent


@router.get("/{agent_id}", response_model=None)
async def get_agent(
    agent_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """Get a specific agent."""
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id)
        .where(Agent.user_id == current_user_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    return agent  # type: ignore[no-any-return]


@router.patch("/{agent_id}", response_model=None)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """Update an agent."""
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id)
        .where(Agent.user_id == current_user_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Update fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    await db.commit()
    await db.refresh(agent)
    
    logger.info(f"Agent updated: {agent_id}")
    
    return agent  # type: ignore[no-any-return]


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete an agent."""
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id)
        .where(Agent.user_id == current_user_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    agent.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Agent deleted: {agent_id}")
    
    return {"message": "Agent deleted successfully"}
