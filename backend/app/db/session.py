"""Database session management.

Connection Pooling Strategy
---------------------------
This module configures SQLAlchemy's connection pool for optimal performance
and reliability. See docs/ARCHITECTURE.md for detailed documentation.

Pool settings are configurable via environment variables:
- DB_POOL_SIZE: Base number of connections (default: 10)
- DB_POOL_MAX_OVERFLOW: Additional connections allowed (default: 20)
- DB_POOL_TIMEOUT: Wait time for connection (default: 30s)
- DB_POOL_RECYCLE: Connection lifetime (default: 1800s)
- DB_POOL_PRE_PING: Verify connections (default: True)
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

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


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
