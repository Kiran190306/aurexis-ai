"""
Unit tests for Knowledge Platform models
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models.knowledge import (
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeEmbedding,
    KnowledgeSearchHistory,
    KnowledgeRerankResult,
    KnowledgeAuditLog,
    KnowledgeIndexingQueue,
    DocumentStatus,
    DocumentType,
    ChunkingStrategy,
    EmbeddingProvider,
    VectorStoreType,
)


class TestKnowledgeDocument:
    """Tests for KnowledgeDocument model"""
    
    def test_create_document(self):
        """Test creating a KnowledgeDocument"""
        doc = KnowledgeDocument(
            user_id=1,
            uuid=str(uuid4()),
            title="Test Document",
            file_name="test.pdf",
            document_type=DocumentType.PDF,
            status=DocumentStatus.PROCESSING,
            raw_content=b"test content",
            processed_content="processed content"
        )
        
        assert doc.user_id == 1
        assert doc.title == "Test Document"
        assert doc.document_type == DocumentType.PDF
        assert doc.status == DocumentStatus.PROCESSING
        assert doc.raw_content == b"test content"
        assert doc.processed_content == "processed content"
    
    def test_document_status_enum(self):
        """Test DocumentStatus enum values"""
        assert DocumentStatus.PROCESSING.value == "processing"
        assert DocumentStatus.INDEXED.value == "indexed"
        assert DocumentStatus.FAILED.value == "failed"
        assert DocumentStatus.ARCHIVED.value == "archived"
        assert DocumentStatus.DELETED.value == "deleted"
    
    def test_document_type_enum(self):
        """Test DocumentType enum values"""
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.MD.value == "md"
        assert DocumentType.DOCX.value == "docx"
        assert DocumentType.PPTX.value == "pptx"
        assert DocumentType.TXT.value == "txt"
        assert DocumentType.HTML.value == "html"
        assert DocumentType.CSV.value == "csv"
        assert DocumentType.JSON.value == "json"
        assert DocumentType.XML.value == "xml"
        assert DocumentType.IMAGE.value == "image"
        assert DocumentType.ZIP.value == "zip"
    
    def test_document_chunking_strategy_enum(self):
        """Test ChunkingStrategy enum values"""
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.RECURSIVE.value == "recursive"
        assert ChunkingStrategy.SLIDING_WINDOW.value == "sliding_window"
        assert ChunkingStrategy.PARENT_CHILD.value == "parent_child"
        assert ChunkingStrategy.ADAPTIVE.value == "adaptive"
    
    def test_document_embedding_provider_enum(self):
        """Test EmbeddingProvider enum values"""
        assert EmbeddingProvider.BAAI_BGE.value == "BAAI_BGE"
        assert EmbeddingProvider.MULTILINGUAL_E5.value == "MULTILINGUAL_E5"
        assert EmbeddingProvider.OPENAI.value == "OPENAI"
        assert EmbeddingProvider.JINA.value == "JINA"


class TestKnowledgeChunk:
    """Tests for KnowledgeChunk model"""
    
    def test_create_chunk(self):
        """Test creating a KnowledgeChunk"""
        chunk = KnowledgeChunk(
            document_id=1,
            content="Test chunk content",
            chunk_index=0,
            token_count=100,
            character_count=500
        )
        
        assert chunk.content == "Test chunk content"
        assert chunk.chunk_index == 0
        assert chunk.token_count == 100
        assert chunk.character_count == 500
    
    def test_chunk_with_parent(self):
        """Test chunk with parent-child relationship"""
        chunk = KnowledgeChunk(
            document_id=1,
            chunk_index=1,
            content="Child chunk",
            parent_chunk_id=5,
            token_count=5,
            character_count=10
        )
        
        assert chunk.parent_chunk_id == 5
        assert chunk.chunk_index == 1


class TestKnowledgeEmbedding:
    """Tests for KnowledgeEmbedding model"""
    
    def test_create_embedding(self):
        """Test creating a KnowledgeEmbedding"""
        embedding = KnowledgeEmbedding(
            chunk_id=1,
            document_id=1,
            embedding=[0.1] * 1024,
            embedding_dimension=1024,
            embedding_provider=EmbeddingProvider.BAAI_BGE,
            embedding_model="bge-large-en-v1.5",
            cache_key="cache_key_123"
        )
        
        assert len(embedding.embedding) == 1024
        assert embedding.embedding_dimension == 1024
        assert embedding.embedding_provider == EmbeddingProvider.BAAI_BGE
        assert embedding.embedding_model == "bge-large-en-v1.5"
        assert embedding.cache_key == "cache_key_123"
    
    def test_embedding_vector_store_type_enum(self):
        """Test VectorStoreType enum values"""
        assert VectorStoreType.PGVECTOR.value == "pgvector"
        assert VectorStoreType.CHROMADB.value == "chromadb"
        assert VectorStoreType.QDRANT.value == "qdrant"


class TestKnowledgeSearchHistory:
    """Tests for KnowledgeSearchHistory model"""
    
    def test_create_search_history(self):
        """Test creating a KnowledgeSearchHistory"""
        history = KnowledgeSearchHistory(
            user_id=1,
            document_id=1,
            query="test query",
            query_type="semantic",
            result_count=10,
            latency_ms=150
        )
        
        assert history.query == "test query"
        assert history.result_count == 10
        assert history.latency_ms == 150


class TestKnowledgeRerankResult:
    """Tests for KnowledgeRerankResult model"""
    
    def test_create_rerank_result(self):
        """Test creating a KnowledgeRerankResult"""
        rerank = KnowledgeRerankResult(
            search_history_id=1,
            reranker_model="cross-encoder",
            original_rank=5,
            reranked_rank=1,
            score_change=0.3,
            chunk_id=1,
            original_score=0.7,
            reranked_score=1.0
        )
        
        assert rerank.original_rank == 5
        assert rerank.reranked_rank == 1
        assert rerank.score_change == 0.3
        assert rerank.original_score == 0.7
        assert rerank.reranked_score == 1.0


class TestKnowledgeAuditLog:
    """Tests for KnowledgeAuditLog model"""
    
    def test_create_audit_log(self):
        """Test creating a KnowledgeAuditLog"""
        audit = KnowledgeAuditLog(
            user_id=1,
            action="upload",
            resource_type="document",
            resource_id=1,
            success=True,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert audit.user_id == 1
        assert audit.action == "upload"
        assert audit.resource_type == "document"
        assert audit.resource_id == 1
        assert audit.success is True
        assert audit.ip_address == "192.168.1.1"
        assert audit.user_agent == "Mozilla/5.0"
    
    def test_audit_log_with_error(self):
        """Test audit log with error"""
        audit = KnowledgeAuditLog(
            user_id=1,
            action="delete",
            resource_type="document",
            resource_id=1,
            success=False,
            error_message="Permission denied"
        )
        
        assert audit.success is False
        assert audit.error_message == "Permission denied"


class TestKnowledgeIndexingQueue:
    """Tests for KnowledgeIndexingQueue model"""
    
    def test_create_indexing_queue(self):
        """Test creating a KnowledgeIndexingQueue"""
        queue = KnowledgeIndexingQueue(
            document_id=1,
            priority=5,
            status="pending"
        )
        
        assert queue.priority == 5
        assert queue.status == "pending"
    
    def test_indexing_queue_with_error(self):
        """Test indexing queue with error"""
        queue = KnowledgeIndexingQueue(
            document_id=1,
            status="failed",
            priority=5,
            error_message="Embedding generation failed"
        )
        
        assert queue.status == "failed"
        assert queue.error_message == "Embedding generation failed"


class TestModelRelationships:
    """Tests for model relationships"""
    
    def test_document_chunk_relationship(self):
        """Test document to chunk relationship"""
        doc = KnowledgeDocument(
            user_id=1,
            uuid=str(uuid4()),
            title="Test",
            file_name="test.pdf",
            document_type=DocumentType.PDF,
            status=DocumentStatus.INDEXED
        )
        
        chunk = KnowledgeChunk(
            document_id=doc.id,
            chunk_index=0,
            content="Test",
            token_count=1,
            character_count=4
        )
        
        # In actual implementation, this would be a SQLAlchemy relationship
        assert chunk.document_id == doc.id
    
    def test_chunk_embedding_relationship(self):
        """Test chunk to embedding relationship"""
        chunk = KnowledgeChunk(
            document_id=1,
            chunk_index=0,
            content="Test",
            token_count=1,
            character_count=4
        )
        
        embedding = KnowledgeEmbedding(
            chunk_id=chunk.id,
            document_id=1,
            embedding=[0.1] * 1024,
            embedding_dimension=1024,
            embedding_provider=EmbeddingProvider.BAAI_BGE,
            embedding_model="bge-large-en-v1.5"
        )
        
        assert embedding.chunk_id == chunk.id
