"""
Enterprise Knowledge Platform Models
Production-grade models for RAG system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, BigInteger, Float, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Optional
import uuid

from app.core.database import Base


class DocumentStatus(PyEnum):
    """Document processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentType(PyEnum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    MD = "md"
    TXT = "txt"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    IMAGE = "image"  # OCR
    ZIP = "zip"


class ChunkingStrategy(PyEnum):
    """Chunking strategies"""
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"
    SLIDING_WINDOW = "sliding_window"
    PARENT_CHILD = "parent_child"
    ADAPTIVE = "adaptive"


class EmbeddingProvider(PyEnum):
    """Embedding providers"""
    BAAI_BGE = "BAAI_BGE"
    MULTILINGUAL_E5 = "MULTILINGUAL_E5"
    OPENAI = "OPENAI"
    JINA = "JINA"


class VectorStoreType(PyEnum):
    """Vector database types"""
    PGVECTOR = "pgvector"
    CHROMADB = "chromadb"
    QDRANT = "qdrant"


class KnowledgeDocument(Base):
    """
    Enterprise knowledge document model
    Enhanced version of existing Document model for RAG platform
    """
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    
    # Basic Info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.PROCESSING, index=True)
    
    # File Information
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_path = Column(String(1000), nullable=True)
    
    # Content
    raw_content = Column(Text, nullable=True)
    processed_content = Column(Text, nullable=True)
    checksum = Column(String(64), nullable=False, index=True)  # SHA-256
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    author = Column(String(255), nullable=True)
    language = Column(String(10), nullable=True, index=True)
    
    # Versioning
    version = Column(Integer, default=1)
    parent_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True)
    
    # Processing Configuration
    chunking_strategy: Mapped[ChunkingStrategy] = mapped_column(Enum(ChunkingStrategy), default=ChunkingStrategy.SEMANTIC)
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # Embedding Configuration
    embedding_provider: Mapped[EmbeddingProvider] = mapped_column(Enum(EmbeddingProvider), default=EmbeddingProvider.OPENAI)
    embedding_model = Column(String(100), nullable=True)
    embedding_dimension = Column(Integer, default=1024)
    vector_store_type: Mapped[VectorStoreType] = mapped_column(Enum(VectorStoreType), default=VectorStoreType.PGVECTOR)
    vector_collection = Column(String(100), nullable=True)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    
    # Access Control
    is_public = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="knowledge_documents")
    file = relationship("File", backref="knowledge_documents")
    parent = relationship("KnowledgeDocument", remote_side=[id], backref="children")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
    embeddings = relationship("KnowledgeEmbedding", back_populates="document", cascade="all, delete-orphan")
    search_history = relationship("KnowledgeSearchHistory", back_populates="document")

    __table_args__ = (
        Index('idx_knowledge_documents_user_status', 'user_id', 'status'),
        Index('idx_knowledge_documents_checksum', 'checksum'),
    )


class KnowledgeChunk(Base):
    """
    Document chunk model for RAG
    """
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Parent/Child Chunking
    parent_chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="SET NULL"), nullable=True)
    is_parent = Column(Boolean, default=False)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    page_number = Column(Integer, nullable=True)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    
    # Statistics
    token_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")
    parent_chunk = relationship("KnowledgeChunk", remote_side=[id], backref="child_chunks")
    embeddings = relationship("KnowledgeEmbedding", back_populates="chunk", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_knowledge_chunks_document_index', 'document_id', 'chunk_index'),
    )


class KnowledgeEmbedding(Base):
    """
    Vector embedding model with pgvector support
    """
    __tablename__ = "knowledge_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Vector Embedding (stored as JSON for pgvector compatibility)
    embedding = Column(JSON, nullable=False)  # Will be converted to vector type in pgvector
    embedding_dimension = Column(Integer, default=1024)
    
    # Provider Information
    embedding_provider: Mapped[EmbeddingProvider] = mapped_column(Enum(EmbeddingProvider), nullable=False)
    embedding_model = Column(String(100), nullable=False)
    
    # Cache Key
    cache_key = Column(String(255), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    chunk = relationship("KnowledgeChunk", back_populates="embeddings")
    document = relationship("KnowledgeDocument", back_populates="embeddings")

    __table_args__ = (
        Index('idx_knowledge_embeddings_chunk', 'chunk_id'),
        Index('idx_knowledge_embeddings_document', 'document_id'),
        Index('idx_knowledge_embeddings_cache', 'cache_key'),
    )


class KnowledgeSearchHistory(Base):
    """
    Search history for analytics and improvement
    """
    __tablename__ = "knowledge_search_history"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True)
    
    # Query Information
    query = Column(Text, nullable=False)
    query_type = Column(String(50), default="semantic")  # semantic, hybrid, keyword
    filters = Column(JSON, nullable=True)
    
    # Results
    results_json = Column(JSON, nullable=True)
    result_count = Column(Integer, default=0)
    
    # Performance
    latency_ms = Column(Integer, nullable=True)
    
    # Feedback
    clicked_result_id = Column(Integer, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="knowledge_search_history")
    document = relationship("KnowledgeDocument", back_populates="search_history")

    __table_args__ = (
        Index('idx_knowledge_search_history_user', 'user_id'),
        Index('idx_knowledge_search_history_created', 'created_at'),
    )


class KnowledgeRerankResult(Base):
    """
    Reranking results for analytics
    """
    __tablename__ = "knowledge_rerank_results"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    search_history_id = Column(Integer, ForeignKey("knowledge_search_history.id", ondelete="CASCADE"), nullable=False)
    
    # Reranking Information
    reranker_model = Column(String(100), nullable=False)
    original_rank = Column(Integer, nullable=False)
    reranked_rank = Column(Integer, nullable=False)
    score_change = Column(Float, nullable=False)
    
    # Chunk Reference
    chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="SET NULL"), nullable=True)
    
    # Scores
    original_score = Column(Float, nullable=False)
    reranked_score = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_knowledge_rerank_search', 'search_history_id'),
    )


class KnowledgeAuditLog(Base):
    """
    Audit log for security and compliance
    """
    __tablename__ = "knowledge_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Action Information
    action = Column(String(50), nullable=False)  # upload, delete, search, view, download
    resource_type = Column(String(50), nullable=False)  # document, chunk, embedding
    resource_id = Column(Integer, nullable=True)
    
    # Details
    details_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_knowledge_audit_user', 'user_id'),
        Index('idx_knowledge_audit_action', 'action'),
        Index('idx_knowledge_audit_created', 'created_at'),
    )


class KnowledgeIndexingQueue(Base):
    """
    Queue for asynchronous document indexing
    """
    __tablename__ = "knowledge_indexing_queue"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Queue Information
    priority = Column(Integer, default=5)  # 1-10, lower is higher priority
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Processing Information
    worker_id = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_knowledge_queue_status', 'status'),
        Index('idx_knowledge_queue_priority', 'priority', 'created_at'),
    )
