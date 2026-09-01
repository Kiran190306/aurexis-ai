from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.notification import Notification, NotificationStatus
from pydantic import BaseModel

router = APIRouter()


class NotificationCreate(BaseModel):
    title: str
    message: str
    notification_type: str = "info"
    channels: Optional[List[str]] = None
    preferred_channel: str = "in_app"
    priority: int = 5
    is_urgent: bool = False
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    metadata: Optional[dict] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class NotificationUpdate(BaseModel):
    status: Optional[str] = None
    is_read: Optional[bool] = None


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    info_enabled: Optional[bool] = None
    success_enabled: Optional[bool] = None
    warning_enabled: Optional[bool] = None
    error_enabled: Optional[bool] = None
    task_enabled: Optional[bool] = None
    reminder_enabled: Optional[bool] = None
    system_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    email_digest: Optional[bool] = None
    email_digest_frequency: Optional[str] = None


@router.get("/", response_model=None)
async def list_notifications(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
) -> List[Notification]:
    """List all notifications for the current user."""
    query = select(Notification).where(Notification.user_id == current_user_id)
    
    if unread_only:
        query = query.where(Notification.status == NotificationStatus.PENDING)
    
    query = query.order_by(Notification.created_at.desc())
    result = await db.execute(query)
    notifications = result.scalars().all()
    return list(notifications)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_notification(
    notification_data: NotificationCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=current_user_id,
        title=notification_data.title,
        message=notification_data.message,
        notification_type=notification_data.notification_type,
        channels=notification_data.channels,
        preferred_channel=notification_data.preferred_channel,
        priority=notification_data.priority,
        is_urgent=notification_data.is_urgent,
        action_url=notification_data.action_url,
        action_label=notification_data.action_label,
        metadata=notification_data.metadata,
        category=notification_data.category,
        tags=notification_data.tags,
        status=NotificationStatus.PENDING,
    )
    
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    logger.info(f"Notification created: {notification.id}")
    
    return notification


@router.post("/mark-all-read")
async def mark_all_read(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Mark all notifications as read."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user_id)
        .where(Notification.status == NotificationStatus.PENDING)
    )
    notifications = result.scalars().all()

    for notification in notifications:
        notification.status = NotificationStatus.READ  # type: ignore[assignment]
        notification.read_at = datetime.utcnow()  # type: ignore[assignment]

    await db.commit()

    logger.info(f"Marked {len(notifications)} notifications as read")

    return {"message": f"Marked {len(notifications)} notifications as read"}


@router.get("/{notification_id}", response_model=None)
async def get_notification(
    notification_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    """Get a specific notification."""
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == current_user_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    return notification  # type: ignore[no-any-return]


@router.patch("/{notification_id}", response_model=None)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    """Update a notification."""
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == current_user_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    # Update fields
    update_data = notification_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notification, field, value)
    
    # Mark as read if requested
    if notification_data.is_read:
        notification.status = NotificationStatus.READ  # type: ignore[assignment]
        notification.read_at = datetime.utcnow()  # type: ignore[assignment]
    
    await db.commit()
    await db.refresh(notification)
    
    logger.info(f"Notification updated: {notification_id}")
    
    return notification  # type: ignore[no-any-return]


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete a notification."""
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == current_user_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    notification.status = NotificationStatus.DISMISSED
    
    await db.commit()
    
    logger.info(f"Notification deleted: {notification_id}")
    
    return {"message": "Notification deleted successfully"}


@router.get("/preferences/")
async def get_notification_preferences(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get notification preferences for the current user."""
    from app.models.notification import NotificationPreference
    
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == current_user_id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreference(user_id=current_user_id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    
    return preferences


@router.patch("/preferences/")
async def update_notification_preferences(
    preferences_data: NotificationPreferenceUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update notification preferences."""
    from app.models.notification import NotificationPreference
    
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == current_user_id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreference(user_id=current_user_id)
        db.add(preferences)
    
    # Update fields
    update_data = preferences_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    await db.commit()
    await db.refresh(preferences)
    
    logger.info(f"Notification preferences updated: {current_user_id}")
    
    return preferences
