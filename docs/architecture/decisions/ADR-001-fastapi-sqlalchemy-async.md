# ADR-001: FastAPI + SQLAlchemy 2.0 (Async)

**Date:** 2024-12
**Status:** Adopted

## Context

The Residency Scheduler requires a backend framework that supports:
- Real-time responsiveness for interactive schedule editing
- Computationally expensive ACGME compliance checks
- Concurrent users modifying schedules simultaneously
- Type safety for complex domain models
- Auto-generated API documentation for frontend integration

Traditional synchronous web frameworks would create bottlenecks during database operations and compliance calculations.

## Decision

Use **FastAPI** with **SQLAlchemy 2.0** async support:
- FastAPI as the web framework (async/await throughout)
- SQLAlchemy 2.0+ with `AsyncSession` for database operations
- PostgreSQL as the primary database
- Pydantic v2 for request/response validation

## Consequences

### Positive
- **High concurrency handling**: Non-blocking I/O enables many concurrent requests
- **Type hints + Pydantic validation**: Compile-time and runtime type safety
- **OpenAPI docs auto-generated**: Reduces documentation burden, enables frontend code generation
- **Modern Python idioms**: async/await is the standard for I/O-bound operations
- **Performance**: Among the fastest Python web frameworks

### Negative
- **All code must be async**: Cannot mix sync database calls (risk of blocking event loop)
- **Learning curve**: AsyncSession patterns differ from traditional SQLAlchemy
- **Debugging complexity**: Async stack traces can be harder to follow
- **Third-party library compatibility**: Some libraries may not support async

## Implementation Notes

### Session Pattern
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db

async def get_person(db: AsyncSession, person_id: str) -> Person | None:
    result = await db.execute(
        select(Person).where(Person.id == person_id)
    )
    return result.scalar_one_or_none()
```

### Route Pattern
```python
@router.get("/people/{person_id}")
async def get_person_endpoint(
    person_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> PersonResponse:
    person = await get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return PersonResponse.from_orm(person)
```

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Async Tutorial](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- `backend/app/db/session.py` - Database session configuration
- `backend/app/api/deps.py` - Dependency injection patterns

## See Also

**Related ADRs:**
- [ADR-007: Monorepo with Docker Compose](../../.claude/dontreadme/synthesis/DECISIONS.md#adr-007-monorepo-with-docker-compose) - Container orchestration
- [ADR-010: Pytest + Jest Testing Strategy](../../.claude/dontreadme/synthesis/DECISIONS.md#adr-010-pytest--jest-testing-strategy) - Async testing patterns

**Implementation Code:**
- `backend/app/main.py` - FastAPI application initialization
- `backend/app/core/config.py` - Application configuration
- `backend/app/db/` - Database session management
- `backend/app/models/` - SQLAlchemy ORM models

**Architecture Documentation:**
- [Backend Architecture](../backend.md) - Detailed backend design
- [Database Architecture](../database.md) - Database patterns and migrations
