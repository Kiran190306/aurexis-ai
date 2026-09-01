"""
Unit tests for Knowledge Platform document ingestion
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from io import BytesIO
import hashlib

from app.knowledge.ingestion import DocumentIngestor, FileValidationError, FileSizeExceededError, UnsupportedFileTypeError
from app.models.knowledge import DocumentType


class TestDocumentIngestor:
    """Tests for DocumentIngestor"""
    
    @pytest.fixture
    def ingestor(self):
        """Create a DocumentIngestor instance"""
        return DocumentIngestor()
    
    @pytest.fixture
    def mock_file(self):
        """Create a mock uploaded file"""
        mock = Mock(spec=Mock)
        mock.filename = "test.pdf"
        mock.content_type = "application/pdf"
        mock.file = BytesIO(b"test content")
        mock.read = AsyncMock(return_value=b"test content")
        return mock
    
    @pytest.mark.asyncio
    async def test_validate_upload_success(self, ingestor, mock_file):
        """Test successful file validation"""
        content, doc_type, checksum = await ingestor.validate_upload(mock_file, user_id=1)
        
        assert content == b"test content"
        assert doc_type == DocumentType.PDF
        assert checksum == hashlib.sha256(b"test content").hexdigest()
    
    @pytest.mark.asyncio
    async def test_validate_upload_empty_file(self, ingestor):
        """Test validation with empty file"""
        mock_file = Mock(spec=Mock)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"")
        
        with pytest.raises(FileValidationError, match="File is empty"):
            await ingestor.validate_upload(mock_file, user_id=1)
    
    @pytest.mark.asyncio
    async def test_validate_upload_size_limit(self, ingestor):
        """Test validation with oversized file"""
        mock_file = Mock(spec=Mock)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"x" * (501 * 1024 * 1024))  # 501MB
        
        with pytest.raises(FileSizeExceededError, match="exceeds maximum"):
            await ingestor.validate_upload(mock_file, user_id=1)
    
    def test_detect_file_type_pdf(self, ingestor):
        """Test PDF type detection"""
        doc_type = ingestor._detect_file_type("test.pdf", b"test content")
        assert doc_type == DocumentType.PDF
    
    def test_detect_file_type_docx(self, ingestor):
        """Test DOCX type detection"""
        doc_type = ingestor._detect_file_type("test.docx", b"test content")
        assert doc_type == DocumentType.DOCX
    
    def test_detect_file_type_markdown(self, ingestor):
        """Test Markdown type detection"""
        doc_type = ingestor._detect_file_type("test.md", b"test content")
        assert doc_type == DocumentType.MD
    
    def test_detect_file_type_text(self, ingestor):
        """Test text type detection"""
        doc_type = ingestor._detect_file_type("test.txt", b"test content")
        assert doc_type == DocumentType.TXT
    
    def test_detect_file_type_html(self, ingestor):
        """Test HTML type detection"""
        doc_type = ingestor._detect_file_type("test.html", b"test content")
        assert doc_type == DocumentType.HTML
    
    def test_detect_file_type_csv(self, ingestor):
        """Test CSV type detection"""
        doc_type = ingestor._detect_file_type("test.csv", b"test content")
        assert doc_type == DocumentType.CSV
    
    def test_detect_file_type_json(self, ingestor):
        """Test JSON type detection"""
        doc_type = ingestor._detect_file_type("test.json", b"test content")
        assert doc_type == DocumentType.JSON
    
    def test_detect_file_type_xml(self, ingestor):
        """Test XML type detection"""
        doc_type = ingestor._detect_file_type("test.xml", b"test content")
        assert doc_type == DocumentType.XML
    
    def test_detect_file_type_image(self, ingestor):
        """Test image type detection"""
        doc_type = ingestor._detect_file_type("test.png", b"test content")
        assert doc_type == DocumentType.IMAGE
    
    def test_detect_file_type_zip(self, ingestor):
        """Test ZIP type detection"""
        doc_type = ingestor._detect_file_type("test.zip", b"test content")
        assert doc_type == DocumentType.ZIP
    
    def test_detect_file_type_unsupported(self, ingestor):
        """Test unsupported file type"""
        with pytest.raises(UnsupportedFileTypeError, match="Unsupported file type"):
            ingestor._detect_file_type("test.exe", b"test content")
    
    def test_generate_checksum(self, ingestor):
        """Test checksum calculation"""
        content = b"test content"
        checksum = ingestor._generate_checksum(content)
        
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected


class TestZIPExtraction:
    """Tests for ZIP archive extraction"""
    
    @pytest.fixture
    def ingestor(self):
        """Create a DocumentIngestor instance"""
        return DocumentIngestor()
    
    @pytest.mark.asyncio
    async def test_extract_zip_contents(self, ingestor):
        """Test ZIP content extraction"""
        import zipfile
        from io import BytesIO
        
        # Create a mock ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr("file1.txt", "content1")
            zip_file.writestr("file2.txt", "content2")
        
        zip_buffer.seek(0)
        contents = await ingestor.extract_zip_contents(zip_buffer.read())
        
        assert len(contents) == 2
        assert any(b"content1" in c[1] for c in contents)
        assert any(b"content2" in c[1] for c in contents)
    
    @pytest.mark.asyncio
    async def test_extract_zip_max_files(self, ingestor):
        """Test ZIP extraction with file limit"""
        import zipfile
        from io import BytesIO
        
        # Create ZIP with many files
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for i in range(150):  # Exceed default limit of 100
                zip_file.writestr(f"file{i}.txt", f"content{i}")
        
        zip_buffer.seek(0)
        contents = await ingestor.extract_zip_contents(zip_buffer.read(), max_files=100)
        
        # Should only extract up to max_files
        assert len(contents) <= 100
