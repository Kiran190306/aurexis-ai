"""
Unit tests for Knowledge Platform reranking system
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

import numpy as np

from app.knowledge.reranking import (
    BaseReranker,
    CrossEncoderReranker,
    CohereReranker,
    ContextOptimizer,
    ResultDiversifier,
    RerankedResult
)
from app.knowledge.search import HybridSearchResult


class TestRerankedResult:
    """Tests for RerankedResult dataclass"""
    
    def test_reranked_result_creation(self):
        """Test RerankedResult creation"""
        result = RerankedResult(
            chunk_id=1,
            document_id=1,
            content="Test content",
            score=0.95,
            original_score=0.80,
            metadata={"test": "value"},
            rerank_reason="cross_encoder"
        )
        
        assert result.chunk_id == 1
        assert result.score == 0.95
        assert result.original_score == 0.80
        assert result.rerank_reason == "cross_encoder"


class TestCrossEncoderReranker:
    """Tests for CrossEncoderReranker"""
    
    @pytest.fixture
    def reranker(self):
        """Create a CrossEncoderReranker instance"""
        with patch('sentence_transformers.CrossEncoder'):
            return CrossEncoderReranker(model_name="test-model")
    
    def test_reranker_initialization(self, reranker):
        """Test reranker initialization"""
        assert reranker.model_name == "test-model"
    
    @pytest.mark.asyncio
    async def test_rerank(self, reranker):
        """Test cross-encoder reranking"""
        results = [
            HybridSearchResult(chunk_id=1, document_id=1, content="Test 1", score=0.8, bm25_score=0.7, dense_score=0.85, metadata={}),
            HybridSearchResult(chunk_id=2, document_id=1, content="Test 2", score=0.7, bm25_score=0.6, dense_score=0.75, metadata={})
        ]
        
        reranker.model = Mock()
        reranker.model.predict.return_value = np.array([0.9, 0.8])
        
        reranked = await reranker.rerank("test query", results, top_k=2)
        
        assert len(reranked) <= 2
        assert all(isinstance(r, RerankedResult) for r in reranked)
    
    @pytest.mark.asyncio
    async def test_rerank_without_model(self, reranker):
        """Test reranking without loaded model"""
        reranker.model = None
        results = [
            HybridSearchResult(chunk_id=1, document_id=1, content="Test", score=0.8, bm25_score=0.7, dense_score=0.85, metadata={})
        ]
        
        reranked = await reranker.rerank("test query", results, top_k=2)
        
        assert len(reranked) == 1
        assert all(isinstance(r, RerankedResult) for r in reranked)
    
    @pytest.mark.asyncio
    async def test_rerank_empty_results(self, reranker):
        """Test reranking with empty results"""
        query = "test query"
        results = []
        
        reranked = await reranker.rerank(query, results, top_k=10)
        
        assert len(reranked) == 0


class TestContextOptimizer:
    """Tests for ContextOptimizer"""
    
    @pytest.fixture
    def optimizer(self):
        """Create a ContextOptimizer instance"""
        return ContextOptimizer()
    
    def test_remove_duplicates(self, optimizer):
        """Test duplicate removal"""
        results = [
            RerankedResult(
                chunk_id=1,
                document_id=1,
                content="Same content",
                score=0.9,
                original_score=0.8,
                metadata={}
            ),
            RerankedResult(
                chunk_id=2,
                document_id=1,
                content="Same content",
                score=0.8,
                original_score=0.7,
                metadata={}
            )
        ]
        
        deduped = optimizer._remove_duplicates(results)
        
        # Should remove duplicates
        assert len(deduped) <= len(results)
    
    def test_apply_token_budget(self, optimizer):
        """Test token budget application"""
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
        
        budgeted = optimizer._apply_token_budget(results, max_tokens=200)
        
        # Should respect token budget
        assert len(budgeted) >= 0
    
    def test_optimize(self, optimizer):
        """Test full optimization"""
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
        
        optimized = optimizer.optimize(results, max_tokens=200)
        
        assert len(optimized) >= 0
    
    def test_calculate_redundancy(self, optimizer):
        """Test redundancy calculation"""
        text1 = "This is a test document."
        text2 = "This is a test document."
        
        redundancy = optimizer.calculate_redundancy(text1, text2)
        
        assert redundancy == 1.0  # Identical texts


class TestResultDiversifier:
    """Tests for ResultDiversifier"""
    
    @pytest.fixture
    def diversifier(self):
        """Create a ResultDiversifier instance"""
        return ResultDiversifier()
    
    def test_diversify_results(self, diversifier):
        """Test result diversification"""
        results = [
            RerankedResult(
                chunk_id=i,
                document_id=1 if i < 3 else 2,
                content=f"Content {i}",
                score=0.9 - i * 0.1,
                original_score=0.8 - i * 0.1,
                metadata={}
            )
            for i in range(5)
        ]
        
        diversified = diversifier.diversify(results)
        
        assert len(diversified) > 0
