"""
Unit tests for Knowledge Platform embedding pipeline
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

import numpy as np

from app.knowledge.embeddings import (
    BaseEmbeddingProvider,
    BAAIEmbeddingProvider,
    MultilingualE5Provider,
    OpenAIEmbeddingProvider,
    JinaEmbeddingProvider,
)
from app.models.knowledge import EmbeddingProvider, KnowledgeChunk


class TestBAAIEmbeddingProvider:
    """Tests for BAAIEmbeddingProvider"""
    
    @pytest.fixture
    def provider(self):
        """Create a BAAIEmbeddingProvider instance"""
        # Mock the model loading to avoid actual model loading
        with patch('sentence_transformers.SentenceTransformer'):
            return BAAIEmbeddingProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.model_name == "BAAI/bge-large-en-v1.5"
        assert provider.dimension == 1024
    
    @pytest.mark.asyncio
    async def test_embed_text(self, provider):
        """Test text embedding"""
        text = "This is a test sentence."
        
        # Mock the model
        provider.model = Mock()
        provider.model.encode.return_value = np.random.rand(1024).astype(np.float32)
        
        embedding = await provider.embed(text)
        
        assert len(embedding) == 1024
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_embed_batch(self, provider):
        """Test batch embedding"""
        texts = ["Text 1", "Text 2", "Text 3"]
        
        provider.model = Mock()
        provider.model.encode.return_value = np.random.rand(3, 1024).astype(np.float32)
        
        embeddings = await provider.embed_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1024 for emb in embeddings)


class TestMultilingualE5Provider:
    """Tests for MultilingualE5Provider"""
    
    @pytest.fixture
    def provider(self):
        """Create a MultilingualE5Provider instance"""
        with patch('sentence_transformers.SentenceTransformer'):
            return MultilingualE5Provider()
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.model_name == "intfloat/multilingual-e5-large"
        assert provider.dimension == 1024
    
    @pytest.mark.asyncio
    async def test_embed_multilingual(self, provider):
        """Test multilingual embedding"""
        text = "This is English text."
        
        provider.model = Mock()
        provider.model.encode.return_value = np.random.rand(1024).astype(np.float32)
        
        embedding = await provider.embed(text)
        
        assert len(embedding) == 1024


class TestOpenAIEmbeddingProvider:
    """Tests for OpenAIEmbeddingProvider"""
    
    @pytest.fixture
    def provider(self):
        """Create an OpenAIEmbeddingProvider instance"""
        with patch('openai.AsyncOpenAI'):
            return OpenAIEmbeddingProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.model_name == "text-embedding-3-small"
        assert provider.dimension == 1536
    
    @pytest.mark.asyncio
    async def test_embed_text(self, provider):
        """Test OpenAI embedding"""
        text = "Test text"
        
        provider.client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        provider.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        embedding = await provider.embed(text)
        
        assert len(embedding) == 1536


class TestJinaEmbeddingProvider:
    """Tests for JinaEmbeddingProvider"""
    
    @pytest.fixture
    def provider(self):
        """Create a JinaEmbeddingProvider instance"""
        with patch('sentence_transformers.SentenceTransformer'):
            return JinaEmbeddingProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.model_name == "jinaai/jina-embeddings-v2-base-en"
        assert provider.dimension == 768
    
    @pytest.mark.asyncio
    async def test_embed_text(self, provider):
        """Test Jina embedding"""
        text = "Test text"
        
        provider.model = Mock()
        provider.model.encode.return_value = np.random.rand(768).astype(np.float32)
        
        embedding = await provider.embed(text)
        
        assert len(embedding) == 768
