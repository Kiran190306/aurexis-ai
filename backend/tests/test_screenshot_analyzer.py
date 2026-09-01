"""
Unit tests for ScreenshotAnalyzer.
"""
import pytest
from unittest.mock import patch
from PIL import Image
import numpy as np

from app.vision.screenshot_analyzer import ScreenshotAnalyzer


@pytest.fixture
def screenshot_analyzer():
    """Create a ScreenshotAnalyzer instance for testing."""
    return ScreenshotAnalyzer()


@pytest.fixture
def sample_screenshot():
    """Create a sample screenshot image."""
    # Create a simple RGB image
    img = Image.new('RGB', (800, 600), color='white')
    return img


@pytest.mark.asyncio
async def test_analyze_screenshot(screenshot_analyzer, sample_screenshot):
    """Test screenshot analysis."""
    result = await screenshot_analyzer.analyze(sample_screenshot)
    
    assert result.description is not None
    assert isinstance(result.ui_elements, list)
    assert isinstance(result.error_dialogs, list)


@pytest.mark.asyncio
async def test_detect_ui_elements(screenshot_analyzer, sample_screenshot):
    """Test UI element detection."""
    elements = await screenshot_analyzer._detect_ui_elements(sample_screenshot, {})
    
    assert isinstance(elements, list)


def test_classify_element(screenshot_analyzer):
    """Test element classification."""
    # Test button classification
    button_result = screenshot_analyzer._classify_element(1.5, 500)
    assert button_result == 'button'
    
    # Test input classification
    input_result = screenshot_analyzer._classify_element(5.0, 600)
    assert input_result == 'input'
    
    # Test no match
    no_match = screenshot_analyzer._classify_element(0.1, 10)
    assert no_match is None


def test_calculate_element_confidence(screenshot_analyzer):
    """Test confidence calculation."""
    # High confidence
    high_conf = screenshot_analyzer._calculate_element_confidence(1.5, 500, 'button')
    assert high_conf > 0.5
    
    # Low confidence
    low_conf = screenshot_analyzer._calculate_element_confidence(10.0, 100, 'button')
    assert low_conf < 1.0


@pytest.mark.asyncio
async def test_identify_application_type(screenshot_analyzer):
    """Test application type identification."""
    # Form type - needs >2 inputs and >1 button per implementation
    elements = [
        type('obj', (object,), {'element_type': 'input'}),
        type('obj', (object,), {'element_type': 'input'}),
        type('obj', (object,), {'element_type': 'input'}),
        type('obj', (object,), {'element_type': 'button'}),
        type('obj', (object,), {'element_type': 'button'})
    ]
    app_type = await screenshot_analyzer._identify_application_type(None, elements)
    assert app_type == 'form'
    
    # Document type - needs >10 text elements
    doc_elements = [type('obj', (object,), {'element_type': 'text'})] * 15
    doc_type = await screenshot_analyzer._identify_application_type(None, doc_elements)
    assert doc_type == 'document'


def test_generate_description(screenshot_analyzer):
    """Test description generation."""
    from app.vision.base import UIElement, BoundingBox, DetectedObject
    
    ui_elements = [
        UIElement(
            element_type='button',
            bounding_box=BoundingBox(x=10, y=10, width=50, height=20, confidence=0.9, label='button'),
            confidence=0.9
        )
    ]
    
    description = screenshot_analyzer._generate_description(ui_elements, [], 'form')
    
    assert 'form' in description.lower()
    assert 'button' in description.lower()


def test_summarize_elements(screenshot_analyzer):
    """Test element summarization."""
    from app.vision.base import UIElement, BoundingBox
    
    elements = [
        UIElement(element_type='button', bounding_box=BoundingBox(x=0, y=0, width=50, height=20, confidence=0.9, label='button'), confidence=0.9),
        UIElement(element_type='button', bounding_box=BoundingBox(x=0, y=0, width=50, height=20, confidence=0.9, label='button'), confidence=0.9),
        UIElement(element_type='input', bounding_box=BoundingBox(x=0, y=0, width=100, height=20, confidence=0.9, label='input'), confidence=0.9)
    ]
    
    summary = screenshot_analyzer._summarize_elements(elements)
    
    assert '2 buttons' in summary
    assert '1 input' in summary
