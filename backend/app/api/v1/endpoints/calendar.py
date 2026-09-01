from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.calendar import CalendarEvent, EventStatus
from pydantic import BaseModel

router = APIRouter()


class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_type: str = "meeting"
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    timezone: str = "UTC"
    recurrence_type: str = "none"
    recurrence_rule: Optional[dict] = None
    recurrence_end_date: Optional[datetime] = None
    attendees: Optional[List[dict]] = None
    organizer: Optional[str] = None
    reminders: Optional[List[dict]] = None
    meeting_link: Optional[str] = None
    meeting_password: Optional[str] = None
    conference_provider: Optional[str] = None
    metadata: Optional[dict] = None
    tags: Optional[List[str]] = None
    priority: int = 5


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendees: Optional[List[dict]] = None
    reminders: Optional[List[dict]] = None
    metadata: Optional[dict] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = None


@router.get("/", response_model=None)
async def list_events(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[CalendarEvent]:
    """List all calendar events for the current user."""
    query = select(CalendarEvent).where(
        CalendarEvent.user_id == current_user_id
    ).where(CalendarEvent.deleted_at.is_(None))
    
    if start_date:
        query = query.where(CalendarEvent.start_time >= start_date)
    if end_date:
        query = query.where(CalendarEvent.end_time <= end_date)
    
    query = query.order_by(CalendarEvent.start_time.asc())
    result = await db.execute(query)
    events = result.scalars().all()
    return list(events)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_event(
    event_data: CalendarEventCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CalendarEvent:
    """Create a new calendar event."""
    event = CalendarEvent(
        user_id=current_user_id,
        title=event_data.title,
        description=event_data.description,
        location=event_data.location,
        event_type=event_data.event_type,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        all_day=event_data.all_day,
        timezone=event_data.timezone,
        recurrence_type=event_data.recurrence_type,
        recurrence_rule=event_data.recurrence_rule,
        recurrence_end_date=event_data.recurrence_end_date,
        attendees=event_data.attendees,
        organizer=event_data.organizer,
        reminders=event_data.reminders,
        meeting_link=event_data.meeting_link,
        meeting_password=event_data.meeting_password,
        conference_provider=event_data.conference_provider,
        metadata=event_data.metadata,
        tags=event_data.tags,
        priority=event_data.priority,
        status=EventStatus.SCHEDULED,
    )
    
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    logger.info(f"Calendar event created: {event.id}")
    
    return event


@router.get("/upcoming/", response_model=None)
async def get_upcoming_events(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
) -> List[CalendarEvent]:
    """Get upcoming events for the current user."""
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.user_id == current_user_id)
        .where(CalendarEvent.start_time > datetime.utcnow())
        .where(CalendarEvent.deleted_at.is_(None))
        .order_by(CalendarEvent.start_time.asc())
        .limit(limit)
    )
    events = result.scalars().all()
    return list(events)


@router.get("/{event_id}", response_model=None)
async def get_event(
    event_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CalendarEvent:
    """Get a specific calendar event."""
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.id == event_id)
        .where(CalendarEvent.user_id == current_user_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event  # type: ignore[no-any-return]


@router.patch("/{event_id}", response_model=None)
async def update_event(
    event_id: int,
    event_data: CalendarEventUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CalendarEvent:
    """Update a calendar event."""
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.id == event_id)
        .where(CalendarEvent.user_id == current_user_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    logger.info(f"Calendar event updated: {event_id}")

    return event  # type: ignore[no-any-return]


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a calendar event."""
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.id == event_id)
        .where(CalendarEvent.user_id == current_user_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    event.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    event.status = EventStatus.CANCELLED  # type: ignore[assignment]

    await db.commit()

    logger.info(f"Calendar event deleted: {event_id}")

    return {"message": "Event deleted successfully"}
