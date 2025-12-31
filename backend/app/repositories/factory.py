"""Repository factory for creating and managing repository instances.

The factory pattern simplifies repository creation and provides centralized
configuration for all repositories in the application.
"""

from typing import Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.async_base import AsyncBaseRepository
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class RepositoryFactory(Generic[ModelType]):
    """
    Factory for creating repository instances.

    Provides:
    - Lazy creation of repositories
    - Centralized configuration
    - Repository registry
    - Type-safe repository access
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository factory.

        Args:
            db: Async database session
        """
        self.db = db
        self._registry: dict[Type, AsyncBaseRepository] = {}
        self._custom_repositories: dict[str, AsyncBaseRepository] = {}

    def create_repository(
        self, model: Type[ModelType]
    ) -> AsyncBaseRepository[ModelType]:
        """
        Create or retrieve cached repository for model.

        Args:
            model: SQLAlchemy model class

        Returns:
            AsyncBaseRepository instance for the model
        """
        if model not in self._registry:
            self._registry[model] = AsyncBaseRepository(model, self.db)
        return self._registry[model]

    def register_custom_repository(
        self, name: str, repository: AsyncBaseRepository
    ) -> None:
        """
        Register custom repository implementation.

        Args:
            name: Name to access repository by
            repository: Custom repository instance
        """
        self._custom_repositories[name] = repository

    def get_custom_repository(self, name: str) -> AsyncBaseRepository:
        """
        Get custom repository by name.

        Args:
            name: Repository name

        Returns:
            Custom repository instance

        Raises:
            KeyError: If repository not found
        """
        return self._custom_repositories[name]

    def clear_cache(self) -> None:
        """Clear repository cache."""
        self._registry.clear()

    def get_all_repositories(
        self,
    ) -> dict[Type, AsyncBaseRepository]:
        """
        Get all cached repositories.

        Returns:
            Dictionary of model -> repository mappings
        """
        return self._registry.copy()


class RepositoryProvider:
    """
    Provides dependency injection for repositories.

    Usage:
        provider = RepositoryProvider(db)
        person_repo = provider.get_repository(Person)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize provider.

        Args:
            db: Async database session
        """
        self.factory = RepositoryFactory(db)

    def get_repository(
        self, model: Type[ModelType]
    ) -> AsyncBaseRepository[ModelType]:
        """
        Get repository for model.

        Args:
            model: SQLAlchemy model class

        Returns:
            AsyncBaseRepository instance
        """
        return self.factory.create_repository(model)
