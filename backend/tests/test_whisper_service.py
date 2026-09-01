"""
Unit tests for WhisperService.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np

from app.voice.whisper_service import WhisperService
from app.voice.base import TranscriptionResult


@pytest.fixture
def whisper_service():
    """Create a WhisperService instance for testing."""
    return WhisperService()


@pytest.fixture
def sample_audio_array():
    """Create a sample audio array."""
    samples = 16000  # 1 second at 16kHz
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
@patch('app.voice.whisper_service.WhisperProcessor')
@patch('app.voice.whisper_service.WhisperForConditionalGeneration')
async def test_initialize(mock_model_class, mock_processor_class, whisper_service):
    """Test Whisper service initialization."""
    mock_processor = MagicMock()
    mock_processor_class.from_pretrained.return_value = mock_processor
    
    mock_model = MagicMock()
    mock_model_class.from_pretrained.return_value = mock_model
    
    await whisper_service.initialize()
    
    assert whisper_service.model is not None
    assert whisper_service.processor is not None


@pytest.mark.asyncio
async def test_shutdown(whisper_service):
    """Test Whisper service shutdown."""
    whisper_service.model = MagicMock()
    whisper_service.processor = MagicMock()
    
    await whisper_service.shutdown()
    
    assert whisper_service.model is None
    assert whisper_service.processor is None


@pytest.mark.asyncio
async def test_transcribe(whisper_service, sample_audio_bytes):
    """Test audio transcription."""
    # Mock model and processor
    whisper_service.model = MagicMock()
    whisper_service.processor = MagicMock()
    
    # Mock processor output
    mock_input_features = MagicMock()
    whisper_service.processor.return_value = mock_input_features
    whisper_service.processor.get_decoder_prompt_ids.return_value = [[1, 2]]
    
    # Mock model generation
    mock_predicted_ids = MagicMock()
    whisper_service.model.generate.return_value = mock_predicted_ids
    
    # Mock decode
    whisper_service.processor.batch_decode.return_value = ["Hello world"]
    
    result = await whisper_service.transcribe(sample_audio_bytes, language="en", detect_language=False)
    
    assert isinstance(result, TranscriptionResult)
    assert result.text == "Hello world"
    assert result.language == "en"
    assert result.confidence > 0
    assert result.duration > 0


@pytest.mark.asyncio
async def test_transcribe_stream(whisper_service, sample_audio_bytes):
    """Test streaming transcription."""
    whisper_service.model = MagicMock()
    whisper_service.processor = MagicMock()
    
    # Mock transcribe as async
    whisper_service.transcribe = AsyncMock(return_value=TranscriptionResult(
        text="Hello",
        language="en",
        confidence=0.9,
        duration=1.0,
        partial=True
    ))
    
    results = []
    async for result in whisper_service.transcribe_stream(sample_audio_bytes, chunk_duration=0.5):
        results.append(result)
    
    assert len(results) > 0


def test_detect_language(whisper_service):
    """Test language detection."""
    audio = np.random.uniform(-0.5, 0.5, 16000).astype(np.float32)
    
    language = whisper_service._detect_language(audio)
    
    assert language is not None
    assert isinstance(language, str)


def test_calculate_confidence(whisper_service):
    """Test confidence calculation."""
    audio = np.random.uniform(-0.5, 0.5, 16000).astype(np.float32)
    transcription = "Hello world"
    
    confidence = whisper_service._calculate_confidence(audio, transcription)
    
    assert 0.0 <= confidence <= 1.0


def test_extract_segments(whisper_service):
    """Test segment extraction."""
    transcription = "Hello world test"
    duration = 3.0
    
    segments = whisper_service._extract_segments(transcription, duration)
    
    assert len(segments) == 3
    assert all('text' in seg for seg in segments)
    assert all('start' in seg for seg in segments)
    assert all('end' in seg for seg in segments)


@pytest.mark.asyncio
async def test_get_supported_languages(whisper_service):
    """Test getting supported languages."""
    languages = await whisper_service.get_supported_languages()
    
    assert isinstance(languages, list)
    assert len(languages) > 0
    assert 'en' in languages


def test_is_initialized(whisper_service):
    """Test initialization check."""
    assert whisper_service.is_initialized() is False
    
    whisper_service.model = MagicMock()
    assert whisper_service.is_initialized() is True
