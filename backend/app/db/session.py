"""Database session management.

Connection Pooling Strategy
---------------------------
This module configures SQLAlchemy's connection pool for optimal performance
and reliability. See ARCHITECTURE.md for detailed documentation.

Pool settings are configurable via environment variables:
- DB_POOL_SIZE: Base number of connections (default: 10)
- DB_POOL_MAX_OVERFLOW: Additional connections allowed (default: 20)
- DB_POOL_TIMEOUT: Wait time for connection (default: 30s)
- DB_POOL_RECYCLE: Connection lifetime (default: 1800s)
- DB_POOL_PRE_PING: Verify connections (default: True)
"""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Synchronous engine (legacy support)
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # Verify connection validity
    pool_size=settings.DB_POOL_SIZE,  # Base pool size
    max_overflow=settings.DB_POOL_MAX_OVERFLOW,  # Allow burst connections
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Wait for connection
    pool_recycle=settings.DB_POOL_RECYCLE,  # Prevent stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine (preferred for all new code)
async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    # Connection pool settings
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_POOL_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session dependency for FastAPI routes (DEPRECATED - use get_async_db).

    Provides a transactional session that:
    - Rolls back uncommitted changes on exception (prevents dirty state)
    - Always closes the connection (prevents connection leaks)

    Routes should call db.commit() explicitly when they want to persist changes.

    Note: This follows the same pattern as task_session_scope() but without
    auto-commit, since FastAPI routes handle commits explicitly.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()  # Clean up dirty state on exception
        raise
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session dependency for FastAPI routes (PREFERRED).

    Provides a transactional async session that:
    - Rolls back uncommitted changes on exception (prevents dirty state)
    - Always closes the connection (prevents connection leaks)
    - Supports concurrent request handling with proper transaction isolation

    Routes should call await db.commit() explicitly when they want to persist changes.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def task_session_scope():
    """
    Provide a transactional scope for Celery tasks.

    Usage:
        @celery_app.task
        def my_task():
            with task_session_scope() as session:
                # Do database work
                session.query(...)
                # Auto-commits on success, rollback on error

    This ensures:
    - Session is always closed (no connection leaks)
    - Transaction is rolled back on exceptions
    - Explicit commit on success
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def async_task_session_scope():
    """Async version of task_session_scope for async tasks."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Alias for backwards compatibility
get_async_session_context = async_task_session_scope
async_session = async_task_session_scope
