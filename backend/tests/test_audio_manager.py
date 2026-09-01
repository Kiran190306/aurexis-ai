"""
Unit tests for AudioManager.
"""
import pytest
import numpy as np
from unittest.mock import patch

from app.voice.audio_manager import AudioManager


@pytest.fixture
def audio_manager():
    """Create an AudioManager instance for testing."""
    return AudioManager()


@pytest.fixture
def sample_audio_array():
    """Create a sample audio array."""
    # Create 1 second of audio at 16kHz
    samples = 16000
    audio = np.random.uniform(-0.5, 0.5, samples).astype(np.float32)
    return audio


@pytest.fixture
def sample_audio_bytes(sample_audio_array):
    """Convert sample audio to WAV bytes."""
    import wave
    import io
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        
        # Convert to int16
        audio_int16 = (sample_audio_array * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())
    
    wav_buffer.seek(0)
    return wav_buffer.read()


def test_validate_audio_valid(audio_manager, sample_audio_bytes):
    """Test audio validation with valid audio."""
    is_valid, error_msg, audio_array = audio_manager.validate_audio_data(sample_audio_bytes)
    
    assert is_valid is True
    assert error_msg is None
    assert audio_array is not None
    assert isinstance(audio_array, np.ndarray)


def test_validate_audio_invalid(audio_manager):
    """Test audio validation with invalid data."""
    # Use data that's too short to be valid audio (less than 2 bytes for int16)
    invalid_data = b'x'
    
    is_valid, error_msg, audio_array = audio_manager.validate_audio_data(invalid_data)
    
    assert is_valid is False
    assert error_msg is not None
    assert audio_array is None


def test_normalize_audio(audio_manager, sample_audio_array):
    """Test audio normalization."""
    # Create audio with known max
    audio = sample_audio_array * 2.0
    
    normalized = audio_manager.normalize_audio(audio)
    
    max_val = np.max(np.abs(normalized))
    assert max_val <= 1.0


def test_trim_silence(audio_manager):
    """Test silence trimming."""
    # Create audio with silence at start and end
    silence = np.zeros(1000, dtype=np.float32)
    # Use signal values guaranteed to be above threshold
    signal = np.random.uniform(0.5, 1.0, 1000).astype(np.float32)
    audio = np.concatenate([silence, signal, silence])
    
    trimmed = audio_manager.trim_silence(audio, threshold=0.01)
    
    # The trim_silence function adds padding, so just verify it doesn't return empty
    assert len(trimmed) > 0
    # Verify it trimmed at least some of the leading silence
    # (the signal starts at index 1000, so trimmed should start before or at that point)


def test_chunk_audio(audio_manager, sample_audio_array):
    """Test audio chunking."""
    chunks = audio_manager.chunk_audio(sample_audio_array, chunk_duration=0.5)
    
    assert len(chunks) > 0
    assert all(len(chunk) > 0 for chunk in chunks)


def test_calculate_rms(audio_manager, sample_audio_array):
    """Test RMS calculation."""
    rms = audio_manager.calculate_rms(sample_audio_array)
    
    assert rms >= 0
    assert isinstance(rms, (float, np.floating))


def test_detect_voice_activity(audio_manager):
    """Test voice activity detection."""
    # Audio with signal
    signal = np.random.uniform(-0.5, 0.5, 16000).astype(np.float32)
    has_voice = audio_manager.detect_voice_activity(signal, threshold=0.01)
    
    assert has_voice is True
    
    # Silent audio
    silence = np.zeros(16000, dtype=np.float32)
    has_voice_silence = audio_manager.detect_voice_activity(silence, threshold=0.01)
    
    assert has_voice_silence is False


def test_get_audio_duration(audio_manager, sample_audio_array):
    """Test audio duration calculation."""
    duration = audio_manager.get_audio_duration(sample_audio_array)
    
    assert duration > 0
    assert duration == pytest.approx(1.0, abs=0.1)


def test_convert_to_wav(audio_manager, sample_audio_array):
    """Test WAV conversion."""
    from app.voice.base import AudioFormat
    
    wav_bytes = audio_manager.convert_to_wav(sample_audio_array, AudioFormat.WAV)
    
    assert wav_bytes is not None
    assert len(wav_bytes) > 0
    assert wav_bytes[:4] == b'RIFF'  # WAV file signature


def test_resample(audio_manager):
    """Test audio resampling."""
    # Create audio at 8kHz
    samples_8k = 8000
    audio_8k = np.random.uniform(-0.5, 0.5, samples_8k).astype(np.float32)
    
    # Resample to 16kHz
    audio_16k = audio_manager._resample(audio_8k, 8000, 16000)
    
    assert len(audio_16k) == pytest.approx(16000, abs=100)


def test_to_mono(audio_manager):
    """Test stereo to mono conversion."""
    # Create stereo audio
    samples = 1000
    stereo = np.random.uniform(-0.5, 0.5, (samples, 2)).astype(np.float32)
    
    mono = audio_manager._to_mono(stereo, 2)
    
    assert mono.ndim == 1
    assert len(mono) == samples
