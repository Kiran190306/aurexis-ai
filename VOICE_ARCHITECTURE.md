# Voice Intelligence System Architecture

## Overview

The Voice Intelligence System (EPIC-013) enables Jarvis AI to communicate naturally using speech in real time. This production-grade system provides comprehensive speech-to-text, text-to-speech, wake word detection, and full-duplex voice conversation capabilities.

## Architecture Principles

- **Modular Design**: Separate services for audio management, STT, TTS, wake word detection, and streaming
- **Async Processing**: All operations are asynchronous for non-blocking execution
- **Multi-Agent Integration**: Voice capabilities integrated with the multi-agent system via VoiceAgent
- **Real-time Streaming**: Support for streaming audio processing and synthesis
- **Production-Grade**: Comprehensive error handling, validation, and logging
- **Backward Compatibility**: Maintains compatibility with existing Jarvis AI architecture

## System Components

### 1. AudioManager (`app/voice/audio_manager.py`)

**Purpose**: Core manager for audio processing and device management.

**Responsibilities**:
- Audio validation and format conversion
- Audio preprocessing (normalization, noise reduction, silence trimming)
- Audio chunking for streaming
- Device enumeration (microphones, speakers)
- Audio recording and playback
- Voice activity detection

**Key Methods**:
- `validate_audio_data()`: Validate audio format and convert to numpy array
- `normalize_audio()`: Normalize audio to [-1, 1] range
- `apply_noise_reduction()`: Apply high-pass filter for noise reduction
- `trim_silence()`: Remove silence from audio
- `chunk_audio()`: Split audio into chunks for processing
- `convert_to_wav()`: Convert audio array to WAV bytes
- `detect_voice_activity()`: Detect if audio contains speech
- `get_input_devices()`: Enumerate available microphones
- `get_output_devices()`: Enumerate available speakers

**Supported Formats**: WAV, MP3, OGG, FLAC, PCM

**Configuration**:
- Sample rate: 16kHz (configurable)
- Channels: 1 (mono)
- Bit depth: 16-bit

### 2. WhisperService (`app/voice/whisper_service.py`)

**Purpose**: Speech-to-text using OpenAI Whisper model.

**Responsibilities**:
- Audio transcription with high accuracy
- Multi-language support (99 languages)
- Streaming transcription with partial results
- Language detection
- Word-level timestamps
- Confidence scoring

**Key Methods**:
- `initialize()`: Load Whisper model
- `transcribe()`: Transcribe audio to text
- `transcribe_stream()`: Stream transcription with partial results
- `get_supported_languages()`: List supported languages

**Supported Models**:
- tiny (fastest, lowest accuracy)
- base (balanced)
- small (better accuracy)
- medium (high accuracy)
- large (best accuracy, slowest)

**Configuration**:
- `WHISPER_MODEL`: Model size (default: base)
- `WHISPER_DEVICE`: CPU or GPU
- `WHISPER_SAMPLE_RATE`: 16kHz
- `WHISPER_LANGUAGE`: Default language or auto-detect

### 3. TTSService (`app/voice/tts_service.py`)

**Purpose**: Text-to-speech using Piper TTS.

**Responsibilities**:
- High-quality speech synthesis
- Multiple voice profiles
- Adjustable speed and pitch
- Streaming synthesis support
- Voice profile management

**Key Methods**:
- `initialize()`: Load TTS model
- `synthesize()`: Convert text to speech
- `synthesize_stream()`: Stream synthesis
- `get_available_voices()`: List available voices
- `estimate_duration()`: Estimate speech duration

**Supported Voices**:
- Amy (Female, US English)
- Dave (Male, US English)
- Emma (Female, UK English)
- Additional voices available via Piper

**Configuration**:
- `TTS_VOICE`: Default voice profile
- `TTS_SPEED`: Speech speed multiplier (default: 1.0)
- `TTS_PITCH`: Pitch multiplier (default: 1.0)
- `TTS_SAMPLE_RATE`: 22.05kHz

### 4. WakeWordService (`app/voice/wake_word_service.py`)

**Purpose**: Wake phrase detection using Porcupine.

**Responsibilities**:
- Low-CPU wake word detection
- Configurable wake phrases
- Sensitivity adjustment
- Background listening
- Callback-based detection

**Key Methods**:
- `initialize()`: Load wake word detector
- `start_listening()`: Start background listening
- `stop_listening()`: Stop listening
- `detect_in_audio()`: Detect wake word in audio
- `set_wake_phrase()`: Set custom wake phrase
- `set_sensitivity()`: Adjust detection sensitivity

**Default Wake Phrase**: "Hey Jarvis"

**Configuration**:
- `WAKE_WORD_ENABLED`: Enable/disable wake word
- `WAKE_WORD_PHRASE`: Custom wake phrase
- `WAKE_WORD_SENSITIVITY`: Detection threshold (0.0-1.0)
- `WAKE_WORD_MODEL`: Detection model (porcupine)

### 5. VoiceAgent (`app/voice/voice_agent.py`)

**Purpose**: Multi-agent integration for voice conversations.

**Responsibilities**:
- Integrate voice capabilities with multi-agent system
- Handle voice conversations with AI
- Execute voice commands
- Route to Planner Agent for complex tasks
- Update Memory Agent with conversation history
- Execute tools via voice commands

**Capabilities**:
- `speech_to_text`: Transcribe audio
- `text_to_speech`: Synthesize speech
- `voice_conversation`: Full voice chat
- `command_execution`: Execute voice commands
- `wake_word_detection`: Detect wake phrases

### 6. StreamingAudioPipeline (`app/voice/streaming_audio_pipeline.py`)

**Purpose**: Real-time streaming audio processing for full-duplex conversations.

**Responsibilities**:
- Real-time audio streaming
- Buffer management
- Conversation mode switching
- Callback-based event handling
- Concurrent transcription and synthesis

**Key Methods**:
- `start()`: Start streaming pipeline
- `stop()`: Stop streaming pipeline
- `add_audio_chunk()`: Add audio to input buffer
- `add_text_to_speak()`: Add text to synthesis queue
- `stream_transcription()`: Stream transcription
- `stream_synthesis()`: Stream synthesis
- `set_mode()`: Switch conversation mode
- `get_buffer_status()`: Get buffer status

**Conversation Modes**:
- `push_to_talk`: Manual activation
- `continuous`: Always listening
- `wake_word`: Activate on wake phrase

## Database Schema

### VoiceConversation

Stores voice conversation sessions.

**Fields**:
- `id`, `uuid`, `user_id`
- `mode`: Conversation mode (push_to_talk, continuous, wake_word)
- `status`: active, paused, completed, failed
- `voice_profile`, `language`, `speed`, `pitch`
- `message_count`, `total_audio_duration`
- `total_transcription_time`, `total_synthesis_time`
- `metadata_json`
- `started_at`, `ended_at`, `created_at`, `updated_at`

### VoiceMessage

Stores individual messages in voice conversations.

**Fields**:
- `id`, `conversation_id`
- `role`: user, assistant
- `text`: Message text
- `audio_data`, `audio_duration`, `audio_format`
- `transcription_confidence`, `detected_language`
- `synthesis_voice`, `synthesis_duration`
- `transcription_time`, `synthesis_time`
- `metadata_json`
- `created_at`

### VoiceSettings

Stores user voice preferences.

**Fields**:
- `id`, `user_id`
- `voice_profile`, `speed`, `pitch`
- `language`, `detect_language`
- `wake_word_enabled`, `wake_word_phrase`, `wake_word_sensitivity`
- `input_device_id`, `output_device_id`
- `default_mode`
- `save_recordings`, `auto_transcribe`
- `created_at`, `updated_at`

## API Endpoints

### POST /api/v1/voice/transcribe

Transcribe audio to text using Whisper.

**Request**:
- `file`: Audio file (multipart/form-data)
- `language`: Language code (optional, e.g., 'en', 'es')
- `detect_language`: Auto-detect language (default: true)
- `stream`: Enable streaming (default: false)

**Response**: TranscriptionResponse

### POST /api/v1/voice/speak

Synthesize text to speech using TTS.

**Request**:
- `text`: Text to synthesize (query parameter)
- `voice`: Voice profile (optional)
- `speed`: Speed multiplier (optional)
- `pitch`: Pitch multiplier (optional)
- `format`: Output format (default: wav)

**Response**: SynthesisResponse

### POST /api/v1/voice/chat

Handle voice conversation with AI.

**Request**:
- `file`: Audio file (multipart/form-data, optional)
- `text`: Text input (optional, alternative to audio)
- `conversation_id`: Existing conversation ID (optional)
- `voice`: Voice for response (optional)
- `mode`: Conversation mode (default: push_to_talk)

**Response**: ChatResponse

### GET /api/v1/voice/history

Get voice conversation history for current user.

**Query Parameters**:
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 100)

**Response**: List of VoiceConversationResponse

### GET /api/v1/voice/history/{conversation_uuid}

Get specific voice conversation with messages.

**Response**: Conversation with messages

### GET /api/v1/voice/settings

Get voice settings for current user.

**Response**: VoiceSettingsResponse

### PATCH /api/v1/voice/settings

Update voice settings for current user.

**Request**: Partial VoiceSettingsResponse

**Response**: Updated VoiceSettingsResponse

## Frontend Integration

### React Hooks (`services/voice-hooks.ts`)

- `useTranscribe()`: Transcribe audio
- `useSynthesize()`: Synthesize speech
- `useVoiceChat()`: Voice conversation
- `useVoiceHistory()`: Get conversation history
- `useVoiceSettings()`: Get voice settings
- `useUpdateVoiceSettings()`: Update voice settings

### Voice Page (`pages/VoicePage.tsx`)

Main page for voice operations with tabs:
- **Voice Chat**: Real-time voice conversation with waveform visualization
- **Transcribe**: Upload audio files for transcription
- **Speak**: Text-to-speech with voice selection and controls
- **History**: View past voice conversations
- **Settings**: Configure voice preferences

### Components

- **Voice Button**: Push-to-talk microphone button with recording indicator
- **Waveform Visualization**: Real-time audio waveform display
- **Microphone Selector**: Select input device (integrated with browser API)
- **Speaker Selector**: Select output device (integrated with browser API)
- **Transcript View**: Display transcription results with confidence
- **Voice Settings**: Comprehensive settings panel with all options
- **History Tab**: Display conversation history with status

## Desktop Integration

### Microphone Permissions

Uses Electron's `navigator.mediaDevices.getUserMedia()` API for microphone access. Permissions are requested on first use and can be managed in system settings.

### Speaker Permissions

Uses Web Audio API for audio playback. No special permissions required.

### Background Listening

Implemented via Electron's background process capabilities. Wake word detection runs in background when enabled.

### Push-to-Talk Shortcut

Configurable global keyboard shortcut (default: Cmd/Ctrl+Shift+V) for quick voice activation.

## Processing Pipeline

### Voice Chat Pipeline

```
1. User speaks (microphone input)
   ↓
2. Audio validation and preprocessing
   ↓
3. Whisper transcription (STT)
   ↓
4. AI response generation
   ↓
5. Piper synthesis (TTS)
   ↓
6. Audio playback (speaker output)
   ↓
7. Store conversation in database
```

### Streaming Pipeline

```
1. Audio chunks received
   ↓
2. Input buffer (deque)
   ↓
3. Voice activity detection
   ↓
4. Real-time transcription
   ↓
5. AI response generation
   ↓
6. Synthesis queue
   ↓
7. Streaming audio output
```

### Wake Word Pipeline

```
1. Background audio capture
   ↓
2. Porcupine detection
   ↓
3. Wake phrase match
   ↓
4. Activation callback
   ↓
5. Start voice conversation
```

## Performance Considerations

### Latency Targets

- Audio validation: < 100ms
- Audio preprocessing: < 500ms
- Whisper transcription: 2-5 seconds (depends on model)
- Piper synthesis: 1-3 seconds
- End-to-end latency: < 10 seconds

### Optimization Tips

- Use appropriate Whisper model (base for balance, tiny for speed)
- Enable streaming for real-time feedback
- Use wake word for hands-free activation
- Adjust TTS speed for faster responses
- Use push-to-talk for precise control

### Resource Usage

- Whisper base model: ~150MB RAM
- Piper voice model: ~50MB RAM
- Wake word detection: ~10MB RAM
- Total idle usage: < 5% CPU
- Peak usage during processing: 30-50% CPU

## Security Considerations

### Audio Privacy

- Audio recordings stored only if enabled in settings
- Transcriptions stored in database
- Option to delete recordings after processing
- User-scoped conversation history

### Permission Validation

- Microphone access requires user consent
- Voice settings scoped to user
- API endpoints require authentication
- Wake word detection respects privacy settings

### Data Protection

- Audio data encrypted at rest
- Transcriptions encrypted in database
- Secure API communication
- GDPR compliance options

## Deployment Guide

### Prerequisites

**System Dependencies**:
- Python 3.9+
- PyTorch (for Whisper)
- Piper TTS
- Porcupine (for wake word)
- sounddevice (for audio I/O)

**Python Packages**:
```
torch
transformers
piper-tts
pvporcupine
sounddevice
scipy
numpy
```

### Installation

1. **Install PyTorch**:
   ```bash
   pip install torch
   ```

2. **Install Whisper dependencies**:
   ```bash
   pip install transformers
   ```

3. **Install Piper TTS**:
   ```bash
   pip install piper-tts
   ```

4. **Install Porcupine** (optional, for wake word):
   ```bash
   pip install pvporcupine
   ```

5. **Install audio libraries**:
   ```bash
   pip install sounddevice scipy numpy
   ```

6. **Configure environment variables**:
   ```bash
   WHISPER_MODEL=base
   WHISPER_DEVICE=cpu
   TTS_VOICE=en_US-amy-medium
   WAKE_WORD_ENABLED=true
   WAKE_WORD_PHRASE="hey jarvis"
   ENABLE_VOICE=true
   ```

7. **Run database migrations**:
   ```bash
   alembic revision --autogenerate -m "Add voice tables"
   alembic upgrade head
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Download models on first run
RUN python -c "from transformers import WhisperProcessor; WhisperProcessor.from_pretrained('openai/whisper-base')"

# Set environment variables
ENV WHISPER_MODEL=base
ENV WHISPER_DEVICE=cpu
ENV ENABLE_VOICE=true

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

**Whisper model not found**:
- Verify transformers installation: `pip show transformers`
- Check internet connection for model download
- Set `WHISPER_MODEL` to available model

**TTS not working**:
- Verify Piper installation: `pip show piper-tts`
- Check voice model is downloaded
- Verify audio device is available

**Wake word not detecting**:
- Verify Porcupine installation and access key
- Check microphone access permissions
- Adjust sensitivity setting
- Verify wake phrase matches exactly

**Audio recording fails**:
- Check microphone permissions in system settings
- Verify audio device is not in use
- Check sounddevice installation
- Test with simple recording script

**High latency**:
- Use smaller Whisper model (tiny or base)
- Enable GPU if available
- Reduce audio chunk size
- Use streaming mode

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("app.voice").setLevel(logging.DEBUG)
```

## Testing

### Unit Tests
```bash
pytest tests/test_audio_manager.py
pytest tests/test_whisper_service.py
```

### Integration Tests
```bash
pytest tests/test_voice_integration.py
```

### Latency Tests
```bash
pytest tests/test_voice_latency.py
```

### Audio Pipeline Tests
```bash
pytest tests/test_audio_pipeline.py
```

### Test Coverage
- AudioManager: Audio validation, processing, device management
- WhisperService: Transcription, streaming, language detection
- TTSService: Synthesis, voice profiles, streaming
- WakeWordService: Detection, sensitivity, background listening
- VoiceAgent: Conversation, commands, multi-agent integration
- StreamingAudioPipeline: Buffer management, streaming, callbacks

## Future Enhancements

### Planned Features
- GPT-4 Audio integration for advanced understanding
- Real-time voice activity detection
- Emotion detection in speech
- Voice cloning capabilities
- Multi-language wake words
- Advanced noise cancellation
- Voice biometrics for authentication
- Meeting transcription and summarization
- Real-time translation
- Voice command macros

### Optimization Opportunities
- GPU acceleration for Whisper
- Model quantization for faster inference
- Distributed processing for large batches
- Result caching with Redis
- Progressive audio loading
- WebAssembly for browser-based processing

## Backward Compatibility

The Voice Intelligence System maintains backward compatibility:
- Existing Jarvis AI features unchanged
- Voice features opt-in via feature flag
- No breaking changes to existing APIs
- Database migrations additive only
- Frontend routes added without modifying existing navigation

## Contributing

### Adding New Voice Capabilities

1. Extend voice service with new functionality
2. Add API endpoint if needed
3. Update database schema if required
4. Add frontend UI components
5. Write tests
6. Update documentation

### Adding New TTS Voices

1. Download voice model from Piper
2. Add to voice profiles in TTSService
3. Update voice settings UI
4. Test voice quality

## License

This Voice Intelligence System is part of Jarvis AI v1.1 and follows the same license terms.

## Contact

For questions or issues related to the Voice Intelligence System, please refer to the main project documentation or contact the development team.
