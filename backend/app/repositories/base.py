from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from loguru import logger

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(
        self,
        db: AsyncSession,
        id: int,
        load_relations: bool = False,
    ) -> Optional[ModelType]:
        """Get a single record by ID."""
        query = select(self.model).where(self.model.id == id)
        
        if load_relations:
            # Load all relationships
            query = query.options(selectinload("*"))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        load_relations: bool = False,
        **filters: Any,
    ) -> List[ModelType]:
        """Get multiple records with optional filtering."""
        query = select(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                if value is None:
                    query = query.where(getattr(self.model, key).is_(None))
                else:
                    query = query.where(getattr(self.model, key) == value)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        if load_relations:
            query = query.options(selectinload("*"))
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        obj_in: CreateSchemaType,
    ) -> ModelType:
        """Create a new record."""
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        db_obj = self.model(**obj_in_data)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Created {self.model.__name__}: {db_obj.id}")
        return db_obj  # type: ignore[no-any-return]

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
    ) -> ModelType:
        """Update an existing record."""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        
        if isinstance(obj_data, dict):
            for field, value in obj_data.items():
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info(f"Updated {self.model.__name__}: {db_obj.id}")
        return db_obj

    async def delete(
        self,
        db: AsyncSession,
        id: int,
    ) -> bool:
        """Delete a record by ID."""
        obj = await self.get(db, id)
        if not obj:
            return False
        
        await db.delete(obj)
        await db.commit()
        
        logger.info(f"Deleted {self.model.__name__}: {id}")
        return True

    async def count(
        self,
        db: AsyncSession,
        **filters: Any,
    ) -> int:
        """Count records matching filters."""
        from sqlalchemy import func
        
        query = select(func.count(self.model.id))
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                if value is None:
                    query = query.where(getattr(self.model, key).is_(None))
                else:
                    query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        scalar_result = result.scalar()
        return scalar_result if scalar_result is not None else 0

    async def exists(
        self,
        db: AsyncSession,
        **filters: Any,
    ) -> bool:
        """Check if a record exists."""
        count = await self.count(db, **filters)
        return count > 0

    async def bulk_create(
        self,
        db: AsyncSession,
        objects_in: List[CreateSchemaType],
    ) -> List[ModelType]:
        """Create multiple records in bulk."""
        db_objs = []
        for obj_in in objects_in:
            obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        await db.commit()
        
        for db_obj in db_objs:
            await db.refresh(db_obj)
        
        logger.info(f"Bulk created {len(db_objs)} {self.model.__name__} records")
        return db_objs

    async def bulk_update(
        self,
        db: AsyncSession,
        ids: List[int],
        obj_in: UpdateSchemaType,
    ) -> List[ModelType]:
        """Update multiple records in bulk."""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        
        if isinstance(obj_data, dict):
            query = update(self.model).where(self.model.id.in_(ids)).values(**obj_data)
            await db.execute(query)
            await db.commit()
        else:
            raise ValueError("obj_in must be a dict or have model_dump method")
        
        # Fetch updated objects
        result = await db.execute(select(self.model).where(self.model.id.in_(ids)))
        updated_objs = result.scalars().all()
        
        logger.info(f"Bulk updated {len(updated_objs)} {self.model.__name__} records")
        return list(updated_objs)

    async def bulk_delete(
        self,
        db: AsyncSession,
        ids: List[int],
    ) -> int:
        """Delete multiple records in bulk."""
        query = delete(self.model).where(self.model.id.in_(ids))
        result = await db.execute(query)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Bulk deleted {deleted_count} {self.model.__name__} records")
        return deleted_count  # type: ignore[no-any-return]
