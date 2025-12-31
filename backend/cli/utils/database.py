"""
Database utilities for CLI.

Provides direct database access for CLI commands.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from cli.config import get_config


class DatabaseManager:
    """Manage database connections for CLI."""

    def __init__(self):
        """Initialize database manager."""
        config = get_config()
        self.engine = create_async_engine(
            config.database_url,
            echo=config.verbose,
        )
        self.SessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session.

        Yields:
            AsyncSession instance
        """
        async with self.SessionLocal() as session:
            yield session

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()


# Global database manager instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
