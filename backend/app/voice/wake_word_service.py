"""
WakeWordService - Wake phrase detection using Porcupine or similar.
"""
from typing import Optional, Callable, AsyncGenerator, Any
import numpy as np
from loguru import logger
import asyncio
from threading import Thread

from app.core.config import settings
from app.voice.base import WakeWordDetection
from app.voice.audio_manager import audio_manager


class WakeWordService:
    """Service for wake word detection."""
    
    def __init__(self) -> None:
        self.phrase = settings.WAKE_WORD_PHRASE
        self.sensitivity = settings.WAKE_WORD_SENSITIVITY
        self.model = settings.WAKE_WORD_MODEL
        self.enabled = settings.WAKE_WORD_ENABLED
        
        self.detector: Any = None
        self.is_listening = False
        self.callback: Optional[Callable] = None
        self._listen_thread: Optional[Thread] = None
        
        logger.info(f"WakeWordService initialized with phrase='{self.phrase}', sensitivity={self.sensitivity}")
    
    async def initialize(self) -> None:
        """Initialize wake word detector."""
        if not self.enabled:
            logger.info("Wake word detection disabled")
            return
        
        try:
            # Try to load Porcupine
            try:
                import pvporcupine
                
                logger.info(f"Loading Porcupine for wake word: {self.phrase}")
                
                # Create keyword
                access_key = settings.PORCUPINE_ACCESS_KEY if hasattr(settings, 'PORCUPINE_ACCESS_KEY') else None
                
                if access_key:
                    self.detector = pvporcupine.create(
                        access_key=access_key,
                        keywords=[self.phrase],
                        sensitivities=[self.sensitivity]
                    )
                else:
                    # Use free tier or fallback
                    logger.warning("Porcupine access key not provided - using fallback")
                    await self._initialize_fallback()
                
                logger.info("Porcupine wake word detector loaded successfully")
            
            except ImportError:
                logger.warning("Porcupine not installed - using fallback")
                await self._initialize_fallback()
        
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
            await self._initialize_fallback()
    
    async def _initialize_fallback(self) -> None:
        """Initialize fallback wake word detection."""
        # Use simple energy-based detection + keyword matching
        logger.info("Using fallback wake word detection")
        self.detector = "fallback"
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup."""
        self.is_listening = False
        
        if self.detector is not None and self.detector != "fallback":
            try:
                self.detector.delete()
            except Exception:
                pass
            self.detector = None
        
        logger.info("WakeWordService shutdown complete")
    
    async def start_listening(
        self,
        callback: Callable[[WakeWordDetection], None]
    ) -> None:
        """Start listening for wake word."""
        if not self.enabled:
            logger.warning("Wake word detection disabled")
            return
        
        self.callback = callback
        self.is_listening = True
        
        # Start listening in background thread
        if self.detector and self.detector != "fallback":
            self._listen_thread = Thread(target=self._listen_porcupine, daemon=True)
            self._listen_thread.start()
        else:
            self._listen_thread = Thread(target=self._listen_fallback, daemon=True)
            self._listen_thread.start()
        
        logger.info("Wake word listening started")
    
    async def stop_listening(self) -> None:
        """Stop listening for wake word."""
        self.is_listening = False
        logger.info("Wake word listening stopped")
    
    def _listen_porcupine(self) -> None:
        """Listen using Porcupine detector."""
        import sounddevice as sd
        
        def audio_callback(indata: Any, frames: int, time: Any, status: Any) -> None:
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            if self.is_listening and self.detector:
                # Process audio
                pcm = indata[:, 0]
                keyword_index = self.detector.process(pcm)
                
                if keyword_index >= 0:
                    detection = WakeWordDetection(
                        detected=True,
                        confidence=0.9,
                        timestamp=time.time(),
                        phrase=self.phrase
                    )
                    
                    if self.callback:
                        self.callback(detection)
        
        try:
            if self.detector:
                with sd.InputStream(
                    samplerate=self.detector.sample_rate,
                    channels=1,
                    callback=audio_callback
                ):
                    while self.is_listening:
                        import time
                        time.sleep(0.1)
        except Exception as e:
            logger.error(f"Porcupine listening error: {e}")
    
    def _listen_fallback(self) -> None:
        """Listen using fallback detection."""
        import sounddevice as sd
        
        def audio_callback(indata: Any, frames: int, time: Any, status: Any) -> None:
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            if self.is_listening:
                # Simple energy-based detection
                pcm = indata[:, 0]
                rms = np.sqrt(np.mean(pcm ** 2))
                
                # If energy exceeds threshold, could be speech
                if rms > 0.1:
                    # In production, would transcribe and check for phrase
                    # For now, just log
                    pass
        
        try:
            with sd.InputStream(
                samplerate=16000,
                channels=1,
                callback=audio_callback
            ):
                while self.is_listening:
                    import time
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Fallback listening error: {e}")
    
    async def detect_in_audio(self, audio_data: bytes) -> WakeWordDetection:
        """Detect wake word in audio data."""
        try:
            # Validate audio
            is_valid, error_msg, audio_array = audio_manager.validate_audio_data(audio_data)
            if not is_valid:
                return WakeWordDetection(
                    detected=False,
                    confidence=0.0,
                    timestamp=0.0,
                    phrase=self.phrase
                )
            
            # Process with detector
            if self.detector and self.detector != "fallback":
                # Use Porcupine
                keyword_index = self.detector.process(audio_array)
                detected = keyword_index >= 0
                confidence = 0.9 if detected else 0.0
            else:
                # Fallback: transcribe and check
                from app.voice.whisper_service import whisper_service
                result = await whisper_service.transcribe(audio_data)
                
                # Check if phrase is in transcription
                phrase_lower = self.phrase.lower()
                text_lower = result.text.lower()
                detected = phrase_lower in text_lower
                confidence = 0.7 if detected else 0.0
            
            return WakeWordDetection(
                detected=detected,
                confidence=confidence,
                timestamp=0.0,
                phrase=self.phrase
            )
        
        except Exception as e:
            logger.error(f"Wake word detection failed: {e}")
            return WakeWordDetection(
                detected=False,
                confidence=0.0,
                timestamp=0.0,
                phrase=self.phrase
            )
    
    def set_wake_phrase(self, phrase: str) -> None:
        """Set custom wake phrase."""
        self.phrase = phrase
        logger.info(f"Wake phrase set to: {phrase}")
    
    def set_sensitivity(self, sensitivity: float) -> None:
        """Set detection sensitivity."""
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        logger.info(f"Wake word sensitivity set to: {self.sensitivity}")
    
    def is_initialized(self) -> bool:
        """Check if detector is initialized."""
        return self.detector is not None


# Global wake word service instance
wake_word_service = WakeWordService()
