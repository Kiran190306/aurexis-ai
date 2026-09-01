from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Optional
import uuid

from app.core.database import Base


class NotificationType(PyEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TASK = "task"
    REMINDER = "reminder"
    SYSTEM = "system"


class NotificationChannel(PyEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationStatus(PyEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    DISMISSED = "dismissed"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), default=NotificationType.INFO)
    
    # Channels
    channels = Column(JSON)  # Array of channels to send to
    preferred_channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), default=NotificationChannel.IN_APP)
    
    # Status
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Priority
    priority = Column(Integer, default=5)  # 1-10
    is_urgent = Column(Boolean, default=False)
    
    # Action
    action_url = Column(String(500), nullable=True)
    action_label = Column(String(100), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    category = Column(String(50), nullable=True)
    tags = Column(JSON)  # Array of tags
    
    # Delivery Tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Channel Preferences
    in_app_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    webhook_enabled = Column(Boolean, default=False)
    
    # Type Preferences
    info_enabled = Column(Boolean, default=True)
    success_enabled = Column(Boolean, default=True)
    warning_enabled = Column(Boolean, default=True)
    error_enabled = Column(Boolean, default=True)
    task_enabled = Column(Boolean, default=True)
    reminder_enabled = Column(Boolean, default=True)
    system_enabled = Column(Boolean, default=True)
    
    # Quiet Hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM
    quiet_hours_end = Column(String(5), nullable=True)  # HH:MM
    quiet_hours_timezone = Column(String(50), default="UTC")
    
    # Email Settings
    email_digest = Column(Boolean, default=False)
    email_digest_frequency = Column(String(20), default="daily")  # daily, weekly
    
    # Webhook Settings
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    
    # Content
    title_template = Column(String(255), nullable=False)
    message_template = Column(Text, nullable=False)
    variables = Column(JSON)  # Array of variable definitions
    
    # Configuration
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), default=NotificationType.INFO)
    default_channels = Column(JSON)  # Array of default channels
    priority = Column(Integer, default=5)
    
    # Action
    action_url_template = Column(String(500), nullable=True)
    action_label_template = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
