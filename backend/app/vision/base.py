"""
Base classes and data models for Vision Intelligence System.
"""
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class VisionTaskType(str, Enum):
    """Types of vision tasks."""
    IMAGE_CAPTIONING = "image_captioning"
    OBJECT_DETECTION = "object_detection"
    SCENE_UNDERSTANDING = "scene_understanding"
    CHART_ANALYSIS = "chart_analysis"
    TABLE_EXTRACTION = "table_extraction"
    OCR = "ocr"
    SCREENSHOT_ANALYSIS = "screenshot_analysis"
    UI_ELEMENT_DETECTION = "ui_element_detection"
    DOCUMENT_PARSING = "document_parsing"
    VISION_REASONING = "vision_reasoning"


class BoundingBox(BaseModel):
    """Bounding box for detected objects."""
    x: float = Field(..., description="X coordinate of top-left corner")
    y: float = Field(..., description="Y coordinate of top-left corner")
    width: float = Field(..., description="Width of the box")
    height: float = Field(..., description="Height of the box")
    confidence: float = Field(..., description="Confidence score (0-1)")
    label: str = Field(..., description="Label/class of the detected object")


class DetectedObject(BaseModel):
    """Detected object in an image."""
    label: str = Field(..., description="Object label")
    confidence: float = Field(..., description="Confidence score")
    bounding_box: BoundingBox = Field(..., description="Bounding box coordinates")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class OCRResult(BaseModel):
    """Result of OCR processing."""
    text: str = Field(..., description="Extracted text")
    confidence: float = Field(..., description="Overall confidence score")
    blocks: List[Dict[str, Any]] = Field(default_factory=list, description="Text blocks with positions")
    language: Optional[str] = Field(default=None, description="Detected language")
    layout: Optional[Dict[str, Any]] = Field(default=None, description="Layout information")


class UIElement(BaseModel):
    """Detected UI element in screenshot."""
    element_type: str = Field(..., description="Type of UI element (button, input, etc.)")
    label: Optional[str] = Field(default=None, description="Element label/text")
    bounding_box: BoundingBox = Field(..., description="Bounding box")
    confidence: float = Field(..., description="Confidence score")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class ScreenshotAnalysis(BaseModel):
    """Result of screenshot analysis."""
    window_title: Optional[str] = Field(default=None, description="Window/application title")
    application_type: Optional[str] = Field(default=None, description="Application type (browser, desktop, etc.)")
    ui_elements: List[UIElement] = Field(default_factory=list, description="Detected UI elements")
    error_dialogs: List[DetectedObject] = Field(default_factory=list, description="Detected error dialogs")
    description: str = Field(..., description="Natural language description")


class TableData(BaseModel):
    """Extracted table data."""
    headers: List[str] = Field(default_factory=list, description="Table headers")
    rows: List[List[str]] = Field(default_factory=list, description="Table rows")
    confidence: float = Field(..., description="Extraction confidence")
    bounding_box: Optional[BoundingBox] = Field(default=None, description="Table location")


class VisionAnalysisResult(BaseModel):
    """Result of vision analysis."""
    task_type: VisionTaskType = Field(..., description="Type of vision task performed")
    success: bool = Field(..., description="Whether the analysis was successful")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Image understanding results
    caption: Optional[str] = Field(default=None, description="Image caption")
    objects: List[DetectedObject] = Field(default_factory=list, description="Detected objects")
    scene_description: Optional[str] = Field(default=None, description="Scene description")
    
    # OCR results
    ocr_result: Optional[OCRResult] = Field(default=None, description="OCR extraction result")
    
    # Screenshot results
    screenshot_analysis: Optional[ScreenshotAnalysis] = Field(default=None, description="Screenshot analysis")
    
    # Document results
    tables: List[TableData] = Field(default_factory=list, description="Extracted tables")
    forms: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted form fields")
    
    # Reasoning results
    reasoning: Optional[str] = Field(default=None, description="Vision reasoning explanation")
    
    # Metadata
    processing_time_seconds: float = Field(..., description="Time taken to process")
    model_used: Optional[str] = Field(default=None, description="Model used for analysis")
    confidence: Optional[float] = Field(default=None, description="Overall confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ImageMetadata(BaseModel):
    """Metadata about an image."""
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    format: str = Field(..., description="Image format (png, jpg, etc.)")
    size_bytes: int = Field(..., description="File size in bytes")
    color_space: Optional[str] = Field(default=None, description="Color space (RGB, grayscale, etc.)")
    has_alpha: bool = Field(default=False, description="Whether image has alpha channel")
