"""
OCRService - Optical Character Recognition service using Tesseract.
"""
from typing import Optional, Dict, Any, List
from PIL import Image
import io
import pytesseract
from pytesseract import Output
import numpy as np
from loguru import logger

from app.core.config import settings
from app.vision.base import OCRResult, BoundingBox


class OCRService:
    """Service for OCR operations using Tesseract."""
    
    def __init__(self) -> None:
        self.tesseract_path = settings.TESSERACT_PATH
        self.languages = settings.TESSERACT_LANGUAGES
        self.confidence_threshold = settings.VISION_OCR_CONFIDENCE_THRESHOLD
        
        # Configure Tesseract path if specified
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        logger.info(f"OCRService initialized with Tesseract at {self.tesseract_path}")
        logger.info(f"Supported languages: {self.languages}")
    
    async def extract_text(
        self,
        image: Image.Image,
        language: Optional[str] = None,
        config: Optional[str] = None
    ) -> OCRResult:
        """Extract text from image using OCR."""
        try:
            # Use specified language or default
            lang = language or self.languages
            
            # Configure Tesseract options
            tesseract_config = config or '--oem 3 --psm 6'
            
            # Get OCR data with confidence scores
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=tesseract_config,
                output_type=Output.DICT
            )
            
            # Extract text and build blocks
            text_blocks = []
            full_text = []
            confidences = []
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > 0:
                    full_text.append(text)
                    confidences.append(conf)
                    
                    # Create block with position
                    block = {
                        'text': text,
                        'confidence': conf / 100.0,
                        'bounding_box': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    }
                    text_blocks.append(block)
            
            # Calculate overall confidence
            overall_confidence = np.mean(confidences) / 100.0 if confidences else 0.0
            
            # Detect language (simplified)
            detected_lang = self._detect_language(lang)
            
            # Extract layout information
            layout = self._extract_layout(data)
            
            return OCRResult(
                text=' '.join(full_text),
                confidence=float(overall_confidence),
                blocks=text_blocks,
                language=detected_lang,
                layout=layout
            )
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    async def extract_text_with_layout(
        self,
        image: Image.Image,
        preserve_structure: bool = True
    ) -> OCRResult:
        """Extract text with layout preservation."""
        if preserve_structure:
            # Use page segmentation mode for layout
            config = '--oem 3 --psm 1'
        else:
            config = '--oem 3 --psm 6'
        
        return await self.extract_text(image, config=config)
    
    async def extract_handwritten_text(self, image: Image.Image) -> OCRResult:
        """Extract handwritten text (experimental)."""
        # Use specialized configuration for handwriting
        config = '--oem 1 --psm 6'
        return await self.extract_text(image, config=config)
    
    async def extract_from_pdf(
        self,
        pdf_path: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[OCRResult]:
        """Extract text from PDF pages."""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            results = []
            
            pages_to_process = page_numbers or range(len(doc))
            
            for page_num in pages_to_process:
                if page_num >= len(doc):
                    logger.warning(f"Page {page_num} not found in PDF")
                    continue
                
                page = doc[page_num]
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                result = await self.extract_text(image)
                result.metadata = {'page_number': page_num}
                results.append(result)
            
            doc.close()
            return results
        
        except ImportError:
            logger.error("PyMuPDF not installed - PDF OCR not available")
            raise RuntimeError("PyMuPDF required for PDF OCR")
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            raise
    
    def _detect_language(self, lang_code: str) -> str:
        """Detect language from language code."""
        lang_map = {
            'eng': 'en',
            'fra': 'fr',
            'deu': 'de',
            'spa': 'es',
            'ita': 'it',
            'por': 'pt',
            'chi_sim': 'zh',
            'jpn': 'ja'
        }
        
        # Handle multiple languages
        if '+' in lang_code:
            primary_lang = lang_code.split('+')[0]
            return lang_map.get(primary_lang, 'en')
        
        return lang_map.get(lang_code, 'en')
    
    def _extract_layout(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract layout information from OCR data."""
        # Find text blocks and their positions
        blocks = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:
                blocks.append({
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'text': text
                })
        
        # Sort by y position (top to bottom)
        blocks.sort(key=lambda b: b['y'])
        
        # Group into lines
        lines = []
        current_line = []
        if blocks:
            current_y = blocks[0]['y']
            line_height_threshold = 20  # pixels
        
        for block in blocks:
            if abs(block['y'] - current_y) < line_height_threshold:
                current_line.append(block)
            else:
                if current_line:
                    lines.append(sorted(current_line, key=lambda b: b['x']))
                current_line = [block]
                current_y = block['y']
        
        if current_line:
            lines.append(sorted(current_line, key=lambda b: b['x']))
        
        return {
            'lines': len(lines),
            'blocks': len(blocks),
            'line_height_estimate': self._estimate_line_height(blocks) if blocks else 0
        }
    
    def _estimate_line_height(self, blocks: List[Dict[str, Any]]) -> float:
        """Estimate line height from text blocks."""
        if len(blocks) < 2:
            return 0
        
        heights = [b['height'] for b in blocks]
        return np.median(heights)  # type: ignore[no-any-return]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported Tesseract languages."""
        try:
            langs = pytesseract.get_languages(config='')
            return [lang for lang in langs if lang and not lang.startswith('.')]
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return ['eng']
    
    def verify_installation(self) -> bool:
        """Verify Tesseract installation."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
            return True
        except Exception as e:
            logger.error(f"Tesseract not installed or not accessible: {e}")
            return False


# Global OCR service instance
ocr_service = OCRService()
