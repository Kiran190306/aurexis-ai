"""
API endpoints for Voice Intelligence System.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List, Any, AsyncGenerator
from loguru import logger
from datetime import datetime
from contextlib import asynccontextmanager
import time

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.config import settings
from app.models.user import User
from app.models.voice import (
    VoiceConversation,
    VoiceMessage,
    VoiceConversationMode,
    VoiceConversationStatus,
    VoiceSettings
)
from app.schemas.voice import (
    TranscriptionRequest,
    TranscriptionResponse,
    SynthesisRequest,
    SynthesisResponse,
    ChatRequest,
    ChatResponse,
    VoiceConversationResponse,
    VoiceSettingsResponse
)
from app.voice.whisper_service import whisper_service
from app.voice.tts_service import tts_service
from app.voice.voice_agent import VoiceAgent

router = APIRouter()

# Initialize voice agent
voice_agent = VoiceAgent()


@asynccontextmanager
async def lifespan(app: Any) -> AsyncGenerator[None, None]:
    """Lifespan context manager for voice services."""
    if settings.ENABLE_VOICE:
        try:
            await voice_agent.initialize()
            logger.info("Voice services initialized")
        except Exception as e:
            logger.error(f"Failed to initialize voice services: {e}")
    yield
    if settings.ENABLE_VOICE:
        try:
            await voice_agent.shutdown()
            logger.info("Voice services shutdown")
        except Exception as e:
            logger.error(f"Failed to shutdown voice services: {e}")


router.lifespan_context = lifespan


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    detect_language: bool = True,
    current_user_id: int = Depends(get_current_user_id)
) -> TranscriptionResponse:
    """Transcribe audio to text using Whisper."""
    logger.info(f"User {current_user_id} requesting transcription")
    
    try:
        if not settings.ENABLE_VOICE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Voice features are disabled"
            )
        
        # Read audio data
        audio_data = await file.read()
        
        # Transcribe
        result = await whisper_service.transcribe(
            audio_data,
            language=language,
            detect_language=detect_language
        )
        
        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration=result.duration,
            segments=result.segments,
            partial=result.partial
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/speak", response_model=SynthesisResponse)
async def synthesize_speech(
    text: str,
    voice: Optional[str] = None,
    speed: float = 1.0,
    pitch: float = 1.0,
    format: str = "wav",
    current_user_id: int = Depends(get_current_user_id)
) -> SynthesisResponse:
    """Synthesize text to speech using TTS."""
    logger.info(f"User {current_user_id} requesting synthesis")
    
    try:
        if not settings.ENABLE_VOICE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Voice features are disabled"
            )
        
        from app.voice.base import SynthesisRequest as BaseSynthesisRequest, AudioFormat
        
        request = BaseSynthesisRequest(
            text=text,
            voice=voice,
            speed=speed,
            pitch=pitch,
            format=AudioFormat(format)
        )
        
        result = await tts_service.synthesize(request)
        
        return SynthesisResponse(
            audio_data=result.audio_data.hex(),
            format=result.format.value,
            sample_rate=result.sample_rate,
            duration=result.duration,
            voice=result.voice
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def voice_chat(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = None,
    conversation_id: Optional[str] = None,
    voice: Optional[str] = None,
    mode: str = "push_to_talk",
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """Handle voice conversation with AI."""
    logger.info(f"User {current_user_id} requesting voice chat")
    
    try:
        if not settings.ENABLE_VOICE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Voice features are disabled"
            )
        
        # Validate input
        if not file and not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either audio file or text must be provided"
            )
        
        start_time = time.time()
        
        # Get or create conversation
        if conversation_id:
            result = await db.execute(
                select(VoiceConversation).where(
                    and_(
                        VoiceConversation.uuid == conversation_id,
                        VoiceConversation.user_id == current_user_id
                    )
                )
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # Create new conversation
            conversation = VoiceConversation(
                user_id=current_user_id,
                mode=VoiceConversationMode(mode),
                status=VoiceConversationStatus.ACTIVE
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
        
        # Process input
        user_text = text
        transcription_confidence = None
        
        if file:
            audio_data = await file.read()
            transcription = await whisper_service.transcribe(audio_data)
            user_text = transcription.text
            transcription_confidence = transcription.confidence
        
        # Generate AI response
        from app.ai.base import Message
        messages = [
            Message(role="system", content="You are Jarvis AI, a helpful assistant."),
            Message(role="user", content=user_text or "")
        ]
        
        from app.ai.engine import ai_engine
        ai_response = await ai_engine.generate(messages)
        assistant_text = ai_response.content
        
        # Synthesize response
        audio_data_hex = None
        if voice:
            from app.voice.base import SynthesisRequest as BaseSynthesisRequest, AudioFormat
            
            synthesis_request = BaseSynthesisRequest(
                text=assistant_text,
                voice=voice,
                format=AudioFormat.WAV
            )
            
            synthesis_result = await tts_service.synthesize(synthesis_request)
            audio_data_hex = synthesis_result.audio_data.hex()
        
        # Save messages
        user_message = VoiceMessage(
            conversation_id=conversation.id,
            role="user",
            text=user_text,
            transcription_confidence=transcription_confidence
        )
        db.add(user_message)
        
        assistant_message = VoiceMessage(
            conversation_id=conversation.id,
            role="assistant",
            text=assistant_text,
            synthesis_voice=voice,
            synthesis_time=time.time() - start_time
        )
        db.add(assistant_message)
        
        # Update conversation
        conversation.message_count += 2  # type: ignore[assignment]
        conversation.updated_at = datetime.utcnow()  # type: ignore[assignment]
        
        await db.commit()
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            conversation_id=str(conversation.uuid),
            user_text=user_text or "",
            assistant_text=assistant_text,
            audio_data=audio_data_hex,
            transcription_confidence=transcription_confidence,
            processing_time=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice chat endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice chat failed: {str(e)}"
        )


@router.get("/history", response_model=List[VoiceConversationResponse])
async def get_voice_history(
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[VoiceConversationResponse]:
    """Get voice conversation history for current user."""
    try:
        query = select(VoiceConversation).where(VoiceConversation.user_id == current_user_id)
        query = query.order_by(VoiceConversation.started_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        return [VoiceConversationResponse.model_validate(conversation) for conversation in conversations]
    
    except Exception as e:
        logger.error(f"Failed to get voice history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/history/{conversation_uuid}")
async def get_voice_conversation(
    conversation_uuid: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get specific voice conversation with messages."""
    try:
        # Get conversation
        conv_result = await db.execute(
            select(VoiceConversation).where(
                and_(
                    VoiceConversation.uuid == conversation_uuid,
                    VoiceConversation.user_id == current_user_id
                )
            )
        )
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages
        msg_result = await db.execute(
            select(VoiceMessage).where(VoiceMessage.conversation_id == conversation.id)
            .order_by(VoiceMessage.created_at)
        )
        messages = msg_result.scalars().all()
        
        return {
            "conversation": VoiceConversationResponse.model_validate(conversation),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "text": msg.text,
                    "audio_duration": msg.audio_duration,
                    "transcription_confidence": msg.transcription_confidence,
                    "synthesis_voice": msg.synthesis_voice,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.get("/settings", response_model=VoiceSettingsResponse)
async def get_voice_settings(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> VoiceSettingsResponse:
    """Get voice settings for current user."""
    try:
        result = await db.execute(
            select(VoiceSettings).where(VoiceSettings.user_id == current_user_id)
        )
        settings_record = result.scalar_one_or_none()
        
        if not settings_record:
            # Create default settings
            settings_record = VoiceSettings(user_id=current_user_id)
            db.add(settings_record)
            await db.commit()
            await db.refresh(settings_record)
        
        return settings_record  # type: ignore[no-any-return]
    
    except Exception as e:
        logger.error(f"Failed to get voice settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@router.patch("/settings", response_model=VoiceSettingsResponse)
async def update_voice_settings(
    voice_profile: Optional[str] = None,
    speed: Optional[float] = None,
    pitch: Optional[float] = None,
    language: Optional[str] = None,
    detect_language: Optional[bool] = None,
    wake_word_enabled: Optional[bool] = None,
    wake_word_phrase: Optional[str] = None,
    wake_word_sensitivity: Optional[float] = None,
    input_device_id: Optional[str] = None,
    output_device_id: Optional[str] = None,
    default_mode: Optional[str] = None,
    save_recordings: Optional[bool] = None,
    auto_transcribe: Optional[bool] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> VoiceSettingsResponse:
    """Update voice settings for current user."""
    try:
        result = await db.execute(
            select(VoiceSettings).where(VoiceSettings.user_id == current_user_id)
        )
        settings_record = result.scalar_one_or_none()
        
        if not settings_record:
            settings_record = VoiceSettings(user_id=current_user_id)
            db.add(settings_record)
        
        # Update fields if provided
        if voice_profile is not None:
            settings_record.voice_profile = voice_profile  # type: ignore[assignment]
        if speed is not None:
            settings_record.speed = speed  # type: ignore[assignment]
        if pitch is not None:
            settings_record.pitch = pitch  # type: ignore[assignment]
        if language is not None:
            settings_record.language = language  # type: ignore[assignment]
        if detect_language is not None:
            settings_record.detect_language = detect_language  # type: ignore[assignment]
        if wake_word_enabled is not None:
            settings_record.wake_word_enabled = wake_word_enabled  # type: ignore[assignment]
        if wake_word_phrase is not None:
            settings_record.wake_word_phrase = wake_word_phrase  # type: ignore[assignment]
        if wake_word_sensitivity is not None:
            settings_record.wake_word_sensitivity = wake_word_sensitivity  # type: ignore[assignment]
        if input_device_id is not None:
            settings_record.input_device_id = input_device_id  # type: ignore[assignment]
        if output_device_id is not None:
            settings_record.output_device_id = output_device_id  # type: ignore[assignment]
        if default_mode is not None:
            settings_record.default_mode = VoiceConversationMode(default_mode)  # type: ignore[assignment]
        if save_recordings is not None:
            settings_record.save_recordings = save_recordings  # type: ignore[assignment]
        if auto_transcribe is not None:
            settings_record.auto_transcribe = auto_transcribe  # type: ignore[assignment]
        
        settings_record.updated_at = datetime.utcnow()  # type: ignore[assignment]
        
        await db.commit()
        await db.refresh(settings_record)
        
        return settings_record  # type: ignore[no-any-return]
    
    except Exception as e:
        logger.error(f"Failed to update voice settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )
