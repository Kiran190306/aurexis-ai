"""
Base classes and data models for Voice Intelligence System.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class VoiceTaskType(str, Enum):
    """Types of voice tasks."""
    TRANSCRIPTION = "transcription"
    SYNTHESIS = "synthesis"
    WAKE_WORD = "wake_word"
    CONVERSATION = "conversation"
    STREAMING = "streaming"


class AudioFormat(str, Enum):
    """Audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    PCM = "pcm"


class TranscriptionResult(BaseModel):
    """Result of speech-to-text transcription."""
    text: str = Field(..., description="Transcribed text")
    language: Optional[str] = Field(default=None, description="Detected language")
    confidence: float = Field(..., description="Overall confidence score (0-1)")
    duration: float = Field(..., description="Audio duration in seconds")
    segments: List[Dict[str, Any]] = Field(default_factory=list, description="Transcription segments")
    words: List[Dict[str, Any]] = Field(default_factory=list, description="Word-level timestamps")
    partial: bool = Field(default=False, description="Whether this is a partial result")


class SynthesisRequest(BaseModel):
    """Request for text-to-speech synthesis."""
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(default=None, description="Voice profile")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, description="Pitch multiplier")
    format: AudioFormat = Field(default=AudioFormat.WAV, description="Output audio format")


class SynthesisResult(BaseModel):
    """Result of text-to-speech synthesis."""
    audio_data: bytes = Field(..., description="Generated audio data")
    format: AudioFormat = Field(..., description="Audio format")
    sample_rate: int = Field(..., description="Sample rate in Hz")
    duration: float = Field(..., description="Audio duration in seconds")
    voice: str = Field(..., description="Voice used")


class WakeWordDetection(BaseModel):
    """Result of wake word detection."""
    detected: bool = Field(..., description="Whether wake word was detected")
    confidence: float = Field(..., description="Detection confidence")
    timestamp: float = Field(..., description="Detection timestamp")
    phrase: str = Field(..., description="Detected phrase")


class VoiceConversation(BaseModel):
    """Voice conversation session."""
    id: str = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="User ID")
    started_at: datetime = Field(..., description="Session start time")
    ended_at: Optional[datetime] = Field(default=None, description="Session end time")
    mode: str = Field(..., description="Conversation mode (push_to_talk, continuous)")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VoiceMessage(BaseModel):
    """Message in voice conversation."""
    role: str = Field(..., description="Message role (user, assistant)")
    text: str = Field(..., description="Message text")
    audio_duration: Optional[float] = Field(default=None, description="Audio duration")
    timestamp: datetime = Field(..., description="Message timestamp")
    transcription_confidence: Optional[float] = Field(default=None, description="Transcription confidence")


class AudioDeviceInfo(BaseModel):
    """Audio device information."""
    device_id: str = Field(..., description="Device ID")
    device_name: str = Field(..., description="Device name")
    device_type: str = Field(..., description="Device type (input/output)")
    sample_rate: Optional[int] = Field(default=None, description="Supported sample rate")
    channels: Optional[int] = Field(default=None, description="Number of channels")
    is_default: bool = Field(default=False, description="Whether this is the default device")


class VoiceProfile(BaseModel):
    """Voice profile for TTS."""
    name: str = Field(..., description="Profile name")
    voice_id: str = Field(..., description="Voice ID")
    language: str = Field(..., description="Language code")
    gender: Optional[str] = Field(default=None, description="Voice gender")
    age: Optional[str] = Field(default=None, description="Voice age")
    description: Optional[str] = Field(default=None, description="Voice description")
