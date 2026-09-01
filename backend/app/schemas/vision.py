"""
Pydantic schemas for Vision Intelligence System API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class VisionAnalyzeRequest(BaseModel):
    """Request for image analysis."""
    task_types: List[str] = Field(default=["image_captioning"], description="Types of analysis to perform")
    target_size: Optional[tuple[int, int]] = Field(default=None, description="Target size for image resizing")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options")


class OCRRequest(BaseModel):
    """Request for OCR processing."""
    language: Optional[str] = Field(default=None, description="Language code (e.g., 'eng', 'fra')")
    preserve_layout: bool = Field(default=True, description="Preserve text layout")
    config: Optional[str] = Field(default=None, description="Tesseract configuration")


class ScreenshotAnalysisRequest(BaseModel):
    """Request for screenshot analysis."""
    detect_ui_elements: bool = Field(default=True, description="Detect UI elements")
    detect_errors: bool = Field(default=True, description="Detect error dialogs")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options")


class DocumentVisionRequest(BaseModel):
    """Request for document vision processing."""
    perform_ocr: bool = Field(default=False, description="Perform OCR on document")
    ocr_language: Optional[str] = Field(default=None, description="OCR language")
    extract_images: bool = Field(default=False, description="Extract images from document")
    extract_tables: bool = Field(default=False, description="Extract tables from document")
    page_numbers: Optional[List[int]] = Field(default=None, description="Specific pages to process")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options")


class VisionAnalysisResponse(BaseModel):
    """Response for vision analysis."""
    uuid: str
    analysis_type: str
    status: str
    caption: Optional[str] = None
    objects_detected: Optional[List[Dict[str, Any]]] = None
    scene_description: Optional[str] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_blocks: Optional[List[Dict[str, Any]]] = None
    screenshot_analysis: Optional[Dict[str, Any]] = None
    tables_extracted: Optional[List[Dict[str, Any]]] = None
    forms_extracted: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    model_used: Optional[str] = None
    overall_confidence: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class OCRResponse(BaseModel):
    """Response for OCR processing."""
    text: str
    confidence: float
    blocks: List[Dict[str, Any]]
    language: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None


class ScreenshotAnalysisResponse(BaseModel):
    """Response for screenshot analysis."""
    window_title: Optional[str] = None
    application_type: Optional[str] = None
    ui_elements: List[Dict[str, Any]]
    error_dialogs: List[Dict[str, Any]]
    description: str


class DocumentVisionResponse(BaseModel):
    """Response for document vision processing."""
    uuid: str
    status: str
    page_count: int
    pages: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    forms: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class VisionHistoryResponse(BaseModel):
    """Response for vision history."""
    id: int
    uuid: str
    analysis_type: str
    status: str
    image_metadata: Optional[Dict[str, Any]] = None
    caption: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    overall_confidence: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True
