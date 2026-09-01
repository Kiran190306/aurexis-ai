from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.tool import Tool, ToolStatus
from pydantic import BaseModel

router = APIRouter()


class ToolCreate(BaseModel):
    name: str
    display_name: str
    description: str
    tool_type: str = "custom"
    config_schema: Optional[dict] = None
    config: Optional[dict] = None
    parameters: Optional[dict] = None
    execution_type: str = "http"
    endpoint: Optional[str] = None
    method: str = "POST"
    headers: Optional[dict] = None
    authentication: Optional[dict] = None
    code: Optional[str] = None
    language: Optional[str] = None
    plugin_id: Optional[int] = None
    required_permissions: Optional[List[str]] = None
    sandbox_enabled: bool = True


class ToolUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    config_schema: Optional[dict] = None
    config: Optional[dict] = None
    parameters: Optional[dict] = None
    execution_type: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[dict] = None
    authentication: Optional[dict] = None
    code: Optional[str] = None
    language: Optional[str] = None
    required_permissions: Optional[List[str]] = None
    sandbox_enabled: Optional[bool] = None


@router.get("/", response_model=None)
async def list_tools(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[Tool]:
    """List all tools for the current user."""
    result = await db.execute(
        select(Tool)
        .where(Tool.user_id == current_user_id)
        .where(Tool.deleted_at.is_(None))
        .order_by(Tool.created_at.desc())
    )
    tools = result.scalars().all()
    return list(tools)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_tool(
    tool_data: ToolCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Tool:
    """Create a new tool."""
    tool = Tool(
        user_id=current_user_id,
        name=tool_data.name,
        display_name=tool_data.display_name,
        description=tool_data.description,
        tool_type=tool_data.tool_type,
        config_schema=tool_data.config_schema,
        config=tool_data.config,
        parameters=tool_data.parameters,
        execution_type=tool_data.execution_type,
        endpoint=tool_data.endpoint,
        method=tool_data.method,
        headers=tool_data.headers,
        authentication=tool_data.authentication,
        code=tool_data.code,
        language=tool_data.language,
        plugin_id=tool_data.plugin_id,
        required_permissions=tool_data.required_permissions,
        sandbox_enabled=tool_data.sandbox_enabled,
        status=ToolStatus.ACTIVE,
    )
    
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    
    logger.info(f"Tool created: {tool.name}")
    
    return tool


@router.get("/{tool_id}", response_model=None)
async def get_tool(
    tool_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Tool:
    """Get a specific tool."""
    result = await db.execute(
        select(Tool)
        .where(Tool.id == tool_id)
        .where(Tool.user_id == current_user_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    
    return tool  # type: ignore[no-any-return]


@router.patch("/{tool_id}", response_model=None)
async def update_tool(
    tool_id: int,
    tool_data: ToolUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Tool:
    """Update a tool."""
    result = await db.execute(
        select(Tool)
        .where(Tool.id == tool_id)
        .where(Tool.user_id == current_user_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    
    # Update fields
    update_data = tool_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)
    
    await db.commit()
    await db.refresh(tool)
    
    logger.info(f"Tool updated: {tool_id}")
    
    return tool  # type: ignore[no-any-return]


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a tool."""
    result = await db.execute(
        select(Tool)
        .where(Tool.id == tool_id)
        .where(Tool.user_id == current_user_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )
    
    tool.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Tool deleted: {tool_id}")
    
    return {"message": "Tool deleted successfully"}
