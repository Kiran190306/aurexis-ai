"""
VisionTool - Tool integration for the Tool Agent to perform vision operations.
"""
from typing import Dict, List, Any, Optional
from PIL import Image
import io
from loguru import logger

from app.vision.base import VisionTaskType, VisionAnalysisResult
from app.vision.vision_service import vision_service
from app.vision.ocr_service import ocr_service
from app.vision.screenshot_analyzer import screenshot_analyzer


class VisionTool:
    """Tool wrapper for vision operations to be used by the Tool Agent."""
    
    def __init__(self) -> None:
        self.name = "vision_tool"
        self.description = "Perform image analysis, OCR, and screenshot understanding"
        self.permissions = ["image_analysis", "ocr", "screenshot_analysis"]
    
    async def execute(
        self,
        operation: str,
        image_data: bytes,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a vision operation."""
        parameters = parameters or {}
        
        try:
            if operation == "analyze":
                return await self._analyze_image(image_data, parameters)
            elif operation == "ocr":
                return await self._perform_ocr(image_data, parameters)
            elif operation == "screenshot":
                return await self._analyze_screenshot(image_data, parameters)
            elif operation == "compare":
                return await self._compare_images(image_data, parameters)
            elif operation == "extract_table":
                return await self._extract_table(image_data, parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
        
        except Exception as e:
            logger.error(f"Vision tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_image(self, image_data: bytes, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image with specified task types."""
        task_types = parameters.get("task_types", ["image_captioning"])
        
        # Convert string task types to enum
        task_type_enums = []
        for task_type in task_types:
            try:
                task_type_enums.append(VisionTaskType(task_type))
            except ValueError:
                logger.warning(f"Invalid task type: {task_type}")
        
        if not task_type_enums:
            task_type_enums = [VisionTaskType.IMAGE_CAPTIONING]
        
        result = await vision_service.analyze_image(image_data, task_type_enums, parameters)
        
        return {
            "success": result.success,
            "caption": result.caption,
            "objects": [obj.dict() for obj in result.objects],
            "scene_description": result.scene_description,
            "processing_time": result.processing_time_seconds,
            "error": result.error_message
        }
    
    async def _perform_ocr(self, image_data: bytes, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform OCR on image."""
        # Validate and open image
        is_valid, error_msg, image = await vision_service.validate_image(image_data)
        if not is_valid:
            return {"success": False, "error": error_msg}
        
        # Extract text
        language = parameters.get("language")
        preserve_structure = parameters.get("preserve_structure", True)
        
        if preserve_structure:
            if image is not None:
                ocr_result = await ocr_service.extract_text_with_layout(image, preserve_structure=preserve_structure)
            else:
                return {"success": False, "error": "Invalid image"}
        else:
            if image is not None:
                ocr_result = await ocr_service.extract_text(image, language=language)
            else:
                return {"success": False, "error": "Invalid image"}
        
        return {
            "success": True,
            "text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "blocks": ocr_result.blocks,
            "language": ocr_result.language,
            "layout": ocr_result.layout
        }
    
    async def _analyze_screenshot(self, image_data: bytes, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze screenshot."""
        # Validate and open image
        is_valid, error_msg, image = await vision_service.validate_image(image_data)
        if not is_valid:
            return {"success": False, "error": error_msg}
        
        # Analyze screenshot
        if image is not None:
            analysis = await screenshot_analyzer.analyze(image, parameters)
        else:
            return {"success": False, "error": "Invalid image"}
        
        return {
            "success": True,
            "window_title": analysis.window_title,
            "application_type": analysis.application_type,
            "ui_elements": [elem.dict() for elem in analysis.ui_elements],
            "error_dialogs": [dialog.dict() for dialog in analysis.error_dialogs],
            "description": analysis.description
        }
    
    async def _compare_images(self, image_data: bytes, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Compare image with another image."""
        # Get comparison image
        comparison_data = parameters.get("comparison_image")
        if not comparison_data:
            return {"success": False, "error": "No comparison image provided"}
        
        # Validate both images
        is_valid1, error_msg1, image1 = await vision_service.validate_image(image_data)
        is_valid2, error_msg2, image2 = await vision_service.validate_image(comparison_data)
        
        if not is_valid1:
            return {"success": False, "error": f"First image invalid: {error_msg1}"}
        if not is_valid2:
            return {"success": False, "error": f"Second image invalid: {error_msg2}"}
        
        # Compare
        if image1 is not None and image2 is not None:
            comparison = vision_service.compare_images(image1, image2)
        else:
            return {"success": False, "error": "Invalid images"}
        
        return {
            "success": True,
            "similarity_score": comparison["similarity_score"],
            "mean_squared_error": comparison["mean_squared_error"],
            "are_identical": comparison["are_identical"]
        }
    
    async def _extract_table(self, image_data: bytes, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract table data from image."""
        # Validate image
        is_valid, error_msg, image = await vision_service.validate_image(image_data)
        if not is_valid:
            return {"success": False, "error": error_msg}
        
        # Extract table
        result = await vision_service.analyze_image(
            image_data,
            [VisionTaskType.TABLE_EXTRACTION],
            parameters
        )
        
        return {
            "success": result.success,
            "tables": [table.dict() for table in result.tables],
            "processing_time": result.processing_time_seconds,
            "error": result.error_message
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for registration."""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "operations": [
                {
                    "name": "analyze",
                    "description": "Analyze image (captioning, object detection, scene understanding)",
                    "parameters": {
                        "task_types": {
                            "type": "array",
                            "description": "List of task types to perform",
                            "default": ["image_captioning"]
                        }
                    }
                },
                {
                    "name": "ocr",
                    "description": "Extract text from image using OCR",
                    "parameters": {
                        "language": {
                            "type": "string",
                            "description": "Language code for OCR (e.g., 'eng', 'fra')",
                            "default": None
                        },
                        "preserve_layout": {
                            "type": "boolean",
                            "description": "Preserve text layout",
                            "default": True
                        }
                    }
                },
                {
                    "name": "screenshot",
                    "description": "Analyze screenshot for UI elements",
                    "parameters": {}
                },
                {
                    "name": "compare",
                    "description": "Compare two images for similarity",
                    "parameters": {
                        "comparison_image": {
                            "type": "bytes",
                            "description": "Second image to compare with",
                            "required": True
                        }
                    }
                },
                {
                    "name": "extract_table",
                    "description": "Extract table data from image",
                    "parameters": {}
                }
            ]
        }


# Global vision tool instance
vision_tool = VisionTool()
