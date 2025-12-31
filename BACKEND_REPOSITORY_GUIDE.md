# Backend Repository Guide
## SESSION 8 BURN: Data Access Layer Best Practices

**Generated:** 2025-12-31
**Based On:** SESSION_1_BACKEND/backend-repository-patterns.md
**Status:** IMPLEMENTATION GUIDE

---

## Executive Summary

**Critical Finding:** Repository layer uses **synchronous-only SQLAlchemy**, blocking async FastAPI routes.

| Pattern | Status | Risk | Action |
|---------|--------|------|--------|
| Async Support | ❌ Sync only | CRITICAL | Migrate to AsyncSession |
| N+1 Prevention | ⚠️ Inconsistent | HIGH | Standardize eager loading |
| Transaction Management | ⚠️ Mixed | MEDIUM | Implement Unit of Work |
| Error Handling | ❌ None | MEDIUM | Add repository exceptions |
| Pagination | ✅ Good | LOW | Maintain current approach |

---

## SECTION 1: ASYNC MIGRATION STRATEGY

### Current Problem

```python
# CURRENT (Synchronous - blocks event loop)
from sqlalchemy.orm import Session

class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID) -> Assignment | None:
        return self.db.query(Assignment).filter(...).first()
        # ↑ This blocks FastAPI async routes!
```

### Migration Approach

**Phase 1 (Immediate):** Add AsyncBaseRepository alongside existing sync

```python
# backend/app/repositories/async_base.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Generic, TypeVar

ModelType = TypeVar('ModelType')

class AsyncBaseRepository(Generic[ModelType]):
    """Async repository for FastAPI 3.1+."""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Fetch by primary key."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int | None = None, offset: int | None = None):
        """Fetch all records with optional pagination."""
        stmt = select(self.model)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        """Create new record."""
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(self, db_obj: ModelType, **kwargs) -> ModelType:
        """Update existing record."""
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        await self.db.flush()
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """Delete record."""
        await self.db.delete(db_obj)
        await self.db.flush()

    async def commit(self) -> None:
        """Commit transaction."""
        await self.db.commit()

    async def refresh(self, db_obj: ModelType) -> ModelType:
        """Refresh object from database."""
        await self.db.refresh(db_obj)
        return db_obj

    async def count(self) -> int:
        """Count total records."""
        stmt = select(func.count(self.model.id))
        result = await self.db.execute(stmt)
        return result.scalar()
```

### Phase 2 (Week 2): Create Async Variants of Critical Repos

```python
# backend/app/repositories/async_assignment.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

class AsyncAssignmentRepository(AsyncBaseRepository[Assignment]):
    """Async assignment repository with eager loading."""

    def __init__(self, db: AsyncSession):
        super().__init__(Assignment, db)

    async def get_by_id_with_relations(self, id: UUID) -> Assignment | None:
        """Get assignment with eager-loaded relationships."""
        stmt = (
            select(Assignment)
            .options(
                selectinload(Assignment.block),
                selectinload(Assignment.person),
                selectinload(Assignment.rotation_template),
            )
            .where(Assignment.id == id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_with_filters(
        self,
        person_id: UUID | None = None,
        block_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[Assignment], int]:
        """List assignments with filters and pagination."""
        stmt = select(Assignment).options(
            selectinload(Assignment.block),
            selectinload(Assignment.person),
        )

        # Apply filters
        if person_id:
            stmt = stmt.where(Assignment.person_id == person_id)
        if block_id:
            stmt = stmt.where(Assignment.block_id == block_id)
        if start_date:
            stmt = stmt.where(Block.date >= start_date)
        if end_date:
            stmt = stmt.where(Block.date <= end_date)

        # Count total
        count_stmt = select(func.count(Assignment.id)).select_from(stmt.froms)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Apply pagination
        stmt = stmt.order_by(Assignment.created_at.desc())
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        assignments = result.unique().scalars().all()

        return assignments, total
```

### Phase 3 (Week 3): Update Database Session

```python
# backend/app/db/session.py (UPDATED)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

# Keep synchronous engine for backward compatibility
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_POOL_MAX_OVERFLOW,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Add async engine
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,  # postgresql+asyncpg://...
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_POOL_MAX_OVERFLOW,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync dependency (existing)
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Async dependency (new)
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## SECTION 2: EAGER LOADING PATTERNS

### Problem: N+1 Queries

```python
# ANTI-PATTERN (N+1 Query Risk)
assignments = repo.list_residents()  # Query 1: Load all residents
for assignment in assignments:
    print(assignment.person.name)  # Query 2..N: Load person for each assignment
```

### Solution: Eager Loading

```python
# PATTERN 1: joinedload (Single Query with Join)
from sqlalchemy.orm import joinedload

def get_with_relations(self, id: UUID) -> Assignment | None:
    """Single query, eager loads related objects."""
    return (
        self.db.query(Assignment)
        .options(joinedload(Assignment.person))
        .filter(Assignment.id == id)
        .first()
    )

# PATTERN 2: selectinload (Multiple Queries but Efficient)
from sqlalchemy.orm import selectinload

def list_with_relations(self) -> list[Assignment]:
    """Efficient multi-query pattern."""
    return (
        self.db.query(Assignment)
        .options(
            selectinload(Assignment.person),
            selectinload(Assignment.block),
            selectinload(Assignment.rotation_template),
        )
        .all()
    )

# PATTERN 3: Nested eager loading
def get_with_deep_relations(self, id: UUID) -> Person | None:
    """Load person with all assignments and their blocks."""
    return (
        self.db.query(Person)
        .options(
            selectinload(Person.assignments).selectinload(Assignment.block),
            selectinload(Person.absences),
        )
        .filter(Person.id == id)
        .first()
    )
```

### Standardization Rule

**Create `_with_relations()` variant for every repository method accessing relationships:**

```python
class PersonRepository(BaseRepository[Person]):
    def get_by_id(self, id: UUID) -> Person | None:
        """Basic get - no eager loading."""
        return self.db.query(Person).filter(Person.id == id).first()

    def get_by_id_with_relations(self, id: UUID) -> Person | None:
        """Get with all relationships eagerly loaded."""
        return (
            self.db.query(Person)
            .options(
                selectinload(Person.assignments),
                selectinload(Person.absences),
                selectinload(Person.certifications),
            )
            .filter(Person.id == id)
            .first()
        )

    def list_residents(self) -> list[Person]:
        """Basic list - no eager loading."""
        return (
            self.db.query(Person)
            .filter(Person.type == "resident")
            .order_by(Person.name)
            .all()
        )

    def list_residents_with_assignments(self) -> list[Person]:
        """List residents with assignments eager loaded."""
        return (
            self.db.query(Person)
            .options(selectinload(Person.assignments))
            .filter(Person.type == "resident")
            .order_by(Person.name)
            .all()
        )
```

---

## SECTION 3: TRANSACTION MANAGEMENT STANDARDIZATION

### Problem: Inconsistent Commit Patterns

```python
# ANTI-PATTERN 1: Repository commits (incorrect)
class SwapRepository:
    def create(self, **kwargs):
        swap = SwapRecord(**kwargs)
        self.db.add(swap)
        self.db.commit()  # ← Repository shouldn't commit!
        return swap

# ANTI-PATTERN 2: Implicit commits (unclear)
class AssignmentService:
    def create_assignment(self, ...):
        assignment = self.assignment_repo.create(...)
        # When does transaction commit? Unclear!
```

### Solution: Unit of Work Pattern

```python
# backend/app/repositories/unit_of_work.py
from contextlib import asynccontextmanager

class UnitOfWork:
    """Manages transaction scope across multiple repositories."""

    def __init__(self, db: Session):
        self.db = db
        self._repositories: dict = {}

    @property
    def assignment(self) -> AssignmentRepository:
        if not self._repositories.get("assignment"):
            self._repositories["assignment"] = AssignmentRepository(self.db)
        return self._repositories["assignment"]

    @property
    def person(self) -> PersonRepository:
        if not self._repositories.get("person"):
            self._repositories["person"] = PersonRepository(self.db)
        return self._repositories["person"]

    @property
    def block(self) -> BlockRepository:
        if not self._repositories.get("block"):
            self._repositories["block"] = BlockRepository(self.db)
        return self._repositories["block"]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.db.commit()
        else:
            self.db.rollback()

    @asynccontextmanager
    async def async_context(self):
        """Async context manager variant."""
        try:
            yield self
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise


# Usage in services
class AssignmentService:
    def __init__(self, db: Session):
        self.uow = UnitOfWork(db)

    def create_assignment_with_cascade(self, ...):
        """Create assignment and update related records atomically."""
        with self.uow as uow:
            # All operations in this block are in same transaction
            assignment = uow.assignment.create(...)
            uow.person.update(person_obj, updated_at=now())
            uow.block.update(block_obj, last_modified=now())

            # Automatically commits on exit, rolls back on exception
```

---

## SECTION 4: ASYNC QUERY BEST PRACTICES

### Using SQLAlchemy 2.0 select() Style

```python
# backend/app/repositories/async_query_examples.py
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

# PATTERN 1: Simple filter
async def get_assignments_for_date(self, date: date):
    stmt = select(Assignment).where(Assignment.block_id == Block.id, Block.date == date)
    result = await self.db.execute(stmt)
    return result.scalars().all()

# PATTERN 2: OR conditions
async def find_by_email_or_id(self, email: str, person_id: UUID):
    stmt = select(Person).where(
        or_(Person.email == email, Person.id == person_id)
    )
    result = await self.db.execute(stmt)
    return result.scalar_one_or_none()

# PATTERN 3: IN clause
async def get_multiple(self, ids: list[UUID]):
    stmt = select(Assignment).where(Assignment.id.in_(ids))
    result = await self.db.execute(stmt)
    return result.scalars().all()

# PATTERN 4: Pagination
async def list_paginated(
    self,
    page: int = 1,
    page_size: int = 50,
    order_by=None,
):
    stmt = select(self.model)
    if order_by:
        stmt = stmt.order_by(order_by)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await self.db.execute(stmt)
    return result.scalars().all()

# PATTERN 5: Count
async def count_filtered(self, **filters):
    stmt = select(func.count(self.model.id))
    for key, value in filters.items():
        stmt = stmt.where(getattr(self.model, key) == value)
    result = await self.db.execute(stmt)
    return result.scalar()

# PATTERN 6: Aggregation
async def get_hours_summary(self, person_id: UUID):
    stmt = (
        select(
            func.sum(Assignment.hours).label("total_hours"),
            func.count(Assignment.id).label("assignment_count"),
        )
        .where(Assignment.person_id == person_id)
        .group_by(Assignment.person_id)
    )
    result = await self.db.execute(stmt)
    row = result.first()
    return {"total_hours": row.total_hours, "count": row.assignment_count}
```

---

## SECTION 5: REPOSITORY TESTING GUIDE

### Unit Testing with Mocks

```python
# backend/tests/repositories/test_assignment_repository.py
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_db():
    """Mock async session."""
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_by_id(mock_db):
    """Test get_by_id with mocked database."""
    from app.repositories.async_assignment import AsyncAssignmentRepository

    repo = AsyncAssignmentRepository(mock_db)

    # Mock the query execution
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = SAMPLE_ASSIGNMENT
    mock_db.execute.return_value = mock_result

    result = await repo.get_by_id(SAMPLE_ASSIGNMENT.id)

    assert result == SAMPLE_ASSIGNMENT
    mock_db.execute.assert_called_once()
```

### Integration Testing with Test Database

```python
# backend/tests/repositories/test_assignment_integration.py
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest_asyncio.fixture
async def test_db():
    """Create test database for integration tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_list_with_filters_integration(test_db):
    """Integration test with real async database."""
    repo = AsyncAssignmentRepository(test_db)

    # Create test data
    assignment = await repo.create(
        person_id=PERSON_ID,
        block_id=BLOCK_ID,
        rotation_template_id=ROTATION_ID,
    )
    await repo.commit()

    # Test filtering
    result, total = await repo.list_with_filters(person_id=PERSON_ID)

    assert len(result) == 1
    assert result[0].id == assignment.id
    assert total == 1
```

---

## SECTION 6: REPOSITORY ERROR HANDLING

### Add Repository-Specific Exceptions

```python
# backend/app/repositories/exceptions.py

class RepositoryError(Exception):
    """Base repository exception."""
    pass

class RecordNotFoundError(RepositoryError):
    """Record not found in database."""
    def __init__(self, model_name: str, id: Any):
        self.model_name = model_name
        self.id = id
        super().__init__(f"{model_name} with id {id} not found")

class DuplicateRecordError(RepositoryError):
    """Duplicate record detected."""
    def __init__(self, model_name: str, field: str, value: Any):
        self.model_name = model_name
        self.field = field
        self.value = value
        super().__init__(f"Duplicate {model_name} with {field}={value}")

class DatabaseError(RepositoryError):
    """Database operation failed."""
    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Database operation '{operation}' failed: {reason}")
```

### Use Exceptions in Repositories

```python
# backend/app/repositories/async_assignment.py

async def get_or_raise(self, id: UUID) -> Assignment:
    """Get assignment or raise exception."""
    assignment = await self.get_by_id(id)
    if not assignment:
        raise RecordNotFoundError("Assignment", id)
    return assignment

async def get_by_block_and_person(
    self,
    block_id: UUID,
    person_id: UUID,
) -> Assignment | None:
    """Get existing assignment (returns None if not found)."""
    stmt = (
        select(Assignment)
        .where(
            and_(
                Assignment.block_id == block_id,
                Assignment.person_id == person_id,
            )
        )
    )
    result = await self.db.execute(stmt)
    return result.scalar_one_or_none()
```

---

## SECTION 7: PAGINATION BEST PRACTICES

### Cursor-Based Pagination (Recommended for Large Data Sets)

```python
async def list_with_cursor(
    self,
    cursor: str | None = None,
    limit: int = 50,
) -> tuple[list[Assignment], str | None]:
    """Cursor-based pagination for stable ordering."""
    stmt = select(Assignment).order_by(Assignment.created_at.desc(), Assignment.id.desc())

    if cursor:
        # Decode cursor to get last_created_at and last_id
        last_created_at, last_id = decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                Assignment.created_at < last_created_at,
                and_(
                    Assignment.created_at == last_created_at,
                    Assignment.id < last_id,
                ),
            )
        )

    result = await self.db.execute(stmt.limit(limit + 1))
    items = result.scalars().all()

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        next_cursor = encode_cursor(last_item.created_at, last_item.id)

    return items, next_cursor
```

### Offset-Based Pagination (Simple, Current Standard)

```python
async def list_paginated(
    self,
    page: int = 1,
    page_size: int = 50,
    **filters,
) -> tuple[list[Assignment], int]:
    """Offset-based pagination."""
    stmt = select(Assignment)

    # Apply filters
    for key, value in filters.items():
        stmt = stmt.where(getattr(Assignment, key) == value)

    # Count total
    count_result = await self.db.execute(
        select(func.count(Assignment.id)).select_from(stmt.froms)
    )
    total = count_result.scalar()

    # Paginate
    stmt = (
        stmt.order_by(Assignment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await self.db.execute(stmt)
    items = result.scalars().all()

    return items, total
```

---

## SECTION 8: BULK OPERATIONS

### Bulk Insert

```python
async def bulk_create(self, objects: list[dict]) -> list[ModelType]:
    """Efficiently create multiple records."""
    db_objs = [self.model(**obj) for obj in objects]
    self.db.add_all(db_objs)
    await self.db.flush()
    return db_objs
```

### Bulk Update

```python
async def bulk_update(self, updates: list[tuple[UUID, dict]]) -> int:
    """Efficiently update multiple records."""
    count = 0
    for obj_id, update_dict in updates:
        stmt = (
            update(self.model)
            .where(self.model.id == obj_id)
            .values(**update_dict)
        )
        result = await self.db.execute(stmt)
        count += result.rowcount
    return count
```

### Bulk Delete

```python
async def bulk_delete(self, ids: list[UUID]) -> int:
    """Efficiently delete multiple records."""
    stmt = delete(self.model).where(self.model.id.in_(ids))
    result = await self.db.execute(stmt)
    return result.rowcount
```

---

## SECTION 9: MIGRATION ROADMAP

### Week 1: Foundation
- [ ] Create AsyncBaseRepository
- [ ] Add AsyncSession configuration
- [ ] Add async get_db dependency

### Week 2: Critical Repos
- [ ] Create AsyncAssignmentRepository
- [ ] Create AsyncPersonRepository
- [ ] Add integration tests

### Week 3: Feature Repos
- [ ] Create AsyncSwapRepository
- [ ] Create AsyncConflictRepository
- [ ] Update services to use async repos

### Week 4: Full Migration
- [ ] Update all routes to use async
- [ ] Deprecate sync repositories
- [ ] Remove sync code (after stabilization)

---

## SECTION 10: CHECKLIST FOR NEW REPOSITORIES

When creating a new repository:

- [ ] Inherit from `AsyncBaseRepository[ModelType]`
- [ ] Implement `__init__(self, db: AsyncSession)`
- [ ] Add `get_by_id()` method (no relations)
- [ ] Add `get_by_id_with_relations()` method (eager loaded)
- [ ] Add `list_all()` or domain-specific list method
- [ ] Use `selectinload()` for relationships
- [ ] Write unit tests with mocks
- [ ] Write integration tests with test database
- [ ] Document query patterns with docstrings
- [ ] Add error handling for RecordNotFoundError
- [ ] Test pagination with multiple pages

---

*Generated by SESSION 8 BURN - Backend Improvements*
*Reference: SESSION_1_BACKEND/backend-repository-patterns.md*
