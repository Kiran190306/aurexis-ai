from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class DocumentType(PyEnum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"
    CODE = "code"


class DocumentStatus(PyEnum):
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    
    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.PROCESSING)
    
    # Content
    raw_content = Column(Text, nullable=True)
    processed_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Document metadata
    author = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)
    
    # Processing
    chunk_count = Column(Integer, default=0)
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # Vector Indexing
    embedding_model = Column(String(100), nullable=True)
    vector_collection = Column(String(100), nullable=True)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    token_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    
    # Access Control
    is_public = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")
    file = relationship("File", backref="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Vector Embedding
    embedding = Column(JSON)  # Vector embedding
    embedding_model = Column(String(100), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    page_number = Column(Integer, nullable=True)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    
    # Statistics
    token_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # Vector Collection
    vector_collection = Column(String(100), nullable=False)
    
    # Statistics
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    
    # Access Control
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    # Status
    is_indexed = Column(Boolean, default=False)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now())
