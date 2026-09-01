from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, JSON, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class FileType(PyEnum):
    IMAGE = "image"
    DOCUMENT = "document"
    CODE = "code"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    OTHER = "other"


class FileStatus(PyEnum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType), nullable=False)
    mime_type = Column(String(100), nullable=False)
    status: Mapped[FileStatus] = mapped_column(Enum(FileStatus), default=FileStatus.UPLOADING)
    
    # Storage
    storage_path = Column(String(500), nullable=False)
    storage_provider = Column(String(50), default="local")  # local, s3, gcs, azure
    storage_bucket = Column(String(100), nullable=True)
    
    # File Properties
    file_size = Column(BigInteger, nullable=False)  # bytes
    file_hash = Column(String(64), nullable=True)  # SHA-256
    checksum = Column(String(64), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    width = Column(Integer, nullable=True)  # For images
    height = Column(Integer, nullable=True)  # For images
    duration = Column(Integer, nullable=True)  # For audio/video in seconds
    
    # Processing
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Access Control
    is_public = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    encryption_key = Column(String(255), nullable=True)
    
    # Sharing
    share_token = Column(String(255), unique=True, nullable=True, index=True)
    share_expires_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="files")


class FileVersion(Base):
    __tablename__ = "file_versions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    
    # Version Info
    version_number = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FileShare(Base):
    __tablename__ = "file_shares"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    shared_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Share Info
    share_token = Column(String(255), unique=True, index=True, nullable=False)
    
    # Access Control
    can_download = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    
    # Limits
    max_accesses = Column(Integer, nullable=True)
    access_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password Protection
    password_hash = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
