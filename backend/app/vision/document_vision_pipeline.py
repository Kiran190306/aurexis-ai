"""
DocumentVisionPipeline - Process documents (PDFs) with vision capabilities.
"""
from typing import Dict, List, Any, Optional
from PIL import Image
import io
from loguru import logger
from pathlib import Path

from app.vision.base import TableData, BoundingBox, OCRResult
from app.vision.ocr_service import ocr_service


class DocumentVisionPipeline:
    """Pipeline for processing documents with vision capabilities."""
    
    def __init__(self) -> None:
        self.supported_formats = ['pdf']
    
    async def process_document(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a document and extract vision-based information."""
        options = options or {}
        
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        
        if file_ext not in self.supported_formats:
            return {
                "success": False,
                "error": f"Unsupported file format: {file_ext}"
            }
        
        results: Dict[str, Any] = {
            "success": True,
            "file_path": file_path,
            "pages": [],
            "tables": [],
            "forms": [],
            "images": []
        }
        
        if file_ext == 'pdf':
            return await self._process_pdf(file_path, options, results)
        
        return {
            "success": False,
            "error": "Format not implemented"
        }
    
    async def _process_pdf(self, pdf_path: str, options: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Process PDF document with vision capabilities."""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            
            results = {
                "success": True,
                "page_count": page_count,
                "pages": [],
                "tables": [],
                "forms": [],
                "images": []
            }
            
            # Process each page
            for page_num in range(page_count):
                page = doc[page_num]
                page_result = await self._process_page(page, page_num, options)
                results["pages"].append(page_result)
                
                # Collect tables from all pages
                results["tables"].extend(page_result.get("tables", []))
                results["forms"].extend(page_result.get("forms", []))
                results["images"].extend(page_result.get("images", []))
            
            doc.close()
            
            return results
        
        except ImportError:
            logger.error("PyMuPDF not installed - PDF processing not available")
            return {
                "success": False,
                "error": "PyMuPDF required for PDF processing"
            }
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_page(
        self,
        page: Any,
        page_num: int,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single PDF page."""
        result: Dict[str, Any] = {
            "page_number": page_num,
            "text": "",
            "tables": [],
            "forms": [],
            "images": []
        }
        
        try:
            # Extract text
            text = page.get_text()
            result["text"] = text
            
            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_data = base_image["image"]
                
                result["images"].append({
                    "index": img_index,
                    "xref": xref,
                    "size": len(image_data),
                    "format": base_image.get("ext", "unknown")
                })
            
            # Detect tables (simplified - in production use table detection model)
            tables = await self._detect_tables(page, page_num)
            result["tables"] = tables
            
            # Detect forms (simplified)
            forms = await self._detect_forms(page, page_num)
            result["forms"] = forms
            
            # OCR if requested
            if options.get("perform_ocr", False):
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                ocr_result = await ocr_service.extract_text(image)
                result["ocr_text"] = ocr_result.text
                result["ocr_confidence"] = ocr_result.confidence
            
        except Exception as e:
            logger.error(f"Page {page_num} processing failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _detect_tables(self, page: Any, page_num: int) -> List[Dict[str, Any]]:
        """Detect tables in PDF page."""
        # In production, use table detection model
        # For now, use simple heuristic based on text layout
        
        text = page.get_text()
        lines = text.split('\n')
        
        tables = []
        current_table = []
        
        for line in lines:
            # Check if line looks like table row (multiple tabs/spaces)
            if '\t' in line or '  ' in line:
                current_table.append(line)
            else:
                if len(current_table) > 2:  # At least 3 rows
                    tables.append({
                        "page_number": page_num,
                        "rows": len(current_table),
                        "content": current_table
                    })
                current_table = []
        
        if len(current_table) > 2:
            tables.append({
                "page_number": page_num,
                "rows": len(current_table),
                "content": current_table
            })
        
        return tables
    
    async def _detect_forms(self, page: Any, page_num: int) -> List[Dict[str, Any]]:
        """Detect form fields in PDF page."""
        # In production, use form field detection
        # For now, check for form widgets
        
        forms = []
        
        if page.widgets:
            for widget in page.widgets:
                field_type = widget.field_type
                rect = widget.rect
                
                forms.append({
                    "page_number": page_num,
                    "field_type": field_type,
                    "rect": {
                        "x0": rect.x0,
                        "y0": rect.y0,
                        "x1": rect.x1,
                        "y1": rect.y1
                    },
                    "field_name": widget.field_name
                })
        
        return forms
    
    async def extract_images_from_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract all images from PDF."""
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            extracted_images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = page.parent.extract_image(xref)
                    image_data = base_image["image"]
                    image_ext = base_image.get("ext", "png")
                    
                    image_info = {
                        "page_number": page_num,
                        "image_index": img_index,
                        "xref": xref,
                        "size": len(image_data),
                        "format": image_ext,
                        "width": base_image.get("width"),
                        "height": base_image.get("height")
                    }
                    
                    # Save if output directory provided
                    if output_dir:
                        output_path = Path(output_dir) / f"page_{page_num}_img_{img_index}.{image_ext}"
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        image_info["saved_path"] = str(output_path)
                    
                    extracted_images.append(image_info)
            
            doc.close()
            
            return {
                "success": True,
                "total_images": len(extracted_images),
                "images": extracted_images
            }
        
        except ImportError:
            logger.error("PyMuPDF not installed")
            return {
                "success": False,
                "error": "PyMuPDF required"
            }
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def ocr_pdf(
        self,
        pdf_path: str,
        page_numbers: Optional[List[int]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform OCR on PDF pages."""
        try:
            ocr_results = await ocr_service.extract_from_pdf(pdf_path, page_numbers)
            
            return {
                "success": True,
                "total_pages": len(ocr_results),
                "results": [
                    {
                        "page_number": getattr(result, "metadata", {}).get("page_number", i) if hasattr(result, "metadata") else i,
                        "text": result.text,
                        "confidence": result.confidence,
                        "language": result.language
                    }
                    for i, result in enumerate(ocr_results)
                ]
            }
        
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Lazy-loaded document vision pipeline singleton
_document_vision_pipeline_instance: Optional[DocumentVisionPipeline] = None


def get_document_vision_pipeline() -> DocumentVisionPipeline:
    """Get or create the document vision pipeline instance (lazy-loaded)."""
    global _document_vision_pipeline_instance
    if _document_vision_pipeline_instance is None:
        _document_vision_pipeline_instance = DocumentVisionPipeline()
    return _document_vision_pipeline_instance


# Backward compatibility: allow importing document_vision_pipeline directly
class _DocumentVisionPipelineProxy:
    """Proxy for lazy-loaded document vision pipeline."""
    def __getattr__(self, name: str) -> Any:
        return getattr(get_document_vision_pipeline(), name)


document_vision_pipeline = _DocumentVisionPipelineProxy()
