"""
Unit tests for OCRService.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import io

from app.vision.ocr_service import OCRService


@pytest.fixture
def ocr_service():
    """Create an OCRService instance for testing."""
    return OCRService()


@pytest.fixture
def sample_image():
    """Create a sample PIL Image with text."""
    img = Image.new('RGB', (200, 100), color='white')
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes."""
    img_bytes = io.BytesIO()
    sample_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.read()


@pytest.mark.asyncio
@patch('app.vision.ocr_service.pytesseract.image_to_data')
async def test_extract_text(mock_image_to_data, ocr_service, sample_image):
    """Test text extraction from image."""
    # Mock Tesseract response
    mock_data = {
        'text': ['Hello', 'World', '', 'Test'],
        'conf': ['95', '90', '-1', '85'],
        'left': [10, 10, 0, 10],
        'top': [10, 30, 0, 50],
        'width': [50, 50, 0, 40],
        'height': [15, 15, 0, 12]
    }
    mock_image_to_data.return_value = mock_data
    
    result = await ocr_service.extract_text(sample_image)
    
    assert result.text == "Hello World Test"
    assert result.confidence > 0
    assert len(result.blocks) > 0


@pytest.mark.asyncio
@patch('app.vision.ocr_service.pytesseract.image_to_data')
async def test_extract_text_with_layout(mock_image_to_data, ocr_service, sample_image):
    """Test text extraction with layout preservation."""
    mock_data = {
        'text': ['Line 1', 'Line 2', '', 'Line 3'],
        'conf': ['90', '85', '-1', '88'],
        'left': [10, 10, 0, 10],
        'top': [10, 30, 0, 50],
        'width': [50, 50, 0, 40],
        'height': [15, 15, 0, 12]
    }
    mock_image_to_data.return_value = mock_data
    
    result = await ocr_service.extract_text_with_layout(sample_image, preserve_structure=True)
    
    assert result.text is not None
    assert result.layout is not None


@pytest.mark.asyncio
@patch('app.vision.ocr_service.pytesseract.image_to_data')
async def test_extract_handwritten_text(mock_image_to_data, ocr_service, sample_image):
    """Test handwritten text extraction."""
    mock_data = {
        'text': ['Handwritten', 'text'],
        'conf': ['70', '65'],
        'left': [10, 10],
        'top': [10, 30],
        'width': [80, 50],
        'height': [20, 15]
    }
    mock_image_to_data.return_value = mock_data
    
    result = await ocr_service.extract_handwritten_text(sample_image)
    
    assert result.text is not None
    assert result.confidence > 0


def test_detect_language(ocr_service):
    """Test language detection from language code."""
    assert ocr_service._detect_language('eng') == 'en'
    assert ocr_service._detect_language('fra') == 'fr'
    assert ocr_service._detect_language('deu') == 'de'
    assert ocr_service._detect_language('chi_sim') == 'zh'
    assert ocr_service._detect_language('jpn') == 'ja'
    assert ocr_service._detect_language('unknown') == 'en'


def test_extract_layout(ocr_service):
    """Test layout extraction from OCR data."""
    data = {
        'text': ['Text 1', 'Text 2', 'Text 3'],
        'left': [10, 10, 10],
        'top': [10, 30, 50],
        'width': [50, 50, 50],
        'height': [15, 15, 15]
    }
    
    layout = ocr_service._extract_layout(data)
    
    assert layout['lines'] >= 1
    assert layout['blocks'] == 3


def test_estimate_line_height(ocr_service):
    """Test line height estimation."""
    blocks = [
        {'height': 15},
        {'height': 16},
        {'height': 14},
        {'height': 15}
    ]
    
    height = ocr_service._estimate_line_height(blocks)
    
    assert height == 15.0


@patch('app.vision.ocr_service.pytesseract.get_languages')
def test_get_supported_languages(mock_get_languages, ocr_service):
    """Test getting supported languages."""
    mock_get_languages.return_value = ['eng', 'fra', 'deu', 'spa']
    
    langs = ocr_service.get_supported_languages()
    
    assert 'eng' in langs
    assert 'fra' in langs
