"""Async repository base class with advanced CRUD operations.

This module provides a comprehensive async base repository implementation with:
- Async CRUD operations
- Pagination support
- Filtering and sorting
- Eager loading patterns
- Transaction management
- Unit of Work pattern
"""

from datetime import datetime
from typing import Any, Generic, TypeVar, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class PaginationParams:
    """Pagination parameters."""

    def __init__(self, skip: int = 0, limit: int = 100):
        """Initialize pagination params."""
        self.skip = max(0, skip)
        self.limit = max(1, min(limit, 1000))  # Cap at 1000

    def offset(self) -> int:
        """Get offset for SQL query."""
        return self.skip

    def count(self) -> int:
        """Get limit for SQL query."""
        return self.limit


class FilterParams:
    """Base filter parameters for querying."""

    def __init__(self, **kwargs: Any):
        """Initialize filters from kwargs."""
        self.filters = kwargs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.filters.items() if v is not None}


class PaginatedResponse(BaseModel):
    """Response model for paginated results."""

    data: list[Any]
    total: int
    skip: int
    limit: int
    pages: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class AsyncBaseRepository(Generic[ModelType]):
    """
    Async repository providing comprehensive CRUD operations.

    Features:
    - Async/await support for all database operations
    - Pagination with configurable limits
    - Advanced filtering and sorting
    - Eager loading to prevent N+1 queries
    - Transaction management
    - Bulk operations for efficiency

    All entity-specific repositories inherit from this class.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession):
        """
        Initialize async repository.

        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db

    # ============= Basic CRUD Operations =============

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new entity.

        Args:
            obj_in: Pydantic schema with data

        Returns:
            Created model instance

        Raises:
            ValueError: If validation fails
        """
        db_obj = self.model(**obj_in.model_dump(exclude_unset=True))
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def get_by_id(self, id: UUID | str) -> Optional[ModelType]:
        """
        Get entity by primary key.

        Args:
            id: Primary key value

        Returns:
            Model instance or None
        """
        return await self.db.get(self.model, id)

    async def get_all(
        self,
        pagination: Optional[PaginationParams] = None,
        eager_fields: Optional[list[str]] = None,
    ) -> list[ModelType]:
        """
        Get all entities with optional pagination.

        Args:
            pagination: Pagination parameters
            eager_fields: Relationship fields to eagerly load

        Returns:
            List of model instances
        """
        query = select(self.model)

        # Add eager loading
        if eager_fields:
            for field in eager_fields:
                if hasattr(self.model, field):
                    query = query.options(selectinload(getattr(self.model, field)))

        # Add pagination
        if pagination:
            query = query.offset(pagination.offset()).limit(pagination.count())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """
        Update an existing entity.

        Args:
            db_obj: Existing model instance
            obj_in: Pydantic schema with updated data

        Returns:
            Updated model instance
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """
        Delete an entity.

        Args:
            db_obj: Model instance to delete
        """
        await self.db.delete(db_obj)
        await self.db.flush()

    async def delete_by_id(self, id: UUID | str) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        obj = await self.get_by_id(id)
        if obj:
            await self.delete(obj)
            return True
        return False

    # ============= Pagination Operations =============

    async def get_paginated(
        self,
        pagination: PaginationParams,
        eager_fields: Optional[list[str]] = None,
        order_by: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> PaginatedResponse:
        """
        Get paginated results with optional filtering and sorting.

        Args:
            pagination: Pagination parameters
            eager_fields: Relationship fields to eagerly load
            order_by: Field name to sort by (prefix with '-' for desc)
            filters: Dictionary of filters {field: value}

        Returns:
            PaginatedResponse with data, total, and pagination info
        """
        query = select(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        # Count total before pagination
        count_query = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    count_query = count_query.where(
                        getattr(self.model, field) == value
                    )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Add eager loading
        if eager_fields:
            for field in eager_fields:
                if hasattr(self.model, field):
                    query = query.options(selectinload(getattr(self.model, field)))

        # Add sorting
        if order_by:
            if order_by.startswith("-"):
                field_name = order_by[1:]
                if hasattr(self.model, field_name):
                    query = query.order_by(desc(getattr(self.model, field_name)))
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))

        # Add pagination
        query = query.offset(pagination.offset()).limit(pagination.count())

        result = await self.db.execute(query)
        data = result.scalars().all()

        pages = (total + pagination.count() - 1) // pagination.count()

        return PaginatedResponse(
            data=data,
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
            pages=pages,
        )

    # ============= Filtering Operations =============

    async def get_by_filters(
        self,
        filters: dict[str, Any],
        eager_fields: Optional[list[str]] = None,
        order_by: Optional[str] = None,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get entities matching multiple filters.

        Args:
            filters: Dictionary of {field: value} pairs
            eager_fields: Relationship fields to eagerly load
            order_by: Field to sort by
            limit: Maximum results to return

        Returns:
            List of matching model instances
        """
        conditions = []
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                conditions.append(getattr(self.model, field) == value)

        query = select(self.model)

        if conditions:
            query = query.where(and_(*conditions))

        # Add eager loading
        if eager_fields:
            for field in eager_fields:
                if hasattr(self.model, field):
                    query = query.options(selectinload(getattr(self.model, field)))

        # Add sorting
        if order_by:
            if order_by.startswith("-"):
                field_name = order_by[1:]
                if hasattr(self.model, field_name):
                    query = query.order_by(desc(getattr(self.model, field_name)))
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))

        query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_first_by_filters(
        self, filters: dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Get first entity matching filters.

        Args:
            filters: Dictionary of {field: value} pairs

        Returns:
            First matching model instance or None
        """
        conditions = []
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                conditions.append(getattr(self.model, field) == value)

        query = select(self.model)
        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalars().first()

    # ============= Eager Loading Operations =============

    async def get_by_id_with_relations(
        self, id: UUID | str, relations: list[str]
    ) -> Optional[ModelType]:
        """
        Get entity by ID with specified relationships eagerly loaded.

        Args:
            id: Primary key value
            relations: List of relationship field names to load

        Returns:
            Model instance with loaded relations or None
        """
        query = select(self.model).where(self.model.id == id)

        for relation in relations:
            if hasattr(self.model, relation):
                query = query.options(selectinload(getattr(self.model, relation)))

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all_with_relations(
        self,
        relations: list[str],
        pagination: Optional[PaginationParams] = None,
    ) -> list[ModelType]:
        """
        Get all entities with specified relationships eagerly loaded.

        Args:
            relations: List of relationship field names to load
            pagination: Optional pagination parameters

        Returns:
            List of model instances with loaded relations
        """
        query = select(self.model)

        for relation in relations:
            if hasattr(self.model, relation):
                query = query.options(selectinload(getattr(self.model, relation)))

        if pagination:
            query = query.offset(pagination.offset()).limit(pagination.count())

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============= Counting and Existence Operations =============

    async def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters.

        Args:
            filters: Optional dictionary of {field: value} pairs

        Returns:
            Count of matching entities
        """
        query = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def exists(self, filters: dict[str, Any]) -> bool:
        """
        Check if entity matching filters exists.

        Args:
            filters: Dictionary of {field: value} pairs

        Returns:
            True if exists, False otherwise
        """
        count = await self.count(filters)
        return count > 0

    # ============= Bulk Operations =============

    async def bulk_create(
        self, objects_in: list[CreateSchemaType]
    ) -> list[ModelType]:
        """
        Create multiple entities efficiently.

        Args:
            objects_in: List of Pydantic schemas

        Returns:
            List of created model instances
        """
        db_objects = [
            self.model(**obj.model_dump(exclude_unset=True)) for obj in objects_in
        ]
        self.db.add_all(db_objects)
        await self.db.flush()
        return db_objects

    async def bulk_update(
        self, objects: list[ModelType]
    ) -> list[ModelType]:
        """
        Update multiple entities efficiently.

        Args:
            objects: List of model instances with updated values

        Returns:
            List of updated model instances
        """
        self.db.add_all(objects)
        await self.db.flush()
        return objects

    async def bulk_delete(self, ids: list[UUID | str]) -> int:
        """
        Delete multiple entities by IDs.

        Args:
            ids: List of primary key values

        Returns:
            Number of deleted entities
        """
        count = 0
        for id_val in ids:
            if await self.delete_by_id(id_val):
                count += 1
        return count

    # ============= Transaction Management =============

    async def commit(self) -> None:
        """Commit current transaction."""
        await self.db.commit()

    async def rollback(self) -> None:
        """Rollback current transaction."""
        await self.db.rollback()

    async def refresh(self, db_obj: ModelType) -> ModelType:
        """
        Refresh entity from database.

        Args:
            db_obj: Model instance to refresh

        Returns:
            Refreshed model instance
        """
        await self.db.refresh(db_obj)
        return db_obj

    # ============= Utility Operations =============

    def detach(self, db_obj: ModelType) -> ModelType:
        """
        Detach object from session (for serialization).

        Args:
            db_obj: Model instance

        Returns:
            Detached model instance
        """
        self.db.expunge(db_obj)
        return db_obj

    async def exists_by_id(self, id: UUID | str) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id: Primary key value

        Returns:
            True if exists, False otherwise
        """
        obj = await self.get_by_id(id)
        return obj is not None

    # ============= Advanced Querying =============

    async def get_with_custom_query(
        self, query: Any
    ) -> list[ModelType]:
        """
        Execute custom select query.

        Args:
            query: SQLAlchemy select query

        Returns:
            List of model instances
        """
        result = await self.db.execute(query)
        return result.scalars().all()

    async def execute_scalar(self, query: Any) -> Any:
        """
        Execute query and return single scalar result.

        Args:
            query: SQLAlchemy query

        Returns:
            Scalar result
        """
        result = await self.db.execute(query)
        return result.scalar()

    async def execute_scalars(self, query: Any) -> Sequence[ModelType]:
        """
        Execute query and return all scalar results.

        Args:
            query: SQLAlchemy query

        Returns:
            Sequence of results
        """
        result = await self.db.execute(query)
        return result.scalars().all()
