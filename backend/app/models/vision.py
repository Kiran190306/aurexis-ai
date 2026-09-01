"""
Database models for Vision Intelligence System.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float, LargeBinary
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class VisionAnalysisType(PyEnum):
    """Types of vision analysis."""
    IMAGE_CAPTIONING = "image_captioning"
    OBJECT_DETECTION = "object_detection"
    SCENE_UNDERSTANDING = "scene_understanding"
    OCR = "ocr"
    SCREENSHOT_ANALYSIS = "screenshot_analysis"
    DOCUMENT_PARSING = "document_parsing"
    CHART_ANALYSIS = "chart_analysis"
    TABLE_EXTRACTION = "table_extraction"
    VISION_REASONING = "vision_reasoning"


class VisionAnalysisStatus(PyEnum):
    """Status of vision analysis."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VisionAnalysis(Base):
    """Vision analysis records."""
    __tablename__ = "vision_analyses"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    
    # Analysis info
    analysis_type: Mapped[VisionAnalysisType] = mapped_column(Enum(VisionAnalysisType), nullable=False, index=True)
    status: Mapped[VisionAnalysisStatus] = mapped_column(Enum(VisionAnalysisStatus), default=VisionAnalysisStatus.PENDING)
    
    # Input
    image_data = Column(LargeBinary, nullable=True)  # For small images
    image_path = Column(String(512), nullable=True)  # For stored images
    image_metadata = Column(JSON, nullable=True)  # Width, height, format, etc.
    
    # Options
    analysis_options = Column(JSON, nullable=True)
    
    # Results
    caption = Column(Text, nullable=True)
    objects_detected = Column(JSON, nullable=True)  # Array of detected objects
    scene_description = Column(Text, nullable=True)
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    ocr_blocks = Column(JSON, nullable=True)
    screenshot_analysis = Column(JSON, nullable=True)
    tables_extracted = Column(JSON, nullable=True)
    forms_extracted = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)
    
    # Performance
    processing_time_seconds = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    overall_confidence = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="vision_analyses")
    file = relationship("File", backref="vision_analyses")
    bounding_boxes = relationship("VisionBoundingBox", back_populates="analysis", cascade="all, delete-orphan")


class VisionBoundingBox(Base):
    """Bounding boxes for detected objects."""
    __tablename__ = "vision_bounding_boxes"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("vision_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bounding box coordinates
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    
    # Detection info
    label = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Additional attributes
    attributes = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("VisionAnalysis", back_populates="bounding_boxes")


class DocumentVision(Base):
    """Document vision processing records."""
    __tablename__ = "document_visions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    
    # Document info
    file_path = Column(String(512), nullable=False)
    file_format = Column(String(50), nullable=False)
    page_count = Column(Integer, default=0)
    
    # Processing status
    status: Mapped[VisionAnalysisStatus] = mapped_column(Enum(VisionAnalysisStatus), default=VisionAnalysisStatus.PENDING)
    
    # Processing options
    perform_ocr = Column(Boolean, default=False)
    ocr_language = Column(String(10), nullable=True)
    extract_images = Column(Boolean, default=False)
    extract_tables = Column(Boolean, default=False)
    
    # Results
    extracted_text = Column(Text, nullable=True)
    extracted_images = Column(JSON, nullable=True)  # Array of image info
    extracted_tables = Column(JSON, nullable=True)  # Array of table data
    extracted_forms = Column(JSON, nullable=True)  # Array of form fields
    
    # Performance
    processing_time_seconds = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="document_visions")
    document = relationship("Document", backref="document_visions")
    file = relationship("File", backref="document_visions")
    pages = relationship("DocumentVisionPage", back_populates="document_vision", cascade="all, delete-orphan")


class DocumentVisionPage(Base):
    """Individual page results from document vision processing."""
    __tablename__ = "document_vision_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_vision_id = Column(Integer, ForeignKey("document_visions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Page info
    page_number = Column(Integer, nullable=False)
    
    # Page results
    text = Column(Text, nullable=True)
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    
    # Extracted content
    tables = Column(JSON, nullable=True)
    forms = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document_vision = relationship("DocumentVision", back_populates="pages")
