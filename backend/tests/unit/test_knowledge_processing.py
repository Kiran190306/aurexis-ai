"""
Unit tests for Knowledge Platform document processing
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.knowledge.processing import (
    MetadataExtractor,
    LanguageDetector,
    DuplicateDetector
)
from app.models.knowledge import KnowledgeDocument, DocumentType


class TestMetadataExtractor:
    """Tests for MetadataExtractor"""
    
    @pytest.fixture
    def extractor(self):
        """Create a MetadataExtractor instance"""
        return MetadataExtractor()
    
    def test_extract_metadata_from_text(self, extractor):
        """Test metadata extraction from text"""
        text = """
        # Test Document
        
        Author: John Doe
        Date: 2024-01-15
        
        This is a test document with some content.
        """
        
        metadata = extractor.extract_metadata(text, "test.md", "md")
        
        assert metadata is not None
        assert "word_count" in metadata
        assert "character_count" in metadata
        assert "line_count" in metadata
        assert metadata["word_count"] > 0
    
    def test_extract_word_count(self, extractor):
        """Test word count extraction"""
        text = "This is a test document with some words."
        metadata = extractor.extract_metadata(text, "test.txt", "txt")
        
        assert "word_count" in metadata
        assert metadata["word_count"] == 8
    
    def test_extract_character_count(self, extractor):
        """Test character count extraction"""
        text = "Test"
        metadata = extractor.extract_metadata(text, "test.txt", "txt")
        
        assert "character_count" in metadata
        assert metadata["character_count"] == 4
    
    def test_extract_line_count(self, extractor):
        """Test line count extraction"""
        text = "Line 1\nLine 2\nLine 3"
        metadata = extractor.extract_metadata(text, "test.txt", "txt")
        
        assert "line_count" in metadata
        assert metadata["line_count"] == 3
    
    def test_extract_paragraph_count(self, extractor):
        """Test paragraph count extraction"""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        metadata = extractor.extract_metadata(text, "test.txt", "txt")
        
        assert "paragraph_count" in metadata
        assert metadata["paragraph_count"] == 3


class TestLanguageDetector:
    """Tests for LanguageDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create a LanguageDetector instance"""
        return LanguageDetector()
    
    def test_detect_english(self, detector):
        """Test English language detection"""
        text = "This is a test document in English language."
        language, confidence = detector.detect_language(text)
        
        assert language is not None
        assert isinstance(language, str)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    def test_detect_empty_text(self, detector):
        """Test language detection with empty text"""
        language, confidence = detector.detect_language("")
        
        assert language is not None
        assert isinstance(language, str)
    
    def test_detect_short_text_fallback(self, detector):
        """Test fallback for very short text"""
        text = "Hi"
        language, confidence = detector.detect_language(text)
        
        # Should use heuristic fallback
        assert language is not None
        assert isinstance(language, str)
    
    def test_detect_multilingual(self, detector):
        """Test detection with mixed language"""
        text = "This is English. Esto es español."
        language, confidence = detector.detect_language(text)
        
        # Should detect dominant language
        assert language is not None
        assert isinstance(language, str)


class TestDuplicateDetector:
    """Tests for DuplicateDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create a DuplicateDetector instance"""
        return DuplicateDetector()
    
    def test_exact_duplicate_detection(self, detector):
        """Test exact duplicate detection"""
        text1 = "This is a test document."
        text2 = "This is a test document."
        
        is_duplicate = detector.is_duplicate(text1, text2)
        
        assert is_duplicate is True
    
    def test_not_duplicate(self, detector):
        """Test non-duplicate detection"""
        text1 = "This is a test document."
        text2 = "This is a different document."
        
        is_duplicate = detector.is_duplicate(text1, text2)
        
        assert is_duplicate is False
    
    def test_near_duplicate_high_similarity(self, detector):
        """Test near-duplicate with high similarity"""
        text1 = "This is a test document with some content."
        text2 = "This is a test document with similar content."
        
        similarity = detector._calculate_similarity(text1, text2)
        
        # Jaccard similarity for these texts is ~0.78
        assert similarity > 0.7
    
    def test_near_duplicate_low_similarity(self, detector):
        """Test near-duplicate with low similarity"""
        text1 = "This is about machine learning."
        text2 = "This is about natural language processing."
        
        similarity = detector._calculate_similarity(text1, text2)
        
        assert similarity < 0.5
    
    def test_jaccard_similarity(self, detector):
        """Test Jaccard similarity calculation"""
        text1 = "apple banana cherry"
        text2 = "apple banana date"
        
        similarity = detector._calculate_similarity(text1, text2)
        
        # Intersection: apple, banana (2)
        # Union: apple, banana, cherry, date (4)
        # Jaccard: 2/4 = 0.5
        assert similarity == 0.5
    
    def test_is_near_duplicate_threshold(self, detector):
        """Test near-duplicate threshold"""
        text1 = "This is a test document with some content."
        text2 = "This is a test document with similar content."
        
        is_near_duplicate = detector.is_duplicate(text1, text2)
        
        # With default threshold of 0.95, these should not be considered duplicates
        assert is_near_duplicate is False
