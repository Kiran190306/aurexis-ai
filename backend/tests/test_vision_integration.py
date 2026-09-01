"""
Integration tests for Vision Intelligence System pipeline.
"""
import pytest
from unittest.mock import patch, AsyncMock
from PIL import Image
import io

from app.vision.vision_service import vision_service
from app.vision.ocr_service import ocr_service
from app.vision.screenshot_analyzer import screenshot_analyzer
from app.vision.vision_tool import vision_tool
from app.vision.base import VisionTaskType


@pytest.fixture
def sample_image():
    """Create a sample PIL Image."""
    img = Image.new('RGB', (200, 150), color='blue')
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes."""
    img_bytes = io.BytesIO()
    sample_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.read()


@pytest.mark.asyncio
async def test_full_vision_analysis_pipeline(sample_image_bytes):
    """Test complete vision analysis pipeline."""
    # Validate image
    is_valid, error_msg, image = await vision_service.validate_image(sample_image_bytes)
    assert is_valid is True
    
    # Extract metadata
    metadata = vision_service.extract_image_metadata(image)
    assert metadata.width == 200
    assert metadata.height == 150
    
    # Perform analysis
    result = await vision_service.analyze_image(
        sample_image_bytes,
        [VisionTaskType.IMAGE_CAPTIONING, VisionTaskType.SCENE_UNDERSTANDING]
    )
    
    assert result.success is True
    assert result.caption is not None
    assert result.processing_time_seconds >= 0


@pytest.mark.asyncio
@patch('app.vision.ocr_service.pytesseract.image_to_data')
async def test_ocr_pipeline(mock_image_to_data, sample_image):
    """Test OCR pipeline."""
    # Mock Tesseract response
    mock_data = {
        'text': ['Sample', 'Text', '', 'OCR'],
        'conf': ['90', '85', '-1', '88'],
        'left': [10, 10, 0, 10],
        'top': [10, 30, 0, 50],
        'width': [50, 50, 0, 40],
        'height': [15, 15, 0, 12]
    }
    mock_image_to_data.return_value = mock_data
    
    # Perform OCR
    result = await ocr_service.extract_text(sample_image)
    
    assert result.text == "Sample Text OCR"
    assert result.confidence > 0
    assert len(result.blocks) > 0


@pytest.mark.asyncio
async def test_screenshot_analysis_pipeline(sample_image):
    """Test screenshot analysis pipeline."""
    # Analyze screenshot
    result = await screenshot_analyzer.analyze(sample_image)
    
    assert result.description is not None
    assert isinstance(result.ui_elements, list)
    assert isinstance(result.error_dialogs, list)


@pytest.mark.asyncio
async def test_vision_tool_analyze_operation(sample_image_bytes):
    """Test vision tool analyze operation."""
    result = await vision_tool.execute(
        "analyze",
        sample_image_bytes,
        {"task_types": ["image_captioning"]}
    )
    
    assert result["success"] is True
    assert "caption" in result


@pytest.mark.asyncio
@patch('app.vision.ocr_service.pytesseract.image_to_data')
async def test_vision_tool_ocr_operation(mock_image_to_data, sample_image_bytes):
    """Test vision tool OCR operation."""
    mock_data = {
        'text': ['Test', 'OCR'],
        'conf': ['90', '85'],
        'left': [10, 10],
        'top': [10, 30],
        'width': [50, 50],
        'height': [15, 15]
    }
    mock_image_to_data.return_value = mock_data
    
    result = await vision_tool.execute(
        "ocr",
        sample_image_bytes,
        {"preserve_structure": True}
    )
    
    assert result["success"] is True
    assert "text" in result
    assert result["text"] == "Test OCR"


@pytest.mark.asyncio
async def test_vision_tool_screenshot_operation(sample_image_bytes):
    """Test vision tool screenshot operation."""
    result = await vision_tool.execute(
        "screenshot",
        sample_image_bytes,
        {}
    )
    
    assert result["success"] is True
    assert "description" in result


@pytest.mark.asyncio
async def test_vision_tool_compare_operation(sample_image_bytes):
    """Test vision tool image comparison."""
    result = await vision_tool.execute(
        "compare",
        sample_image_bytes,
        {"comparison_image": sample_image_bytes}
    )
    
    assert result["success"] is True
    assert "similarity_score" in result
    assert result["are_identical"] is True


@pytest.mark.asyncio
async def test_vision_tool_table_extraction(sample_image_bytes):
    """Test vision tool table extraction."""
    result = await vision_tool.execute(
        "extract_table",
        sample_image_bytes,
        {}
    )
    
    assert result["success"] is True
    assert "tables" in result


def test_vision_tool_info():
    """Test vision tool information."""
    info = vision_tool.get_tool_info()
    
    assert info["name"] == "vision_tool"
    assert "operations" in info
    assert len(info["operations"]) > 0
    
    # Check required operations exist
    operation_names = [op["name"] for op in info["operations"]]
    assert "analyze" in operation_names
    assert "ocr" in operation_names
    assert "screenshot" in operation_names
    assert "compare" in operation_names
