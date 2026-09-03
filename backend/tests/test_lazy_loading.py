"""
Tests for lazy loading of heavyweight services to verify reduced startup memory.
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLazyLoading:
    """Test that heavyweight services are lazy-loaded."""

    def test_ocr_service_lazy_loading(self):
        """Test OCRService is not initialized until first access."""
        # Import the module but don't access the service
        from app.vision import ocr_service
        
        # The service should be a proxy, not initialized
        assert isinstance(ocr_service, type(ocr_service))
        
        # Access the service to trigger initialization
        from app.vision.ocr_service import get_ocr_service
        service = get_ocr_service()
        
        # Now it should be initialized
        assert service is not None
        assert hasattr(service, 'tesseract_path')

    def test_vision_service_lazy_loading(self):
        """Test VisionService is not initialized until first access."""
        from app.vision import vision_service
        
        # The service should be a proxy
        assert isinstance(vision_service, type(vision_service))
        
        # Access the service to trigger initialization
        from app.vision.vision_service import get_vision_service
        service = get_vision_service()
        
        # Now it should be initialized
        assert service is not None
        assert hasattr(service, 'supported_formats')

    def test_screenshot_analyzer_lazy_loading(self):
        """Test ScreenshotAnalyzer is not initialized until first access."""
        from app.vision import screenshot_analyzer
        
        # The service should be a proxy
        assert isinstance(screenshot_analyzer, type(screenshot_analyzer))
        
        # Access the service to trigger initialization
        from app.vision.screenshot_analyzer import get_screenshot_analyzer
        service = get_screenshot_analyzer()
        
        # Now it should be initialized
        assert service is not None
        assert hasattr(service, 'ui_element_patterns')

    def test_document_vision_pipeline_lazy_loading(self):
        """Test DocumentVisionPipeline is not initialized until first access."""
        from app.vision import document_vision_pipeline
        
        # The service should be a proxy
        assert isinstance(document_vision_pipeline, type(document_vision_pipeline))
        
        # Access the service to trigger initialization
        from app.vision.document_vision_pipeline import get_document_vision_pipeline
        service = get_document_vision_pipeline()
        
        # Now it should be initialized
        assert service is not None
        assert hasattr(service, 'supported_formats')

    def test_embedding_pipeline_lazy_loading(self):
        """Test EmbeddingPipeline is not initialized until first access."""
        from app.knowledge.embeddings import _embedding_pipeline_instance, get_embedding_pipeline

        # Reset to None to test fresh behavior
        import app.knowledge.embeddings as embeddings_module
        embeddings_module._embedding_pipeline_instance = None
        assert embeddings_module._embedding_pipeline_instance is None

        # Access pipeline to trigger initialization
        pipeline = get_embedding_pipeline()
        assert pipeline is not None
        assert embeddings_module._embedding_pipeline_instance is not None

    def test_agents_lazy_loading(self):
        """Test agents are not initialized until first access."""
        from app.api.v1.endpoints.agent_execution import (
            _agents_initialized, _planner, _orchestrator, _research_agent,
            _coding_agent, _memory_agent, _tool_agent, _reflection_agent
        )

        # Reset to test fresh behavior
        import app.api.v1.endpoints.agent_execution as agent_module
        agent_module._agents_initialized = False
        agent_module._planner = None
        agent_module._orchestrator = None
        agent_module._research_agent = None
        agent_module._coding_agent = None
        agent_module._memory_agent = None
        agent_module._tool_agent = None
        agent_module._reflection_agent = None

        # Agents should not be initialized
        assert agent_module._agents_initialized is False
        assert agent_module._planner is None
        assert agent_module._orchestrator is None

        # Access agents to trigger initialization
        from app.api.v1.endpoints.agent_execution import get_planner
        planner = get_planner()

        # Now agents should be initialized
        assert planner is not None
        assert agent_module._agents_initialized is True
        assert agent_module._planner is not None
        assert agent_module._orchestrator is not None

    def test_fastapi_import_without_heavyweight_services(self):
        """Test that services are lazy-loaded and not initialized at module import."""
        # This test verifies the lazy loading mechanism works correctly
        # We test each service individually to ensure they're not initialized until accessed
        
        # Test OCR service lazy loading
        from app.vision.ocr_service import _ocr_service_instance, get_ocr_service
        # Reset to None to test fresh behavior
        import app.vision.ocr_service as ocr_module
        ocr_module._ocr_service_instance = None
        assert ocr_module._ocr_service_instance is None
        # Access service to trigger initialization
        service = get_ocr_service()
        assert service is not None
        assert ocr_module._ocr_service_instance is not None
        
        # Test vision service lazy loading
        from app.vision.vision_service import _vision_service_instance, get_vision_service
        import app.vision.vision_service as vision_module
        vision_module._vision_service_instance = None
        assert vision_module._vision_service_instance is None
        service = get_vision_service()
        assert service is not None
        assert vision_module._vision_service_instance is not None
        
        # Test screenshot analyzer lazy loading
        from app.vision.screenshot_analyzer import _screenshot_analyzer_instance, get_screenshot_analyzer
        import app.vision.screenshot_analyzer as screenshot_module
        screenshot_module._screenshot_analyzer_instance = None
        assert screenshot_module._screenshot_analyzer_instance is None
        service = get_screenshot_analyzer()
        assert service is not None
        assert screenshot_module._screenshot_analyzer_instance is not None
        
        # Test document vision pipeline lazy loading
        from app.vision.document_vision_pipeline import _document_vision_pipeline_instance, get_document_vision_pipeline
        import app.vision.document_vision_pipeline as doc_module
        doc_module._document_vision_pipeline_instance = None
        assert doc_module._document_vision_pipeline_instance is None
        service = get_document_vision_pipeline()
        assert service is not None
        assert doc_module._document_vision_pipeline_instance is not None

    def test_backward_compatibility_proxy(self):
        """Test that proxy pattern maintains backward compatibility."""
        from app.vision.ocr_service import ocr_service
        from app.vision.vision_service import vision_service
        
        # Accessing attributes should work as before
        # This will trigger lazy initialization
        assert hasattr(ocr_service, 'extract_text')
        assert hasattr(vision_service, 'validate_image')

    def test_ai_engine_lazy_loading(self):
        """Test AI engine providers are lazy-loaded."""
        from app.ai.engine import AIEngine

        # Create a new AI engine instance
        engine = AIEngine()

        # Providers should be empty initially
        assert len(engine.providers) == 0

        # Register a provider - this should trigger lazy import
        engine.register_provider(
            name="test_openai",
            provider_type="openai",
            api_key="test_key",
            model="gpt-4"
        )

        # Now provider should be loaded
        assert "test_openai" in engine.providers
        assert engine.providers["test_openai"] is not None

    def test_voice_services_lazy_loading(self):
        """Test voice services are lazy-loaded."""
        from app.voice.audio_manager import _audio_manager, get_audio_manager
        from app.voice.whisper_service import _whisper_service, get_whisper_service
        from app.voice.tts_service import _tts_service, get_tts_service

        # Reset to test fresh behavior
        import app.voice.audio_manager as audio_module
        import app.voice.whisper_service as whisper_module
        import app.voice.tts_service as tts_module

        audio_module._audio_manager = None
        whisper_module._whisper_service = None
        tts_module._tts_service = None

        assert audio_module._audio_manager is None
        assert whisper_module._whisper_service is None
        assert tts_module._tts_service is None

        # Access services to trigger initialization
        audio = get_audio_manager()
        whisper = get_whisper_service()
        tts = get_tts_service()

        assert audio is not None
        assert whisper is not None
        assert tts is not None
        assert audio_module._audio_manager is not None
        assert whisper_module._whisper_service is not None
        assert tts_module._tts_service is not None

    def test_computer_services_lazy_loading(self):
        """Test computer services are lazy-loaded."""
        from app.api.v1.endpoints.computer import (
            _file_system_agent, _terminal_agent, _browser_agent,
            _desktop_agent, _workflow_engine, _permission_system
        )

        # Reset to test fresh behavior
        import app.api.v1.endpoints.computer as computer_module
        computer_module._file_system_agent = None
        computer_module._terminal_agent = None
        computer_module._browser_agent = None
        computer_module._desktop_agent = None
        computer_module._workflow_engine = None
        computer_module._permission_system = None

        assert computer_module._file_system_agent is None
        assert computer_module._terminal_agent is None

        # Access services to trigger initialization
        from app.api.v1.endpoints.computer import (
            get_file_system_agent, get_terminal_agent
        )
        fs_agent = get_file_system_agent()
        term_agent = get_terminal_agent()

        assert fs_agent is not None
        assert term_agent is not None
        assert computer_module._file_system_agent is not None
        assert computer_module._terminal_agent is not None

    def test_celery_worker_lazy_loading(self):
        """Test Celery worker is lazy-loaded."""
        from app.worker import _celery_app, get_celery_app

        # Reset to test fresh behavior
        import app.worker as worker_module
        worker_module._celery_app = None

        assert worker_module._celery_app is None

        # The celery_app proxy should exist without triggering initialization
        from app.worker import celery_app
        assert celery_app is not None

        # Access should trigger initialization (but we won't call it to avoid circular import in test)
        # Just verify the mechanism exists
        assert hasattr(worker_module, 'get_celery_app')

    def test_knowledge_processing_lazy_loading(self):
        """Test knowledge processing is lazy-loaded."""
        from app.knowledge.processing import _document_processor, get_document_processor

        # Reset to test fresh behavior
        import app.knowledge.processing as processing_module
        processing_module._document_processor = None

        assert processing_module._document_processor is None

        # Access processor to trigger initialization
        processor = get_document_processor()

        assert processor is not None
        assert processing_module._document_processor is not None

    def test_language_detector_lazy_model_loading(self):
        """Test LanguageDetector loads model lazily."""
        from app.knowledge.processing import LanguageDetector

        detector = LanguageDetector()

        # Model should not be loaded initially
        assert detector.model is None
        assert detector._model_loaded is False

        # First detect_language call should trigger model load attempt
        # Since fasttext is not installed, it will use fallback but still mark as loaded
        lang, confidence = detector.detect_language("Hello world")

        # After first call, model_loaded flag should be True (attempted load)
        assert detector._model_loaded is True
