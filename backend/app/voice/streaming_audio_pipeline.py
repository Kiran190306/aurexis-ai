"""
StreamingAudioPipeline - Real-time audio processing for full-duplex voice conversations.
"""
from typing import Optional, AsyncGenerator, Callable, Any, Dict
import numpy as np
from loguru import logger
import asyncio
from collections import deque
import time

from app.core.config import settings
from app.voice.base import TranscriptionResult, SynthesisResult
from app.voice.whisper_service import whisper_service
from app.voice.tts_service import tts_service
from app.voice.audio_manager import audio_manager


class StreamingAudioPipeline:
    """Pipeline for real-time streaming audio processing."""
    
    def __init__(self) -> None:
        self.sample_rate = settings.WHISPER_SAMPLE_RATE
        self.chunk_size = 1024
        self.buffer_duration = 2.0  # 2 seconds buffer
        
        # Audio buffers
        self.input_buffer: deque = deque(maxlen=int(self.sample_rate * self.buffer_duration))
        self.output_buffer: deque = deque()
        
        # State
        self.is_running = False
        self.is_speaking = False
        self.mode = "push_to_talk"  # push_to_talk, continuous
        
        # Callbacks
        self.on_transcription: Optional[Callable[[TranscriptionResult], None]] = None
        self.on_synthesis: Optional[Callable[[bytes], None]] = None
        self.on_wake_word: Optional[Callable] = None
        
        logger.info("StreamingAudioPipeline initialized")
    
    async def start(self) -> None:
        """Start the streaming pipeline."""
        self.is_running = True
        
        # Start processing tasks
        self._transcription_task = asyncio.create_task(self._process_transcription())
        self._synthesis_task = asyncio.create_task(self._process_synthesis())
        
        logger.info("StreamingAudioPipeline started")
    
    async def stop(self) -> None:
        """Stop the streaming pipeline."""
        self.is_running = False
        
        # Cancel tasks
        if hasattr(self, '_transcription_task'):
            self._transcription_task.cancel()
        if hasattr(self, '_synthesis_task'):
            self._synthesis_task.cancel()
        
        logger.info("StreamingAudioPipeline stopped")
    
    async def add_audio_chunk(self, audio_data: bytes) -> None:
        """Add audio chunk to input buffer."""
        try:
            # Validate and convert
            is_valid, error_msg, audio_array = audio_manager.validate_audio_data(audio_data)
            if not is_valid:
                logger.warning(f"Invalid audio chunk: {error_msg}")
                return
            
            # Add to buffer
            if audio_array is not None:
                for sample in audio_array:
                    self.input_buffer.append(sample)
        
        except Exception as e:
            logger.error(f"Failed to add audio chunk: {e}")
    
    async def add_text_to_speak(self, text: str) -> None:
        """Add text to synthesis queue."""
        self.output_buffer.append(text)
    
    async def _process_transcription(self) -> None:
        """Process audio for transcription."""
        while self.is_running:
            try:
                # Wait for enough audio
                if len(self.input_buffer) < self.sample_rate:
                    await asyncio.sleep(0.1)
                    continue
                
                # Extract audio chunk
                chunk_samples = int(self.sample_rate * 0.5)  # 500ms chunks
                chunk = np.array([self.input_buffer.popleft() for _ in range(chunk_samples)])
                
                # Detect voice activity
                if audio_manager.detect_voice_activity(chunk):
                    # Transcribe
                    chunk_bytes = audio_manager.convert_to_wav(chunk)
                    
                    try:
                        result = await whisper_service.transcribe(
                            chunk_bytes,
                            language=settings.WHISPER_LANGUAGE,
                            detect_language=False
                        )
                        
                        # Call callback if set
                        if self.on_transcription and result.text:
                            self.on_transcription(result)
                    
                    except Exception as e:
                        logger.error(f"Transcription error: {e}")
                
                await asyncio.sleep(0.05)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Transcription processing error: {e}")
    
    async def _process_synthesis(self) -> None:
        """Process text for synthesis."""
        while self.is_running:
            try:
                # Check for text to synthesize
                if not self.output_buffer:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get text
                text = self.output_buffer.popleft()
                
                # Synthesize
                from app.voice.base import SynthesisRequest, AudioFormat
                
                request = SynthesisRequest(
                    text=text,
                    format=AudioFormat.WAV
                )
                
                result = await tts_service.synthesize(request)
                
                # Call callback if set
                if self.on_synthesis:
                    self.on_synthesis(result.audio_data)
                
                await asyncio.sleep(0.05)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Synthesis processing error: {e}")
    
    async def stream_transcription(
        self,
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """Stream transcription from audio stream."""
        async for audio_chunk in audio_stream:
            try:
                result = await whisper_service.transcribe(audio_chunk)
                yield result
            except Exception as e:
                logger.error(f"Stream transcription error: {e}")
    
    async def stream_synthesis(
        self,
        text_stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesis from text stream."""
        async for text in text_stream:
            try:
                from app.voice.base import SynthesisRequest, AudioFormat
                
                request = SynthesisRequest(
                    text=text,
                    format=AudioFormat.WAV
                )
                
                result = await tts_service.synthesize(request)
                yield result.audio_data
            
            except Exception as e:
                logger.error(f"Stream synthesis error: {e}")
    
    def set_mode(self, mode: str) -> None:
        """Set conversation mode."""
        self.mode = mode
        logger.info(f"Conversation mode set to: {mode}")
    
    def clear_buffers(self) -> None:
        """Clear audio buffers."""
        self.input_buffer.clear()
        self.output_buffer.clear()
        logger.info("Audio buffers cleared")
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """Get status of audio buffers."""
        return {
            "input_buffer_size": len(self.input_buffer),
            "output_buffer_size": len(self.output_buffer),
            "input_buffer_duration": len(self.input_buffer) / self.sample_rate,
            "is_running": self.is_running,
            "is_speaking": self.is_speaking,
            "mode": self.mode
        }


# Global streaming audio pipeline instance
streaming_audio_pipeline = StreamingAudioPipeline()
