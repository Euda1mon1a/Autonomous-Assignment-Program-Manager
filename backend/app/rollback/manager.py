"""
Rollback manager service for state restoration and recovery.

This service provides comprehensive rollback capabilities for the Residency Scheduler,
allowing controlled state restoration for assignments, absences, swaps, and other entities.
Integrates with SQLAlchemy-Continuum for version tracking and audit trails.

Key Features:
- Rollback point creation with state snapshots
- Selective rollback (specific entities)
- Full rollback execution (entire snapshot)
- Rollback verification and integrity checks
- Cascading rollback handling (dependent entities)
- Rollback history tracking
- Authorization checks (RBAC)

Usage:
    from app.rollback.manager import RollbackManager

    # Create rollback manager
    manager = RollbackManager(db)

    # Create rollback point
    point = manager.create_rollback_point(
        name="Pre-schedule-generation",
        description="Before generating fall semester schedule",
        created_by=user_id,
        entity_types=["assignment", "absence"],
    )

    # Execute rollback
    result = manager.execute_rollback(
        rollback_point_id=point.id,
        executed_by=user_id,
        reason="Schedule generation failed",
    )
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session, selectinload

# Optional import - sqlalchemy_continuum may not be installed
try:
    from sqlalchemy_continuum import version_class
    HAS_CONTINUUM = True
except ImportError:
    version_class = None
    HAS_CONTINUUM = False

from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.schedule_run import ScheduleRun
from app.models.swap import SwapRecord
from app.models.user import User

logger = logging.getLogger(__name__)


class RollbackStatus(str, Enum):
    """Status of a rollback point or operation."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"


class RollbackScope(str, Enum):
    """Scope of rollback operation."""
    FULL = "full"  # Rollback entire snapshot
    SELECTIVE = "selective"  # Rollback specific entities
    CASCADING = "cascading"  # Rollback with dependencies


@dataclass
class EntitySnapshot:
    """
    Snapshot of a single entity's state at rollback point creation.

    Captures the complete state including version history and relationships.
    """
    entity_type: str
    entity_id: UUID
    version_id: int | None
    state: dict[str, Any]
    timestamp: datetime
    dependencies: list[tuple[str, UUID]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackPoint:
    """
    A point-in-time snapshot for potential rollback.

    Captures complete state of specified entities for later restoration.
    Includes metadata, authorization info, and dependency tracking.
    """
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    created_by: UUID
    entity_snapshots: list[EntitySnapshot]
    status: RollbackStatus
    scope: RollbackScope
    metadata: dict[str, Any] = field(default_factory=dict)
    expires_at: datetime | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class RollbackResult:
    """
    Result of a rollback operation.

    Provides detailed information about success/failure, entities affected,
    and any errors encountered during rollback.
    """
    success: bool
    rollback_point_id: UUID
    executed_at: datetime
    executed_by: UUID
    scope: RollbackScope
    entities_restored: list[tuple[str, UUID]]
    entities_failed: list[tuple[str, UUID, str]]
    verification_passed: bool
    status: RollbackStatus
    message: str
    error_details: dict[str, Any] | None = None


@dataclass
class RollbackVerificationResult:
    """
    Result of rollback verification.

    Validates that rollback successfully restored entities to expected state.
    """
    passed: bool
    rollback_point_id: UUID
    verified_at: datetime
    verified_by: UUID | None
    mismatches: list[dict[str, Any]]
    entities_verified: int
    entities_failed: int
    details: dict[str, Any] = field(default_factory=dict)


class RollbackAuthorizationError(ForbiddenError):
    """Raised when user lacks authorization for rollback operation."""

    def __init__(self, message: str = "Insufficient permissions for rollback operation"):
        super().__init__(message)


class RollbackExpiredError(ValidationError):
    """Raised when attempting to use an expired rollback point."""

    def __init__(self, message: str = "Rollback point has expired"):
        super().__init__(message)


class RollbackManager:
    """
    Service for managing rollback points and executing rollback operations.

    Provides comprehensive state restoration capabilities with authorization,
    verification, and dependency tracking.
    """

    # Default rollback point expiration (days)
    DEFAULT_EXPIRATION_DAYS = 30

    # Maximum number of entities per rollback point (prevent memory issues)
    MAX_ENTITIES_PER_ROLLBACK = 10000

    # Entity types supported for rollback
    SUPPORTED_ENTITY_TYPES = {
        "assignment": Assignment,
        "absence": Absence,
        "schedule_run": ScheduleRun,
        "swap_record": SwapRecord,
    }

    # Roles authorized to create/execute rollbacks
    AUTHORIZED_ROLES = {"admin", "coordinator"}

    def __init__(self, db: Session):
        """
        Initialize rollback manager.

        Args:
            db: Database session
        """
        self.db = db

    def create_rollback_point(
        self,
        name: str,
        created_by: UUID,
        description: str | None = None,
        entity_types: list[str] | None = None,
        entity_ids: list[tuple[str, UUID]] | None = None,
        scope: RollbackScope = RollbackScope.FULL,
        tags: list[str] | None = None,
        expires_in_days: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RollbackPoint:
        """
        Create a rollback point with state snapshots.

        Args:
            name: Human-readable name for rollback point
            created_by: UUID of user creating rollback point
            description: Optional detailed description
            entity_types: List of entity types to snapshot (if None, all supported)
            entity_ids: Specific entity IDs to snapshot (selective rollback)
            scope: Scope of rollback (full, selective, cascading)
            tags: Optional tags for categorization
            expires_in_days: Days until rollback point expires (default 30)
            metadata: Additional metadata to store

        Returns:
            RollbackPoint: Created rollback point with snapshots

        Raises:
            RollbackAuthorizationError: If user lacks authorization
            ValidationError: If invalid parameters provided
        """
        # Verify authorization
        self._verify_authorization(created_by, "create_rollback")

        # Validate inputs
        if entity_types:
            invalid_types = set(entity_types) - set(self.SUPPORTED_ENTITY_TYPES.keys())
            if invalid_types:
                raise ValidationError(
                    f"Unsupported entity types: {', '.join(invalid_types)}"
                )

        # Default to all entity types if none specified
        if not entity_types and not entity_ids:
            entity_types = list(self.SUPPORTED_ENTITY_TYPES.keys())

        # Create rollback point
        rollback_id = uuid4()
        created_at = datetime.utcnow()
        expires_at = None
        if expires_in_days or expires_in_days is None:
            days = expires_in_days or self.DEFAULT_EXPIRATION_DAYS
            expires_at = created_at + timedelta(days=days)

        # Capture entity snapshots
        snapshots = self._capture_entity_snapshots(
            entity_types=entity_types,
            entity_ids=entity_ids,
            timestamp=created_at,
        )

        # Check entity count limit
        if len(snapshots) > self.MAX_ENTITIES_PER_ROLLBACK:
            logger.warning(
                f"Rollback point {rollback_id} exceeds max entities "
                f"({len(snapshots)} > {self.MAX_ENTITIES_PER_ROLLBACK})"
            )

        # Create rollback point object
        rollback_point = RollbackPoint(
            id=rollback_id,
            name=name,
            description=description,
            created_at=created_at,
            created_by=created_by,
            entity_snapshots=snapshots,
            status=RollbackStatus.CREATED,
            scope=scope,
            metadata=metadata or {},
            expires_at=expires_at,
            tags=tags or [],
        )

        # Persist rollback point (stored as JSON in metadata table or file system)
        self._persist_rollback_point(rollback_point)

        logger.info(
            f"Created rollback point {rollback_id} with {len(snapshots)} snapshots "
            f"by user {created_by}"
        )

        return rollback_point

    def execute_rollback(
        self,
        rollback_point_id: UUID,
        executed_by: UUID,
        reason: str,
        scope: RollbackScope | None = None,
        entity_ids: list[tuple[str, UUID]] | None = None,
        verify_after: bool = True,
        dry_run: bool = False,
    ) -> RollbackResult:
        """
        Execute a rollback operation to restore entity states.

        Args:
            rollback_point_id: UUID of rollback point to restore
            executed_by: UUID of user executing rollback
            reason: Reason for rollback (audit trail)
            scope: Override rollback scope (selective/full/cascading)
            entity_ids: Specific entities to rollback (for selective scope)
            verify_after: Whether to verify rollback after execution
            dry_run: If True, simulate rollback without applying changes

        Returns:
            RollbackResult: Result of rollback operation

        Raises:
            RollbackAuthorizationError: If user lacks authorization
            NotFoundError: If rollback point not found
            RollbackExpiredError: If rollback point has expired
            ValidationError: If invalid parameters
        """
        # Verify authorization
        self._verify_authorization(executed_by, "execute_rollback")

        # Load rollback point
        rollback_point = self._load_rollback_point(rollback_point_id)
        if not rollback_point:
            raise NotFoundError(f"Rollback point {rollback_point_id} not found")

        # Check expiration
        if rollback_point.expires_at and datetime.utcnow() > rollback_point.expires_at:
            raise RollbackExpiredError(
                f"Rollback point expired at {rollback_point.expires_at}"
            )

        # Determine scope
        effective_scope = scope or rollback_point.scope

        # Determine entities to restore
        if effective_scope == RollbackScope.SELECTIVE and entity_ids:
            snapshots_to_restore = [
                s for s in rollback_point.entity_snapshots
                if (s.entity_type, s.entity_id) in entity_ids
            ]
        elif effective_scope == RollbackScope.CASCADING:
            # Include dependent entities
            snapshots_to_restore = self._resolve_dependencies(
                rollback_point.entity_snapshots,
                entity_ids or [],
            )
        else:
            # Full rollback
            snapshots_to_restore = rollback_point.entity_snapshots

        if not snapshots_to_restore:
            raise ValidationError("No entities selected for rollback")

        executed_at = datetime.utcnow()
        entities_restored = []
        entities_failed = []

        try:
            # Update rollback point status
            if not dry_run:
                rollback_point.status = RollbackStatus.IN_PROGRESS
                self._persist_rollback_point(rollback_point)

            # Restore each entity
            for snapshot in snapshots_to_restore:
                try:
                    if not dry_run:
                        self._restore_entity(snapshot)
                    entities_restored.append((snapshot.entity_type, snapshot.entity_id))
                    logger.debug(
                        f"Restored {snapshot.entity_type} {snapshot.entity_id}"
                    )
                except Exception as e:
                    error_msg = str(e)
                    entities_failed.append(
                        (snapshot.entity_type, snapshot.entity_id, error_msg)
                    )
                    logger.error(
                        f"Failed to restore {snapshot.entity_type} "
                        f"{snapshot.entity_id}: {error_msg}"
                    )

            # Commit transaction if not dry run
            if not dry_run and not entities_failed:
                self.db.commit()
            elif not dry_run:
                self.db.rollback()

            # Determine final status
            if not entities_failed:
                final_status = RollbackStatus.COMPLETED
                success = True
            elif entities_restored:
                final_status = RollbackStatus.PARTIALLY_COMPLETED
                success = False
            else:
                final_status = RollbackStatus.FAILED
                success = False

            # Update rollback point status
            if not dry_run:
                rollback_point.status = final_status
                self._persist_rollback_point(rollback_point)

            # Verify rollback if requested
            verification_passed = True
            if verify_after and success and not dry_run:
                verification_result = self.verify_rollback(
                    rollback_point_id=rollback_point_id,
                    verified_by=executed_by,
                )
                verification_passed = verification_result.passed

            # Build result
            message = self._build_rollback_message(
                success=success,
                entities_restored=len(entities_restored),
                entities_failed=len(entities_failed),
                dry_run=dry_run,
            )

            result = RollbackResult(
                success=success,
                rollback_point_id=rollback_point_id,
                executed_at=executed_at,
                executed_by=executed_by,
                scope=effective_scope,
                entities_restored=entities_restored,
                entities_failed=entities_failed,
                verification_passed=verification_passed,
                status=final_status,
                message=message,
            )

            # Log rollback execution
            self._log_rollback_execution(rollback_point, result, reason)

            logger.info(
                f"Rollback {rollback_point_id} executed by {executed_by}: "
                f"{len(entities_restored)} restored, {len(entities_failed)} failed"
            )

            return result

        except Exception as e:
            if not dry_run:
                self.db.rollback()
                rollback_point.status = RollbackStatus.FAILED
                self._persist_rollback_point(rollback_point)

            logger.error(f"Rollback execution failed: {str(e)}", exc_info=True)
            raise AppException(
                f"Rollback execution failed: {str(e)}",
                status_code=500,
            )

    def verify_rollback(
        self,
        rollback_point_id: UUID,
        verified_by: UUID | None = None,
        entity_ids: list[tuple[str, UUID]] | None = None,
    ) -> RollbackVerificationResult:
        """
        Verify that rollback successfully restored entities to expected state.

        Compares current entity state with snapshot state to detect mismatches.

        Args:
            rollback_point_id: UUID of rollback point to verify
            verified_by: Optional UUID of user performing verification
            entity_ids: Specific entities to verify (if None, verify all)

        Returns:
            RollbackVerificationResult: Verification results

        Raises:
            NotFoundError: If rollback point not found
        """
        rollback_point = self._load_rollback_point(rollback_point_id)
        if not rollback_point:
            raise NotFoundError(f"Rollback point {rollback_point_id} not found")

        verified_at = datetime.utcnow()
        mismatches = []
        entities_verified = 0
        entities_failed = 0

        # Determine which snapshots to verify
        snapshots_to_verify = rollback_point.entity_snapshots
        if entity_ids:
            snapshots_to_verify = [
                s for s in snapshots_to_verify
                if (s.entity_type, s.entity_id) in entity_ids
            ]

        # Verify each entity
        for snapshot in snapshots_to_verify:
            try:
                current_state = self._get_entity_current_state(
                    snapshot.entity_type,
                    snapshot.entity_id,
                )

                if not current_state:
                    entities_failed += 1
                    mismatches.append({
                        "entity_type": snapshot.entity_type,
                        "entity_id": str(snapshot.entity_id),
                        "error": "Entity not found",
                    })
                    continue

                # Compare states (ignore timestamps and audit fields)
                state_mismatches = self._compare_states(
                    snapshot.state,
                    current_state,
                    ignore_fields={"created_at", "updated_at", "version"},
                )

                if state_mismatches:
                    entities_failed += 1
                    mismatches.append({
                        "entity_type": snapshot.entity_type,
                        "entity_id": str(snapshot.entity_id),
                        "mismatches": state_mismatches,
                    })
                else:
                    entities_verified += 1

            except Exception as e:
                entities_failed += 1
                mismatches.append({
                    "entity_type": snapshot.entity_type,
                    "entity_id": str(snapshot.entity_id),
                    "error": str(e),
                })
                logger.error(
                    f"Verification failed for {snapshot.entity_type} "
                    f"{snapshot.entity_id}: {str(e)}"
                )

        # Determine verification result
        passed = len(mismatches) == 0

        # Update rollback point status
        if passed:
            rollback_point.status = RollbackStatus.VERIFIED
        else:
            rollback_point.status = RollbackStatus.VERIFICATION_FAILED
        self._persist_rollback_point(rollback_point)

        result = RollbackVerificationResult(
            passed=passed,
            rollback_point_id=rollback_point_id,
            verified_at=verified_at,
            verified_by=verified_by,
            mismatches=mismatches,
            entities_verified=entities_verified,
            entities_failed=entities_failed,
        )

        logger.info(
            f"Rollback verification for {rollback_point_id}: "
            f"passed={passed}, verified={entities_verified}, "
            f"failed={entities_failed}"
        )

        return result

    def list_rollback_points(
        self,
        created_by: UUID | None = None,
        status: RollbackStatus | None = None,
        tags: list[str] | None = None,
        include_expired: bool = False,
        limit: int = 100,
    ) -> list[RollbackPoint]:
        """
        List available rollback points with optional filtering.

        Args:
            created_by: Filter by creator user ID
            status: Filter by rollback status
            tags: Filter by tags (any match)
            include_expired: Whether to include expired rollback points
            limit: Maximum number of results

        Returns:
            List of RollbackPoint objects
        """
        # In production, this would query a database table or file system
        # For now, return empty list as placeholder
        rollback_points = self._list_persisted_rollback_points(limit=limit)

        # Apply filters
        filtered_points = []
        for point in rollback_points:
            if created_by and point.created_by != created_by:
                continue
            if status and point.status != status:
                continue
            if tags and not any(tag in point.tags for tag in tags):
                continue
            if not include_expired and point.expires_at:
                if datetime.utcnow() > point.expires_at:
                    continue

            filtered_points.append(point)

        return filtered_points[:limit]

    def get_rollback_history(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> list[dict[str, Any]]:
        """
        Get rollback history for a specific entity.

        Shows all rollback operations that affected this entity.

        Args:
            entity_type: Type of entity
            entity_id: UUID of entity

        Returns:
            List of rollback history entries
        """
        if entity_type not in self.SUPPORTED_ENTITY_TYPES:
            raise ValidationError(f"Unsupported entity type: {entity_type}")

        # Query all rollback points that include this entity
        rollback_points = self._list_persisted_rollback_points(limit=1000)

        history = []
        for point in rollback_points:
            # Check if entity is in this rollback point
            for snapshot in point.entity_snapshots:
                if (
                    snapshot.entity_type == entity_type
                    and snapshot.entity_id == entity_id
                ):
                    history.append({
                        "rollback_point_id": str(point.id),
                        "rollback_point_name": point.name,
                        "created_at": point.created_at.isoformat(),
                        "created_by": str(point.created_by),
                        "status": point.status.value,
                        "snapshot_timestamp": snapshot.timestamp.isoformat(),
                    })
                    break

        # Sort by timestamp descending
        history.sort(key=lambda x: x["created_at"], reverse=True)

        return history

    def delete_rollback_point(
        self,
        rollback_point_id: UUID,
        deleted_by: UUID,
        reason: str | None = None,
    ) -> bool:
        """
        Delete a rollback point.

        Args:
            rollback_point_id: UUID of rollback point to delete
            deleted_by: UUID of user deleting rollback point
            reason: Optional reason for deletion

        Returns:
            True if deleted successfully

        Raises:
            RollbackAuthorizationError: If user lacks authorization
            NotFoundError: If rollback point not found
        """
        # Verify authorization
        self._verify_authorization(deleted_by, "delete_rollback")

        # Load rollback point
        rollback_point = self._load_rollback_point(rollback_point_id)
        if not rollback_point:
            raise NotFoundError(f"Rollback point {rollback_point_id} not found")

        # Delete rollback point
        self._delete_persisted_rollback_point(rollback_point_id)

        logger.info(
            f"Deleted rollback point {rollback_point_id} by user {deleted_by}"
            + (f": {reason}" if reason else "")
        )

        return True

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    def _verify_authorization(self, user_id: UUID, operation: str) -> None:
        """
        Verify user is authorized for rollback operation.

        Args:
            user_id: UUID of user
            operation: Operation being performed

        Raises:
            RollbackAuthorizationError: If user lacks authorization
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise RollbackAuthorizationError("User not found")

        if user.role not in self.AUTHORIZED_ROLES:
            raise RollbackAuthorizationError(
                f"User role '{user.role}' not authorized for {operation}"
            )

    def _capture_entity_snapshots(
        self,
        entity_types: list[str] | None = None,
        entity_ids: list[tuple[str, UUID]] | None = None,
        timestamp: datetime | None = None,
    ) -> list[EntitySnapshot]:
        """
        Capture state snapshots for specified entities.

        Args:
            entity_types: Entity types to snapshot
            entity_ids: Specific entity IDs to snapshot
            timestamp: Timestamp for snapshots

        Returns:
            List of EntitySnapshot objects
        """
        timestamp = timestamp or datetime.utcnow()
        snapshots = []

        if entity_ids:
            # Snapshot specific entities
            for entity_type, entity_id in entity_ids:
                snapshot = self._create_entity_snapshot(
                    entity_type, entity_id, timestamp
                )
                if snapshot:
                    snapshots.append(snapshot)
        elif entity_types:
            # Snapshot all entities of specified types
            for entity_type in entity_types:
                entity_snapshots = self._snapshot_all_entities_of_type(
                    entity_type, timestamp
                )
                snapshots.extend(entity_snapshots)

        return snapshots

    def _create_entity_snapshot(
        self,
        entity_type: str,
        entity_id: UUID,
        timestamp: datetime,
    ) -> EntitySnapshot | None:
        """Create snapshot for a single entity."""
        model_class = self.SUPPORTED_ENTITY_TYPES.get(entity_type)
        if not model_class:
            logger.warning(f"Unsupported entity type: {entity_type}")
            return None

        try:
            # Get entity
            entity = self.db.query(model_class).filter(
                model_class.id == entity_id
            ).first()

            if not entity:
                logger.warning(f"Entity not found: {entity_type} {entity_id}")
                return None

            # Get current version ID if versioned
            version_id = None
            if HAS_CONTINUUM and version_class:
                try:
                    VersionClass = version_class(model_class)
                    version_obj = self.db.query(VersionClass).filter(
                        VersionClass.id == entity_id
                    ).order_by(VersionClass.transaction_id.desc()).first()
                    if version_obj:
                        version_id = version_obj.transaction_id
                except Exception:
                    pass  # Entity may not be versioned

            # Serialize entity state
            state = self._serialize_entity(entity)

            # Detect dependencies
            dependencies = self._detect_dependencies(entity_type, entity)

            return EntitySnapshot(
                entity_type=entity_type,
                entity_id=entity_id,
                version_id=version_id,
                state=state,
                timestamp=timestamp,
                dependencies=dependencies,
            )

        except Exception as e:
            logger.error(
                f"Failed to create snapshot for {entity_type} {entity_id}: {str(e)}"
            )
            return None

    def _snapshot_all_entities_of_type(
        self,
        entity_type: str,
        timestamp: datetime,
    ) -> list[EntitySnapshot]:
        """Snapshot all entities of a given type."""
        model_class = self.SUPPORTED_ENTITY_TYPES.get(entity_type)
        if not model_class:
            return []

        snapshots = []
        try:
            # Get all entities (with limit to prevent memory issues)
            entities = self.db.query(model_class).limit(
                self.MAX_ENTITIES_PER_ROLLBACK
            ).all()

            for entity in entities:
                snapshot = self._create_entity_snapshot(
                    entity_type, entity.id, timestamp
                )
                if snapshot:
                    snapshots.append(snapshot)

        except Exception as e:
            logger.error(
                f"Failed to snapshot entities of type {entity_type}: {str(e)}"
            )

        return snapshots

    def _serialize_entity(self, entity: Any) -> dict[str, Any]:
        """Serialize entity to dictionary."""
        state = {}
        for column in entity.__table__.columns:
            value = getattr(entity, column.name, None)
            # Convert to JSON-serializable format
            if isinstance(value, (datetime, UUID)):
                value = str(value)
            elif hasattr(value, '__dict__'):
                value = str(value)
            state[column.name] = value
        return state

    def _detect_dependencies(
        self,
        entity_type: str,
        entity: Any,
    ) -> list[tuple[str, UUID]]:
        """
        Detect dependencies for an entity.

        For example, assignments depend on blocks and persons.
        """
        dependencies = []

        if entity_type == "assignment":
            if hasattr(entity, "block_id") and entity.block_id:
                dependencies.append(("block", entity.block_id))
            if hasattr(entity, "person_id") and entity.person_id:
                dependencies.append(("person", entity.person_id))

        elif entity_type == "absence":
            if hasattr(entity, "person_id") and entity.person_id:
                dependencies.append(("person", entity.person_id))

        elif entity_type == "swap_record":
            if hasattr(entity, "source_faculty_id") and entity.source_faculty_id:
                dependencies.append(("person", entity.source_faculty_id))
            if hasattr(entity, "target_faculty_id") and entity.target_faculty_id:
                dependencies.append(("person", entity.target_faculty_id))

        return dependencies

    def _restore_entity(self, snapshot: EntitySnapshot) -> None:
        """
        Restore entity to snapshot state.

        Args:
            snapshot: EntitySnapshot to restore

        Raises:
            Exception: If restoration fails
        """
        model_class = self.SUPPORTED_ENTITY_TYPES.get(snapshot.entity_type)
        if not model_class:
            raise ValidationError(f"Unsupported entity type: {snapshot.entity_type}")

        # Get current entity
        entity = self.db.query(model_class).filter(
            model_class.id == snapshot.entity_id
        ).first()

        if not entity:
            # Entity was deleted, recreate it
            entity = model_class(id=snapshot.entity_id)
            self.db.add(entity)

        # Restore state
        for key, value in snapshot.state.items():
            if key == "id":
                continue  # Don't overwrite ID

            # Convert string back to proper type if needed
            column = getattr(model_class, key, None)
            if column is not None:
                # Handle datetime conversion
                if "created_at" in key or "updated_at" in key or "_at" in key:
                    if value and isinstance(value, str):
                        try:
                            value = datetime.fromisoformat(value.replace('Z', ''))
                        except Exception:
                            pass

                # Handle UUID conversion
                if "_id" in key and value:
                    try:
                        value = UUID(value) if isinstance(value, str) else value
                    except Exception:
                        pass

                setattr(entity, key, value)

        # Mark entity as modified
        self.db.flush()

    def _resolve_dependencies(
        self,
        snapshots: list[EntitySnapshot],
        entity_ids: list[tuple[str, UUID]],
    ) -> list[EntitySnapshot]:
        """
        Resolve dependencies for cascading rollback.

        Args:
            snapshots: All available snapshots
            entity_ids: Initial entities to rollback

        Returns:
            List of snapshots including dependencies
        """
        # Build dependency graph
        snapshots_to_include = []
        entity_set = set(entity_ids)
        checked = set()

        # BFS to find all dependencies
        queue = list(entity_ids)

        while queue:
            current = queue.pop(0)
            if current in checked:
                continue
            checked.add(current)

            # Find snapshot for this entity
            for snapshot in snapshots:
                if (snapshot.entity_type, snapshot.entity_id) == current:
                    snapshots_to_include.append(snapshot)

                    # Add dependencies to queue
                    for dep in snapshot.dependencies:
                        if dep not in checked:
                            queue.append(dep)
                    break

        return snapshots_to_include

    def _get_entity_current_state(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> dict[str, Any] | None:
        """Get current state of an entity."""
        model_class = self.SUPPORTED_ENTITY_TYPES.get(entity_type)
        if not model_class:
            return None

        entity = self.db.query(model_class).filter(
            model_class.id == entity_id
        ).first()

        if not entity:
            return None

        return self._serialize_entity(entity)

    def _compare_states(
        self,
        state1: dict[str, Any],
        state2: dict[str, Any],
        ignore_fields: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Compare two entity states and return mismatches.

        Args:
            state1: First state (snapshot)
            state2: Second state (current)
            ignore_fields: Fields to ignore in comparison

        Returns:
            List of field mismatches
        """
        ignore_fields = ignore_fields or set()
        mismatches = []

        all_keys = set(state1.keys()) | set(state2.keys())

        for key in all_keys:
            if key in ignore_fields:
                continue

            val1 = state1.get(key)
            val2 = state2.get(key)

            # Normalize for comparison
            if isinstance(val1, str) and isinstance(val2, str):
                val1 = val1.strip()
                val2 = val2.strip()

            if val1 != val2:
                mismatches.append({
                    "field": key,
                    "expected": val1,
                    "actual": val2,
                })

        return mismatches

    def _build_rollback_message(
        self,
        success: bool,
        entities_restored: int,
        entities_failed: int,
        dry_run: bool,
    ) -> str:
        """Build human-readable rollback message."""
        if dry_run:
            return (
                f"Dry run: Would restore {entities_restored} entities, "
                f"{entities_failed} would fail"
            )

        if success:
            return f"Successfully restored {entities_restored} entities"

        if entities_restored > 0:
            return (
                f"Partially completed: {entities_restored} entities restored, "
                f"{entities_failed} failed"
            )

        return f"Rollback failed: {entities_failed} entities could not be restored"

    def _log_rollback_execution(
        self,
        rollback_point: RollbackPoint,
        result: RollbackResult,
        reason: str,
    ) -> None:
        """Log rollback execution for audit trail."""
        logger.info(
            f"Rollback executed - Point: {rollback_point.name} ({rollback_point.id}), "
            f"By: {result.executed_by}, Reason: {reason}, "
            f"Status: {result.status.value}, "
            f"Restored: {len(result.entities_restored)}, "
            f"Failed: {len(result.entities_failed)}"
        )

    # =========================================================================
    # Persistence Methods (Placeholder - implement based on storage choice)
    # =========================================================================

    def _persist_rollback_point(self, rollback_point: RollbackPoint) -> None:
        """
        Persist rollback point to storage.

        This is a placeholder. In production, implement using:
        - Database table (recommended for small snapshots)
        - File system (for large snapshots)
        - Object storage (S3, etc.)
        """
        # For now, store in metadata as JSON
        # In production, use proper storage
        pass

    def _load_rollback_point(self, rollback_point_id: UUID) -> RollbackPoint | None:
        """
        Load rollback point from storage.

        This is a placeholder. Implement based on storage choice.
        """
        # Placeholder - return None for now
        return None

    def _list_persisted_rollback_points(self, limit: int = 100) -> list[RollbackPoint]:
        """
        List persisted rollback points.

        This is a placeholder. Implement based on storage choice.
        """
        # Placeholder - return empty list
        return []

    def _delete_persisted_rollback_point(self, rollback_point_id: UUID) -> None:
        """
        Delete persisted rollback point.

        This is a placeholder. Implement based on storage choice.
        """
        pass
