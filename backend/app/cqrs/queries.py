"""Query pattern implementation for CQRS read operations.

This module provides the query side of CQRS, handling all read operations
in the Residency Scheduler application.

Queries represent requests for data (e.g., GetAssignmentsByPerson,
GetScheduleForWeek). They return denormalized, optimized read models
rather than domain entities.

Architecture:
    Query -> QueryBus -> QueryHandler -> Read Database -> ReadModel

Read Models:
    Read models are denormalized, optimized projections of the write
    database, designed specifically for query performance. They are
    updated asynchronously via event-driven projectors.

Example:
    # Define a query
    @dataclass(frozen=True)
    class GetAssignmentsByPersonQuery(Query):
        person_id: UUID
        start_date: date | None = None
        end_date: date | None = None

    # Define a read model
    @dataclass
    class AssignmentReadModel(ReadModel):
        assignment_id: UUID
        person_name: str
        block_date: date
        rotation_name: str
        location: str
        # Denormalized for fast querying

    # Define a handler
    class GetAssignmentsByPersonHandler(QueryHandler[GetAssignmentsByPersonQuery]):
        async def handle(self, query: GetAssignmentsByPersonQuery) -> QueryResult:
            # Query optimized read model
            assignments = await self._query_assignments(query.person_id)
            return QueryResult(
                success=True,
                data=assignments
            )

    # Execute query
    bus = QueryBus(db_read)
    bus.register_handler(GetAssignmentsByPersonQuery, handler)
    result = await bus.execute(GetAssignmentsByPersonQuery(person_id=person_id))
"""

import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.cqrs.commands import DomainEvent

logger = logging.getLogger(__name__)

# Type variables for generic query handling
TQuery = TypeVar("TQuery", bound="Query")
TReadModel = TypeVar("TReadModel", bound="ReadModel")

settings = get_settings()


@dataclass(frozen=True)
class Query(ABC):
    """
    Base class for all queries (read operations).

    Queries are immutable, request-based objects that represent
    data retrieval operations. They should be named as questions
    (e.g., GetAssignmentsByPerson, FindAvailableFaculty).

    All queries are frozen (immutable) after creation.

    Attributes:
        query_id: Unique identifier for this query instance
        timestamp: When the query was created
        user_id: Optional user who initiated the query
        metadata: Optional additional context (e.g., for caching)
    """

    query_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReadModel(ABC):
    """
    Base class for read models (query results).

    Read models are denormalized projections optimized for querying.
    Unlike domain entities, they:
    - Are flat and denormalized
    - Include computed/aggregated fields
    - Are optimized for specific use cases
    - May combine data from multiple aggregates

    Read models are updated via projectors that listen to domain events.
    """

    pass


@dataclass
class QueryResult:
    """
    Result of query execution.

    Encapsulates the outcome of a query, including success status,
    data (usually read models), and optional metadata.

    Attributes:
        success: Whether the query executed successfully
        data: Result data (list of read models or single model)
        error: Error message if failed
        total_count: Total count for paginated queries
        metadata: Additional result metadata (e.g., cache hit, query time)
    """

    success: bool
    data: Any = None
    error: str | None = None
    total_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        data: Any,
        total_count: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "QueryResult":
        """Create a successful result."""
        return cls(
            success=True,
            data=data,
            total_count=total_count,
            metadata=metadata or {},
        )

    @classmethod
    def fail(cls, error: str, metadata: dict[str, Any] | None = None) -> "QueryResult":
        """Create a failed result."""
        return cls(success=False, error=error, metadata=metadata or {})


class QueryHandler(ABC, Generic[TQuery]):
    """
    Base class for query handlers.

    Each query should have exactly one handler responsible for
    executing the query and returning read models.

    Handlers should:
    - Query read database (not write database)
    - Return denormalized read models
    - Leverage database indexes and materialized views
    - Cache results when appropriate

    Type Parameters:
        TQuery: The type of query this handler processes
    """

    def __init__(self, db: Session):
        """
        Initialize query handler.

        Args:
            db: Database session for read operations
        """
        self.db = db

    @abstractmethod
    async def handle(self, query: TQuery) -> QueryResult:
        """
        Handle the query execution.

        This method must be implemented by concrete handlers.

        Args:
            query: The query to execute

        Returns:
            QueryResult: Result containing read models

        Raises:
            Exception: For query execution errors
        """
        pass


class ReadModelProjector(ABC):
    """
    Base class for read model projectors.

    Projectors listen to domain events and update read models accordingly.
    They maintain eventual consistency between the write database and
    optimized read models.

    Example:
        class AssignmentReadModelProjector(ReadModelProjector):
            def __init__(self, db_write: Session, db_read: Session):
                super().__init__(db_write, db_read)

            async def project(self, event: DomainEvent) -> None:
                if isinstance(event, AssignmentCreatedEvent):
                    await self._on_assignment_created(event)
                elif isinstance(event, AssignmentUpdatedEvent):
                    await self._on_assignment_updated(event)

            async def _on_assignment_created(self, event: AssignmentCreatedEvent):
                # Fetch data from write DB
                assignment = self.db_write.get(Assignment, event.aggregate_id)

                # Create read model in read DB
                read_model = AssignmentReadModel(
                    assignment_id=assignment.id,
                    person_name=assignment.person.name,
                    block_date=assignment.block.date,
                    rotation_name=assignment.rotation.name,
                )
                self.db_read.add(read_model)
                await self.db_read.commit()
    """

    def __init__(self, db_write: Session, db_read: Session):
        """
        Initialize projector.

        Args:
            db_write: Session for reading from write database
            db_read: Session for writing to read database
        """
        self.db_write = db_write
        self.db_read = db_read

    @abstractmethod
    async def project(self, event: DomainEvent) -> None:
        """
        Project a domain event to update read models.

        Args:
            event: Domain event to process
        """
        pass

    async def rebuild(self) -> None:
        """
        Rebuild all read models from scratch.

        This method should be implemented to support full rebuilds
        of read models from the write database. Useful for:
        - Initial setup
        - Recovery from corruption
        - Schema migrations
        """
        raise NotImplementedError("Rebuild not implemented for this projector")


class QueryBus:
    """
    Query bus for dispatching queries to handlers.

    The QueryBus is responsible for:
    - Routing queries to appropriate handlers
    - Managing query execution lifecycle
    - Optional query result caching
    - Performance monitoring

    Example:
        # Setup
        bus = QueryBus(db_read)
        bus.register_handler(GetAssignmentsByPersonQuery, handler)

        # Execute query
        query = GetAssignmentsByPersonQuery(person_id=person_id)
        result = await bus.execute(query)

        if result.success:
            for assignment in result.data:
                print(assignment.person_name, assignment.block_date)
        else:
            print(f"Error: {result.error}")
    """

    def __init__(self, db: Session, enable_cache: bool = False):
        """
        Initialize query bus.

        Args:
            db: Database session for read operations
            enable_cache: Whether to enable query result caching
        """
        self.db = db
        self.enable_cache = enable_cache
        self._handlers: dict[type[Query], QueryHandler] = {}
        self._cache: dict[str, tuple[QueryResult, datetime]] = {}

    def register_handler(
        self, query_type: type[TQuery], handler: QueryHandler[TQuery]
    ) -> None:
        """
        Register a query handler.

        Args:
            query_type: The query class this handler processes
            handler: The handler instance
        """
        if query_type in self._handlers:
            logger.warning(
                f"Handler for {query_type.__name__} already registered. Overwriting."
            )
        self._handlers[query_type] = handler
        logger.debug(f"Registered handler for {query_type.__name__}")

    async def execute(self, query: TQuery) -> QueryResult:
        """
        Execute a query.

        This method:
        1. Checks cache (if enabled)
        2. Routes query to appropriate handler
        3. Executes the handler
        4. Caches result (if enabled)
        5. Returns the result

        Args:
            query: The query to execute

        Returns:
            QueryResult: Result containing read models

        Raises:
            ValueError: If no handler is registered for query type
        """
        query_type = type(query)
        query_name = query_type.__name__

        logger.debug(
            f"Executing query: {query_name} (ID: {query.query_id})",
            extra={"query_id": str(query.query_id), "query_type": query_name},
        )

        # Check cache
        if self.enable_cache:
            cached_result = self._get_cached_result(query)
            if cached_result:
                logger.debug(
                    f"Cache hit for query: {query_name}",
                    extra={"query_id": str(query.query_id)},
                )
                cached_result.metadata["cache_hit"] = True
                return cached_result

        # Get handler
        if query_type not in self._handlers:
            error_msg = f"No handler registered for query type: {query_name}"
            logger.error(error_msg, extra={"query_type": query_name})
            raise ValueError(error_msg)

        handler = self._handlers[query_type]

        try:
            # Execute query
            start_time = datetime.utcnow()
            result = await handler.handle(query)
            elapsed = (datetime.utcnow() - start_time).total_seconds()

            result.metadata["query_time_seconds"] = elapsed
            result.metadata["cache_hit"] = False

            logger.debug(
                f"Query executed: {query_name}",
                extra={
                    "query_id": str(query.query_id),
                    "elapsed_seconds": elapsed,
                    "result_count": (
                        len(result.data) if isinstance(result.data, list) else 1
                    ),
                },
            )

            # Cache result
            if self.enable_cache and result.success:
                self._cache_result(query, result)

            return result

        except Exception as e:
            logger.error(
                f"Query execution error: {query_name}",
                extra={"query_id": str(query.query_id), "error": str(e)},
                exc_info=True,
            )
            return QueryResult.fail(
                error="An unexpected error occurred",
                metadata={"exception_type": type(e).__name__},
            )

    def _get_cached_result(self, query: Query) -> QueryResult | None:
        """
        Get cached result for a query.

        Args:
            query: The query to check cache for

        Returns:
            Cached QueryResult or None if not cached
        """
        cache_key = self._make_cache_key(query)
        if cache_key in self._cache:
            cached_result, cached_at = self._cache[cache_key]
            # Simple TTL check (could be made configurable)
            age = (datetime.utcnow() - cached_at).total_seconds()
            if age < 300:  # 5 minutes TTL
                return cached_result
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
        return None

    def _cache_result(self, query: Query, result: QueryResult) -> None:
        """
        Cache a query result.

        Args:
            query: The query that was executed
            result: The result to cache
        """
        cache_key = self._make_cache_key(query)
        self._cache[cache_key] = (result, datetime.utcnow())

    def _make_cache_key(self, query: Query) -> str:
        """
        Generate a cache key for a query.

        Args:
            query: The query to generate a key for

        Returns:
            Cache key string
        """
        # Simple implementation - could be enhanced with better hashing
        query_type = type(query).__name__
        query_data = {
            k: v
            for k, v in query.__dict__.items()
            if k not in ("query_id", "timestamp", "metadata")
        }
        return f"{query_type}:{hash(frozenset(query_data.items()))}"

    def clear_cache(self) -> None:
        """Clear all cached query results."""
        self._cache.clear()
        logger.info("Query cache cleared")


class ReadDatabaseConnectionManager:
    """
    Manager for separate read database connections.

    In a full CQRS implementation, read and write databases can be
    physically separate for optimal scaling. This manager handles
    connections to the read database.

    Configuration:
        Set READ_DATABASE_URL in settings to use a separate read database.
        If not set, falls back to the main DATABASE_URL.

    Example:
        # In settings
        READ_DATABASE_URL: str = "postgresql://read_user:password@read-replica:5432/db"

        # Usage
        manager = ReadDatabaseConnectionManager()
        db_read = manager.get_session()
        # Use db_read for queries
    """

    def __init__(self):
        """Initialize read database connection manager."""
        # Check if READ_DATABASE_URL is set in settings
        read_db_url = getattr(settings, "READ_DATABASE_URL", None)
        if not read_db_url:
            # Fall back to main database
            logger.info("READ_DATABASE_URL not set, using main database for reads")
            read_db_url = settings.DATABASE_URL

        self.engine = create_engine(
            read_db_url,
            # Read-only connection pool settings
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            # Enable read-only mode if supported
            connect_args={"options": "-c default_transaction_read_only=on"}
            if "postgresql" in read_db_url
            else {},
        )

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_session(self) -> Session:
        """
        Get a read database session.

        Returns:
            Session: Read-only database session
        """
        return self.SessionLocal()

    @asynccontextmanager
    async def session_scope(self):
        """
        Provide a transactional scope for read operations.

        Yields:
            Session: Read-only database session
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Example query implementations for reference
@dataclass(frozen=True)
class ExampleGetByIdQuery(Query):
    """Example query for getting an entity by ID."""

    entity_id: UUID


@dataclass(frozen=True)
class ExampleListQuery(Query):
    """Example query for listing entities with filters."""

    status: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class ExampleSearchQuery(Query):
    """Example query for searching entities."""

    search_term: str
    filters: dict[str, Any] = field(default_factory=dict)


# Example read model for reference
@dataclass
class ExampleReadModel(ReadModel):
    """Example read model with denormalized data."""

    id: UUID
    name: str
    email: str
    created_at: datetime
    # Denormalized fields for fast querying
    total_assignments: int
    latest_assignment_date: datetime | None
    compliance_status: str
