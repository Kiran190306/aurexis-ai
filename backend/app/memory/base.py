from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class MemoryItem(BaseModel):
    """Base memory item"""
    id: Optional[int] = None
    content: str
    summary: str
    importance: float = 0.5
    memory_type: str = "episodic"  # episodic, semantic, procedural
    metadata: Dict[str, Any] = {}
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    is_pinned: bool = False


class MemorySearchResult(BaseModel):
    """Result of a memory search"""
    memory: MemoryItem
    score: float


class BaseMemoryStore(ABC):
    """Base class for memory stores"""
    
    @abstractmethod
    async def add(self, memory: MemoryItem) -> MemoryItem:
        """Add a memory to the store"""
        pass
    
    @abstractmethod
    async def get(self, memory_id: int) -> Optional[MemoryItem]:
        """Get a memory by ID"""
        pass
    
    @abstractmethod
    async def update(self, memory_id: int, memory: MemoryItem) -> Optional[MemoryItem]:
        """Update a memory"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: int) -> bool:
        """Delete a memory"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search memories by query"""
        pass
    
    @abstractmethod
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """Get recent memories"""
        pass
    
    @abstractmethod
    async def get_pinned(self) -> List[MemoryItem]:
        """Get all pinned memories"""
        pass
