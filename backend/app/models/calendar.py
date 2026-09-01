from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class EventType(PyEnum):
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    TASK = "task"
    DEADLINE = "deadline"


class EventStatus(PyEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class RecurrenceType(PyEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), default=EventType.MEETING)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.SCHEDULED)
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    all_day = Column(Boolean, default=False)
    timezone = Column(String(50), default="UTC")
    
    # Recurrence
    recurrence_type: Mapped[RecurrenceType] = mapped_column(Enum(RecurrenceType), default=RecurrenceType.NONE)
    recurrence_rule = Column(JSON)  # Recurrence rule configuration
    recurrence_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Attendees
    attendees = Column(JSON)  # Array of attendee information
    organizer = Column(String(255), nullable=True)
    
    # External Integration
    external_event_id = Column(String(255), nullable=True)  # Google Calendar, Outlook, etc.
    external_calendar = Column(String(50), nullable=True)
    sync_status = Column(String(20), default="synced")
    
    # Reminders
    reminders = Column(JSON)  # Array of reminder configurations
    reminder_sent = Column(Boolean, default=False)
    
    # Meeting Details
    meeting_link = Column(String(500), nullable=True)
    meeting_password = Column(String(100), nullable=True)
    conference_provider = Column(String(50), nullable=True)  # zoom, google_meet, teams
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    tags = Column(JSON)  # Array of tags
    
    # Priority
    priority = Column(Integer, default=5)  # 1-10
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="calendar_events")


class CalendarIntegration(Base):
    __tablename__ = "calendar_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Google Calendar
    google_enabled = Column(Boolean, default=False)
    google_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_calendar_id = Column(String(255), nullable=True)
    google_sync_enabled = Column(Boolean, default=True)
    
    # Outlook Calendar
    outlook_enabled = Column(Boolean, default=False)
    outlook_token = Column(Text, nullable=True)
    outlook_refresh_token = Column(Text, nullable=True)
    outlook_calendar_id = Column(String(255), nullable=True)
    outlook_sync_enabled = Column(Boolean, default=True)
    
    # Sync Settings
    sync_direction = Column(String(20), default="both")  # both, import, export
    sync_frequency = Column(Integer, default=3600)  # seconds
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
