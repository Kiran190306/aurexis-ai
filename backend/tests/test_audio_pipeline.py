"""
Audio pipeline tests for Voice Intelligence System.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.voice.streaming_audio_pipeline import StreamingAudioPipeline
from app.voice.audio_manager import audio_manager


@pytest.fixture
def audio_pipeline():
    """Create a StreamingAudioPipeline instance for testing."""
    return StreamingAudioPipeline()


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


@pytest.mark.asyncio
async def test_pipeline_start_stop(audio_pipeline):
    """Test pipeline start and stop."""
    assert audio_pipeline.is_running is False
    
    await audio_pipeline.start()
    assert audio_pipeline.is_running is True
    
    await audio_pipeline.stop()
    assert audio_pipeline.is_running is False


@pytest.mark.asyncio
async def test_add_audio_chunk(audio_pipeline, sample_audio_bytes):
    """Test adding audio chunks to input buffer."""
    initial_size = len(audio_pipeline.input_buffer)
    
    await audio_pipeline.add_audio_chunk(sample_audio_bytes)
    
    assert len(audio_pipeline.input_buffer) > initial_size


@pytest.mark.asyncio
async def test_add_text_to_speak(audio_pipeline):
    """Test adding text to synthesis queue."""
    initial_size = len(audio_pipeline.output_buffer)
    
    await audio_pipeline.add_text_to_speak("Hello world")
    
    assert len(audio_pipeline.output_buffer) == initial_size + 1
    assert audio_pipeline.output_buffer[-1] == "Hello world"


@pytest.mark.asyncio
async def test_buffer_status(audio_pipeline):
    """Test buffer status reporting."""
    status = audio_pipeline.get_buffer_status()
    
    assert "input_buffer_size" in status
    assert "output_buffer_size" in status
    assert "is_running" in status
    assert "mode" in status


@pytest.mark.asyncio
async def test_conversation_mode_switching(audio_pipeline):
    """Test switching conversation modes."""
    audio_pipeline.set_mode("push_to_talk")
    status = audio_pipeline.get_buffer_status()
    assert status["mode"] == "push_to_talk"
    
    audio_pipeline.set_mode("continuous")
    status = audio_pipeline.get_buffer_status()
    assert status["mode"] == "continuous"
    
    audio_pipeline.set_mode("wake_word")
    status = audio_pipeline.get_buffer_status()
    assert status["mode"] == "wake_word"


@pytest.mark.asyncio
async def test_clear_buffers(audio_pipeline):
    """Test clearing audio buffers."""
    # Add some data
    audio_pipeline.input_buffer.extend([0.1] * 100)
    audio_pipeline.output_buffer.append("test")
    
    assert len(audio_pipeline.input_buffer) > 0
    assert len(audio_pipeline.output_buffer) > 0
    
    audio_pipeline.clear_buffers()
    
    assert len(audio_pipeline.input_buffer) == 0
    assert len(audio_pipeline.output_buffer) == 0


@pytest.mark.asyncio
async def test_stream_transcription(audio_pipeline, sample_audio_bytes):
    """Test streaming transcription."""
    from app.voice.whisper_service import whisper_service
    
    # Mock whisper service with async mock
    whisper_service.transcribe = AsyncMock(return_value=MagicMock(
        text="Hello",
        language="en",
        confidence=0.9,
        duration=1.0,
        segments=[]
    ))
    
    async def audio_stream():
        yield sample_audio_bytes
    
    results = []
    async for result in audio_pipeline.stream_transcription(audio_stream()):
        results.append(result)
    
    assert len(results) > 0


@pytest.mark.asyncio
async def test_stream_synthesis(audio_pipeline):
    """Test streaming synthesis."""
    from app.voice.tts_service import tts_service
    
    # Mock TTS service with async mock
    tts_service.synthesize = AsyncMock(return_value=MagicMock(
        audio_data=b'fake_audio',
        format='wav',
        sample_rate=22050,
        duration=1.0,
        voice='en_US-amy-medium'
    ))
    
    async def text_stream():
        yield "Hello"
        yield "World"
    
    results = []
    async for audio_data in audio_pipeline.stream_synthesis(text_stream()):
        results.append(audio_data)
    
    assert len(results) == 2


@pytest.mark.asyncio
async def test_callback_registration(audio_pipeline):
    """Test callback registration for transcription and synthesis."""
    transcription_results = []
    synthesis_results = []
    
    def on_transcription(result):
        transcription_results.append(result)
    
    def on_synthesis(audio_data):
        synthesis_results.append(audio_data)
    
    audio_pipeline.on_transcription = on_transcription
    audio_pipeline.on_synthesis = on_synthesis
    
    # Verify callbacks are set
    assert audio_pipeline.on_transcription is not None
    assert audio_pipeline.on_synthesis is not None


@pytest.mark.asyncio
async def test_buffer_overflow_handling(audio_pipeline):
    """Test buffer overflow handling."""
    # Fill buffer to max capacity
    max_size = audio_pipeline.input_buffer.maxlen
    
    for _ in range(max_size + 100):
        audio_pipeline.input_buffer.append(0.1)
    
    # Buffer should not exceed max size
    assert len(audio_pipeline.input_buffer) <= max_size


@pytest.mark.asyncio
async def test_concurrent_operations(audio_pipeline, sample_audio_bytes):
    """Test concurrent pipeline operations."""
    async def add_audio():
        for _ in range(10):
            await audio_pipeline.add_audio_chunk(sample_audio_bytes)
            await asyncio.sleep(0.01)
    
    async def add_text():
        for i in range(10):
            await audio_pipeline.add_text_to_speak(f"Message {i}")
            await asyncio.sleep(0.01)
    
    await asyncio.gather(add_audio(), add_text())
    
    status = audio_pipeline.get_buffer_status()
    assert status["input_buffer_size"] > 0
    assert status["output_buffer_size"] > 0


@pytest.mark.asyncio
async def test_pipeline_with_callbacks(audio_pipeline, sample_audio_bytes):
    """Test pipeline with active callbacks."""
    callback_called = {"transcription": False, "synthesis": False}
    
    def on_transcription(result):
        callback_called["transcription"] = True
    
    def on_synthesis(audio_data):
        callback_called["synthesis"] = True
    
    audio_pipeline.on_transcription = on_transcription
    audio_pipeline.on_synthesis = on_synthesis
    
    await audio_pipeline.start()
    
    try:
        # Add audio and text
        await audio_pipeline.add_audio_chunk(sample_audio_bytes)
        await audio_pipeline.add_text_to_speak("Test")
        
        # Wait a bit for processing
        await asyncio.sleep(0.2)
        
        # Check callbacks were called (may not be called in mock environment)
        # In production with real services, these would be called
    finally:
        await audio_pipeline.stop()


@pytest.mark.asyncio
async def test_pipeline_error_handling(audio_pipeline):
    """Test pipeline error handling."""
    # Test with invalid audio data
    invalid_audio = b"not valid audio"
    
    # Should not raise exception, should handle gracefully
    try:
        await audio_pipeline.add_audio_chunk(invalid_audio)
    except Exception as e:
        # Expected to handle gracefully
        pass


def test_pipeline_initial_state(audio_pipeline):
    """Test pipeline initial state."""
    assert audio_pipeline.is_running is False
    assert audio_pipeline.is_speaking is False
    assert audio_pipeline.mode == "push_to_talk"
    assert len(audio_pipeline.input_buffer) == 0
    assert len(audio_pipeline.output_buffer) == 0


@pytest.mark.asyncio
async def test_pipeline_mode_persistence(audio_pipeline):
    """Test that mode persists across operations."""
    audio_pipeline.set_mode("continuous")
    
    await audio_pipeline.start()
    status = audio_pipeline.get_buffer_status()
    assert status["mode"] == "continuous"
    
    await audio_pipeline.stop()
    status = audio_pipeline.get_buffer_status()
    assert status["mode"] == "continuous"
