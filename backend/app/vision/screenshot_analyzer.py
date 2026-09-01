"""
ScreenshotAnalyzer - Analyze screenshots for UI elements and application context.
"""
from typing import Dict, List, Any, Optional
from PIL import Image
import numpy as np
from loguru import logger

from app.vision.base import ScreenshotAnalysis, UIElement, BoundingBox, DetectedObject


class ScreenshotAnalyzer:
    """Analyzer for screenshots and UI elements."""
    
    def __init__(self) -> None:
        self.ui_element_patterns = {
            'button': {'aspect_ratio_range': (0.3, 3.0), 'min_area': 400},
            'input': {'aspect_ratio_range': (2.0, 10.0), 'min_area': 500},
            'checkbox': {'aspect_ratio_range': (0.8, 1.2), 'min_area': 100},
            'dropdown': {'aspect_ratio_range': (1.5, 5.0), 'min_area': 400},
            'text': {'aspect_ratio_range': (0.1, 10.0), 'min_area': 50},
            'icon': {'aspect_ratio_range': (0.8, 1.2), 'min_area': 64},
        }
    
    async def analyze(self, image: Image.Image, options: Optional[Dict[str, Any]] = None) -> ScreenshotAnalysis:
        """Analyze screenshot for UI elements and context."""
        options = options or {}
        
        try:
            # Detect UI elements
            ui_elements = await self._detect_ui_elements(image, options)
            
            # Detect error dialogs
            error_dialogs = await self._detect_error_dialogs(image, options)
            
            # Identify application type
            app_type = await self._identify_application_type(image, ui_elements)
            
            # Extract window title (simplified)
            window_title = await self._extract_window_title(image)
            
            # Generate description
            description = self._generate_description(ui_elements, error_dialogs, app_type)
            
            return ScreenshotAnalysis(
                window_title=window_title,
                application_type=app_type,
                ui_elements=ui_elements,
                error_dialogs=error_dialogs,
                description=description
            )
        
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            raise
    
    async def _detect_ui_elements(
        self,
        image: Image.Image,
        options: Dict[str, Any]
    ) -> List[UIElement]:
        """Detect UI elements using image analysis."""
        # Convert to grayscale for edge detection
        gray = image.convert('L')
        img_array = np.array(gray)
        
        # Simple edge detection (in production, use trained model)
        edges = self._detect_edges(img_array)
        
        # Find contours and classify as UI elements
        elements = []
        contours = self._find_contours(edges)
        
        for contour in contours:
            x, y, w, h = contour
            area = w * h
            aspect_ratio = w / h if h > 0 else 0
            
            # Classify element type based on properties
            element_type = self._classify_element(aspect_ratio, area)
            
            if element_type:
                confidence = self._calculate_element_confidence(aspect_ratio, area, element_type)
                
                if confidence > 0.5:
                    elements.append(UIElement(
                        element_type=element_type,
                        bounding_box=BoundingBox(
                            x=float(x),
                            y=float(y),
                            width=float(w),
                            height=float(h),
                            confidence=confidence,
                            label=element_type
                        ),
                        confidence=confidence,
                        attributes={
                            'area': area,
                            'aspect_ratio': aspect_ratio
                        }
                    ))
        
        return elements
    
    def _detect_edges(self, img_array: np.ndarray) -> np.ndarray:
        """Simple edge detection using Sobel filter."""
        from scipy import ndimage
        
        # Sobel filters
        sx = ndimage.sobel(img_array, axis=0, mode='constant')
        sy = ndimage.sobel(img_array, axis=1, mode='constant')
        
        # Magnitude
        edges = np.hypot(sx, sy)
        
        # Threshold
        threshold = np.percentile(edges, 80)
        return (edges > threshold).astype(np.uint8)  # type: ignore[no-any-return]
    
    def _find_contours(self, edges: np.ndarray) -> List[tuple]:
        """Find bounding boxes from edge image."""
        from scipy import ndimage
        
        # Label connected components
        labeled, num_features = ndimage.label(edges)
        
        # Get bounding boxes
        contours = []
        for i in range(1, num_features + 1):
            mask = labeled == i
            coords = np.argwhere(mask)
            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)  # type: ignore[attr-defined]
                y_max, x_max = coords.max(axis=0)  # type: ignore[attr-defined]
                contours.append((x_min, y_min, x_max - x_min, y_max - y_min))
        
        return contours
    
    def _classify_element(self, aspect_ratio: float, area: int) -> Optional[str]:
        """Classify UI element based on properties."""
        for element_type, pattern in self.ui_element_patterns.items():
            ar_min, ar_max = pattern['aspect_ratio_range']  # type: ignore[misc]
            min_area = pattern['min_area']
            
            if ar_min <= aspect_ratio <= ar_max and area >= min_area:  # type: ignore[operator, has-type]
                return element_type
        
        return None
    
    def _calculate_element_confidence(
        self,
        aspect_ratio: float,
        area: int,
        element_type: str
    ) -> float:
        """Calculate confidence score for element classification."""
        pattern = self.ui_element_patterns.get(element_type, {})
        ar_min, ar_max = pattern.get('aspect_ratio_range', (0, 100))  # type: ignore[misc]
        min_area = pattern.get('min_area', 0)
        
        # Aspect ratio confidence
        ar_range = ar_max - ar_min  # type: ignore[has-type]
        ar_center = (ar_min + ar_max) / 2  # type: ignore[has-type]
        ar_distance = abs(aspect_ratio - ar_center)
        ar_confidence = 1.0 - (ar_distance / (ar_range / 2))
        
        # Area confidence
        area_confidence = min(1.0, area / (min_area * 2))  # type: ignore[operator]
        
        return max(0.0, min(1.0, (ar_confidence + area_confidence) / 2))  # type: ignore[no-any-return]
    
    async def _detect_error_dialogs(
        self,
        image: Image.Image,
        options: Dict[str, Any]
    ) -> List[DetectedObject]:
        """Detect error dialogs in screenshot."""
        # In production, use trained model for error dialog detection
        # For now, use simple heuristics based on color and layout
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        img_array = np.array(image)
        
        # Look for red regions (common in error dialogs)
        if img_array is not None and img_array.size > 0:
            red_mask = (img_array[:, :, 0] > 150) & (img_array[:, :, 1] < 100) & (img_array[:, :, 2] < 100)  # type: ignore[index]
        else:
            red_mask = np.array([], dtype=bool)
        
        if np.sum(red_mask) > 1000:  # Significant red content
            # Find bounding box of red region
            coords = np.argwhere(red_mask)
            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)  # type: ignore[attr-defined]
                y_max, x_max = coords.max(axis=0)  # type: ignore[attr-defined]
                
                return [DetectedObject(
                    label="error_dialog",
                    confidence=0.6,
                    bounding_box=BoundingBox(
                        x=float(x_min),
                        y=float(y_min),
                        width=float(x_max - x_min),
                        height=float(y_max - y_min),
                        confidence=0.6,
                        label="error_dialog"
                    )
                )]
        
        return []
    
    async def _identify_application_type(
        self,
        image: Image.Image,
        ui_elements: List[UIElement]
    ) -> Optional[str]:
        """Identify application type from screenshot."""
        # Count element types
        element_counts: Dict[str, int] = {}
        for element in ui_elements:
            element_counts[element.element_type] = element_counts.get(element.element_type, 0) + 1
        
        # Heuristics for application type
        if element_counts.get('input', 0) > 2 and element_counts.get('button', 0) > 1:
            return "form"
        elif element_counts.get('text', 0) > 10:
            return "document"
        elif element_counts.get('dropdown', 0) > 0:
            return "application"
        elif element_counts.get('button', 0) > 5:
            return "toolbar"
        else:
            return "general"
    
    async def _extract_window_title(self, image: Image.Image) -> Optional[str]:
        """Extract window title from screenshot."""
        # In production, use OCR on top region
        # For now, return None
        return None
    
    def _generate_description(
        self,
        ui_elements: List[UIElement],
        error_dialogs: List[DetectedObject],
        app_type: Optional[str]
    ) -> str:
        """Generate natural language description."""
        parts = []
        
        if app_type:
            parts.append(f"This appears to be a {app_type} interface")
        
        if ui_elements:
            element_summary = self._summarize_elements(ui_elements)
            parts.append(f"with {element_summary}")
        
        if error_dialogs:
            parts.append("An error dialog is visible")
        
        return " ".join(parts) if parts else "A screenshot with no clear UI elements detected"
    
    def _summarize_elements(self, elements: List[UIElement]) -> str:
        """Summarize detected UI elements."""
        counts: Dict[str, int] = {}
        for element in elements:
            counts[element.element_type] = counts.get(element.element_type, 0) + 1
        
        summary_parts = []
        for element_type, count in counts.items():
            if count > 1:
                summary_parts.append(f"{count} {element_type}s")
            else:
                summary_parts.append(f"1 {element_type}")
        
        return ", ".join(summary_parts)


# Global screenshot analyzer instance
screenshot_analyzer = ScreenshotAnalyzer()
