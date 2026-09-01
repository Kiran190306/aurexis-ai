from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.plugin import Plugin, PluginStatus
from pydantic import BaseModel

router = APIRouter()


class PluginCreate(BaseModel):
    name: str
    display_name: str
    description: str
    plugin_type: str = "external"
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    config_schema: Optional[dict] = None
    default_config: Optional[dict] = None
    capabilities: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    dependencies: Optional[dict] = None
    python_dependencies: Optional[List[str]] = None
    hooks: Optional[dict] = None


class PluginUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    config_schema: Optional[dict] = None
    default_config: Optional[dict] = None
    capabilities: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


@router.get("/", response_model=None)
async def list_plugins(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[Plugin]:
    """List all plugins for the current user."""
    result = await db.execute(
        select(Plugin)
        .where(Plugin.user_id == current_user_id)
        .where(Plugin.deleted_at.is_(None))
        .order_by(Plugin.created_at.desc())
    )
    plugins = result.scalars().all()
    return list(plugins)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_plugin(
    plugin_data: PluginCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Plugin:
    """Create a new plugin."""
    plugin = Plugin(
        user_id=current_user_id,
        name=plugin_data.name,
        display_name=plugin_data.display_name,
        description=plugin_data.description,
        plugin_type=plugin_data.plugin_type,
        package_name=plugin_data.package_name,
        package_version=plugin_data.package_version,
        config_schema=plugin_data.config_schema,
        default_config=plugin_data.default_config,
        capabilities=plugin_data.capabilities,
        permissions=plugin_data.permissions,
        dependencies=plugin_data.dependencies,
        python_dependencies=plugin_data.python_dependencies,
        hooks=plugin_data.hooks,
        status=PluginStatus.ACTIVE,
    )
    
    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)
    
    logger.info(f"Plugin created: {plugin.name}")
    
    return plugin


@router.get("/{plugin_id}", response_model=None)
async def get_plugin(
    plugin_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Plugin:
    """Get a specific plugin."""
    result = await db.execute(
        select(Plugin)
        .where(Plugin.id == plugin_id)
        .where(Plugin.user_id == current_user_id)
    )
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )
    
    return plugin  # type: ignore[no-any-return]


@router.patch("/{plugin_id}", response_model=None)
async def update_plugin(
    plugin_id: int,
    plugin_data: PluginUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Plugin:
    """Update a plugin."""
    result = await db.execute(
        select(Plugin)
        .where(Plugin.id == plugin_id)
        .where(Plugin.user_id == current_user_id)
    )
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )
    
    # Update fields
    update_data = plugin_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plugin, field, value)
    
    await db.commit()
    await db.refresh(plugin)
    
    logger.info(f"Plugin updated: {plugin_id}")
    
    return plugin  # type: ignore[no-any-return]


@router.delete("/{plugin_id}")
async def delete_plugin(
    plugin_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a plugin."""
    result = await db.execute(
        select(Plugin)
        .where(Plugin.id == plugin_id)
        .where(Plugin.user_id == current_user_id)
    )
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )
    
    plugin.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"Plugin deleted: {plugin_id}")
    
    return {"message": "Plugin deleted successfully"}
