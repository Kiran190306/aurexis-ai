"""
Document Ingestion System
Supports PDF, DOCX, PPTX, MD, TXT, HTML, CSV, JSON, XML, OCR, ZIP
"""
import hashlib
import zipfile
import io
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import mimetypes

from fastapi import UploadFile, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import (
    KnowledgeDocument,
    DocumentType,
    DocumentStatus,
)
from app.models.file import File
from app.core.config import settings


class DocumentIngestionError(Exception):
    """Base exception for document ingestion errors"""
    pass


class FileValidationError(DocumentIngestionError):
    """Exception for file validation errors"""
    pass


class FileSizeExceededError(FileValidationError):
    """Exception for file size exceeded"""
    pass


class UnsupportedFileTypeError(FileValidationError):
    """Exception for unsupported file types"""
    pass


class DocumentIngestor:
    """
    Production-grade document ingestion system
    Handles file validation, extraction, and initial processing
    """
    
    # Supported file types and their MIME types
    SUPPORTED_TYPES = {
        DocumentType.PDF: ['application/pdf'],
        DocumentType.DOCX: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        DocumentType.PPTX: ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
        DocumentType.MD: ['text/markdown', 'text/x-markdown'],
        DocumentType.TXT: ['text/plain'],
        DocumentType.HTML: ['text/html', 'application/xhtml+xml'],
        DocumentType.CSV: ['text/csv', 'application/csv'],
        DocumentType.JSON: ['application/json'],
        DocumentType.XML: ['application/xml', 'text/xml'],
        DocumentType.IMAGE: ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'image/bmp'],
        DocumentType.ZIP: ['application/zip', 'application/x-zip-compressed'],
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        DocumentType.PDF: 50 * 1024 * 1024,  # 50MB
        DocumentType.DOCX: 50 * 1024 * 1024,
        DocumentType.PPTX: 50 * 1024 * 1024,
        DocumentType.MD: 10 * 1024 * 1024,  # 10MB
        DocumentType.TXT: 10 * 1024 * 1024,
        DocumentType.HTML: 10 * 1024 * 1024,
        DocumentType.CSV: 50 * 1024 * 1024,
        DocumentType.JSON: 10 * 1024 * 1024,
        DocumentType.XML: 10 * 1024 * 1024,
        DocumentType.IMAGE: 20 * 1024 * 1024,  # 20MB
        DocumentType.ZIP: 100 * 1024 * 1024,  # 100MB
    }
    
    def __init__(self) -> None:
        self.max_total_size = settings.MAX_UPLOAD_SIZE or 500 * 1024 * 1024  # 500MB default
    
    async def validate_upload(
        self,
        file: UploadFile,
        user_id: int
    ) -> Tuple[bytes, DocumentType, str]:
        """
        Validate uploaded file and return content, type, and checksum
        
        Args:
            file: UploadFile from FastAPI
            user_id: User ID for permission checking
            
        Returns:
            Tuple of (content, document_type, checksum)
            
        Raises:
            FileValidationError: If file validation fails
        """
        # Read file content
        content = await file.read()
        
        # Validate file size
        file_size = len(content)
        if file_size == 0:
            raise FileValidationError("File is empty")
        
        if file_size > self.max_total_size:
            raise FileSizeExceededError(
                f"File size {file_size} bytes exceeds maximum {self.max_total_size} bytes"
            )
        
        # Detect file type
        file_type = self._detect_file_type(file.filename or "unknown", content)
        
        # Validate size for specific type
        max_size = self.MAX_FILE_SIZES.get(file_type, self.max_total_size)
        if file_size > max_size:
            raise FileSizeExceededError(
                f"File size {file_size} bytes exceeds maximum {max_size} bytes for {file_type.value}"
            )
        
        # Generate checksum
        checksum = self._generate_checksum(content)
        
        logger.info(
            f"File validated: {file.filename}, type={file_type.value}, "
            f"size={file_size}, checksum={checksum[:16]}..."
        )
        
        return content, file_type, checksum
    
    def _detect_file_type(self, filename: str, content: bytes) -> DocumentType:
        """
        Detect document type from filename and content
        
        Args:
            filename: File name
            content: File content
            
        Returns:
            DocumentType enum value
            
        Raises:
            UnsupportedFileTypeError: If file type is not supported
        """
        # Get file extension
        ext = Path(filename).suffix.lower()
        
        # Map extensions to types
        ext_map = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.pptx': DocumentType.PPTX,
            '.md': DocumentType.MD,
            '.txt': DocumentType.TXT,
            '.html': DocumentType.HTML,
            '.htm': DocumentType.HTML,
            '.csv': DocumentType.CSV,
            '.json': DocumentType.JSON,
            '.xml': DocumentType.XML,
            '.png': DocumentType.IMAGE,
            '.jpg': DocumentType.IMAGE,
            '.jpeg': DocumentType.IMAGE,
            '.tiff': DocumentType.IMAGE,
            '.tif': DocumentType.IMAGE,
            '.bmp': DocumentType.IMAGE,
            '.zip': DocumentType.ZIP,
        }
        
        doc_type = ext_map.get(ext)
        
        if doc_type is None:
            # Try MIME type detection
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                for dtype, mimes in self.SUPPORTED_TYPES.items():
                    if mime_type in mimes:
                        doc_type = dtype
                        break
        
        if doc_type is None:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {ext}. Supported types: {list(ext_map.keys())}"
            )
        
        return doc_type
    
    def _generate_checksum(self, content: bytes) -> str:
        """
        Generate SHA-256 checksum for content
        
        Args:
            content: File content
            
        Returns:
            SHA-256 checksum as hex string
        """
        return hashlib.sha256(content).hexdigest()
    
    async def extract_zip_contents(
        self,
        content: bytes,
        max_files: int = 100
    ) -> List[Tuple[str, bytes, DocumentType]]:
        """
        Extract contents from ZIP archive
        
        Args:
            content: ZIP file content
            max_files: Maximum number of files to extract
            
        Returns:
            List of (filename, content, document_type) tuples
            
        Raises:
            DocumentIngestionError: If ZIP extraction fails
        """
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(content))
            extracted_files: List[tuple[str, bytes, DocumentType]] = []
            
            for file_info in zip_file.infolist()[:max_files]:
                if file_info.is_dir():
                    continue
                
                # Skip hidden files
                if Path(file_info.filename).name.startswith('.'):
                    continue
                
                # Extract file
                file_content = zip_file.read(file_info.filename)
                
                # Detect type
                try:
                    doc_type = self._detect_file_type(file_info.filename, file_content)
                    
                    # Skip unsupported types in ZIP
                    if doc_type == DocumentType.ZIP:
                        continue
                    
                    extracted_files.append((file_info.filename, file_content, doc_type))
                    
                except UnsupportedFileTypeError:
                    logger.warning(f"Skipping unsupported file in ZIP: {file_info.filename}")
                    continue
            
            logger.info(f"Extracted {len(extracted_files)} files from ZIP archive")
            return extracted_files
            
        except zipfile.BadZipFile as e:
            raise DocumentIngestionError(f"Invalid ZIP file: {str(e)}")
        except Exception as e:
            raise DocumentIngestionError(f"Failed to extract ZIP: {str(e)}")
    
    async def create_document_record(
        self,
        file: UploadFile,
        content: bytes,
        doc_type: DocumentType,
        checksum: str,
        user_id: int,
        file_record: Optional[File] = None,
        title: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> KnowledgeDocument:
        """
        Create a document record in the database
        
        Args:
            file: UploadFile
            content: File content
            doc_type: Document type
            checksum: SHA-256 checksum
            user_id: User ID
            file_record: Optional File record
            title: Optional title (defaults to filename)
            db: Optional database session (if not provided, creates new one)
            
        Returns:
            KnowledgeDocument instance
        """
        from app.core.database import get_db
        from sqlalchemy import select
        
        if db is None:
            async for session in get_db():
                return await self._create_document_in_session(
                    session, file, content, doc_type, checksum, user_id, file_record, title
                )
        else:
            return await self._create_document_in_session(
                db, file, content, doc_type, checksum, user_id, file_record, title
            )
    
    async def _create_document_in_session(
        self,
        db: AsyncSession,
        file: UploadFile,
        content: bytes,
        doc_type: DocumentType,
        checksum: str,
        user_id: int,
        file_record: Optional[File],
        title: Optional[str]
    ) -> KnowledgeDocument:
        """Internal method to create document in a specific session"""
        # Check for duplicate by checksum
        existing = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.checksum == checksum,
                KnowledgeDocument.user_id == user_id,
                KnowledgeDocument.deleted_at.is_(None)
            )
        )
        existing_doc = existing.scalar_one_or_none()
        
        if existing_doc:
            logger.info(f"Duplicate document found: {file.filename}")
            return existing_doc
        
        # Create new document
        document = KnowledgeDocument(
            user_id=user_id,
            file_id=file_record.id if file_record else None,
            title=title or file.filename,
            file_name=file.filename,
            document_type=doc_type,
            file_size=len(content),
            checksum=checksum,
            status=DocumentStatus.PROCESSING,
            raw_content=content.decode('utf-8', errors='ignore') if doc_type in [DocumentType.TXT, DocumentType.MD, DocumentType.JSON, DocumentType.XML] else None
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"Created document record: {document.uuid}")
        return document


class DocumentExtractor:
    """
    Extract text content from various document formats
    """
    
    def __init__(self) -> None:
        pass
    
    async def extract_text(
        self,
        content: bytes,
        doc_type: DocumentType,
        filename: str
    ) -> str:
        """
        Extract text from document based on type
        
        Args:
            content: File content
            doc_type: Document type
            filename: File name
            
        Returns:
            Extracted text content
            
        Raises:
            DocumentIngestionError: If extraction fails
        """
        if doc_type == DocumentType.TXT:
            return content.decode('utf-8', errors='ignore')
        
        elif doc_type == DocumentType.MD:
            return content.decode('utf-8', errors='ignore')
        
        elif doc_type == DocumentType.JSON:
            import json
            try:
                data = json.loads(content.decode('utf-8'))
                return json.dumps(data, indent=2)
            except json.JSONDecodeError as e:
                raise DocumentIngestionError(f"Invalid JSON: {str(e)}")
        
        elif doc_type == DocumentType.XML:
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(content.decode('utf-8'))
                return ET.tostring(root, encoding='unicode', method='text')
            except ET.ParseError as e:
                raise DocumentIngestionError(f"Invalid XML: {str(e)}")
        
        elif doc_type == DocumentType.HTML:
            from bs4 import BeautifulSoup
            try:
                soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                return str(soup.get_text(separator='\n', strip=True))
            except Exception as e:
                raise DocumentIngestionError(f"Failed to parse HTML: {str(e)}")
        
        elif doc_type == DocumentType.CSV:
            import csv
            import io
            try:
                csv_text = content.decode('utf-8', errors='ignore')
                reader = csv.reader(io.StringIO(csv_text))
                rows = [' | '.join(row) for row in reader]
                return '\n'.join(rows)
            except Exception as e:
                raise DocumentIngestionError(f"Failed to parse CSV: {str(e)}")
        
        elif doc_type == DocumentType.PDF:
            import PyPDF2
            try:
                pdf_file = io.BytesIO(content)
                reader = PyPDF2.PdfReader(pdf_file)
                text = []
                for page in reader.pages:  # type: ignore
                    text.append(page.extract_text())
                return '\n\n'.join(text)
            except Exception as e:
                raise DocumentIngestionError(f"Failed to extract PDF text: {str(e)}")
        
        elif doc_type == DocumentType.DOCX:
            import docx
            try:
                doc = docx.Document(io.BytesIO(content))
                text = [paragraph.text for paragraph in doc.paragraphs]
                return '\n'.join(text)
            except Exception as e:
                raise DocumentIngestionError(f"Failed to extract DOCX text: {str(e)}")
        
        elif doc_type == DocumentType.PPTX:
            import pptx
            try:
                presentation = pptx.Presentation(io.BytesIO(content))
                text = []
                for slide in presentation.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text.append(shape.text)
                return '\n'.join(text)
            except Exception as e:
                raise DocumentIngestionError(f"Failed to extract PPTX text: {str(e)}")
        
        elif doc_type == DocumentType.IMAGE:
            # OCR extraction
            import pytesseract
            from PIL import Image
            try:
                image = Image.open(io.BytesIO(content))
                text = pytesseract.image_to_string(image)
                return str(text)
            except Exception as e:
                raise DocumentIngestionError(f"Failed to perform OCR: {str(e)}")
        
        else:
            raise DocumentIngestionError(f"Unsupported document type for extraction: {doc_type}")


# Singleton instances
document_ingestor = DocumentIngestor()
document_extractor = DocumentExtractor()
