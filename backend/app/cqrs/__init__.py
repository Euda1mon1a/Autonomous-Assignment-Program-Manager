"""CQRS (Command Query Responsibility Segregation) pattern implementation.

This module provides a complete CQRS implementation for separating read and write
operations in the Residency Scheduler application.

Key Components:
- Command: Represents state-changing operations (write side)
- Query: Represents data retrieval operations (read side)
- CommandBus: Dispatches commands to appropriate handlers
- QueryBus: Dispatches queries to appropriate handlers
- Event: Domain events triggered by commands
- ReadModel: Optimized projections for query operations

Architecture:
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Command   │────────>│ CommandBus   │────────>│   Handler    │
└─────────────┘         └──────────────┘         └──────────────┘
                                                         │
                                                         ▼
                                                   ┌──────────────┐
                                                   │  Write DB    │
                                                   └──────────────┘
                                                         │
                                                         ▼
                                                   ┌──────────────┐
                                                   │   Events     │
                                                   └──────────────┘
                                                         │
                                                         ▼
                                                   ┌──────────────┐
                                                   │  Projectors  │
                                                   └──────────────┘
                                                         │
                                                         ▼
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│    Query    │────────>│  QueryBus    │────────>│   Handler    │
└─────────────┘         └──────────────┘         └──────────────┘
                                                         │
                                                         ▼
                                                   ┌──────────────┐
                                                   │   Read DB    │
                                                   └──────────────┘

Usage:
    # Commands (write operations)
    from app.cqrs import CommandBus, CreateAssignmentCommand

    command_bus = CommandBus(db)
    command = CreateAssignmentCommand(
        person_id=person_id,
        block_id=block_id,
        rotation_id=rotation_id
    )
    result = await command_bus.execute(command)

    # Queries (read operations)
    from app.cqrs import QueryBus, GetAssignmentsByPersonQuery

    query_bus = QueryBus(db)
    query = GetAssignmentsByPersonQuery(person_id=person_id)
    assignments = await query_bus.execute(query)

Benefits:
- Separation of concerns between read and write operations
- Optimized read models for complex queries
- Event-driven architecture for eventual consistency
- Better scalability through separate read/write databases
- Improved testability and maintainability
"""

from app.cqrs.commands import (
    Command,
    CommandBus,
    CommandHandler,
    CommandResult,
    CommandValidationMiddleware,
)
from app.cqrs.projection_builder import (
    BaseProjection,
    BuildMode,
    BuildResult,
    ProjectionBuilder,
    ProjectionBuildLog,
    ProjectionCheckpoint,
    ProjectionDefinition,
    ProjectionError,
    ProjectionMetadata,
    ProjectionNotFoundError,
    ProjectionStatus,
)
from app.cqrs.queries import (
    Query,
    QueryBus,
    QueryHandler,
    QueryResult,
    ReadModel,
    ReadModelProjector,
)
from app.cqrs.read_model_sync import (
    ConflictResolutionStrategy,
    ReadModelSyncService,
    SyncCheckpoint,
    SyncConflict,
    SyncMetrics,
    SyncPriority,
    SyncStatus,
    create_sync_service,
)

__all__ = [
    # Commands
    "Command",
    "CommandBus",
    "CommandHandler",
    "CommandResult",
    "CommandValidationMiddleware",
    # Queries
    "Query",
    "QueryBus",
    "QueryHandler",
    "QueryResult",
    "ReadModel",
    "ReadModelProjector",
    # Projection Builder
    "BaseProjection",
    "BuildMode",
    "BuildResult",
    "ProjectionBuilder",
    "ProjectionBuildLog",
    "ProjectionCheckpoint",
    "ProjectionDefinition",
    "ProjectionError",
    "ProjectionMetadata",
    "ProjectionNotFoundError",
    "ProjectionStatus",
    # Read Model Sync
    "ConflictResolutionStrategy",
    "ReadModelSyncService",
    "SyncCheckpoint",
    "SyncConflict",
    "SyncMetrics",
    "SyncPriority",
    "SyncStatus",
    "create_sync_service",
]
