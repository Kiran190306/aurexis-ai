"""
ImageAnalysisAgent - Multi-agent integration for vision analysis.
"""
from typing import Dict, List, Any, Optional
from PIL import Image
import io
from loguru import logger

from app.agents.base import BaseAgent, AgentRole, Task, AgentResponse
from app.vision.base import VisionTaskType, VisionAnalysisResult
from app.vision.vision_service import vision_service
from app.vision.ocr_service import ocr_service


class ImageAnalysisAgent(BaseAgent):
    """Agent for image analysis within the multi-agent system."""
    
    def __init__(self, agent_id: str = "image_analysis", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.TOOL  # Vision is a tool capability
        self.system_prompt = """You are an Image Analysis Agent for Jarvis AI. Your role is to:
1. Analyze images and extract meaningful information
2. Perform OCR to extract text from images
3. Detect and identify objects in images
4. Understand scenes and contexts
5. Analyze screenshots and UI elements
6. Extract data from charts and tables
7. Provide detailed visual descriptions and insights"""
    
    async def initialize(self) -> None:
        """Initialize the image analysis agent."""
        logger.info(f"Initializing Image Analysis Agent: {self.agent_id}")
        
        # Verify OCR installation
        if not ocr_service.verify_installation():
            logger.warning("Tesseract OCR not properly installed - OCR features may be limited")
    
    async def shutdown(self) -> None:
        """Shutdown the image analysis agent."""
        logger.info(f"Shutting down Image Analysis Agent: {self.agent_id}")
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute an image analysis task."""
        logger.info(f"Image Analysis Agent executing task: {task.id}")
        
        try:
            analysis_type = task.input_data.get("analysis_type", "general")
            image_data = task.input_data.get("image_data")
            image_path = task.input_data.get("image_path")
            
            # Get image from data or path
            if image_data:
                image_bytes = image_data
            elif image_path:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
            else:
                return AgentResponse(
                    success=False,
                    error="No image data or path provided"
                )
            
            # Route to appropriate analysis method
            if analysis_type == "ocr":
                return await self._perform_ocr(image_bytes, task)
            elif analysis_type == "object_detection":
                return await self._detect_objects(image_bytes, task)
            elif analysis_type == "scene_understanding":
                return await self._understand_scene(image_bytes, task)
            elif analysis_type == "screenshot":
                return await self._analyze_screenshot(image_bytes, task)
            elif analysis_type == "chart":
                return await self._analyze_chart(image_bytes, task)
            elif analysis_type == "table":
                return await self._extract_table(image_bytes, task)
            elif analysis_type == "general":
                return await self._general_analysis(image_bytes, task)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown analysis type: {analysis_type}"
                )
        
        except Exception as e:
            logger.error(f"Image Analysis Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _perform_ocr(self, image_bytes: bytes, task: Task) -> AgentResponse:
        """Perform OCR on image."""
        try:
            # Validate and open image
            is_valid, error_msg, image = await vision_service.validate_image(image_bytes)
            if not is_valid:
                return AgentResponse(success=False, error=error_msg)
            
            # Extract text
            language = task.input_data.get("language")
            preserve_layout = task.input_data.get("preserve_layout", True)
            
            if preserve_layout:
                if image is not None:
                    ocr_result = await ocr_service.extract_text_with_layout(image)
                else:
                    return AgentResponse(success=False, error="Invalid image")
            else:
                if image is not None:
                    ocr_result = await ocr_service.extract_text(image, language=language)
                else:
                    return AgentResponse(success=False, error="Invalid image")
            
            return AgentResponse(
                success=True,
                data={
                    "text": ocr_result.text,
                    "confidence": ocr_result.confidence,
                    "blocks": ocr_result.blocks,
                    "language": ocr_result.language,
                    "layout": ocr_result.layout
                }
            )
        
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _detect_objects(self, image_bytes: bytes, task: Task) -> AgentResponse:
        """Detect objects in image."""
        try:
            # Validate image
            is_valid, error_msg, image = await vision_service.validate_image(image_bytes)
            if not is_valid:
                return AgentResponse(success=False, error=error_msg)
            
            # Perform object detection
            result = await vision_service.analyze_image(
                image_bytes,
                [VisionTaskType.OBJECT_DETECTION],
                task.input_data
            )
            
            return AgentResponse(
                success=result.success,
                data={
                    "objects": [obj.dict() for obj in result.objects],
                    "caption": result.caption,
                    "processing_time": result.processing_time_seconds
                },
                error=result.error_message
            )
        
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _understand_scene(self, image_bytes: bytes, task: Task) -> AgentResponse:
        """Understand scene in image."""
        try:
            # Validate image
            is_valid, error_msg, image = await vision_service.validate_image(image_bytes)
            if not is_valid:
                return AgentResponse(success=False, error=error_msg)
            
            # Perform scene understanding
            result = await vision_service.analyze_image(
                image_bytes,
                [VisionTaskType.SCENE_UNDERSTANDING, VisionTaskType.IMAGE_CAPTIONING],
                task.input_data
            )
            
            return AgentResponse(
                success=result.success,
                data={
                    "description": result.scene_description,
                    "caption": result.caption,
                    "processing_time": result.processing_time_seconds
                },
                error=result.error_message
            )
        
        except Exception as e:
            logger.error(f"Scene understanding failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _analyze_screenshot(self, image_bytes: bytes, task: Task) -> AgentResponse:
        """Analyze screenshot for UI elements."""
        try:
            # Validate image
            is_valid, error_msg, image = await vision_service.validate_image(image_bytes)
            if not is_valid:
                return AgentResponse(success=False, error=error_msg)
            
            # Perform screenshot analysis
            from app.vision.screenshot_analyzer import screenshot_analyzer
            if image is not None:
                analysis = await screenshot_analyzer.analyze(image, task.input_data)
            else:
                return AgentResponse(success=False, error="Invalid image")
            
            return AgentResponse(
                success=True,
                data=analysis.dict()
            )
        
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _analyze_chart(self, image_bytes: bytes, task: Task) -> AgentResponse:
        """Analyze chart or diagram."""
        try:
            # Validate image
            is_valid, error_msg, image = await vision_service.validate_image(image_bytes)
            if not is_valid:
                return AgentResponse(success=False, error=error_msg)
            
            # Perform chart analysis
            result = await vision_service.analyze_image(
                image_bytes,
                [VisionTaskType.CHART_ANALYSIS],
                task.input_data
            )
            
            return AgentResponse(
                success=result.success,
                data={
                    "chart_analysis": result.metadata.get('task_results', {}).get('chart_analysis'),
                    "processing_time": result.processing_time_seconds
                },
                error=result.error_message
            )
        
        except Exception as e:
            logger.error(f"Chart analysis failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _extract_table(self, image_bytes: bytes, task: Task) -> AgentResponse:
        """Extract table data from image."""
        try:
            # Validate image
            is_valid, error_msg, image = await vision_service.validate_image(image_bytes)
            if not is_valid:
                return AgentResponse(success=False, error=error_msg)
            
            # Perform table extraction
            result = await vision_service.analyze_image(
                image_bytes,
                [VisionTaskType.TABLE_EXTRACTION],
                task.input_data
            )
            
            return AgentResponse(
                success=result.success,
                data={
                    "tables": [table.dict() for table in result.tables],
                    "processing_time": result.processing_time_seconds
                },
                error=result.error_message
            )
        
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _general_analysis(self, image_bytes: bytes, task: Task) -> AgentResponse:
        """Perform general image analysis."""
        try:
            # Validate image
            is_valid, error_msg, image = await vision_service.validate_image(image_bytes)
            if not is_valid:
                return AgentResponse(success=False, error=error_msg)
            
            # Perform comprehensive analysis
            result = await vision_service.analyze_image(
                image_bytes,
                [
                    VisionTaskType.IMAGE_CAPTIONING,
                    VisionTaskType.OBJECT_DETECTION,
                    VisionTaskType.SCENE_UNDERSTANDING
                ],
                task.input_data
            )
            
            return AgentResponse(
                success=result.success,
                data={
                    "caption": result.caption,
                    "objects": [obj.dict() for obj in result.objects],
                    "scene_description": result.scene_description,
                    "processing_time": result.processing_time_seconds,
                    "metadata": result.metadata
                },
                error=result.error_message
            )
        
        except Exception as e:
            logger.error(f"General analysis failed: {e}")
            return AgentResponse(success=False, error=str(e))
    
    def get_capabilities(self) -> List[str]:
        """Return image analysis agent capabilities."""
        return [
            "image_captioning",
            "object_detection",
            "scene_understanding",
            "ocr",
            "screenshot_analysis",
            "chart_analysis",
            "table_extraction",
            "vision_reasoning"
        ]
