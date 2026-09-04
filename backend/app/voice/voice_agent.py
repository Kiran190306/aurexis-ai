"""
VoiceAgent - Multi-agent integration for voice conversations.
"""
from typing import Dict, List, Any, Optional
from loguru import logger

from app.agents.base import BaseAgent, AgentRole, Task, AgentResponse
from app.voice.base import VoiceConversation, VoiceMessage
from app.ai.engine import ai_engine
from app.ai.base import Message


class VoiceAgent(BaseAgent):
    """Agent for voice conversations within the multi-agent system."""
    
    def __init__(self, agent_id: str = "voice_agent", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.TOOL
        self.system_prompt = """You are a Voice Agent for Jarvis AI. Your role is to:
1. Process voice input and convert to text
2. Generate appropriate responses
3. Convert responses to speech
4. Maintain conversation context
5. Integrate with Planner Agent for complex tasks
6. Update Memory Agent with conversation history
7. Execute tools via voice commands"""
    
    async def initialize(self) -> None:
        """Initialize the voice agent."""
        logger.info(f"Initializing Voice Agent: {self.agent_id}")
        
        # Lazy import voice services
        from app.voice.whisper_service import get_whisper_service
        from app.voice.tts_service import get_tts_service
        
        whisper_service = get_whisper_service()
        tts_service = get_tts_service()
        
        # Initialize voice services
        if not whisper_service.is_initialized():
            await whisper_service.initialize()
        
        if not tts_service.is_initialized():
            await tts_service.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the voice agent."""
        logger.info(f"Shutting down Voice Agent: {self.agent_id}")
        
        # Lazy import voice services
        from app.voice.whisper_service import get_whisper_service
        from app.voice.tts_service import get_tts_service
        
        whisper_service = get_whisper_service()
        tts_service = get_tts_service()
        
        # Shutdown voice services
        await whisper_service.shutdown()
        await tts_service.shutdown()
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute a voice conversation task."""
        logger.info(f"Voice Agent executing task: {task.id}")
        
        try:
            task_type = task.input_data.get("task_type", "conversation")
            
            if task_type == "transcribe":
                return await self._transcribe(task)
            elif task_type == "synthesize":
                return await self._synthesize(task)
            elif task_type == "conversation":
                return await self._conversation(task)
            elif task_type == "command":
                return await self._execute_command(task)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown task type: {task_type}"
                )
        
        except Exception as e:
            logger.error(f"Voice Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _transcribe(self, task: Task) -> AgentResponse:
        """Transcribe audio to text."""
        try:
            audio_data = task.input_data.get("audio_data")
            language = task.input_data.get("language")
            
            if not audio_data:
                return AgentResponse(
                    success=False,
                    error="No audio data provided"
                )
            
            # Transcribe
            result = await whisper_service.transcribe(
                audio_data,
                language=language,
                detect_language=True
            )
            
            return AgentResponse(
                success=True,
                data={
                    "text": result.text,
                    "language": result.language,
                    "confidence": result.confidence,
                    "duration": result.duration,
                    "segments": result.segments
                }
            )
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _synthesize(self, task: Task) -> AgentResponse:
        """Synthesize text to speech."""
        try:
            text = task.input_data.get("text")
            voice = task.input_data.get("voice")
            speed = task.input_data.get("speed", 1.0)
            pitch = task.input_data.get("pitch", 1.0)
            
            if not text:
                return AgentResponse(
                    success=False,
                    error="No text provided"
                )
            
            from app.voice.base import SynthesisRequest, AudioFormat
            
            request = SynthesisRequest(
                text=text,
                voice=voice,
                speed=speed,
                pitch=pitch,
                format=AudioFormat.WAV
            )
            
            result = await tts_service.synthesize(request)
            
            return AgentResponse(
                success=True,
                data={
                    "audio_data": result.audio_data.hex(),
                    "format": result.format.value,
                    "sample_rate": result.sample_rate,
                    "duration": result.duration,
                    "voice": result.voice
                }
            )
        
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _conversation(self, task: Task) -> AgentResponse:
        """Handle voice conversation."""
        try:
            audio_data = task.input_data.get("audio_data")
            conversation_id = task.input_data.get("conversation_id")
            user_id = task.input_data.get("user_id")
            
            if not audio_data:
                return AgentResponse(
                    success=False,
                    error="No audio data provided"
                )
            
            # Transcribe user input
            transcription = await whisper_service.transcribe(audio_data)
            user_text = transcription.text
            
            # Generate AI response
            messages = [
                Message(role="system", content="You are Jarvis AI, a helpful assistant."),
                Message(role="user", content=user_text)
            ]
            
            ai_response = await ai_engine.generate(messages)
            assistant_text = ai_response.content
            
            # Synthesize response
            from app.voice.base import SynthesisRequest, AudioFormat
            
            synthesis_request = SynthesisRequest(
                text=assistant_text,
                format=AudioFormat.WAV
            )
            
            synthesis_result = await tts_service.synthesize(synthesis_request)
            
            return AgentResponse(
                success=True,
                data={
                    "user_text": user_text,
                    "assistant_text": assistant_text,
                    "audio_data": synthesis_result.audio_data.hex(),
                    "transcription_confidence": transcription.confidence,
                    "conversation_id": conversation_id
                }
            )
        
        except Exception as e:
            logger.error(f"Conversation failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _execute_command(self, task: Task) -> AgentResponse:
        """Execute voice command."""
        try:
            audio_data = task.input_data.get("audio_data")
            
            if not audio_data:
                return AgentResponse(
                    success=False,
                    error="No audio data provided"
                )
            
            # Transcribe command
            transcription = await whisper_service.transcribe(audio_data)
            command_text = transcription.text
            
            # Parse command (simplified)
            # In production, use NLP to extract intent and entities
            command = self._parse_command(command_text)
            
            # Execute via Tool Agent
            # For now, return the parsed command
            return AgentResponse(
                success=True,
                data={
                    "command": command,
                    "original_text": command_text,
                    "confidence": transcription.confidence
                }
            )
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    def _parse_command(self, text: str) -> Dict[str, Any]:
        """Parse command from text."""
        text_lower = text.lower()
        
        # Simple command detection
        if "search" in text_lower:
            return {"intent": "search", "query": text.replace("search", "").strip()}
        elif "open" in text_lower:
            return {"intent": "open", "target": text.replace("open", "").strip()}
        elif "create" in text_lower:
            return {"intent": "create", "content": text.replace("create", "").strip()}
        elif "delete" in text_lower:
            return {"intent": "delete", "target": text.replace("delete", "").strip()}
        else:
            return {"intent": "unknown", "text": text}
    
    def get_capabilities(self) -> List[str]:
        """Return voice agent capabilities."""
        return [
            "speech_to_text",
            "text_to_speech",
            "voice_conversation",
            "command_execution",
            "wake_word_detection"
        ]
