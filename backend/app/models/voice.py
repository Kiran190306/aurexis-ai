"""
Database models for Voice Intelligence System.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float, LargeBinary
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class VoiceConversationMode(PyEnum):
    """Voice conversation modes."""
    PUSH_TO_TALK = "push_to_talk"
    CONTINUOUS = "continuous"
    WAKE_WORD = "wake_word"


class VoiceConversationStatus(PyEnum):
    """Status of voice conversation."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class VoiceConversation(Base):
    """Voice conversation records."""
    __tablename__ = "voice_conversations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conversation info
    mode: Mapped[VoiceConversationMode] = mapped_column(Enum(VoiceConversationMode), nullable=False, default=VoiceConversationMode.PUSH_TO_TALK)
    status: Mapped[VoiceConversationStatus] = mapped_column(Enum(VoiceConversationStatus), default=VoiceConversationStatus.ACTIVE)
    
    # Settings
    voice_profile = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)
    speed = Column(Float, default=1.0)
    pitch = Column(Float, default=1.0)
    
    # Statistics
    message_count = Column(Integer, default=0)
    total_audio_duration = Column(Float, default=0.0)
    total_transcription_time = Column(Float, default=0.0)
    total_synthesis_time = Column(Float, default=0.0)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="voice_conversations")
    messages = relationship("VoiceMessage", back_populates="conversation", cascade="all, delete-orphan")


class VoiceMessage(Base):
    """Messages in voice conversations."""
    __tablename__ = "voice_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("voice_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant
    text = Column(Text, nullable=False)
    
    # Audio info
    audio_data = Column(LargeBinary, nullable=True)  # For small audio clips
    audio_duration = Column(Float, nullable=True)
    audio_format = Column(String(10), nullable=True)
    
    # Transcription info
    transcription_confidence = Column(Float, nullable=True)
    detected_language = Column(String(10), nullable=True)
    
    # Synthesis info
    synthesis_voice = Column(String(100), nullable=True)
    synthesis_duration = Column(Float, nullable=True)
    
    # Processing times
    transcription_time = Column(Float, nullable=True)
    synthesis_time = Column(Float, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("VoiceConversation", back_populates="messages")


class VoiceSettings(Base):
    """User voice settings."""
    __tablename__ = "voice_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # TTS settings
    voice_profile = Column(String(100), default="en_US-amy-medium")
    speed = Column(Float, default=1.0)
    pitch = Column(Float, default=1.0)
    
    # STT settings
    language = Column(String(10), default="en")
    detect_language = Column(Boolean, default=True)
    
    # Wake word settings
    wake_word_enabled = Column(Boolean, default=False)
    wake_word_phrase = Column(String(100), default="hey jarvis")
    wake_word_sensitivity = Column(Float, default=0.5)
    
    # Audio device settings
    input_device_id = Column(String(100), nullable=True)
    output_device_id = Column(String(100), nullable=True)
    
    # Conversation mode
    default_mode: Mapped[VoiceConversationMode] = mapped_column(Enum(VoiceConversationMode), default=VoiceConversationMode.PUSH_TO_TALK)
    
    # Privacy settings
    save_recordings = Column(Boolean, default=False)
    auto_transcribe = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="voice_settings")
