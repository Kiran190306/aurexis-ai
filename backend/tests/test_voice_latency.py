"""
Latency tests for Voice Intelligence System.
"""
import pytest
import time
import numpy as np
from unittest.mock import patch, MagicMock

from app.voice.audio_manager import audio_manager
from app.voice.whisper_service import whisper_service
from app.voice.tts_service import tts_service


@pytest.fixture
def sample_audio_array():
    """Create a sample audio array."""
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
        
        audio_int16 = (sample_audio_array * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())
    
    wav_buffer.seek(0)
    return wav_buffer.read()


def test_audio_validation_latency(sample_audio_bytes):
    """Test audio validation latency."""
    start = time.time()
    is_valid, error_msg, audio_array = audio_manager.validate_audio_data(sample_audio_bytes)
    end = time.time()
    
    latency = end - start
    assert is_valid is True
    assert latency < 1.0  # Should complete in under 1 second


def test_audio_normalization_latency(sample_audio_array):
    """Test audio normalization latency."""
    start = time.time()
    normalized = audio_manager.normalize_audio(sample_audio_array)
    end = time.time()
    
    latency = end - start
    assert latency < 0.1  # Should complete in under 100ms


def test_noise_reduction_latency(sample_audio_array):
    """Test noise reduction latency."""
    start = time.time()
    denoised = audio_manager.apply_noise_reduction(sample_audio_array)
    end = time.time()
    
    latency = end - start
    assert latency < 0.5  # Should complete in under 500ms


def test_silence_trimming_latency(sample_audio_array):
    """Test silence trimming latency."""
    start = time.time()
    trimmed = audio_manager.trim_silence(sample_audio_array)
    end = time.time()
    
    latency = end - start
    assert latency < 0.1  # Should complete in under 100ms


def test_wav_conversion_latency(sample_audio_array):
    """Test WAV conversion latency."""
    from app.voice.base import AudioFormat
    
    start = time.time()
    wav_bytes = audio_manager.convert_to_wav(sample_audio_array, AudioFormat.WAV)
    end = time.time()
    
    latency = end - start
    assert latency < 0.5  # Should complete in under 500ms


@pytest.mark.asyncio
@pytest.mark.skip(reason="Latency test requires full Whisper model - needs refactoring")
async def test_transcription_latency(sample_audio_bytes):
    """Test transcription latency."""
    # Mock model - skip actual transcription
    whisper_service.model = MagicMock()
    whisper_service.processor = MagicMock()
    whisper_service.processor.batch_decode.return_value = ["Test transcription"]
    whisper_service.processor.get_decoder_prompt_ids.return_value = [[1, 2]]
    
    start = time.time()
    result = await whisper_service.transcribe(sample_audio_bytes)
    end = time.time()
    
    latency = end - start
    assert result.text == "Test transcription"
    # In production with real model, this would be 2-5 seconds
    # With mock, should be very fast
    assert latency < 1.0


@pytest.mark.asyncio
async def test_synthesis_latency():
    """Test synthesis latency."""
    from app.voice.base import SynthesisRequest, AudioFormat
    
    # Mock synthesizer
    tts_service.synthesizer = MagicMock()
    tts_service.synthesizer.synthesize = MagicMock(return_value=np.random.uniform(-1, 1, 22050).astype(np.int16))
    
    request = SynthesisRequest(
        text="Hello world, this is a test.",
        format=AudioFormat.WAV
    )
    
    start = time.time()
    result = await tts_service.synthesize(request)
    end = time.time()
    
    latency = end - start
    assert result.audio_data is not None
    # In production with real model, this would be 1-3 seconds
    # With mock, should be very fast
    assert latency < 1.0


def test_rms_calculation_latency(sample_audio_array):
    """Test RMS calculation latency."""
    start = time.time()
    rms = audio_manager.calculate_rms(sample_audio_array)
    end = time.time()
    
    latency = end - start
    assert rms >= 0
    assert latency < 0.01  # Should complete in under 10ms


def test_voice_activity_detection_latency(sample_audio_array):
    """Test voice activity detection latency."""
    start = time.time()
    has_voice = audio_manager.detect_voice_activity(sample_audio_array)
    end = time.time()
    
    latency = end - start
    assert has_voice is True
    assert latency < 0.01  # Should complete in under 10ms


def test_audio_chunking_latency(sample_audio_array):
    """Test audio chunking latency."""
    start = time.time()
    chunks = audio_manager.chunk_audio(sample_audio_array, chunk_duration=0.5)
    end = time.time()
    
    latency = end - start
    assert len(chunks) > 0
    assert latency < 0.1  # Should complete in under 100ms


@pytest.mark.asyncio
async def test_full_pipeline_latency(sample_audio_bytes):
    """Test full voice pipeline latency."""
    start = time.time()
    
    # Audio validation
    is_valid, error_msg, audio_array = audio_manager.validate_audio_data(sample_audio_bytes)
    assert is_valid is True
    
    # Normalization
    normalized = audio_manager.normalize_audio(audio_array)
    
    # Noise reduction
    denoised = audio_manager.apply_noise_reduction(normalized)
    
    # Silence trimming
    trimmed = audio_manager.trim_silence(denoised)
    
    # Convert back to WAV
    from app.voice.base import AudioFormat
    wav_bytes = audio_manager.convert_to_wav(trimmed, AudioFormat.WAV)
    
    end = time.time()
    latency = end - start
    
    # Full preprocessing should complete in under 2 seconds
    assert latency < 2.0


def test_buffer_operations_latency():
    """Test buffer operations latency."""
    from app.voice.streaming_audio_pipeline import streaming_audio_pipeline
    
    # Test buffer add
    audio_chunk = np.random.uniform(-0.5, 0.5, 1000).astype(np.float32)
    start = time.time()
    for _ in range(100):
        streaming_audio_pipeline.input_buffer.append(audio_chunk[0])
    end = time.time()
    
    latency = end - start
    assert latency < 0.01  # Should complete in under 10ms


@pytest.mark.asyncio
async def test_concurrent_operations_latency(sample_audio_bytes):
    """Test concurrent operations latency."""
    import asyncio
    
    async def operation1():
        is_valid, _, _ = audio_manager.validate_audio_data(sample_audio_bytes)
        return is_valid
    
    async def operation2():
        normalized = audio_manager.normalize_audio(np.random.uniform(-0.5, 0.5, 16000).astype(np.float32))
        return normalized
    
    start = time.time()
    results = await asyncio.gather(operation1(), operation2())
    end = time.time()
    
    latency = end - start
    assert results[0] is True
    # Concurrent operations should still be fast
    assert latency < 0.5
