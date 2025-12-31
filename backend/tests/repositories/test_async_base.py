"""
Tests for async repository base class.

Covers:
- CRUD operations
- Pagination
- Filtering and sorting
- Eager loading
- Bulk operations
- Transaction management
"""

import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.repositories.async_base import (
    AsyncBaseRepository,
    PaginationParams,
    PaginatedResponse,
)


# ============= Test Models =============


class TestModelSchema(BaseModel):
    """Pydantic schema for test model."""

    name: str
    description: str = ""
    count: int = 0

    class Config:
        from_attributes = True


class TestModel(Base):
    """Simple test model."""

    __tablename__ = "test_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TestModel(id={self.id}, name={self.name})>"


# ============= Fixtures =============


@pytest.fixture
async def db_session():
    """Create in-memory async test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def repository(db_session):
    """Create repository instance."""
    return AsyncBaseRepository(TestModel, db_session)


# ============= CRUD Tests =============


class TestAsyncBaseRepositoryCRUD:
    """Test CRUD operations."""

    async def test_create(self, repository: AsyncBaseRepository):
        """Test creating an entity."""
        schema = TestModelSchema(name="Test", description="Test description")
        obj = await repository.create(schema)

        assert obj.id is not None
        assert obj.name == "Test"
        assert obj.description == "Test description"

    async def test_get_by_id(self, repository, db_session):
        """Test retrieving entity by ID."""
        schema = TestModelSchema(name="Get Test")
        obj = await repository.create(schema)
        await repository.commit()

        retrieved = await repository.get_by_id(obj.id)
        assert retrieved is not None
        assert retrieved.name == "Get Test"

    async def test_get_by_id_not_found(self, repository):
        """Test get_by_id with non-existent ID."""
        fake_id = str(uuid4())
        result = await repository.get_by_id(fake_id)
        assert result is None

    async def test_get_all(self, repository):
        """Test retrieving all entities."""
        objs = []
        for i in range(5):
            schema = TestModelSchema(name=f"Test {i}")
            obj = await repository.create(schema)
            objs.append(obj)
        await repository.commit()

        all_objs = await repository.get_all()
        assert len(all_objs) == 5

    async def test_update(self, repository):
        """Test updating an entity."""
        schema = TestModelSchema(name="Original")
        obj = await repository.create(schema)
        await repository.commit()

        update_schema = TestModelSchema(name="Updated", description="Updated desc")
        updated = await repository.update(obj, update_schema)
        await repository.commit()

        retrieved = await repository.get_by_id(updated.id)
        assert retrieved.name == "Updated"
        assert retrieved.description == "Updated desc"

    async def test_delete(self, repository):
        """Test deleting an entity."""
        schema = TestModelSchema(name="To Delete")
        obj = await repository.create(schema)
        await repository.commit()

        await repository.delete(obj)
        await repository.commit()

        retrieved = await repository.get_by_id(obj.id)
        assert retrieved is None

    async def test_delete_by_id(self, repository):
        """Test deleting by ID."""
        schema = TestModelSchema(name="Delete by ID")
        obj = await repository.create(schema)
        await repository.commit()

        result = await repository.delete_by_id(obj.id)
        await repository.commit()

        assert result is True
        retrieved = await repository.get_by_id(obj.id)
        assert retrieved is None

    async def test_delete_by_id_not_found(self, repository):
        """Test delete_by_id with non-existent ID."""
        fake_id = str(uuid4())
        result = await repository.delete_by_id(fake_id)
        assert result is False


# ============= Pagination Tests =============


class TestAsyncRepositoryPagination:
    """Test pagination operations."""

    async def test_pagination_params(self):
        """Test pagination parameter initialization."""
        params = PaginationParams(skip=10, limit=50)
        assert params.skip == 10
        assert params.limit == 50
        assert params.offset() == 10
        assert params.count() == 50

    async def test_pagination_params_limits(self):
        """Test pagination parameter bounds."""
        params = PaginationParams(skip=-5, limit=2000)
        assert params.skip == 0
        assert params.limit == 1000  # Capped at 1000

    async def test_get_paginated(self, repository):
        """Test paginated retrieval."""
        for i in range(25):
            schema = TestModelSchema(name=f"Item {i}")
            await repository.create(schema)
        await repository.commit()

        pagination = PaginationParams(skip=0, limit=10)
        result = await repository.get_paginated(pagination)

        assert len(result.data) == 10
        assert result.total == 25
        assert result.pages == 3
        assert result.skip == 0
        assert result.limit == 10

    async def test_get_paginated_with_sorting(self, repository):
        """Test paginated retrieval with sorting."""
        for i in range(5, 0, -1):
            schema = TestModelSchema(name=f"Item {i}", count=i)
            await repository.create(schema)
        await repository.commit()

        pagination = PaginationParams(skip=0, limit=10)
        result = await repository.get_paginated(
            pagination,
            order_by="count",
        )

        names = [item.name for item in result.data]
        assert names == ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]

    async def test_get_paginated_descending_sort(self, repository):
        """Test paginated retrieval with descending sort."""
        for i in range(1, 6):
            schema = TestModelSchema(name=f"Item {i}", count=i)
            await repository.create(schema)
        await repository.commit()

        pagination = PaginationParams(skip=0, limit=10)
        result = await repository.get_paginated(
            pagination,
            order_by="-count",
        )

        counts = [item.count for item in result.data]
        assert counts == [5, 4, 3, 2, 1]


# ============= Filtering Tests =============


class TestAsyncRepositoryFiltering:
    """Test filtering operations."""

    async def test_get_by_filters(self, repository):
        """Test retrieving entities by filters."""
        for i in range(5):
            schema = TestModelSchema(name="Test", count=i)
            await repository.create(schema)
        await repository.commit()

        results = await repository.get_by_filters({"name": "Test"})
        assert len(results) == 5

    async def test_get_by_filters_multiple(self, repository):
        """Test retrieving with multiple filters."""
        for i in range(3):
            schema = TestModelSchema(name="Test", count=10)
            await repository.create(schema)
        for i in range(2):
            schema = TestModelSchema(name="Other", count=10)
            await repository.create(schema)
        await repository.commit()

        results = await repository.get_by_filters({"name": "Test", "count": 10})
        assert len(results) == 3

    async def test_get_first_by_filters(self, repository):
        """Test retrieving first entity by filters."""
        for i in range(3):
            schema = TestModelSchema(name="Test", count=i)
            await repository.create(schema)
        await repository.commit()

        result = await repository.get_first_by_filters({"name": "Test"})
        assert result is not None
        assert result.name == "Test"

    async def test_get_first_by_filters_not_found(self, repository):
        """Test get_first_by_filters with no matches."""
        schema = TestModelSchema(name="Test")
        await repository.create(schema)
        await repository.commit()

        result = await repository.get_first_by_filters({"name": "NotFound"})
        assert result is None


# ============= Counting Tests =============


class TestAsyncRepositoryCounting:
    """Test counting operations."""

    async def test_count_all(self, repository):
        """Test counting all entities."""
        for i in range(5):
            schema = TestModelSchema(name=f"Test {i}")
            await repository.create(schema)
        await repository.commit()

        count = await repository.count()
        assert count == 5

    async def test_count_with_filters(self, repository):
        """Test counting with filters."""
        for i in range(3):
            schema = TestModelSchema(name="Test", count=10)
            await repository.create(schema)
        for i in range(2):
            schema = TestModelSchema(name="Other", count=20)
            await repository.create(schema)
        await repository.commit()

        count = await repository.count({"name": "Test"})
        assert count == 3

    async def test_exists(self, repository):
        """Test existence check."""
        schema = TestModelSchema(name="Exists")
        await repository.create(schema)
        await repository.commit()

        exists = await repository.exists({"name": "Exists"})
        assert exists is True

    async def test_exists_not_found(self, repository):
        """Test existence check when not found."""
        exists = await repository.exists({"name": "NotFound"})
        assert exists is False

    async def test_exists_by_id(self, repository):
        """Test existence check by ID."""
        schema = TestModelSchema(name="Test")
        obj = await repository.create(schema)
        await repository.commit()

        exists = await repository.exists_by_id(obj.id)
        assert exists is True

    async def test_exists_by_id_not_found(self, repository):
        """Test exists_by_id when not found."""
        fake_id = str(uuid4())
        exists = await repository.exists_by_id(fake_id)
        assert exists is False


# ============= Bulk Operations Tests =============


class TestAsyncRepositoryBulkOps:
    """Test bulk operations."""

    async def test_bulk_create(self, repository):
        """Test creating multiple entities."""
        schemas = [TestModelSchema(name=f"Bulk {i}") for i in range(5)]
        objs = await repository.bulk_create(schemas)
        await repository.commit()

        assert len(objs) == 5
        all_objs = await repository.get_all()
        assert len(all_objs) == 5

    async def test_bulk_update(self, repository):
        """Test updating multiple entities."""
        # Create initial objects
        schemas = [TestModelSchema(name=f"Item {i}") for i in range(3)]
        objs = await repository.bulk_create(schemas)
        await repository.commit()

        # Update objects
        for obj in objs:
            obj.count = 100
        updated = await repository.bulk_update(objs)
        await repository.commit()

        all_objs = await repository.get_all()
        assert all(obj.count == 100 for obj in all_objs)

    async def test_bulk_delete(self, repository):
        """Test deleting multiple entities."""
        schemas = [TestModelSchema(name=f"Delete {i}") for i in range(5)]
        objs = await repository.bulk_create(schemas)
        await repository.commit()

        ids = [obj.id for obj in objs]
        deleted_count = await repository.bulk_delete(ids)
        await repository.commit()

        assert deleted_count == 5
        all_objs = await repository.get_all()
        assert len(all_objs) == 0


# ============= Transaction Management Tests =============


class TestAsyncRepositoryTransactions:
    """Test transaction management."""

    async def test_commit(self, repository):
        """Test explicit commit."""
        schema = TestModelSchema(name="Commit Test")
        obj = await repository.create(schema)
        await repository.commit()

        retrieved = await repository.get_by_id(obj.id)
        assert retrieved is not None

    async def test_rollback(self, repository):
        """Test rollback."""
        schema = TestModelSchema(name="Rollback Test")
        obj = await repository.create(schema)
        await repository.rollback()

        retrieved = await repository.get_by_id(obj.id)
        assert retrieved is None

    async def test_refresh(self, repository):
        """Test refreshing entity from database."""
        schema = TestModelSchema(name="Refresh Test")
        obj = await repository.create(schema)
        await repository.commit()

        obj.name = "Modified"
        refreshed = await repository.refresh(obj)
        assert refreshed.name == "Refresh Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
