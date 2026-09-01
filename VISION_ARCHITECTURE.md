# Vision Intelligence System Architecture

## Overview

The Vision Intelligence System (EPIC-012) enables Jarvis AI to understand and interact with visual information including images, screenshots, scanned documents, and user interfaces. This production-grade system provides comprehensive image analysis, OCR capabilities, screenshot understanding, and document processing.

## Architecture Principles

- **Modular Design**: Separate services for vision, OCR, screenshot analysis, and document processing
- **Async Processing**: All operations are asynchronous for non-blocking execution
- **Multi-Agent Integration**: Vision capabilities integrated with the multi-agent system via ImageAnalysisAgent
- **Tool Integration**: VisionTool provides tool agent integration for dynamic tool selection
- **Production-Grade**: Comprehensive error handling, validation, and logging
- **Backward Compatibility**: Maintains compatibility with existing Jarvis AI architecture

## System Components

### 1. VisionService (`app/vision/vision_service.py`)

**Purpose**: Core service for image understanding and analysis.

**Responsibilities**:
- Image validation and preprocessing
- Image metadata extraction
- Image captioning
- Object detection
- Scene understanding
- Chart and diagram analysis
- Table extraction
- Image comparison

**Key Methods**:
- `validate_image()`: Validates image format, size, and integrity
- `extract_image_metadata()`: Extracts width, height, format, color space
- `preprocess_image()`: Resizes and normalizes images for analysis
- `analyze_image()`: Main entry point for image analysis with multiple task types
- `compare_images()`: Compares two images for similarity

**Supported Formats**: PNG, JPG, JPEG, GIF, BMP, WebP, TIFF

**Configuration**:
- `VISION_MAX_IMAGE_SIZE`: Maximum image size (default: 10MB)
- `VISION_SUPPORTED_FORMATS`: List of supported image formats
- `VISION_OCR_CONFIDENCE_THRESHOLD`: OCR confidence threshold (default: 0.6)
- `VISION_OBJECT_DETECTION_CONFIDENCE`: Object detection threshold (default: 0.5)

### 2. OCRService (`app/vision/ocr_service.py`)

**Purpose**: Optical Character Recognition using Tesseract OCR engine.

**Responsibilities**:
- Text extraction from images
- Layout-aware OCR
- Multi-language support
- PDF OCR processing
- Handwritten text extraction (experimental)
- Confidence scoring

**Key Methods**:
- `extract_text()`: Extract text with confidence scores
- `extract_text_with_layout()`: Preserve text layout during extraction
- `extract_handwritten_text()`: Extract handwritten text
- `extract_from_pdf()`: Process PDF pages with OCR
- `get_supported_languages()`: List available Tesseract languages

**Supported Languages**:
- English (eng)
- French (fra)
- German (deu)
- Spanish (spa)
- Italian (ita)
- Portuguese (por)
- Chinese Simplified (chi_sim)
- Japanese (jpn)

**Configuration**:
- `TESSERACT_PATH`: Path to Tesseract executable
- `TESSERACT_LANGUAGES`: Default language configuration
- `VISION_OCR_CONFIDENCE_THRESHOLD`: Minimum confidence threshold

### 3. ImageAnalysisAgent (`app/vision/image_analysis_agent.py`)

**Purpose**: Multi-agent integration for vision analysis.

**Responsibilities**:
- Integrate vision capabilities with multi-agent system
- Route vision tasks to appropriate services
- Provide unified interface for agent coordination
- Handle OCR, object detection, scene understanding
- Analyze screenshots and documents

**Capabilities**:
- `image_captioning`
- `object_detection`
- `scene_understanding`
- `ocr`
- `screenshot_analysis`
- `chart_analysis`
- `table_extraction`
- `vision_reasoning`

### 4. VisionTool (`app/vision/vision_tool.py`)

**Purpose**: Tool wrapper for Tool Agent integration.

**Responsibilities**:
- Provide tool interface for vision operations
- Enable dynamic tool selection
- Handle permission validation
- Support tool chaining

**Operations**:
- `analyze`: General image analysis
- `ocr`: Text extraction
- `screenshot`: Screenshot analysis
- `compare`: Image comparison
- `extract_table`: Table extraction

### 5. ScreenshotAnalyzer (`app/vision/screenshot_analyzer.py`)

**Purpose**: Analyze screenshots for UI elements and application context.

**Responsibilities**:
- Detect UI elements (buttons, inputs, checkboxes, etc.)
- Identify application type (browser, desktop, form)
- Detect error dialogs
- Extract window titles
- Generate natural language descriptions

**UI Element Detection**:
- Edge detection using Sobel filters
- Contour finding and classification
- Aspect ratio and area-based classification
- Confidence scoring

### 6. DocumentVisionPipeline (`app/vision/document_vision_pipeline.py`)

**Purpose**: Process documents (PDFs) with vision capabilities.

**Responsibilities**:
- PDF page processing
- OCR on document pages
- Image extraction from PDFs
- Table detection in documents
- Form field detection
- Multi-page processing

**Dependencies**:
- PyMuPDF (fitz) for PDF processing

## Database Schema

### VisionAnalysis

Stores image analysis records.

**Fields**:
- `id`, `uuid`, `user_id`, `file_id`
- `analysis_type`: Type of analysis performed
- `status`: pending, processing, completed, failed
- `image_data`: Binary image data (for small images)
- `image_path`: Path to stored image
- `image_metadata`: Width, height, format, etc.
- `caption`, `objects_detected`, `scene_description`
- `ocr_text`, `ocr_confidence`, `ocr_blocks`
- `screenshot_analysis`, `tables_extracted`, `forms_extracted`
- `processing_time_seconds`, `model_used`, `overall_confidence`
- `error_message`, `error_code`
- `created_at`, `updated_at`, `completed_at`

### VisionBoundingBox

Stores bounding boxes for detected objects.

**Fields**:
- `id`, `analysis_id`
- `x`, `y`, `width`, `height`: Bounding box coordinates
- `label`: Object label/class
- `confidence`: Detection confidence
- `attributes`: Additional attributes

### DocumentVision

Stores document vision processing records.

**Fields**:
- `id`, `uuid`, `user_id`, `document_id`, `file_id`
- `file_path`, `file_format`, `page_count`
- `status`: Processing status
- `perform_ocr`, `ocr_language`
- `extract_images`, `extract_tables`
- `extracted_text`, `extracted_images`, `extracted_tables`, `extracted_forms`
- `processing_time_seconds`, `error_message`
- `created_at`, `updated_at`, `completed_at`

### DocumentVisionPage

Stores individual page results.

**Fields**:
- `id`, `document_vision_id`, `page_number`
- `text`, `ocr_text`, `ocr_confidence`
- `tables`, `forms`, `images`
- `metadata_json`

## API Endpoints

### POST /api/v1/vision/analyze

Analyze image with vision capabilities.

**Request**:
- `file`: Image file (multipart/form-data)
- `task_types`: JSON array of task types (e.g., `["image_captioning", "object_detection"]`)
- `options`: JSON string of additional options

**Response**: VisionAnalysisResponse

**Task Types**:
- `image_captioning`: Generate image caption
- `object_detection`: Detect objects in image
- `scene_understanding`: Understand scene context
- `chart_analysis`: Analyze charts and diagrams
- `table_extraction`: Extract table data

### POST /api/v1/vision/ocr

Perform OCR on uploaded image.

**Request**:
- `file`: Image file (multipart/form-data)
- `language`: Language code (optional, e.g., 'eng', 'fra')
- `preserve_layout`: Boolean (default: true)

**Response**: OCRResponse

### POST /api/v1/vision/screenshot

Analyze screenshot for UI elements.

**Request**:
- `file`: Screenshot image (multipart/form-data)
- `detect_ui_elements`: Boolean (default: true)
- `detect_errors`: Boolean (default: true)

**Response**: ScreenshotAnalysisResponse

### POST /api/v1/vision/document

Process document (PDF) with vision capabilities.

**Request**:
- `file`: PDF file (multipart/form-data)
- `perform_ocr`: Boolean (default: false)
- `ocr_language`: Language code (optional)
- `extract_images`: Boolean (default: false)
- `extract_tables`: Boolean (default: false)
- `page_numbers`: JSON array of specific pages (optional)

**Response**: DocumentVisionResponse

### GET /api/v1/vision/history

Get vision analysis history for current user.

**Query Parameters**:
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 100)
- `analysis_type`: Filter by analysis type (optional)

**Response**: List of VisionHistoryResponse

### GET /api/v1/vision/history/{analysis_uuid}

Get specific vision analysis by UUID.

**Response**: VisionAnalysisResponse

## Frontend Integration

### React Hooks (`services/vision-hooks.ts`)

- `useAnalyzeImage()`: Analyze image with task types
- `usePerformOCR()`: Perform OCR on image
- `useAnalyzeScreenshot()`: Analyze screenshot
- `useProcessDocument()`: Process PDF document
- `useVisionHistory()`: Get analysis history
- `useVisionAnalysis()`: Get specific analysis

### Vision Page (`pages/VisionPage.tsx`)

Main page for vision operations with tabs:
- **Analyze Image**: Image analysis with multiple task types
- **OCR**: Text extraction with language options
- **Screenshot**: UI element detection and analysis
- **Document**: PDF processing with OCR and extraction
- **History**: View past analyses

### Components

- **ImageUpload**: Drag-and-drop image upload
- **ScreenshotUpload**: Screenshot upload component
- **OCRViewer**: Display OCR results with confidence scores
- **BoundingBoxOverlay**: Display detected objects with bounding boxes
- **ConfidenceScores**: Display confidence metrics and processing time
- **HistoryTab**: Display analysis history with status and results

## Processing Pipeline

### Image Analysis Pipeline

```
1. Image Upload
   ↓
2. Validation (format, size, integrity)
   ↓
3. Metadata Extraction (width, height, format)
   ↓
4. Preprocessing (resize, normalize)
   ↓
5. Task Execution (captioning, detection, etc.)
   ↓
6. Result Aggregation
   ↓
7. Database Storage
   ↓
8. Response
```

### OCR Pipeline

```
1. Image Upload
   ↓
2. Validation
   ↓
3. Tesseract Processing
   ↓
4. Text Block Extraction
   ↓
5. Confidence Scoring
   ↓
6. Layout Analysis
   ↓
7. Language Detection
   ↓
8. Response
```

### Screenshot Analysis Pipeline

```
1. Screenshot Upload
   ↓
2. Validation
   ↓
3. Edge Detection
   ↓
4. Contour Finding
   ↓
5. UI Element Classification
   ↓
6. Error Dialog Detection
   ↓
7. Application Type Identification
   ↓
8. Description Generation
   ↓
9. Response
```

### Document Processing Pipeline

```
1. PDF Upload
   ↓
2. Page Extraction
   ↓
3. Per-Page Processing
   ├─ Text Extraction
   ├─ OCR (if enabled)
   ├─ Image Extraction
   ├─ Table Detection
   └─ Form Detection
   ↓
4. Result Aggregation
   ↓
5. Database Storage
   ↓
6. Response
```

## Supported Formats

### Image Formats
- PNG
- JPG/JPEG
- GIF
- BMP
- WebP
- TIFF

### Document Formats
- PDF (requires PyMuPDF)

## Performance Considerations

### Image Size Limits
- Maximum image size: 10MB (configurable)
- Images larger than 1MB stored as file path, not binary data
- Recommended resolution: 1920x1080 or lower

### Processing Time
- Image captioning: ~2-5 seconds
- OCR: ~1-3 seconds per image
- Screenshot analysis: ~1-2 seconds
- Document processing: ~2-5 seconds per page

### Optimization Tips
- Use appropriate image sizes
- Enable only required task types
- Batch process multiple images when possible
- Cache frequently analyzed images
- Use layout-aware OCR for structured documents

## Security Considerations

### File Validation
- Strict format validation
- Size limits enforced
- Malicious file detection
- Sanitization of extracted text

### Permission Validation
- VisionTool validates user permissions
- File access restricted to user's own files
- Analysis records scoped to user

### Data Privacy
- Image data stored securely
- OCR results encrypted at rest
- User-scoped analysis history
- Optional image data deletion after processing

## Deployment Guide

### Prerequisites

**System Dependencies**:
- Tesseract OCR engine
- Python 3.9+
- PostgreSQL database
- Redis (for caching)

**Python Packages**:
```
Pillow
pytesseract
numpy
scipy
PyMuPDF
```

### Installation

1. **Install Tesseract OCR**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra
   
   # macOS
   brew install tesseract
   
   # Windows
   Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install Pillow pytesseract numpy scipy PyMuPDF
   ```

3. **Configure Environment Variables**:
   ```bash
   TESSERACT_PATH=/usr/bin/tesseract
   TESSERACT_LANGUAGES=eng+fra+deu+spa+ita+por+chi_sim+jpn
   VISION_MAX_IMAGE_SIZE=10485760
   ENABLE_VISION=true
   ```

4. **Run Database Migrations**:
   ```bash
   alembic revision --autogenerate -m "Add vision tables"
   alembic upgrade head
   ```

5. **Verify Installation**:
   ```python
   from app.vision.ocr_service import ocr_service
   ocr_service.verify_installation()  # Should return True
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

# Install Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set environment variables
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV ENABLE_VISION=true

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

**Tesseract not found**:
- Verify Tesseract installation: `tesseract --version`
- Set `TESSERACT_PATH` in configuration
- Check file permissions

**OCR accuracy low**:
- Ensure image quality is sufficient
- Use appropriate language setting
- Enable layout preservation for structured documents
- Preprocess images (contrast, denoise)

**Memory errors with large images**:
- Reduce image size before upload
- Enable image compression
- Process images in batches

**PDF processing fails**:
- Verify PyMuPDF installation: `pip show PyMuPDF`
- Check PDF file integrity
- Ensure sufficient disk space for temporary files

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("app.vision").setLevel(logging.DEBUG)
```

## Testing

### Unit Tests
```bash
pytest tests/test_vision_service.py
pytest tests/test_ocr_service.py
pytest tests/test_screenshot_analyzer.py
```

### Integration Tests
```bash
pytest tests/test_vision_integration.py
```

### Test Coverage
- VisionService: Image validation, metadata extraction, analysis
- OCRService: Text extraction, layout analysis, language detection
- ScreenshotAnalyzer: UI element detection, classification
- VisionTool: Tool operations, integration
- DocumentVisionPipeline: PDF processing, extraction

## Future Enhancements

### Planned Features
- GPT-4 Vision integration for advanced understanding
- Real-time video analysis
- Face detection and recognition
- Barcode and QR code scanning
- Advanced table extraction with cell merging
- Form field auto-filling
- Handwriting recognition improvement
- Multi-page document comparison
- Image search and similarity matching

### Optimization Opportunities
- GPU acceleration for image processing
- Distributed processing for large batches
- Model quantization for faster inference
- Result caching with Redis
- Progressive image loading
- Streaming OCR for large documents

## Backward Compatibility

The Vision Intelligence System maintains backward compatibility:
- Existing Jarvis AI features unchanged
- Vision features opt-in via feature flag
- No breaking changes to existing APIs
- Database migrations additive only
- Frontend routes added without modifying existing navigation

## Contributing

### Adding New Vision Capabilities

1. Extend `VisionTaskType` enum in `base.py`
2. Implement capability in `VisionService`
3. Add API endpoint if needed
4. Update database schema if required
5. Add frontend UI components
6. Write tests
7. Update documentation

### Adding New OCR Languages

1. Install Tesseract language data
2. Update `TESSERACT_LANGUAGES` configuration
3. Update language mapping in `OCRService`
4. Test with sample documents

## License

This Vision Intelligence System is part of Jarvis AI v1.1 and follows the same license terms.

## Contact

For questions or issues related to the Vision Intelligence System, please refer to the main project documentation or contact the development team.
