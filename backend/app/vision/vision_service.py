"""
VisionService - Core service for image understanding and analysis.
"""
from typing import Optional, Dict, Any, List
from PIL import Image
import io
import numpy as np
from loguru import logger
from pathlib import Path

from app.core.config import settings
from app.vision.base import (
    VisionAnalysisResult,
    VisionTaskType,
    ImageMetadata,
    BoundingBox,
    DetectedObject
)


class VisionService:
    """Core service for vision intelligence operations."""
    
    def __init__(self) -> None:
        self.supported_formats = settings.VISION_SUPPORTED_FORMATS
        self.max_image_size = settings.VISION_MAX_IMAGE_SIZE
    
    async def validate_image(self, image_data: bytes) -> tuple[bool, Optional[str], Optional[Image.Image]]:
        """Validate image data and return PIL Image."""
        try:
            # Check size
            if len(image_data) > self.max_image_size:
                return False, f"Image size exceeds maximum of {self.max_image_size} bytes", None
            
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Check format
            if image.format and image.format.lower() not in self.supported_formats:
                return False, f"Unsupported format: {image.format}", None
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')  # type: ignore[assignment]
            
            return True, None, image
        
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False, f"Invalid image: {str(e)}", None
    
    def extract_image_metadata(self, image: Image.Image) -> ImageMetadata:
        """Extract metadata from PIL Image."""
        return ImageMetadata(
            width=image.width,
            height=image.height,
            format=image.format.lower() if image.format else "unknown",
            size_bytes=len(image.tobytes()) if hasattr(image, 'tobytes') else 0,
            color_space=image.mode,
            has_alpha=image.mode in ('RGBA', 'LA', 'PA')
        )
    
    def preprocess_image(self, image: Image.Image, target_size: Optional[tuple[int, int]] = None) -> Image.Image:
        """Preprocess image for analysis."""
        # Resize if target size specified
        if target_size:
            try:
                image = image.resize(target_size, Image.Resampling.LANCZOS)  # type: ignore[attr-defined]
            except AttributeError:
                image = image.resize(target_size, Image.LANCZOS)  # type: ignore[attr-defined]
        
        # Normalize pixel values
        if image.mode == 'RGB':
            img_array = np.array(image, dtype=np.float32) / 255.0
            image = Image.fromarray((img_array * 255).astype(np.uint8))  # type: ignore[attr-defined]
        
        return image
    
    async def analyze_image(
        self,
        image_data: bytes,
        task_types: List[VisionTaskType],
        options: Optional[Dict[str, Any]] = None
    ) -> VisionAnalysisResult:
        """Analyze image with specified task types."""
        import time
        start_time = time.time()
        
        # Validate image
        is_valid, error_msg, image = await self.validate_image(image_data)
        if not is_valid or image is None:
            return VisionAnalysisResult(
                task_type=task_types[0] if task_types else VisionTaskType.IMAGE_CAPTIONING,
                success=False,
                error_message=error_msg,
                processing_time_seconds=time.time() - start_time
            )
        
        # Extract metadata
        metadata = self.extract_image_metadata(image)
        
        # Preprocess
        options = options or {}
        target_size = options.get('target_size')
        if target_size:
            image = self.preprocess_image(image, target_size)
        
        # Perform analysis based on task types
        results: Dict[str, Any] = {}
        for task_type in task_types:
            try:
                if task_type == VisionTaskType.IMAGE_CAPTIONING:
                    results['caption'] = await self._caption_image(image, options)
                elif task_type == VisionTaskType.OBJECT_DETECTION:
                    results['objects'] = await self._detect_objects(image, options)
                elif task_type == VisionTaskType.SCENE_UNDERSTANDING:
                    results['scene_description'] = await self._understand_scene(image, options)
                elif task_type == VisionTaskType.CHART_ANALYSIS:
                    results['chart_analysis'] = await self._analyze_chart(image, options)
                elif task_type == VisionTaskType.TABLE_EXTRACTION:
                    results['tables'] = await self._extract_tables(image, options)
            
            except Exception as e:
                logger.error(f"Task {task_type} failed: {e}")
                results[f'{task_type}_error'] = str(e)
        
        # Build result
        processing_time = time.time() - start_time
        
        return VisionAnalysisResult(
            task_type=task_types[0] if task_types else VisionTaskType.IMAGE_CAPTIONING,
            success=True,
            caption=results.get('caption'),
            objects=results.get('objects', []),
            scene_description=results.get('scene_description'),
            tables=results.get('tables', []),
            processing_time_seconds=processing_time,
            metadata={
                'image_metadata': metadata.dict(),
                'task_results': results
            }
        )
    
    async def _caption_image(self, image: Image.Image, options: Dict[str, Any]) -> str:
        """Generate image caption using vision model."""
        # In production, integrate with GPT-4 Vision or similar
        # For now, return a basic description based on image properties
        width, height = image.size
        aspect_ratio = width / height
        
        if aspect_ratio > 1.5:
            return f"A landscape image ({width}x{height}) showing a wide scene"
        elif aspect_ratio < 0.67:
            return f"A portrait image ({width}x{height}) showing a vertical composition"
        else:
            return f"A square-ish image ({width}x{height}) with balanced composition"
    
    async def _detect_objects(self, image: Image.Image, options: Dict[str, Any]) -> List[DetectedObject]:
        """Detect objects in image using object detection model."""
        # In production, integrate with YOLO, Faster R-CNN, or similar
        # For now, return empty list (placeholder for actual implementation)
        logger.warning("Object detection not fully implemented - returning empty results")
        return []
    
    async def _understand_scene(self, image: Image.Image, options: Dict[str, Any]) -> str:
        """Understand scene context."""
        # In production, use scene classification model
        caption = await self._caption_image(image, options)
        return f"Scene analysis: {caption}. The image appears to be a standard photograph."
    
    async def _analyze_chart(self, image: Image.Image, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze charts and diagrams."""
        # In production, use chart-specific analysis
        return {
            "chart_type": "unknown",
            "description": "Chart analysis requires specialized model",
            "confidence": 0.0
        }
    
    async def _extract_tables(self, image: Image.Image, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tables from image."""
        # In production, use table extraction model
        logger.warning("Table extraction not fully implemented - returning empty results")
        return []
    
    def compare_images(self, image1: Image.Image, image2: Image.Image) -> Dict[str, Any]:
        """Compare two images for similarity."""
        # Convert to numpy arrays
        arr1 = np.array(image1.resize((256, 256))).flatten()  # type: ignore[attr-defined]
        arr2 = np.array(image2.resize((256, 256))).flatten()  # type: ignore[attr-defined]
        
        # Calculate similarity
        mse = np.mean((arr1 - arr2) ** 2)
        similarity = 1 - (mse / (255 * 255))
        
        # Use a more reasonable threshold for "identical" - requires very high similarity
        return {
            "similarity_score": float(similarity),
            "mean_squared_error": float(mse),
            "are_identical": bool(similarity > 0.9999)
        }


# Lazy-loaded vision service singleton
_vision_service_instance: Optional[VisionService] = None


def get_vision_service() -> VisionService:
    """Get or create the vision service instance (lazy-loaded)."""
    global _vision_service_instance
    if _vision_service_instance is None:
        _vision_service_instance = VisionService()
    return _vision_service_instance


# Backward compatibility: allow importing vision_service directly
class _VisionServiceProxy:
    """Proxy for lazy-loaded vision service."""
    def __getattr__(self, name: str) -> Any:
        return getattr(get_vision_service(), name)


vision_service = _VisionServiceProxy()
