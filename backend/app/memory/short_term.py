from typing import List, Dict, Optional
from collections import deque
from datetime import datetime, timedelta
from .base import BaseMemoryStore, MemoryItem, MemorySearchResult
from loguru import logger


class ShortTermMemoryStore(BaseMemoryStore):
    """Short-term memory store (in-memory with limited capacity)"""
    
    def __init__(self, max_items: int = 100, ttl_hours: int = 24):
        self.max_items = max_items
        self.ttl = timedelta(hours=ttl_hours)
        self.memories: Dict[int, MemoryItem] = {}
        self.memory_queue: deque = deque()
        self._next_id = 1
    
    async def add(self, memory: MemoryItem) -> MemoryItem:
        """Add a memory to short-term store"""
        memory.id = self._next_id
        memory.created_at = datetime.utcnow()
        memory.updated_at = datetime.utcnow()
        
        # Remove oldest if at capacity
        if len(self.memories) >= self.max_items:
            oldest_id = self.memory_queue.popleft()
            del self.memories[oldest_id]
        
        self.memories[memory.id] = memory
        self.memory_queue.append(memory.id)
        self._next_id += 1
        
        logger.info(f"Added short-term memory: {memory.id}")
        return memory
    
    async def get(self, memory_id: int) -> Optional[MemoryItem]:
        """Get a memory by ID"""
        memory = self.memories.get(memory_id)
        
        # Check if expired
        if memory and (datetime.utcnow() - memory.created_at) > self.ttl:
            await self.delete(memory_id)
            return None
        
        return memory
    
    async def update(self, memory_id: int, memory: MemoryItem) -> Optional[MemoryItem]:
        """Update a memory"""
        if memory_id not in self.memories:
            return None
        
        existing = self.memories[memory_id]
        
        # Check if expired
        if (datetime.utcnow() - existing.created_at) > self.ttl:
            await self.delete(memory_id)
            return None
        
        memory.id = memory_id
        memory.created_at = existing.created_at
        memory.updated_at = datetime.utcnow()
        
        self.memories[memory_id] = memory
        
        logger.info(f"Updated short-term memory: {memory_id}")
        return memory
    
    async def delete(self, memory_id: int) -> bool:
        """Delete a memory"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            # Remove from queue
            self.memory_queue = deque([id for id in self.memory_queue if id != memory_id])
            logger.info(f"Deleted short-term memory: {memory_id}")
            return True
        return False
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search memories by query"""
        now = datetime.utcnow()
        results = []
        
        for memory in self.memories.values():
            # Check if expired
            if (now - memory.created_at) > self.ttl:
                continue
            
            # Filter by type if specified
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # Simple text matching
            if query.lower() in memory.content.lower() or query.lower() in memory.summary.lower():
                results.append(
                    MemorySearchResult(
                        memory=memory,
                        score=memory.importance
                    )
                )
        
        # Sort by importance and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """Get recent memories"""
        now = datetime.utcnow()
        results = []
        
        for memory in self.memories.values():
            # Check if expired
            if (now - memory.created_at) > self.ttl:
                continue
            
            # Filter by type if specified
            if memory_type and memory.memory_type != memory_type:
                continue
            
            results.append(memory)
        
        # Sort by creation time and limit
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]
    
    async def get_pinned(self) -> List[MemoryItem]:
        """Get all pinned memories"""
        now = datetime.utcnow()
        results = []
        
        for memory in self.memories.values():
            # Check if expired
            if (now - memory.created_at) > self.ttl:
                continue
            
            if memory.is_pinned:
                results.append(memory)
        
        # Sort by importance
        results.sort(key=lambda x: x.importance, reverse=True)
        return results
    
    async def cleanup_expired(self) -> int:
        """Remove expired memories"""
        now = datetime.utcnow()
        expired_ids = []
        
        for memory_id, memory in self.memories.items():
            if (now - memory.created_at) > self.ttl:
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            await self.delete(memory_id)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired short-term memories")
        
        return len(expired_ids)
