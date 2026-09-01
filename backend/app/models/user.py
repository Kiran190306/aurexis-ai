from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Optional
import uuid

from app.core.database import Base


class UserRole(PyEnum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    DEVELOPER = "developer"


class OAuthProvider(PyEnum):
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic Info
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(500))
    bio = Column(Text)
    
    # Authentication
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    
    # OAuth
    oauth_provider: Mapped[Optional[OAuthProvider]] = mapped_column(Enum(OAuthProvider), nullable=True)
    oauth_id = Column(String(255), nullable=True, index=True)
    
    # Security
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    theme = Column(String(20), default="dark")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    tools = relationship("Tool", back_populates="user", cascade="all, delete-orphan")
    plugins = relationship("Plugin", back_populates="user", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    prompts = relationship("Prompt", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # AI Preferences
    default_model = Column(String(50), default="gpt-4-turbo-preview")
    default_temperature = Column(Integer, default=70)  # 0-100
    default_max_tokens = Column(Integer, default=4096)
    enable_streaming = Column(Boolean, default=True)
    
    # Memory Preferences
    memory_retention_days = Column(Integer, default=90)
    enable_long_term_memory = Column(Boolean, default=True)
    enable_short_term_memory = Column(Boolean, default=True)
    
    # Tool Preferences
    enable_browse = Column(Boolean, default=True)
    enable_terminal = Column(Boolean, default=True)
    enable_github = Column(Boolean, default=True)
    enable_voice = Column(Boolean, default=True)
    enable_image = Column(Boolean, default=True)
    enable_document = Column(Boolean, default=True)
    enable_calendar = Column(Boolean, default=True)
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    notification_frequency = Column(String(20), default="instant")
    
    # Privacy
    data_sharing_enabled = Column(Boolean, default=False)
    analytics_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="settings")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    key = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    scopes = Column(Text)  # JSON array of scopes
    is_active = Column(Boolean, default=True)
    
    # Rate limits
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True, nullable=True)
    
    # Device Info
    device_type = Column(String(50))  # desktop, mobile, tablet
    device_name = Column(String(100))
    os = Column(String(50))
    browser = Column(String(50))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")
