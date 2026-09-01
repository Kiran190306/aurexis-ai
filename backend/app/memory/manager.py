from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .base import MemoryItem, MemorySearchResult
from .long_term import LongTermMemoryStore
from .short_term import ShortTermMemoryStore
from loguru import logger


class MemoryManager:
    """Manager for coordinating long-term and short-term memory stores"""
    
    def __init__(self, db: AsyncSession, user_id: int):
        self.user_id = user_id
        self.long_term = LongTermMemoryStore(db, user_id)
        self.short_term = ShortTermMemoryStore(max_items=100, ttl_hours=24)
    
    async def add(
        self,
        content: str,
        summary: str,
        importance: float = 0.5,
        memory_type: str = "episodic",
        metadata: Optional[Dict[str, Any]] = None,
        is_pinned: bool = False,
        store: str = "long_term"
    ) -> MemoryItem:
        """Add a memory to the specified store"""
        memory = MemoryItem(
            content=content,
            summary=summary,
            importance=importance,
            memory_type=memory_type,
            metadata=metadata or {},
            is_pinned=is_pinned
        )
        
        if store == "long_term":
            return await self.long_term.add(memory)
        else:
            return await self.short_term.add(memory)
    
    async def get(self, memory_id: int, store: str = "long_term") -> Optional[MemoryItem]:
        """Get a memory by ID from the specified store"""
        if store == "long_term":
            return await self.long_term.get(memory_id)
        else:
            return await self.short_term.get(memory_id)
    
    async def update(
        self,
        memory_id: int,
        memory: MemoryItem,
        store: str = "long_term"
    ) -> Optional[MemoryItem]:
        """Update a memory in the specified store"""
        if store == "long_term":
            return await self.long_term.update(memory_id, memory)
        else:
            return await self.short_term.update(memory_id, memory)
    
    async def delete(self, memory_id: int, store: str = "long_term") -> bool:
        """Delete a memory from the specified store"""
        if store == "long_term":
            return await self.long_term.delete(memory_id)
        else:
            return await self.short_term.delete(memory_id)
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None,
        store: str = "both"
    ) -> List[MemorySearchResult]:
        """Search memories across stores"""
        results = []
        
        if store in ["long_term", "both"]:
            lt_results = await self.long_term.search(query, limit, memory_type)
            results.extend(lt_results)
        
        if store in ["short_term", "both"]:
            st_results = await self.short_term.search(query, limit, memory_type)
            results.extend(st_results)
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[str] = None,
        store: str = "both"
    ) -> List[MemoryItem]:
        """Get recent memories across stores"""
        results = []
        
        if store in ["long_term", "both"]:
            lt_results = await self.long_term.get_recent(limit, memory_type)
            results.extend(lt_results)
        
        if store in ["short_term", "both"]:
            st_results = await self.short_term.get_recent(limit, memory_type)
            results.extend(st_results)
        
        # Sort by creation time and limit
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]
    
    async def get_pinned(self, store: str = "both") -> List[MemoryItem]:
        """Get pinned memories across stores"""
        results = []
        
        if store in ["long_term", "both"]:
            lt_results = await self.long_term.get_pinned()
            results.extend(lt_results)
        
        if store in ["short_term", "both"]:
            st_results = await self.short_term.get_pinned()
            results.extend(st_results)
        
        # Sort by importance
        results.sort(key=lambda x: x.importance, reverse=True)
        return results
    
    async def promote_to_long_term(self, memory_id: int) -> Optional[MemoryItem]:
        """Promote a short-term memory to long-term storage"""
        memory = await self.short_term.get(memory_id)
        
        if not memory:
            return None
        
        # Add to long-term
        lt_memory = await self.long_term.add(memory)
        
        # Remove from short-term
        await self.short_term.delete(memory_id)
        
        logger.info(f"Promoted memory {memory_id} to long-term storage")
        return lt_memory
    
    async def cleanup_short_term(self) -> int:
        """Clean up expired short-term memories"""
        return await self.short_term.cleanup_expired()
    
    async def get_context_for_conversation(
        self,
        conversation_id: Optional[int] = None,
        limit: int = 20
    ) -> List[MemoryItem]:
        """Get relevant memories for conversation context"""
        # Get pinned memories first
        pinned = await self.get_pinned()
        
        # Get recent memories
        recent = await self.get_recent(limit=limit)
        
        # Combine and deduplicate
        seen_ids = set()
        context = []
        
        for memory in pinned + recent:
            if memory.id not in seen_ids:
                context.append(memory)
                seen_ids.add(memory.id)
        
        return context[:limit]
