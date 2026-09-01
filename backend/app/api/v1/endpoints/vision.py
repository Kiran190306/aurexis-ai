"""
API endpoints for Vision Intelligence System.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from loguru import logger
from datetime import datetime
import io

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.config import settings
from app.models.user import User
from app.models.vision import (
    VisionAnalysis,
    VisionAnalysisType,
    VisionAnalysisStatus,
    VisionBoundingBox,
    DocumentVision
)
from app.schemas.vision import (
    VisionAnalyzeRequest,
    OCRRequest,
    ScreenshotAnalysisRequest,
    DocumentVisionRequest,
    VisionAnalysisResponse,
    OCRResponse,
    ScreenshotAnalysisResponse,
    DocumentVisionResponse,
    VisionHistoryResponse
)
from app.vision.base import VisionTaskType
from app.vision.vision_service import vision_service
from app.vision.ocr_service import ocr_service
from app.vision.screenshot_analyzer import screenshot_analyzer
from app.vision.document_vision_pipeline import document_vision_pipeline

router = APIRouter()


@router.post("/analyze", response_model=VisionAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    task_types: str = Form(default="image_captioning"),
    options: Optional[str] = Form(default=None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> VisionAnalysisResponse:
    """Analyze image with vision capabilities."""
    logger.info(f"User {current_user_id} requesting image analysis")
    
    try:
        # Check if vision is enabled
        if not settings.ENABLE_VISION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vision features are disabled"
            )
        
        # Read image data
        image_data = await file.read()
        
        # Validate image
        is_valid, error_msg, image = await vision_service.validate_image(image_data)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Parse task types
        import json
        task_types_list = json.loads(task_types) if isinstance(task_types, str) else task_types
        options_dict = json.loads(options) if options else {}
        
        # Convert to VisionTaskType enums
        vision_task_types = []
        for tt in task_types_list:
            try:
                vision_task_types.append(VisionTaskType(tt))
            except ValueError:
                logger.warning(f"Invalid task type: {tt}")
        
        if not vision_task_types:
            vision_task_types = [VisionTaskType.IMAGE_CAPTIONING]
        
        # Create database record
        analysis = VisionAnalysis(
            user_id=current_user_id,
            analysis_type=VisionAnalysisType(vision_task_types[0].value),
            status=VisionAnalysisStatus.PROCESSING,
            image_data=image_data if len(image_data) < 1048576 else None,  # Store if < 1MB
            image_metadata=vision_service.extract_image_metadata(image).dict() if image is not None else {},
            analysis_options=options_dict
        )
        
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        # Perform analysis
        import time
        start_time = time.time()
        
        try:
            result = await vision_service.analyze_image(image_data, vision_task_types, options_dict)
            
            # Update database with results
            analysis.status = VisionAnalysisStatus.COMPLETED  # type: ignore[assignment]
            analysis.caption = result.caption  # type: ignore[assignment]
            analysis.objects_detected = [obj.dict() for obj in result.objects]  # type: ignore[assignment]
            analysis.scene_description = result.scene_description  # type: ignore[assignment]
            analysis.tables_extracted = [table.dict() for table in result.tables]  # type: ignore[assignment]
            analysis.reasoning = result.reasoning  # type: ignore[assignment]
            analysis.processing_time_seconds = result.processing_time_seconds  # type: ignore[assignment]
            analysis.overall_confidence = result.confidence  # type: ignore[assignment]
            analysis.completed_at = datetime.utcnow()  # type: ignore[assignment]
            
            # Store bounding boxes
            for obj in result.objects:
                bbox = VisionBoundingBox(
                    analysis_id=analysis.id,
                    x=obj.bounding_box.x,
                    y=obj.bounding_box.y,
                    width=obj.bounding_box.width,
                    height=obj.bounding_box.height,
                    label=obj.bounding_box.label,
                    confidence=obj.bounding_box.confidence,
                    attributes=obj.attributes
                )
                db.add(bbox)
            
            await db.commit()
            await db.refresh(analysis)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            analysis.status = VisionAnalysisStatus.FAILED  # type: ignore[assignment]
            analysis.error_message = str(e)  # type: ignore[assignment]
            analysis.completed_at = datetime.utcnow()  # type: ignore[assignment]
            await db.commit()
            await db.refresh(analysis)
        
        return analysis
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
    preserve_layout: bool = Form(default=True),
    current_user_id: int = Depends(get_current_user_id)
) -> OCRResponse:
    """Perform OCR on uploaded image."""
    logger.info(f"User {current_user_id} requesting OCR")
    
    try:
        if not settings.ENABLE_VISION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vision features are disabled"
            )
        
        # Read image data
        image_data = await file.read()
        
        # Validate image
        is_valid, error_msg, image = await vision_service.validate_image(image_data)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Perform OCR
        if preserve_layout:
            if image is not None:
                ocr_result = await ocr_service.extract_text_with_layout(image)
            else:
                raise HTTPException(status_code=400, detail="Invalid image")
        else:
            if image is not None:
                ocr_result = await ocr_service.extract_text(image, language=language)
            else:
                raise HTTPException(status_code=400, detail="Invalid image")
        
        return OCRResponse(
            text=ocr_result.text,
            confidence=ocr_result.confidence,
            blocks=ocr_result.blocks,
            language=ocr_result.language,
            layout=ocr_result.layout
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR failed: {str(e)}"
        )


@router.post("/screenshot", response_model=ScreenshotAnalysisResponse)
async def analyze_screenshot(
    file: UploadFile = File(...),
    detect_ui_elements: bool = Form(default=True),
    detect_errors: bool = Form(default=True),
    current_user_id: int = Depends(get_current_user_id)
) -> ScreenshotAnalysisResponse:
    """Analyze screenshot for UI elements."""
    logger.info(f"User {current_user_id} requesting screenshot analysis")
    
    try:
        if not settings.ENABLE_VISION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vision features are disabled"
            )
        
        # Read image data
        image_data = await file.read()
        
        # Validate image
        is_valid, error_msg, image = await vision_service.validate_image(image_data)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Analyze screenshot
        options = {
            "detect_ui_elements": detect_ui_elements,
            "detect_errors": detect_errors
        }
        
        if image is not None:
            analysis = await screenshot_analyzer.analyze(image, options)
        else:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        return ScreenshotAnalysisResponse(
            window_title=analysis.window_title,
            application_type=analysis.application_type,
            ui_elements=[elem.dict() for elem in analysis.ui_elements],
            error_dialogs=[dialog.dict() for dialog in analysis.error_dialogs],
            description=analysis.description
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screenshot analysis endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screenshot analysis failed: {str(e)}"
        )


@router.post("/document", response_model=DocumentVisionResponse)
async def process_document_vision(
    file: UploadFile = File(...),
    perform_ocr: bool = Form(default=False),
    ocr_language: Optional[str] = Form(default=None),
    extract_images: bool = Form(default=False),
    extract_tables: bool = Form(default=False),
    page_numbers: Optional[str] = Form(default=None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> DocumentVisionResponse:
    """Process document (PDF) with vision capabilities."""
    logger.info(f"User {current_user_id} requesting document vision processing")
    
    try:
        if not settings.ENABLE_VISION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vision features are disabled"
            )
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name
        
        try:
            # Parse page numbers
            page_nums = None
            if page_numbers:
                import json
                page_nums = json.loads(page_numbers)
            
            # Process document
            result = await document_vision_pipeline.process_document(
                tmp_path,
                {
                    "perform_ocr": perform_ocr,
                    "ocr_language": ocr_language,
                    "extract_images": extract_images,
                    "extract_tables": extract_tables
                }
            )
            
            # Create database record
            doc_vision = DocumentVision(
                user_id=current_user_id,
                file_path=tmp_path,
                file_format="pdf",
                page_count=result.get("page_count", 0),
                status=VisionAnalysisStatus.COMPLETED if result.get("success") else VisionAnalysisStatus.FAILED,
                perform_ocr=perform_ocr,
                ocr_language=ocr_language,
                extract_images=extract_images,
                extract_tables=extract_tables,
                error_message=result.get("error")
            )
            
            db.add(doc_vision)
            await db.commit()
            await db.refresh(doc_vision)
            
            return doc_vision
        
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document vision endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/history", response_model=List[VisionHistoryResponse])
async def get_vision_history(
    skip: int = 0,
    limit: int = 100,
    analysis_type: Optional[str] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[VisionHistoryResponse]:
    """Get vision analysis history for current user."""
    try:
        query = select(VisionAnalysis).where(VisionAnalysis.user_id == current_user_id)
        
        if analysis_type:
            try:
                query = query.where(VisionAnalysis.analysis_type == VisionAnalysisType(analysis_type))
            except ValueError:
                pass
        
        query = query.order_by(VisionAnalysis.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        analyses = result.scalars().all()
        
        # Convert to response format
        return [
            VisionHistoryResponse(
                id=int(analysis.id),
                uuid=str(analysis.uuid),
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                created_at=str(analysis.created_at),
                completed_at=str(analysis.completed_at) if analysis.completed_at else None,
                processing_time_seconds=float(analysis.processing_time_seconds) if analysis.processing_time_seconds is not None else None,
                overall_confidence=float(analysis.overall_confidence) if analysis.overall_confidence is not None else None
            )
            for analysis in analyses
        ]
    
    except Exception as e:
        logger.error(f"Failed to get vision history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/history/{analysis_uuid}", response_model=VisionAnalysisResponse)
async def get_vision_analysis(
    analysis_uuid: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> VisionAnalysisResponse:
    """Get specific vision analysis by UUID."""
    try:
        result = await db.execute(
            select(VisionAnalysis).where(
                and_(
                    VisionAnalysis.uuid == analysis_uuid,
                    VisionAnalysis.user_id == current_user_id
                )
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return analysis  # type: ignore[no-any-return]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vision analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )
