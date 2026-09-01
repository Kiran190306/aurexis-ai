from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class PluginType(PyEnum):
    BUILTIN = "builtin"
    EXTERNAL = "external"
    MARKETPLACE = "marketplace"


class PluginStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"
    BANNED = "banned"


class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    version = Column(String(20), default="1.0.0")
    author = Column(String(100))
    repository_url = Column(String(500))
    
    # Type & Status
    plugin_type: Mapped[PluginType] = mapped_column(Enum(PluginType), default=PluginType.EXTERNAL)
    status: Mapped[PluginStatus] = mapped_column(Enum(PluginStatus), default=PluginStatus.ACTIVE)
    
    # Package Info
    package_name = Column(String(200), nullable=True)
    package_version = Column(String(100), nullable=True)
    
    # Configuration
    config_schema = Column(JSON)  # JSON Schema for plugin configuration
    default_config = Column(JSON)
    
    # Capabilities
    capabilities = Column(JSON)  # Array of capabilities
    permissions = Column(JSON)  # Required permissions
    
    # Dependencies
    dependencies = Column(JSON)  # Plugin dependencies
    python_dependencies = Column(JSON)  # Python package dependencies
    
    # Hooks
    hooks = Column(JSON)  # Event hooks
    
    # Statistics
    install_count = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Marketplace
    is_featured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="plugins")
    tools = relationship("Tool", back_populates="plugin", cascade="all, delete-orphan")


class PluginInstallation(Base):
    __tablename__ = "plugin_installations"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Installation
    config = Column(JSON)  # User-specific configuration
    is_enabled = Column(Boolean, default=True)
    
    # Statistics
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    installed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
