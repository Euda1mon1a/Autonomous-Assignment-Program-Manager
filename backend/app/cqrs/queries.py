"""
Query Pattern Implementation for CQRS Read Operations
======================================================

This module provides the query side of CQRS, handling all read operations
in the Residency Scheduler application.

Overview
--------
Queries represent **requests for data**. Unlike commands, they:

- **Never modify state**: Queries are pure reads with no side effects
- **Are immutable**: Query objects cannot be changed after creation
- **Named as questions**: GetAssignmentsByPerson, FindAvailableFaculty
- **Return read models**: Optimized, denormalized views (not domain entities)

The query side is optimized for read performance, potentially using separate
read replicas, caching, and denormalized data structures.

Data Flow
---------
::

    Query -> QueryBus -> QueryHandler -> Read Database (Read Models)
                |                              |
                v                              v
           (Cache Check)              (Denormalized Data)
                                              |
                                              v
                                         QueryResult

Read Models vs Domain Entities
------------------------------

**Domain Entities** (Write Side):
    - Normalized data structures
    - Enforce business invariants
    - May require joins across tables
    - Optimized for write consistency

**Read Models** (Query Side):
    - Denormalized for query performance
    - Pre-computed aggregations
    - No join complexity
    - Eventually consistent with writes
    - Optimized for specific query patterns

Example: An AssignmentReadModel might include person_name and rotation_name
directly (denormalized), avoiding joins with Person and Rotation tables.

Key Components
--------------

**Query**:
    Base class for all queries. Includes metadata (query_id, timestamp, user_id)
    and is frozen (immutable). Queries should be named as questions.

**QueryBus**:
    Routes queries to registered handlers. Manages:
    - Handler registration
    - Optional result caching (with TTL)
    - Query execution timing
    - Error handling and logging

**QueryHandler**:
    Abstract base class for query processors. Each query type should have
    exactly one handler. Handlers:
    - Query read models (not write database!)
    - Apply any filtering/sorting
    - Return QueryResult with data

**QueryResult**:
    Encapsulates the query outcome:
    - success: Boolean indicating success/failure
    - data: Result data (single model or list)
    - total_count: For paginated queries
    - metadata: Timing, cache hit, etc.

**ReadModel**:
    Base class for denormalized read model entities. Read models:
    - Are flat and denormalized
    - Include computed/aggregated fields
    - Are optimized for specific use cases
    - May combine data from multiple aggregates

**ReadModelProjector**:
    Updates read models in response to domain events. Maintains eventual
    consistency between write and read databases.

**ReadDatabaseConnectionManager**:
    Manages separate read database connections. Supports:
    - Read replicas for scalability
    - Read-only connection mode
    - Separate connection pool settings

Usage Example
-------------
::

    from app.cqrs.queries import Query, QueryBus, QueryHandler, QueryResult, ReadModel
    from dataclasses import dataclass

    # 1. Define a read model (denormalized for fast queries)
    @dataclass
    class AssignmentSummary(ReadModel):
        assignment_id: UUID
        person_name: str        # Denormalized from Person table
        block_date: date        # Denormalized from Block table
        rotation_name: str      # Denormalized from Rotation table
        location: str
        total_hours: float      # Pre-computed aggregate

    # 2. Define a query (immutable, question-based naming)
    @dataclass(frozen=True)
    class GetPersonAssignmentsQuery(Query):
        person_id: UUID
        start_date: date | None = None
        end_date: date | None = None
        include_completed: bool = True

    # 3. Define a handler
    class GetPersonAssignmentsHandler(QueryHandler[GetPersonAssignmentsQuery]):
        async def handle(self, query: GetPersonAssignmentsQuery) -> QueryResult:
            # Query the read model table (not the normalized write tables!)
            assignments = await self._query_assignment_summaries(
                person_id=query.person_id,
                start_date=query.start_date,
                end_date=query.end_date
            )

            if not query.include_completed:
                assignments = [a for a in assignments if not a.is_completed]

            return QueryResult.ok(
                data=assignments,
                total_count=len(assignments)
            )

    # 4. Execute with caching enabled
    query_bus = QueryBus(db_read, enable_cache=True)
    query_bus.register_handler(GetPersonAssignmentsQuery, handler)

    result = await query_bus.execute(
        GetPersonAssignmentsQuery(person_id=person_id)
    )

    if result.success:
        for assignment in result.data:
            print(f"{assignment.person_name}: {assignment.rotation_name}")
        print(f"Cache hit: {result.metadata.get('cache_hit')}")
        print(f"Query time: {result.metadata.get('query_time_seconds')}s")

Projector Example
-----------------
::

    class AssignmentSummaryProjector(ReadModelProjector):
        '''Updates AssignmentSummary read model from domain events.'''

        def __init__(self, db_write: Session, db_read: Session):
            super().__init__(db_write, db_read)

        async def project(self, event: DomainEvent) -> None:
            if isinstance(event, AssignmentCreatedEvent):
                await self._on_assignment_created(event)
            elif isinstance(event, AssignmentUpdatedEvent):
                await self._on_assignment_updated(event)
            elif isinstance(event, PersonUpdatedEvent):
                await self._on_person_updated(event)  # Update denormalized name

        async def _on_assignment_created(self, event):
            # Fetch related data from write DB to build denormalized read model
            assignment = await self.db_write.get(Assignment, event.aggregate_id)
            person = await self.db_write.get(Person, assignment.person_id)
            rotation = await self.db_write.get(Rotation, assignment.rotation_id)

            # Create denormalized read model
            summary = AssignmentSummary(
                assignment_id=assignment.id,
                person_name=person.name,  # Denormalized!
                block_date=assignment.block.date,
                rotation_name=rotation.name,  # Denormalized!
                location=rotation.location,
                total_hours=self._calculate_hours(assignment)
            )

            self.db_read.add(summary)
            await self.db_read.commit()

        async def rebuild(self) -> None:
            '''Rebuild all read models from scratch.'''
            # Clear existing read models
            await self.db_read.execute("DELETE FROM assignment_summaries")

            # Rebuild from all assignments
            assignments = await self.db_write.query(Assignment).all()
            for assignment in assignments:
                await self._build_summary(assignment)

Best Practices
--------------

1. **Query read models, not write tables**: Read handlers should never query
   the normalized write database directly
2. **Keep queries focused**: One query type for one specific use case
3. **Use caching wisely**: Enable for frequently-accessed, stable data
4. **Handle eventual consistency**: Read models may lag behind writes
5. **Denormalize aggressively**: Optimize for query patterns, not normalization
6. **Include pagination**: Use limit/offset or cursor-based for large results

Eventual Consistency
--------------------

Read models are updated asynchronously via event projectors. This means:

- Queries may return stale data immediately after writes
- Sync lag is typically < 1 second in normal operation
- For strong consistency, query the write model or use the event store

The ``ReadModelSyncService`` (see read_model_sync.py) monitors sync lag
and can alert when projections fall behind.

See Also
--------
- ``app.cqrs.commands``: Command side implementation
- ``app.cqrs.projection_builder``: Building and rebuilding projections
- ``app.cqrs.read_model_sync``: Real-time sync monitoring
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

    def __init__(self, db: Session) -> None:
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

    def __init__(self, db_write: Session, db_read: Session) -> None:
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

    def __init__(self, db: Session, enable_cache: bool = False) -> None:
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
            logger.error(error_msg, query_type=query_name)
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

    def __init__(self) -> None:
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
            connect_args=(
                {"options": "-c default_transaction_read_only=on"}
                if "postgresql" in read_db_url
                else {}
            ),
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


@dataclass(frozen=True, kw_only=True)
class ExampleGetByIdQuery(Query):
    """Example query for getting an entity by ID."""

    entity_id: UUID


@dataclass(frozen=True)
class ExampleListQuery(Query):
    """Example query for listing entities with filters."""

    status: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True, kw_only=True)
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
