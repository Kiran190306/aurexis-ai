"""
TTSService - Text-to-Speech using Piper TTS.
"""
from typing import Optional, List, Dict, Any
import numpy as np
from loguru import logger
import time

from app.core.config import settings
from app.voice.base import SynthesisRequest, SynthesisResult, AudioFormat, VoiceProfile


class TTSService:
    """Service for text-to-speech using Piper TTS."""
    
    def __init__(self) -> None:
        self.voice = settings.TTS_VOICE
        self.speed = settings.TTS_SPEED
        self.pitch = settings.TTS_PITCH
        self.sample_rate = settings.TTS_SAMPLE_RATE
        
        self.model = None
        self.synthesizer = None
        
        # Available voices
        self.voices = [
            VoiceProfile(
                name="Amy",
                voice_id="en_US-amy-medium",
                language="en-US",
                gender="female",
                age="adult",
                description="American English female voice"
            ),
            VoiceProfile(
                name="Dave",
                voice_id="en_US-dave-medium",
                language="en-US",
                gender="male",
                age="adult",
                description="American English male voice"
            ),
            VoiceProfile(
                name="Emma",
                voice_id="en_GB-emma-medium",
                language="en-GB",
                gender="female",
                age="adult",
                description="British English female voice"
            ),
        ]
        
        logger.info(f"TTSService initialized with voice={self.voice}, sample_rate={self.sample_rate}")
    
    async def initialize(self) -> None:
        """Initialize TTS model."""
        try:
            # Try to load Piper TTS
            try:
                from piper import PiperVoice
                from piper.download import get_voices_list, ensure_voice_model
                
                logger.info(f"Loading Piper voice: {self.voice}")
                
                # Ensure voice model is downloaded
                voice_path = ensure_voice_model(self.voice)
                
                # Load voice
                self.model = PiperVoice.load(voice_path)
                self.synthesizer = self.model
                
                logger.info("Piper TTS model loaded successfully")
            
            except ImportError:
                logger.warning("Piper not installed - falling back to alternative TTS")
                # Fallback to alternative (e.g., pyttsx3 or edge-tts)
                await self._initialize_fallback()
        
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise
    
    async def _initialize_fallback(self) -> None:
        """Initialize fallback TTS engine."""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 200 * self.speed)
            self.engine.setProperty('volume', 1.0)
            logger.info("Fallback TTS engine (pyttsx3) initialized")
        except ImportError:
            logger.error("No TTS engine available")
            raise RuntimeError("Piper or pyttsx3 required for TTS")
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup TTS model."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if hasattr(self, 'engine'):
            self.engine.stop()
            del self.engine
        
        logger.info("TTSService shutdown complete")
    
    async def synthesize(
        self,
        request: SynthesisRequest
    ) -> SynthesisResult:
        """Synthesize speech from text."""
        start_time = time.time()
        
        try:
            # Apply voice settings
            voice = request.voice or self.voice
            speed = request.speed
            pitch = request.pitch
            
            # Load model if not loaded
            if self.model is None:
                await self.initialize()
            
            # Synthesize audio
            if self.synthesizer is not None:
                # Use Piper
                audio_data = await self._synthesize_piper(request.text, voice, speed, pitch)
            elif hasattr(self, 'engine'):
                # Use fallback
                audio_data = await self._synthesize_fallback(request.text, speed)
            else:
                raise RuntimeError("No TTS synthesizer available")
            
            # Calculate duration
            duration = len(audio_data) / self.sample_rate
            
            processing_time = time.time() - start_time
            
            return SynthesisResult(
                audio_data=audio_data,
                format=request.format,
                sample_rate=self.sample_rate,
                duration=duration,
                voice=voice
            )
        
        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            raise
    
    async def _synthesize_piper(
        self,
        text: str,
        voice: str,
        speed: float,
        pitch: float
    ) -> bytes:
        """Synthesize using Piper TTS."""
        import io
        import wave
        
        # Synthesize
        if self.synthesizer:
            audio_array = self.synthesizer.synthesize(text, length_scale=1.0/speed)
        else:
            audio_array = np.array([], dtype=np.int16)
        
        # Convert to WAV
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            if audio_array is not None and hasattr(audio_array, 'tobytes'):
                wav_file.writeframes(audio_array.tobytes())  # type: ignore[attr-defined]
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    async def _synthesize_fallback(
        self,
        text: str,
        speed: float
    ) -> bytes:
        """Synthesize using fallback engine."""
        import io
        import wave
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            self.engine.save_to_file(text, tmp_path)
            self.engine.runAndWait()
            
            # Read back
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
        
        finally:
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def synthesize_stream(
        self,
        text: str,
        chunk_size: int = 1024
    ) -> bytes:
        """Synthesize speech with streaming support."""
        # For now, synthesize entire text
        # In production, implement true streaming
        request = SynthesisRequest(text=text)
        result = await self.synthesize(request)
        return result.audio_data
    
    def get_available_voices(self) -> List[VoiceProfile]:
        """Get list of available voices."""
        return self.voices
    
    def get_voice_profile(self, voice_id: str) -> Optional[VoiceProfile]:
        """Get voice profile by ID."""
        for voice in self.voices:
            if voice.voice_id == voice_id:
                return voice
        return None
    
    def is_initialized(self) -> bool:
        """Check if model is initialized."""
        return self.model is not None or hasattr(self, 'engine')
    
    def estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate speech duration for text."""
        # Average speaking rate: ~150 words per minute
        words = len(text.split())
        minutes = words / 150.0
        return (minutes / speed) * 60.0


# Lazy-loaded TTS service instance
_tts_service = None


def get_tts_service():
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


# Backward compatibility
tts_service = property(lambda: get_tts_service())
