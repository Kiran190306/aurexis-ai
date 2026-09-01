"""
Unit tests for Knowledge Platform context builder
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.knowledge.context import (
    TokenBudgetManager,
    ContextCompressor,
    CitationGenerator,
    ConfidenceScorer,
    ContextBuilder,
    Citation,
    BuiltContext
)
from app.knowledge.reranking import RerankedResult


class TestTokenBudgetManager:
    """Tests for TokenBudgetManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a TokenBudgetManager instance"""
        return TokenBudgetManager(max_tokens=4000, reserve_tokens=500)
    
    def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert manager.max_tokens == 4000
        assert manager.reserve_tokens == 500
        assert manager.available_tokens == 3500
    
    def test_estimate_tokens(self, manager):
        """Test token estimation"""
        text = "This is a test sentence."
        tokens = manager.estimate_tokens(text)
        
        assert tokens > 0
        assert tokens <= len(text)  # Tokens should be <= characters
    
    def test_allocate_budget(self, manager):
        """Test budget allocation"""
        results = [
            RerankedResult(
                chunk_id=i,
                document_id=1,
                content=f"Content {i} " * 50,
                score=0.9 - i * 0.1,
                original_score=0.8 - i * 0.1,
                metadata={}
            )
            for i in range(5)
        ]
        
        allocation = manager.allocate_budget(results, query_tokens=0)
        
        assert isinstance(allocation, dict)
        assert len(allocation) <= len(results)


class TestContextCompressor:
    """Tests for ContextCompressor"""
    
    @pytest.fixture
    def compressor(self):
        """Create a ContextCompressor instance"""
        return ContextCompressor()
    
    def test_compress_truncate(self, compressor):
        """Test truncation compression"""
        text = "This is a test. " * 100
        compressed = compressor.compress(text, target_tokens=50, method="truncate")
        
        assert len(compressed) <= len(text)
    
    def test_compress_summarize(self, compressor):
        """Test summarization compression"""
        text = "This is a test. " * 20
        compressed = compressor.compress(text, target_tokens=20, method="summarize")
        
        # Summarization uses extractive approach
        assert compressed is not None
    
    def test_compress_extractive(self, compressor):
        """Test extractive compression"""
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        compressed = compressor.compress(text, target_tokens=30, method="extractive")
        
        assert compressed is not None
    
    def test_compress_no_compression_needed(self, compressor):
        """Test when no compression is needed"""
        text = "Short text."
        compressed = compressor.compress(text, target_tokens=100, method="truncate")
        
        # Should return original if within budget
        assert compressed == text


class TestCitationGenerator:
    """Tests for CitationGenerator"""
    
    @pytest.fixture
    def generator(self):
        """Create a CitationGenerator instance"""
        return CitationGenerator()
    
    def test_generate_citations(self, generator):
        """Test citation generation from results"""
        results = [
            RerankedResult(
                chunk_id=1,
                document_id=1,
                content="Test content",
                score=0.9,
                original_score=0.8,
                metadata={"page_number": 5},
                document_title="Test Document",
                document_uuid="test-uuid"
            )
        ]
        
        citations = generator.generate_citations(results)
        
        assert len(citations) == 1
        assert citations[0].document_title == "Test Document"
        assert citations[0].document_uuid == "test-uuid"
        assert citations[0].page_number == 5
    
    def test_format_citations_numeric(self, generator):
        """Test formatting citations in numeric style"""
        citations = [
            Citation(chunk_id=1, document_id=1, document_title="Doc 1", document_uuid="uuid1", confidence=0.9, relevance_score=0.8),
            Citation(chunk_id=2, document_id=1, document_title="Doc 2", document_uuid="uuid2", confidence=0.8, relevance_score=0.7)
        ]
        
        formatted = generator.format_citations(citations, style="numeric")
        
        assert "[1]" in formatted or "[2]" in formatted
    
    def test_format_citations_apa(self, generator):
        """Test formatting citations in APA style"""
        citations = [
            Citation(chunk_id=1, document_id=1, document_title="Doc 1", document_uuid="uuid1", confidence=0.9, relevance_score=0.8)
        ]
        
        formatted = generator.format_citations(citations, style="apa")
        
        assert formatted is not None
        assert "Doc 1" in formatted


class TestConfidenceScorer:
    """Tests for ConfidenceScorer"""
    
    @pytest.fixture
    def scorer(self):
        """Create a ConfidenceScorer instance"""
        return ConfidenceScorer()
    
    def test_calculate_confidence(self, scorer):
        """Test confidence calculation"""
        results = [
            RerankedResult(
                chunk_id=1,
                document_id=1,
                content="Test content",
                score=0.9,
                original_score=0.8,
                metadata={}
            )
        ]
        
        confidence = scorer.calculate_confidence(results, query="test query")
        
        assert isinstance(confidence, dict)
    
    def test_calculate_confidence_empty(self, scorer):
        """Test confidence calculation with empty results"""
        confidence = scorer.calculate_confidence([], query="test query")
        
        assert isinstance(confidence, dict)


class TestContextBuilder:
    """Tests for ContextBuilder"""
    
    @pytest.fixture
    def builder(self):
        """Create a ContextBuilder instance"""
        return ContextBuilder()
    
    def test_build_context(self, builder):
        """Test context building"""
        results = [
            RerankedResult(
                chunk_id=1,
                document_id=1,
                content="Test content",
                score=0.9,
                original_score=0.8,
                metadata={},
                document_title="Test Doc",
                document_uuid="test-uuid"
            )
        ]
        
        context = builder.build_context(query="test query", results=results, include_citations=True)
        
        assert isinstance(context, BuiltContext)
        assert context.context_text is not None
        assert context.total_sources == 1
    
    def test_build_context_empty(self, builder):
        """Test building context with empty results"""
        context = builder.build_context(query="test query", results=[], include_citations=True)
        
        assert isinstance(context, BuiltContext)
        assert context.total_sources == 0


class TestBuiltContext:
    """Tests for BuiltContext dataclass"""
    
    def test_built_context_creation(self):
        """Test BuiltContext creation"""
        context = BuiltContext(
            context_text="Test context text",
            citations=[],
            total_tokens=10,
            total_sources=1,
            average_confidence=0.9,
            metadata={}
        )
        
        assert context.context_text == "Test context text"
        assert context.total_tokens == 10
        assert context.average_confidence == 0.9


class TestCitation:
    """Tests for Citation dataclass"""
    
    def test_citation_creation(self):
        """Test Citation creation"""
        citation = Citation(
            chunk_id=1,
            document_id=1,
            document_title="Test Document",
            document_uuid="test-uuid",
            page_number=5,
            confidence=0.9,
            relevance_score=0.8
        )
        
        assert citation.document_title == "Test Document"
        assert citation.document_uuid == "test-uuid"
        assert citation.page_number == 5
        assert citation.confidence == 0.9
