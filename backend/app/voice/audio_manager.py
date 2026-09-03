"""
AudioManager - Core audio processing and device management.
"""
from typing import Optional, List, Dict, Any, AsyncGenerator
import numpy as np
import io
from loguru import logger
from pathlib import Path

from app.core.config import settings
from app.voice.base import AudioFormat, AudioDeviceInfo


class AudioManager:
    """Core manager for audio processing and device management."""
    
    def __init__(self) -> None:
        self.sample_rate = settings.WHISPER_SAMPLE_RATE
        self.channels = 1  # Mono for speech
        self.bit_depth = 16
        self.chunk_size = 1024
        
        # Audio format mappings
        self.format_map = {
            AudioFormat.WAV: 'wav',
            AudioFormat.MP3: 'mp3',
            AudioFormat.OGG: 'ogg',
            AudioFormat.FLAC: 'flac',
            AudioFormat.PCM: 'pcm'
        }
        
        logger.info(f"AudioManager initialized with sample_rate={self.sample_rate}")
    
    def validate_audio_data(self, audio_data: bytes) -> tuple[bool, Optional[str], Optional[np.ndarray]]:
        """Validate and convert audio data to numpy array."""
        try:
            # Try to load audio data
            import wave
            
            # Check if it's WAV format
            try:
                audio_file = io.BytesIO(audio_data)
                with wave.open(audio_file, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    audio_bytes = wav_file.readframes(frames)
                    
                    # Convert to numpy array
                    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                    
                    # Convert to float and normalize
                    audio_float = audio_array.astype(np.float32) / 32768.0  # type: ignore[attr-defined]
                    
                    # Resample if necessary
                    if sample_rate != self.sample_rate:
                        audio_float = self._resample(audio_float, sample_rate, self.sample_rate)
                    
                    # Convert to mono if stereo
                    if channels > 1:
                        audio_float = self._to_mono(audio_float, channels)
                    
                    return True, None, audio_float
            
            except Exception as wav_error:
                # Try raw PCM
                try:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    audio_float = audio_array.astype(np.float32) / 32768.0  # type: ignore[attr-defined]
                    return True, None, audio_float
                except Exception as pcm_error:
                    return False, f"Unable to parse audio data: {pcm_error}", None
        
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False, str(e), None
    
    def _resample(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        from scipy import signal
        
        number_of_samples = round(len(audio) * float(to_rate) / from_rate)
        resampled = signal.resample(audio, number_of_samples)
        return resampled  # type: ignore[no-any-return]
    
    def _to_mono(self, audio: np.ndarray, channels: int) -> np.ndarray:
        """Convert multi-channel audio to mono."""
        if channels == 1:
            return audio
        
        # Reshape and average channels
        reshaped = audio.reshape(-1, channels)
        mono = np.mean(reshaped, axis=1)
        return mono  # type: ignore[no-any-return]
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def apply_noise_reduction(self, audio: np.ndarray) -> np.ndarray:
        """Apply basic noise reduction."""
        # Simple high-pass filter to remove low-frequency noise
        from scipy import signal
        
        # Design high-pass filter
        nyquist = 0.5 * self.sample_rate
        cutoff = 80  # Remove frequencies below 80Hz
        b, a = signal.butter(4, cutoff / nyquist, btype='high')
        
        filtered = signal.filtfilt(b, a, audio)
        return filtered  # type: ignore[no-any-return]
    
    def trim_silence(self, audio: np.ndarray, threshold: float = 0.02) -> np.ndarray:
        """Trim silence from beginning and end of audio."""
        # Find non-silent regions
        above_threshold = np.abs(audio) > threshold
        
        if not np.any(above_threshold):
            return audio
        
        # Find first and last non-silent samples
        indices = np.where(above_threshold)[0]
        if len(indices) > 0:
            first = indices[0]  # type: ignore[index]
            last = indices[-1]  # type: ignore[index]
        else:
            return audio
        
        # Add small padding
        padding = int(self.sample_rate * 0.1)  # 100ms padding
        first = max(0, first - padding)
        last = min(len(audio), last + padding)
        
        return audio[first:last]
    
    def chunk_audio(self, audio: np.ndarray, chunk_duration: float = 30.0) -> List[np.ndarray]:
        """Split audio into chunks for processing."""
        chunk_samples = int(chunk_duration * self.sample_rate)
        chunks = []
        
        for i in range(0, len(audio), chunk_samples):
            chunk = audio[i:i + chunk_samples]
            if len(chunk) > 0:
                chunks.append(chunk)
        
        return chunks
    
    def convert_to_wav(self, audio: np.ndarray, format: AudioFormat = AudioFormat.WAV) -> bytes:
        """Convert audio array to WAV bytes."""
        import wave
        
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def get_audio_duration(self, audio: np.ndarray) -> float:
        """Get duration of audio in seconds."""
        return len(audio) / self.sample_rate
    
    def calculate_rms(self, audio: np.ndarray) -> float:
        """Calculate RMS (root mean square) of audio."""
        return np.sqrt(np.mean(audio ** 2))  # type: ignore[no-any-return]
    
    def detect_voice_activity(self, audio: np.ndarray, threshold: float = 0.01) -> bool:
        """Detect if audio contains voice activity."""
        rms = self.calculate_rms(audio)
        return bool(rms > threshold)
    
    async def get_input_devices(self) -> List[AudioDeviceInfo]:
        """Get list of available input devices (microphones)."""
        # In production, use sounddevice or pyaudio
        # For now, return mock data
        logger.warning("Input device enumeration not fully implemented")
        return [
            AudioDeviceInfo(
                device_id="default",
                device_name="Default Microphone",
                device_type="input",
                sample_rate=self.sample_rate,
                channels=1,
                is_default=True
            )
        ]
    
    async def get_output_devices(self) -> List[AudioDeviceInfo]:
        """Get list of available output devices (speakers)."""
        # In production, use sounddevice or pyaudio
        # For now, return mock data
        logger.warning("Output device enumeration not fully implemented")
        return [
            AudioDeviceInfo(
                device_id="default",
                device_name="Default Speaker",
                device_type="output",
                sample_rate=22050,
                channels=2,
                is_default=True
            )
        ]
    
    async def record_audio(
        self,
        duration: float,
        device_id: Optional[str] = None
    ) -> np.ndarray:
        """Record audio from microphone."""
        # In production, use sounddevice or pyaudio
        # For now, return silent audio
        logger.warning("Audio recording not fully implemented - returning silent audio")
        samples = int(duration * self.sample_rate)
        return np.zeros(samples, dtype=np.float32)
    
    async def play_audio(
        self,
        audio: np.ndarray,
        device_id: Optional[str] = None
    ) -> None:
        """Play audio through speaker."""
        # In production, use sounddevice or pyaudio
        logger.warning("Audio playback not fully implemented")
        pass


# Lazy-loaded audio manager instance
_audio_manager = None


def get_audio_manager():
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


# Backward compatibility
audio_manager = property(lambda: get_audio_manager())
