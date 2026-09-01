from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from .base import BaseMemoryStore, MemoryItem, MemorySearchResult
from app.models.memory import Memory
from loguru import logger
from datetime import datetime


class LongTermMemoryStore(BaseMemoryStore):
    """Long-term memory store backed by database"""
    
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
    
    async def add(self, memory: MemoryItem) -> MemoryItem:
        """Add a memory to the database"""
        db_memory = Memory(
            user_id=self.user_id,
            content=memory.content,
            summary=memory.summary,
            importance=memory.importance,
            memory_type=memory.memory_type,
            metadata=memory.metadata,
            is_pinned=memory.is_pinned
        )
        
        self.db.add(db_memory)
        await self.db.commit()
        await self.db.refresh(db_memory)
        
        logger.info(f"Added long-term memory: {db_memory.id}")
        return MemoryItem(
            id=int(db_memory.id),
            content=str(db_memory.content),
            summary=str(db_memory.summary),
            importance=float(db_memory.importance),
            memory_type=str(db_memory.memory_type.value),
            metadata=db_memory.metadata,
            created_at=db_memory.created_at,  # type: ignore[arg-type]
            updated_at=db_memory.updated_at,  # type: ignore[arg-type]
            is_pinned=bool(db_memory.is_pinned)
        )
    
    async def get(self, memory_id: int) -> Optional[MemoryItem]:
        """Get a memory by ID"""
        result = await self.db.execute(
            select(Memory).where(
                and_(
                    Memory.id == memory_id,
                    Memory.user_id == self.user_id,
                    Memory.is_deleted == False
                )
            )
        )
        db_memory = result.scalar_one_or_none()
        
        if not db_memory:
            return None
        
        return MemoryItem(
            id=int(db_memory.id),
            content=str(db_memory.content),
            summary=str(db_memory.summary),
            importance=float(db_memory.importance),
            memory_type=str(db_memory.memory_type.value),
            metadata=db_memory.metadata,
            created_at=db_memory.created_at,  # type: ignore[arg-type]
            updated_at=db_memory.updated_at,  # type: ignore[arg-type]
            is_pinned=bool(db_memory.is_pinned)
        )
    
    async def update(self, memory_id: int, memory: MemoryItem) -> Optional[MemoryItem]:
        """Update a memory"""
        result = await self.db.execute(
            select(Memory).where(
                and_(
                    Memory.id == memory_id,
                    Memory.user_id == self.user_id,
                    Memory.is_deleted == False
                )
            )
        )
        db_memory = result.scalar_one_or_none()
        
        if not db_memory:
            return None
        
        db_memory.content = memory.content  # type: ignore[assignment]
        db_memory.summary = memory.summary  # type: ignore[assignment]
        db_memory.importance = memory.importance  # type: ignore[assignment]
        db_memory.memory_type = memory.memory_type  # type: ignore[assignment]
        db_memory.metadata = memory.metadata  # type: ignore[assignment]
        db_memory.is_pinned = memory.is_pinned  # type: ignore[assignment]
        db_memory.updated_at = datetime.utcnow()  # type: ignore[assignment]
        
        await self.db.commit()
        await self.db.refresh(db_memory)
        
        logger.info(f"Updated long-term memory: {db_memory.id}")
        return MemoryItem(
            id=int(db_memory.id),
            content=str(db_memory.content),
            summary=str(db_memory.summary),
            importance=float(db_memory.importance),
            memory_type=str(db_memory.memory_type.value),
            metadata=db_memory.metadata,
            created_at=db_memory.created_at,  # type: ignore[arg-type]
            updated_at=db_memory.updated_at,  # type: ignore[arg-type]
            is_pinned=bool(db_memory.is_pinned)
        )
    
    async def delete(self, memory_id: int) -> bool:
        """Soft delete a memory"""
        result = await self.db.execute(
            select(Memory).where(
                and_(
                    Memory.id == memory_id,
                    Memory.user_id == self.user_id,
                    Memory.is_deleted == False
                )
            )
        )
        db_memory = result.scalar_one_or_none()
        
        if not db_memory:
            return False
        
        db_memory.is_deleted = True  # type: ignore[assignment]
        db_memory.deleted_at = datetime.utcnow()  # type: ignore[assignment]
        
        await self.db.commit()
        
        logger.info(f"Deleted long-term memory: {memory_id}")
        return True
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search memories by query (simple text search)"""
        conditions = [
            Memory.user_id == self.user_id,
            Memory.is_deleted == False,
            Memory.content.ilike(f"%{query}%")
        ]
        
        if memory_type:
            conditions.append(Memory.memory_type == memory_type)
        
        result = await self.db.execute(
            select(Memory)
            .where(and_(*conditions))
            .order_by(Memory.importance.desc())
            .limit(limit)
        )
        memories = result.scalars().all()
        
        return [
            MemorySearchResult(
                memory=MemoryItem(
                    id=int(m.id),
                    content=str(m.content),
                    summary=str(m.summary),
                    importance=float(m.importance),
                    memory_type=str(m.memory_type.value),
                    metadata=m.metadata,
                    created_at=m.created_at,  # type: ignore[arg-type]
                    updated_at=m.updated_at,  # type: ignore[arg-type]
                    is_pinned=bool(m.is_pinned)
                ),
                score=float(m.importance)
            )
            for m in memories
        ]
    
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """Get recent memories"""
        conditions = [
            Memory.user_id == self.user_id,
            Memory.is_deleted == False
        ]
        
        if memory_type:
            conditions.append(Memory.memory_type == memory_type)
        
        result = await self.db.execute(
            select(Memory)
            .where(and_(*conditions))
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        memories = result.scalars().all()
        
        return [
            MemoryItem(
                id=int(m.id),
                content=str(m.content),
                summary=str(m.summary),
                importance=float(m.importance),
                memory_type=str(m.memory_type.value),
                metadata=m.metadata,
                created_at=m.created_at,  # type: ignore[arg-type]
                updated_at=m.updated_at,  # type: ignore[arg-type]
                is_pinned=bool(m.is_pinned)
            )
            for m in memories
        ]
    
    async def get_pinned(self) -> List[MemoryItem]:
        """Get all pinned memories"""
        result = await self.db.execute(
            select(Memory)
            .where(
                and_(
                    Memory.user_id == self.user_id,
                    Memory.is_deleted == False,
                    Memory.is_pinned == True
                )
            )
            .order_by(Memory.importance.desc())
        )
        memories = result.scalars().all()
        
        return [
            MemoryItem(
                id=int(m.id),
                content=str(m.content),
                summary=str(m.summary),
                importance=float(m.importance),
                memory_type=str(m.memory_type.value),
                metadata=m.metadata,
                created_at=m.created_at,  # type: ignore[arg-type]
                updated_at=m.updated_at,  # type: ignore[arg-type]
                is_pinned=bool(m.is_pinned)
            )
            for m in memories
        ]
