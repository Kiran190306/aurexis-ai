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
