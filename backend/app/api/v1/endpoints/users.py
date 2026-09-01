from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.auth import UserResponse
from app.models.user import User, UserSettings
from pydantic import BaseModel
from typing import Optional, Any

router = APIRouter()


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None


class UserSettingsUpdate(BaseModel):
    default_model: Optional[str] = None
    default_temperature: Optional[int] = None
    default_max_tokens: Optional[int] = None
    enable_streaming: Optional[bool] = None
    memory_retention_days: Optional[int] = None
    enable_long_term_memory: Optional[bool] = None
    enable_short_term_memory: Optional[bool] = None
    enable_browse: Optional[bool] = None
    enable_terminal: Optional[bool] = None
    enable_github: Optional[bool] = None
    enable_voice: Optional[bool] = None
    enable_image: Optional[bool] = None
    enable_document: Optional[bool] = None
    enable_calendar: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    notification_frequency: Optional[str] = None
    data_sharing_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get current user information."""
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user  # type: ignore[no-any-return]


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update current user information."""
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"User updated: {user.email}")
    
    return user  # type: ignore[no-any-return]


@router.get("/me/settings")
async def get_user_settings(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current user settings."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = UserSettings(user_id=current_user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


@router.patch("/me/settings")
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update current user settings."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = UserSettings(user_id=current_user_id)
        db.add(settings)
    
    # Update fields
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    logger.info(f"User settings updated: {current_user_id}")
    
    return settings
