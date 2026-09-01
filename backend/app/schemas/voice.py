"""
Pydantic schemas for Voice Intelligence System API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class TranscriptionRequest(BaseModel):
    """Request for speech-to-text transcription."""
    language: Optional[str] = Field(default=None, description="Language code (e.g., 'en', 'es')")
    detect_language: bool = Field(default=True, description="Auto-detect language")
    stream: bool = Field(default=False, description="Enable streaming transcription")


class TranscriptionResponse(BaseModel):
    """Response for transcription."""
    text: str
    language: Optional[str] = None
    confidence: float
    duration: float
    segments: List[Dict[str, Any]] = []
    partial: bool = False


class SynthesisRequest(BaseModel):
    """Request for text-to-speech synthesis."""
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(default=None, description="Voice profile")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, description="Pitch multiplier")
    format: str = Field(default="wav", description="Output format")


class SynthesisResponse(BaseModel):
    """Response for synthesis."""
    audio_data: str  # Hex encoded
    format: str
    sample_rate: int
    duration: float
    voice: str


class ChatRequest(BaseModel):
    """Request for voice chat."""
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    text: Optional[str] = Field(default=None, description="Text input (alternative to audio)")
    voice: Optional[str] = Field(default=None, description="Voice for response")
    mode: str = Field(default="push_to_talk", description="Conversation mode")


class ChatResponse(BaseModel):
    """Response for voice chat."""
    conversation_id: str
    user_text: str
    assistant_text: str
    audio_data: Optional[str] = None  # Hex encoded
    transcription_confidence: Optional[float] = None
    processing_time: float


class VoiceConversationResponse(BaseModel):
    """Response for voice conversation."""
    id: int
    uuid: str
    mode: str
    status: str
    message_count: int
    total_audio_duration: float
    started_at: str
    ended_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class VoiceSettingsResponse(BaseModel):
    """Response for voice settings."""
    voice_profile: str
    speed: float
    pitch: float
    language: str
    detect_language: bool
    wake_word_enabled: bool
    wake_word_phrase: str
    wake_word_sensitivity: float
    input_device_id: Optional[str] = None
    output_device_id: Optional[str] = None
    default_mode: str
    save_recordings: bool
    auto_transcribe: bool
    
    class Config:
        from_attributes = True
