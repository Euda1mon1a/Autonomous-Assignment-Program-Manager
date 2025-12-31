"""Unit of Work pattern implementation for managing multiple repositories.

The Unit of Work pattern coordinates multiple repositories within a single
transaction, ensuring data consistency and simplifying transaction management.
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.async_base import AsyncBaseRepository


class UnitOfWork:
    """
    Unit of Work implementation for managing multiple repositories.

    Features:
    - Coordinates multiple repositories in a single transaction
    - Automatic rollback on failure
    - Batch commit of all changes
    - Repository registration and access
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize Unit of Work.

        Args:
            db: Async database session
        """
        self.db = db
        self._repositories: dict[str, AsyncBaseRepository] = {}
        self._transactional = False

    def register_repository(self, name: str, repository: AsyncBaseRepository) -> None:
        """
        Register a repository with the UoW.

        Args:
            name: Name to access repository by
            repository: AsyncBaseRepository instance
        """
        self._repositories[name] = repository

    def get_repository(self, name: str) -> AsyncBaseRepository | None:
        """
        Get registered repository by name.

        Args:
            name: Repository name

        Returns:
            Repository instance or None if not found
        """
        return self._repositories.get(name)

    async def __aenter__(self) -> "UnitOfWork":
        """
        Enter context manager for transaction.

        Returns:
            Self for use as context variable
        """
        self._transactional = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager, committing or rolling back as appropriate.

        Args:
            exc_type: Exception type if occurred
            exc_val: Exception value if occurred
            exc_tb: Exception traceback if occurred
        """
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        self._transactional = False

    async def commit(self) -> None:
        """
        Commit all changes from registered repositories.

        All changes made through any registered repository are committed atomically.
        """
        if self._transactional:
            await self.db.commit()

    async def rollback(self) -> None:
        """
        Rollback all changes from registered repositories.

        All changes made through any registered repository are discarded.
        """
        if self._transactional:
            await self.db.rollback()

    async def flush(self) -> None:
        """
        Flush all pending changes without committing.

        Useful for getting generated IDs before final commit.
        """
        if self._transactional:
            await self.db.flush()

    def get_session(self) -> AsyncSession:
        """
        Get underlying async session.

        Returns:
            AsyncSession instance
        """
        return self.db

    def is_transactional(self) -> bool:
        """
        Check if UoW is in transactional mode.

        Returns:
            True if in transactional context
        """
        return self._transactional
