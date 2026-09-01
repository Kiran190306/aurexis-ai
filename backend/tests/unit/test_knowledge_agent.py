"""
Unit tests for Knowledge Platform agent
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.knowledge.agent import (
    RAGQuery,
    RAGResult,
    KnowledgeAgent
)
from app.knowledge.context import BuiltContext
from app.knowledge.reranking import RerankedResult
from app.knowledge.search import HybridSearchResult


class TestRAGQuery:
    """Tests for RAGQuery dataclass"""
    
    def test_rag_query_creation(self):
        """Test RAGQuery creation"""
        query = RAGQuery(
            query="test query",
            user_id=1,
            top_k=10,
            use_hybrid=True,
            max_tokens=4000,
            include_citations=True
        )
        
        assert query.query == "test query"
        assert query.user_id == 1
        assert query.top_k == 10
        assert query.use_hybrid is True
        assert query.max_tokens == 4000
        assert query.include_citations is True


class TestRAGResult:
    """Tests for RAGResult dataclass"""
    
    def test_rag_result_creation(self):
        """Test RAGResult creation"""
        result = RAGResult(
            query="test query",
            context=BuiltContext(
                context_text="Test context",
                citations=[],
                total_tokens=10,
                total_sources=1,
                average_confidence=0.9,
                metadata={}
            ),
            sources=[],
            metadata={},
            latency_ms=250
        )
        
        assert result.query == "test query"
        assert result.context.context_text == "Test context"
        assert result.latency_ms == 250


class TestKnowledgeAgent:
    """Tests for KnowledgeAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a KnowledgeAgent instance"""
        with patch('app.knowledge.agent.get_hybrid_search_engine'), \
             patch('app.knowledge.agent.get_reranking_pipeline'), \
             patch('app.knowledge.agent.get_context_builder'):
            return KnowledgeAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.search_engine is not None
        assert agent.reranking_pipeline is not None
        assert agent.context_builder is not None
    
    @pytest.mark.asyncio
    async def test_query(self, agent):
        """Test RAG query"""
        query = RAGQuery(
            query="test query",
            user_id=1,
            top_k=10,
            use_hybrid=True,
            max_tokens=1000
        )
        
        agent.search_engine = Mock()
        agent.search_engine.search = AsyncMock(return_value=[
            HybridSearchResult(chunk_id=1, document_id=1, content="Test", score=0.9, bm25_score=0.8, dense_score=0.85, metadata={})
        ])
        
        agent.reranking_pipeline = Mock()
        agent.reranking_pipeline.rerank = AsyncMock(return_value=[
            RerankedResult(chunk_id=1, document_id=1, content="Test", score=0.9, original_score=0.8, metadata={})
        ])
        
        agent.context_builder = Mock()
        agent.context_builder.build_context = Mock(return_value=BuiltContext(
            context_text="Test context",
            citations=[],
            total_tokens=10,
            total_sources=1,
            average_confidence=0.9,
            metadata={}
        ))
        
        agent._get_user_chunks = AsyncMock(return_value=[])
        
        result = await agent.query(query)
        
        assert isinstance(result, RAGResult)
        assert result.query == "test query"
