"""
WhisperService - Speech-to-Text using OpenAI Whisper.
"""
from typing import Optional, List, Dict, Any, AsyncGenerator
from loguru import logger
import time

from app.core.config import settings
from app.voice.base import TranscriptionResult
from app.voice.audio_manager import audio_manager


class WhisperService:
    """Service for speech-to-text using Whisper model."""
    
    def __init__(self) -> None:
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.sample_rate = settings.WHISPER_SAMPLE_RATE
        self.chunk_length = settings.WHISPER_CHUNK_LENGTH
        self.language = settings.WHISPER_LANGUAGE
        
        self.model: Optional[Any] = None
        self.processor: Optional[Any] = None
        
        logger.info(f"WhisperService initialized with model={self.model_name}, device={self.device}")
    
    async def initialize(self) -> None:
        """Initialize Whisper model."""
        try:
            import numpy as np
            import torch
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            
            logger.info(f"Loading Whisper model: {self.model_name}")
            
            # Load model and processor
            self.processor = WhisperProcessor.from_pretrained(f"openai/whisper-{self.model_name}")
            self.model = WhisperForConditionalGeneration.from_pretrained(
                f"openai/whisper-{self.model_name}"
            ).to(self.device)
            
            # Set to eval mode
            if self.model:
                self.model.eval()
            
            logger.info("Whisper model loaded successfully")
        
        except ImportError:
            logger.error("transformers or torch not installed - Whisper not available")
            raise RuntimeError("transformers and torch required for Whisper")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup Whisper model."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.processor is not None:
            del self.processor
            self.processor = None
        
        logger.info("WhisperService shutdown complete")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        detect_language: bool = True
    ) -> TranscriptionResult:
        """Transcribe audio to text."""
        start_time = time.time()
        
        try:
            # Validate and convert audio
            is_valid, error_msg, audio_array = audio_manager.validate_audio_data(audio_data)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Preprocess audio
            if audio_array is not None:
                audio_array = audio_manager.normalize_audio(audio_array)
                audio_array = audio_manager.apply_noise_reduction(audio_array)
            
            # Get duration
            if audio_array is not None:
                duration = audio_manager.get_audio_duration(audio_array)
            else:
                duration = 0.0
            
            # Load model if not loaded
            if self.model is None:
                await self.initialize()
            
            # Process audio
            import torch
            
            # Convert to input features
            if self.processor:
                input_features = self.processor(
                    audio_array,
                    sampling_rate=self.sample_rate,
                    return_tensors="pt"
                ).input_features.to(self.device)
            else:
                raise ValueError("Processor not initialized")
            
            # Generate transcription
            if self.processor:
                forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                    language=language or self.language,
                    task="transcribe"
                )
            else:
                forced_decoder_ids = None
            
            with torch.no_grad():
                if self.model:
                    predicted_ids = self.model.generate(
                        input_features,
                        forced_decoder_ids=forced_decoder_ids,
                        max_new_tokens=448
                    )
                else:
                    raise ValueError("Model not initialized")
            
            # Decode transcription
            if self.processor:
                transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            else:
                transcription = ""
            
            # Get language if not specified
            detected_language = language
            if detect_language and language is None and audio_array is not None:
                # Use model's language detection
                detected_language = self._detect_language(audio_array)
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(audio_array, transcription) if audio_array is not None else 0.0
            
            # Extract segments
            segments = self._extract_segments(transcription, duration)
            
            processing_time = time.time() - start_time
            
            return TranscriptionResult(
                text=transcription,
                language=detected_language,
                confidence=confidence,
                duration=duration,
                segments=segments,
                partial=False
            )
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise
    
    async def transcribe_stream(
        self,
        audio_data: bytes,
        chunk_duration: float = 5.0
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """Stream transcription with partial results."""
        try:
            # Validate and convert audio
            is_valid, error_msg, audio_array = audio_manager.validate_audio_data(audio_data)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Preprocess audio
            if audio_array is not None:
                audio_array = audio_manager.normalize_audio(audio_array)
                audio_array = audio_manager.apply_noise_reduction(audio_array)
            
            # Split into chunks
            if audio_array is not None:
                chunks = audio_manager.chunk_audio(audio_array, chunk_duration)
            else:
                chunks = []
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                chunk_bytes = audio_manager.convert_to_wav(chunk)
                
                try:
                    result = await self.transcribe(
                        chunk_bytes,
                        language=self.language,
                        detect_language=False
                    )
                    
                    # Mark as partial if not last chunk
                    result.partial = (i < len(chunks) - 1)
                    
                    yield result
                
                except Exception as e:
                    logger.error(f"Chunk {i} transcription failed: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Streaming transcription failed: {e}")
            raise
    
    def _detect_language(self, audio: Any) -> str:
        """Detect language from audio (simplified)."""
        # In production, use Whisper's built-in language detection
        # For now, return default language
        return self.language or "en"
    
    def _calculate_confidence(self, audio: Any, transcription: str) -> float:
        """Calculate confidence score for transcription."""
        # Simplified confidence based on audio quality and transcription length
        rms = audio_manager.calculate_rms(audio)
        
        # Base confidence from audio quality
        confidence = min(1.0, rms * 10)
        
        # Adjust based on transcription length
        if len(transcription) > 0:
            confidence = confidence * 0.9 + 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _extract_segments(self, transcription: str, duration: float) -> List[Dict[str, Any]]:
        """Extract segments from transcription."""
        # Simplified segment extraction
        # In production, use Whisper's timestamp information
        words = transcription.split()
        
        if not words:
            return []
        
        # Create segments based on word count
        segment_duration = duration / len(words)
        segments = []
        
        for i, word in enumerate(words):
            segments.append({
                "start": i * segment_duration,
                "end": (i + 1) * segment_duration,
                "text": word,
                "confidence": 0.9
            })
        
        return segments
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        # Whisper supports 99 languages
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "tr", "nl", "pl", "sv", "da", "no", "fi", "el"
        ]
    
    def is_initialized(self) -> bool:
        """Check if model is initialized."""
        return self.model is not None


# Lazy-loaded Whisper service instance
_whisper_service = None


def get_whisper_service():
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service


# Backward compatibility
whisper_service = property(lambda: get_whisper_service())
