# N+1 Query Optimization Guide

This document describes the N+1 query optimization patterns implemented in the Residency Scheduler backend services.

## Overview

The N+1 query problem occurs when code executes N additional queries to fetch related data for N records returned by an initial query. This causes significant performance degradation as the dataset grows.

### Example of N+1 Problem

```python
# BAD: N+1 queries
persons = await db.execute(select(Person))  # 1 query
for person in persons.scalars():
    assignments = await db.execute(         # N queries
        select(Assignment).where(Assignment.person_id == person.id)
    )
```

**Result:** 51 queries for 50 people

### Solution: Eager Loading

```python
# GOOD: 1-2 queries with eager loading
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Person).options(
        selectinload(Person.assignments)
    )
)
persons = result.scalars().all()
```

**Result:** 2 queries regardless of record count

---

## SQLAlchemy Loading Strategies

### `selectinload()`

Best for one-to-many relationships. Executes a second query with an IN clause.

```python
select(Person).options(
    selectinload(Person.assignments)
)
# Query 1: SELECT * FROM persons
# Query 2: SELECT * FROM assignments WHERE person_id IN (1, 2, 3, ...)
```

### `joinedload()`

Best for many-to-one or one-to-one relationships. Uses a JOIN in a single query.

```python
select(Assignment).options(
    joinedload(Assignment.person)
)
# Query: SELECT * FROM assignments JOIN persons ON ...
```

### `contains_eager()`

Used when you've already written a JOIN and want to populate the relationship.

```python
select(Person).join(Person.assignments).options(
    contains_eager(Person.assignments)
)
```

---

## Optimized Services

### 1. `assignment_service.py`

**Method:** `get_assignment()`
```python
async def get_assignment(db: AsyncSession, assignment_id: str) -> Optional[Assignment]:
    result = await db.execute(
        select(Assignment)
        .options(
            selectinload(Assignment.person),
            selectinload(Assignment.block),
            selectinload(Assignment.rotation_template)
        )
        .where(Assignment.id == assignment_id)
    )
    return result.scalar_one_or_none()
```

### 2. `person_service.py`

**New Method:** `get_person_with_assignments()`
```python
async def get_person_with_assignments(
    db: AsyncSession,
    person_id: str,
    include_blocks: bool = True
) -> Optional[Person]:
    query = select(Person).options(
        selectinload(Person.assignments)
    ).where(Person.id == person_id)

    if include_blocks:
        query = query.options(
            selectinload(Person.assignments).selectinload(Assignment.block)
        )

    result = await db.execute(query)
    return result.scalar_one_or_none()
```

**Enhanced Method:** `list_people()`
```python
async def list_people(
    db: AsyncSession,
    include_assignments: bool = False,  # NEW parameter
    ...
) -> list[Person]:
    query = select(Person)

    if include_assignments:
        query = query.options(
            selectinload(Person.assignments).selectinload(Assignment.block),
            selectinload(Person.assignments).selectinload(Assignment.rotation_template)
        )

    result = await db.execute(query)
    return list(result.scalars().all())
```

### 3. `block_service.py`

**New Method:** `get_block_with_assignments()`
```python
async def get_block_with_assignments(
    db: AsyncSession,
    block_id: str
) -> Optional[Block]:
    result = await db.execute(
        select(Block)
        .options(
            selectinload(Block.assignments).selectinload(Assignment.person),
            selectinload(Block.assignments).selectinload(Assignment.rotation_template)
        )
        .where(Block.id == block_id)
    )
    return result.scalar_one_or_none()
```

### 4. `swap_request_service.py`

**7 Methods Optimized:**
- `create_swap_request()`
- `get_swap_request()`
- `list_swap_requests()`
- `get_pending_swaps_for_faculty()`
- `get_swap_history()`
- `approve_swap_request()`
- `reject_swap_request()`

**Example:**
```python
async def list_swap_requests(
    db: AsyncSession,
    status: Optional[SwapStatus] = None
) -> list[SwapRequest]:
    query = select(SwapRequest).options(
        joinedload(SwapRequest.requester),
        joinedload(SwapRequest.target_faculty),
        joinedload(SwapRequest.source_assignment),
        joinedload(SwapRequest.target_assignment)
    )

    if status:
        query = query.where(SwapRequest.status == status)

    result = await db.execute(query)
    return list(result.unique().scalars().all())
```

### 5. `swap_executor.py`

**Method:** `_update_schedule_assignments()`
```python
async def _update_schedule_assignments(
    self,
    db: AsyncSession,
    assignment_ids: list[str]
) -> None:
    # N+1 OPTIMIZATION: Batch load all assignments in one query
    result = await db.execute(
        select(Assignment)
        .options(
            selectinload(Assignment.person),
            selectinload(Assignment.block)
        )
        .where(Assignment.id.in_(assignment_ids))
    )
    assignments = result.scalars().all()
```

---

## Performance Impact

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| List 50 people with 10 assignments each | 551 queries | 3-4 queries | **99%** |
| List 100 swap requests | 401 queries | 3 queries | **99%** |
| Update 14 assignments in swap | 15 queries | 2 queries | **87%** |
| Get person with full details | 12 queries | 2 queries | **83%** |

---

## Best Practices

### 1. Opt-in Loading

Add optional parameters to control eager loading:

```python
async def list_items(
    db: AsyncSession,
    include_related: bool = False  # Default to lazy loading
) -> list[Item]:
    query = select(Item)
    if include_related:
        query = query.options(selectinload(Item.related))
    return list((await db.execute(query)).scalars().all())
```

### 2. Chained Loading for Deep Relationships

```python
select(Person).options(
    selectinload(Person.assignments)
        .selectinload(Assignment.block)
        .selectinload(Block.rotations)
)
```

### 3. Use `.unique()` with `joinedload()`

When using `joinedload()` on collections, use `.unique()` to deduplicate:

```python
result = await db.execute(query)
return list(result.unique().scalars().all())
```

### 4. Profile Before Optimizing

Enable SQL logging to identify N+1 patterns:

```python
# In development
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## Testing

Run the service tests to verify optimizations:

```bash
cd backend
pytest tests/services/test_person_service.py -v
pytest tests/services/test_assignment_service.py -v
pytest tests/services/test_swap_request_service.py -v
```

---

## References

- [SQLAlchemy Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [Avoiding N+1 Queries](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#what-kind-of-loading-to-use)
