"""
Integration tests for Voice Intelligence System pipeline.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np

from app.voice.audio_manager import audio_manager
from app.voice.whisper_service import whisper_service
from app.voice.tts_service import tts_service
from app.voice.voice_agent import VoiceAgent
from app.voice.streaming_audio_pipeline import streaming_audio_pipeline


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
@pytest.mark.skip(reason="Complex integration test requiring full TTS dependencies - needs refactoring")
async def test_full_voice_pipeline(sample_audio_bytes):
    """Test complete voice pipeline: transcription -> AI response -> synthesis."""
    # Initialize services
    await whisper_service.initialize()
    
    # Mock TTS service if dependencies not available
    try:
        await tts_service.initialize()
        tts_available = True
    except RuntimeError as e:
        if "Piper or pyttsx3 required" in str(e):
            tts_available = False
            # Mock TTS service
            tts_service.synthesize = AsyncMock(return_value=MagicMock(
                audio_data=b'fake_audio',
                format='wav',
                sample_rate=22050,
                duration=1.0,
                voice='mock'
            ))
        else:
            raise
    
    try:
        # Transcribe
        with patch('app.voice.whisper_service.torch'):
            whisper_service.model = MagicMock()
            whisper_service.processor = MagicMock()
            whisper_service.processor.batch_decode.return_value = ["Hello Jarvis"]
            whisper_service.processor.get_decoder_prompt_ids.return_value = [[1, 2]]
            
            transcription = await whisper_service.transcribe(sample_audio_bytes)
            assert transcription.text == "Hello Jarvis"
        
        # Generate AI response
        with patch('app.voice.integration.ai_engine') as mock_ai:
            mock_ai.generate = MagicMock(return_value=MagicMock(content="Hi there!"))
            ai_response = mock_ai.generate("Hello Jarvis")
            assert ai_response.content == "Hi there!"
        
        # Synthesize
        with patch('app.voice.tts_service.piper'):
            tts_service.synthesizer = MagicMock()
            
            from app.voice.base import SynthesisRequest, AudioFormat
            synthesis_request = SynthesisRequest(
                text=ai_response,
                format=AudioFormat.WAV
            )
            
            synthesis_result = await tts_service.synthesize(synthesis_request)
            assert synthesis_result.audio_data is not None
            assert synthesis_result.duration > 0
    
    finally:
        await whisper_service.shutdown()
        await tts_service.shutdown()


@pytest.mark.asyncio
@patch('app.voice.voice_agent.whisper_service')
@patch('app.voice.voice_agent.tts_service')
@pytest.mark.skip(reason="Complex integration test requiring full agent mocking - needs refactoring")
async def test_voice_agent_conversation(mock_tts_service, mock_whisper_service, sample_audio_bytes):
    """Test voice agent conversation flow."""
    from app.agents.base import Task
    
    # Mock whisper service
    mock_whisper_service.initialize = AsyncMock()
    mock_whisper_service.transcribe = AsyncMock(return_value=MagicMock(
        text="What is the weather?",
        language="en",
        confidence=0.9,
        duration=2.0,
        segments=[]
    ))
    mock_whisper_service.shutdown = AsyncMock()
    
    # Mock TTS service
    mock_tts_service.initialize = AsyncMock()
    mock_tts_service.synthesize = AsyncMock(return_value=MagicMock(
        audio_data=b'fake_audio',
        format='wav',
        sample_rate=22050,
        duration=2.5,
        voice='en_US-amy-medium'
    ))
    mock_tts_service.shutdown = AsyncMock()
    
    voice_agent = VoiceAgent()
    
    # Override the services with mocks before initialization
    voice_agent.whisper_service = mock_whisper_service
    voice_agent.tts_service = mock_tts_service
    
    await voice_agent.initialize()
    
    try:
        # Mock AI engine - make it async
        with patch('app.voice.voice_agent.ai_engine') as mock_ai:
            mock_ai.generate = AsyncMock(return_value=MagicMock(content="The weather is sunny."))
            
            task = Task(
                id="test_task",
                task_type="conversation",
                description="Voice conversation test",
                agent_role="tool",
                input_data={
                    "audio_data": sample_audio_bytes,
                    "user_id": 1
                }
            )
            
            response = await voice_agent.execute(task)
            
            assert response.success is True
            assert "user_text" in response.data
            assert "assistant_text" in response.data
    
    finally:
        await voice_agent.shutdown()


@pytest.mark.asyncio
async def test_streaming_audio_pipeline(sample_audio_bytes):
    """Test streaming audio pipeline."""
    await streaming_audio_pipeline.start()
    
    try:
        # Add audio chunk
        await streaming_audio_pipeline.add_audio_chunk(sample_audio_bytes)
        
        # Check buffer status
        status = streaming_audio_pipeline.get_buffer_status()
        assert status["is_running"] is True
        assert status["input_buffer_size"] > 0
        
        # Add text to speak
        await streaming_audio_pipeline.add_text_to_speak("Test message")
        status = streaming_audio_pipeline.get_buffer_status()
        assert status["output_buffer_size"] > 0
    
    finally:
        await streaming_audio_pipeline.stop()


@pytest.mark.asyncio
async def test_audio_processing_chain(sample_audio_bytes):
    """Test audio processing chain: validation -> normalization -> transcription."""
    # Validate
    is_valid, error_msg, audio_array = audio_manager.validate_audio_data(sample_audio_bytes)
    assert is_valid is True
    
    # Normalize
    normalized = audio_manager.normalize_audio(audio_array)
    max_val = np.max(np.abs(normalized))
    assert max_val <= 1.0
    
    # Noise reduction
    denoised = audio_manager.apply_noise_reduction(normalized)
    assert denoised is not None
    
    # Trim silence
    trimmed = audio_manager.trim_silence(denoised)
    assert len(trimmed) <= len(denoised)


@pytest.mark.asyncio
@patch('app.voice.voice_agent.whisper_service')
@patch('app.voice.voice_agent.tts_service')
@pytest.mark.skip(reason="Complex integration test requiring full agent mocking - needs refactoring")
async def test_voice_agent_command_execution(mock_tts_service, mock_whisper_service, sample_audio_bytes):
    """Test voice agent command execution."""
    from app.agents.base import Task
    
    # Mock whisper service
    mock_whisper_service.initialize = AsyncMock()
    mock_whisper_service.transcribe = AsyncMock(return_value=MagicMock(
        text="search for python tutorials",
        language="en",
        confidence=0.9,
        duration=2.0,
        segments=[]
    ))
    mock_whisper_service.shutdown = AsyncMock()
    
    # Mock TTS service
    mock_tts_service.initialize = AsyncMock()
    mock_tts_service.synthesize = AsyncMock(return_value=MagicMock(
        audio_data=b'fake_audio',
        format='wav',
        sample_rate=22050,
        duration=1.0,
        voice='mock'
    ))
    mock_tts_service.shutdown = AsyncMock()
    
    voice_agent = VoiceAgent()
    
    # Override the services with mocks before initialization
    voice_agent.whisper_service = mock_whisper_service
    voice_agent.tts_service = mock_tts_service
    
    await voice_agent.initialize()
    
    try:
        
        task = Task(
            id="test_task",
            task_type="command",
            description="Voice command test",
            agent_role="tool",
            input_data={
                "audio_data": sample_audio_bytes
            }
        )
        
        response = await voice_agent.execute(task)
        
        assert response.success is True
        assert "command" in response.data
        assert response.data["command"]["intent"] == "search"
    
    finally:
        await voice_agent.shutdown()


@pytest.mark.asyncio
async def test_conversation_mode_switching():
    """Test switching between conversation modes."""
    # Test push-to-talk mode
    streaming_audio_pipeline.set_mode("push_to_talk")
    status = streaming_audio_pipeline.get_buffer_status()
    assert status["mode"] == "push_to_talk"
    
    # Test continuous mode
    streaming_audio_pipeline.set_mode("continuous")
    status = streaming_audio_pipeline.get_buffer_status()
    assert status["mode"] == "continuous"
    
    # Test wake word mode
    streaming_audio_pipeline.set_mode("wake_word")
    status = streaming_audio_pipeline.get_buffer_status()
    assert status["mode"] == "wake_word"


@pytest.mark.asyncio
async def test_buffer_management():
    """Test audio buffer management."""
    # Clear buffers
    streaming_audio_pipeline.clear_buffers()
    status = streaming_audio_pipeline.get_buffer_status()
    assert status["input_buffer_size"] == 0
    assert status["output_buffer_size"] == 0
    
    # Add data
    streaming_audio_pipeline.output_buffer.append("test1")
    streaming_audio_pipeline.output_buffer.append("test2")
    status = streaming_audio_pipeline.get_buffer_status()
    assert status["output_buffer_size"] == 2
    
    # Clear again
    streaming_audio_pipeline.clear_buffers()
    status = streaming_audio_pipeline.get_buffer_status()
    assert status["output_buffer_size"] == 0
