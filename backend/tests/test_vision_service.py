"""
Unit tests for VisionService.
"""
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
import io

from app.vision.vision_service import VisionService
from app.vision.base import VisionTaskType


@pytest.fixture
def vision_service():
    """Create a VisionService instance for testing."""
    return VisionService()


@pytest.fixture
def sample_image():
    """Create a sample PIL Image for testing."""
    # Create a simple RGB image
    img = Image.new('RGB', (100, 100), color='red')
    img.format = 'PNG'  # Set format for metadata test
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes."""
    img_bytes = io.BytesIO()
    sample_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.read()


@pytest.mark.asyncio
async def test_validate_image_valid(vision_service, sample_image_bytes):
    """Test image validation with valid image."""
    is_valid, error_msg, image = await vision_service.validate_image(sample_image_bytes)
    
    assert is_valid is True
    assert error_msg is None
    assert image is not None


@pytest.mark.asyncio
async def test_validate_image_invalid_size(vision_service):
    """Test image validation with oversized image."""
    # Create image data larger than max size
    large_data = b'x' * (vision_service.max_image_size + 1)
    
    is_valid, error_msg, image = await vision_service.validate_image(large_data)
    
    assert is_valid is False
    assert "exceeds maximum" in error_msg
    assert image is None


@pytest.mark.asyncio
async def test_validate_image_invalid_format(vision_service):
    """Test image validation with invalid format."""
    invalid_data = b'not an image'
    
    is_valid, error_msg, image = await vision_service.validate_image(invalid_data)
    
    assert is_valid is False
    assert "Invalid image" in error_msg
    assert image is None


def test_extract_image_metadata(vision_service, sample_image):
    """Test image metadata extraction."""
    metadata = vision_service.extract_image_metadata(sample_image)
    
    assert metadata.width == 100
    assert metadata.height == 100
    assert metadata.format == 'png'
    assert metadata.color_space == 'RGB'
    assert metadata.has_alpha is False


def test_preprocess_image(vision_service, sample_image):
    """Test image preprocessing."""
    # Test with target size
    processed = vision_service.preprocess_image(sample_image, target_size=(50, 50))
    
    assert processed.size == (50, 50)


@pytest.mark.asyncio
async def test_analyze_image_captioning(vision_service, sample_image_bytes):
    """Test image captioning analysis."""
    result = await vision_service.analyze_image(
        sample_image_bytes,
        [VisionTaskType.IMAGE_CAPTIONING]
    )
    
    assert result.success is True
    assert result.caption is not None
    assert result.processing_time_seconds >= 0


@pytest.mark.asyncio
async def test_analyze_image_multiple_tasks(vision_service, sample_image_bytes):
    """Test image analysis with multiple task types."""
    result = await vision_service.analyze_image(
        sample_image_bytes,
        [VisionTaskType.IMAGE_CAPTIONING, VisionTaskType.SCENE_UNDERSTANDING]
    )
    
    assert result.success is True
    assert result.caption is not None
    assert result.scene_description is not None


def test_compare_images(vision_service, sample_image):
    """Test image comparison."""
    # Create identical image
    img2 = Image.new('RGB', (100, 100), color='red')
    
    comparison = vision_service.compare_images(sample_image, img2)
    
    assert "similarity_score" in comparison
    assert comparison["are_identical"] is True
    assert comparison["similarity_score"] > 0.9999


def test_compare_different_images(vision_service, sample_image):
    """Test comparison of different images."""
    # Create different image with actual pixel variation
    import numpy as np
    img2_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img2 = Image.fromarray(img2_array)
    
    comparison = vision_service.compare_images(sample_image, img2)
    
    assert "similarity_score" in comparison
    # Random noise image should not be identical to solid color
    assert comparison["are_identical"] is False
    # Just verify similarity score is computed
    assert 0 <= comparison["similarity_score"] <= 1
