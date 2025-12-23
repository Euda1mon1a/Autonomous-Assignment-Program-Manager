"""
Snapshot Store Service for Event Sourcing

Provides aggregate state snapshots to optimize event replay performance.
Instead of replaying thousands of events, we restore from the latest snapshot
and only replay events since that snapshot.

Key Features:
- Automatic snapshot creation based on event count thresholds
- Snapshot compression to reduce storage costs
- Snapshot versioning for schema evolution
- Snapshot validation to ensure data integrity
- Cleanup policies for old snapshots
- Restore from snapshot with incremental event replay

Architecture:
    Event Store (1...N events) → Snapshot → Quick Restore + Incremental Replay

Benefits:
- Faster aggregate reconstruction (O(log n) vs O(n))
- Reduced database load during event replay
- Archival of aggregate state at specific points in time

Usage:
    from app.events.snapshot_store import SnapshotStore

    # Create snapshot
    snapshot_store = SnapshotStore(db)
    snapshot_id = await snapshot_store.create_snapshot(
        aggregate_id="schedule-123",
        aggregate_type="Schedule",
        state_data={"assignments": [...], "blocks": [...]}
    )

    # Restore from snapshot
    state = await snapshot_store.restore_from_snapshot(
        aggregate_id="schedule-123"
    )
"""

import gzip
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.events.event_store import EventSnapshot, EventStore

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


class SnapshotConfig(BaseModel):
    """
    Configuration for snapshot creation and management.

    Controls when snapshots are created and how they're maintained.
    """

    # Frequency settings
    snapshot_frequency_events: int = Field(
        100, ge=1, description="Create snapshot every N events (default: 100)"
    )
    snapshot_frequency_time_hours: int = Field(
        24, ge=1, description="Create snapshot every N hours (default: 24)"
    )
    min_events_for_snapshot: int = Field(
        10, ge=1, description="Minimum events before first snapshot (default: 10)"
    )

    # Compression settings
    enable_compression: bool = Field(
        True, description="Enable gzip compression for snapshots"
    )
    compression_level: int = Field(
        6, ge=1, le=9, description="Gzip compression level (1-9, default: 6)"
    )
    compression_threshold_bytes: int = Field(
        1024, ge=0, description="Only compress snapshots larger than this (bytes)"
    )

    # Versioning settings
    snapshot_version: int = Field(
        1, ge=1, description="Current snapshot schema version"
    )
    validate_on_restore: bool = Field(
        True, description="Validate snapshot data when restoring"
    )

    # Cleanup policies
    max_snapshots_per_aggregate: int = Field(
        10, ge=1, description="Maximum snapshots to keep per aggregate"
    )
    snapshot_retention_days: int = Field(
        90, ge=1, description="Delete snapshots older than this (days)"
    )
    auto_cleanup_enabled: bool = Field(
        True, description="Automatically cleanup old snapshots"
    )

    # Performance settings
    parallel_snapshot_creation: bool = Field(
        False, description="Allow parallel snapshot creation (requires locking)"
    )
    snapshot_creation_timeout_seconds: int = Field(
        300, ge=1, description="Timeout for snapshot creation (seconds)"
    )

    class Config:
        frozen = True


# Default configuration
DEFAULT_SNAPSHOT_CONFIG = SnapshotConfig()


# =============================================================================
# Snapshot Metadata and Validation
# =============================================================================


class SnapshotMetadata(BaseModel):
    """
    Metadata for a snapshot.

    Provides information about snapshot creation, compression, and validation.
    """

    snapshot_id: str
    aggregate_id: str
    aggregate_type: str
    aggregate_version: int
    event_count: int
    snapshot_version: int = 1
    created_at: datetime
    created_by: str | None = None

    # Compression info
    is_compressed: bool = False
    original_size_bytes: int = 0
    compressed_size_bytes: int = 0
    compression_ratio: float = 1.0

    # Validation info
    checksum: str
    is_validated: bool = False
    validation_timestamp: datetime | None = None

    class Config:
        from_attributes = True


class SnapshotValidationResult(BaseModel):
    """
    Result of snapshot validation.

    Indicates whether a snapshot is valid and can be safely restored.
    """

    is_valid: bool
    snapshot_id: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    checksum_verified: bool = False
    schema_version_compatible: bool = False


# =============================================================================
# Snapshot Store Service
# =============================================================================


class SnapshotStore:
    """
    Snapshot Store for managing aggregate state snapshots.

    Provides high-level interface for creating, storing, retrieving,
    and managing snapshots for event-sourced aggregates.
    """

    def __init__(self, db: Session, config: SnapshotConfig | None = None):
        """
        Initialize Snapshot Store.

        Args:
            db: Database session
            config: Optional snapshot configuration (uses defaults if not provided)
        """
        self.db = db
        self.config = config or DEFAULT_SNAPSHOT_CONFIG
        self.event_store = EventStore(db)

    async def create_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        state_data: dict[str, Any],
        created_by: str | None = None,
        force: bool = False,
    ) -> str:
        """
        Create a snapshot of aggregate state.

        Args:
            aggregate_id: ID of the aggregate
            aggregate_type: Type of the aggregate (e.g., "Schedule", "Assignment")
            state_data: Current state of the aggregate
            created_by: User creating the snapshot (optional)
            force: Force snapshot creation even if frequency rules not met

        Returns:
            Snapshot ID (UUID)

        Raises:
            ValueError: If state_data is invalid or empty
        """
        if not state_data:
            raise ValueError("Cannot create snapshot with empty state data")

        # Check if snapshot is needed (unless forced)
        if not force and not await self._should_create_snapshot(
            aggregate_id, aggregate_type
        ):
            logger.debug(
                f"Snapshot not needed for {aggregate_type}:{aggregate_id} "
                "(frequency threshold not met)"
            )
            # Return ID of latest snapshot if exists
            latest = await self.get_latest_snapshot_metadata(aggregate_id)
            if latest:
                return latest.snapshot_id
            # If no snapshot exists, continue with creation
            logger.info("No existing snapshot found, creating first snapshot")

        # Get current aggregate version and event count
        current_version = self.event_store._get_aggregate_version(
            aggregate_id, aggregate_type
        )
        event_count = self.event_store._get_event_count(aggregate_id)

        # Serialize and optionally compress data
        serialized_data = json.dumps(state_data, default=str)
        original_size = len(serialized_data.encode("utf-8"))

        snapshot_data = state_data
        is_compressed = False
        compressed_size = original_size

        if (
            self.config.enable_compression
            and original_size > self.config.compression_threshold_bytes
        ):
            try:
                compressed_data = self._compress_data(serialized_data)
                compressed_size = len(compressed_data)
                snapshot_data = {
                    "_compressed": True,
                    "_data": compressed_data.hex(),
                    "_original_size": original_size,
                }
                is_compressed = True
                logger.debug(
                    f"Snapshot compressed: {original_size} → {compressed_size} bytes "
                    f"({compressed_size / original_size * 100:.1f}%)"
                )
            except Exception as e:
                logger.warning(f"Compression failed, storing uncompressed: {e}")
                snapshot_data = state_data
                is_compressed = False

        # Calculate checksum
        checksum = self._calculate_checksum(serialized_data)

        # Create snapshot record
        snapshot = EventSnapshot(
            id=uuid.uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            aggregate_version=current_version,
            snapshot_data=snapshot_data,
            event_count=event_count,
            created_by=created_by,
            snapshot_timestamp=datetime.utcnow(),
        )

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        # Store metadata separately for quick access
        metadata = {
            "snapshot_version": self.config.snapshot_version,
            "is_compressed": is_compressed,
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "compression_ratio": compressed_size / original_size
            if original_size > 0
            else 1.0,
            "checksum": checksum,
        }

        # Update snapshot with metadata (stored in snapshot_data)
        snapshot_data_with_meta = dict(snapshot.snapshot_data)
        snapshot_data_with_meta["_metadata"] = metadata
        snapshot.snapshot_data = snapshot_data_with_meta
        self.db.commit()

        logger.info(
            f"Snapshot created for {aggregate_type}:{aggregate_id} "
            f"(id={snapshot.id}, version={current_version}, "
            f"events={event_count}, size={compressed_size} bytes)"
        )

        # Cleanup old snapshots if enabled
        if self.config.auto_cleanup_enabled:
            await self._cleanup_old_snapshots(aggregate_id)

        return str(snapshot.id)

    async def get_latest_snapshot(
        self,
        aggregate_id: str,
        validate: bool = True,
    ) -> dict[str, Any] | None:
        """
        Get the latest snapshot for an aggregate.

        Args:
            aggregate_id: ID of the aggregate
            validate: Whether to validate snapshot before returning

        Returns:
            Snapshot data dictionary or None if no snapshot exists

        Raises:
            ValueError: If snapshot is invalid and validation is enabled
        """
        snapshot = (
            self.db.query(EventSnapshot)
            .filter(EventSnapshot.aggregate_id == aggregate_id)
            .order_by(desc(EventSnapshot.aggregate_version))
            .first()
        )

        if not snapshot:
            return None

        # Validate if requested
        if validate and self.config.validate_on_restore:
            validation = await self.validate_snapshot(str(snapshot.id))
            if not validation.is_valid:
                raise ValueError(
                    f"Snapshot {snapshot.id} validation failed: "
                    f"{', '.join(validation.errors)}"
                )

        # Extract and decompress data
        snapshot_data = snapshot.snapshot_data
        metadata = snapshot_data.get("_metadata", {})

        # Handle compressed data
        if snapshot_data.get("_compressed", False):
            try:
                compressed_hex = snapshot_data["_data"]
                compressed_bytes = bytes.fromhex(compressed_hex)
                decompressed = self._decompress_data(compressed_bytes)
                actual_data = json.loads(decompressed)
            except Exception as e:
                logger.error(f"Failed to decompress snapshot {snapshot.id}: {e}")
                raise ValueError(f"Snapshot decompression failed: {e}")
        else:
            # Remove metadata keys from actual data
            actual_data = {
                k: v for k, v in snapshot_data.items() if not k.startswith("_")
            }

        return {
            "snapshot_id": str(snapshot.id),
            "aggregate_id": snapshot.aggregate_id,
            "aggregate_type": snapshot.aggregate_type,
            "aggregate_version": snapshot.aggregate_version,
            "event_count": snapshot.event_count,
            "snapshot_timestamp": snapshot.snapshot_timestamp,
            "data": actual_data,
            "metadata": metadata,
        }

    async def restore_from_snapshot(
        self,
        aggregate_id: str,
        include_events_after_snapshot: bool = True,
    ) -> dict[str, Any] | None:
        """
        Restore aggregate state from latest snapshot with incremental replay.

        This is the main optimization: instead of replaying ALL events,
        we restore from snapshot and only replay events since snapshot.

        Args:
            aggregate_id: ID of the aggregate to restore
            include_events_after_snapshot: If True, replay events after snapshot

        Returns:
            Complete current state of aggregate or None if no snapshot exists

        Example:
            # Without snapshot: Replay 10,000 events (slow)
            # With snapshot: Restore snapshot + replay 100 events (fast)
        """
        # Get latest snapshot
        snapshot_result = await self.get_latest_snapshot(aggregate_id, validate=True)

        if not snapshot_result:
            logger.debug(f"No snapshot found for aggregate {aggregate_id}")
            return None

        snapshot_version = snapshot_result["aggregate_version"]
        state = snapshot_result["data"]

        logger.info(
            f"Restored snapshot for {aggregate_id} at version {snapshot_version}"
        )

        # If requested, replay events after snapshot
        if include_events_after_snapshot:
            events_after_snapshot = await self.event_store.get_events(
                aggregate_id=aggregate_id,
                from_version=snapshot_version + 1,
            )

            if events_after_snapshot:
                logger.info(
                    f"Replaying {len(events_after_snapshot)} events "
                    f"after snapshot for {aggregate_id}"
                )

                # Note: Actual event replay logic would be implemented
                # by the specific aggregate type. We just return the data
                # and event count for the caller to handle replay.
                state["_events_replayed"] = len(events_after_snapshot)
                state["_events_after_snapshot"] = [
                    event.to_dict() for event in events_after_snapshot
                ]

        return {
            "aggregate_id": aggregate_id,
            "restored_from_snapshot": snapshot_result["snapshot_id"],
            "snapshot_version": snapshot_version,
            "current_state": state,
            "events_replayed": len(events_after_snapshot)
            if include_events_after_snapshot
            else 0,
        }

    async def get_snapshot_by_id(
        self,
        snapshot_id: str,
    ) -> dict[str, Any] | None:
        """
        Get a specific snapshot by ID.

        Args:
            snapshot_id: UUID of the snapshot

        Returns:
            Snapshot data or None if not found
        """
        snapshot = (
            self.db.query(EventSnapshot).filter(EventSnapshot.id == snapshot_id).first()
        )

        if not snapshot:
            return None

        return await self._deserialize_snapshot(snapshot)

    async def get_latest_snapshot_metadata(
        self,
        aggregate_id: str,
    ) -> SnapshotMetadata | None:
        """
        Get metadata for the latest snapshot without loading data.

        Useful for checking if snapshot exists and getting info.

        Args:
            aggregate_id: ID of the aggregate

        Returns:
            Snapshot metadata or None
        """
        snapshot = (
            self.db.query(EventSnapshot)
            .filter(EventSnapshot.aggregate_id == aggregate_id)
            .order_by(desc(EventSnapshot.aggregate_version))
            .first()
        )

        if not snapshot:
            return None

        metadata_dict = snapshot.snapshot_data.get("_metadata", {})

        return SnapshotMetadata(
            snapshot_id=str(snapshot.id),
            aggregate_id=snapshot.aggregate_id,
            aggregate_type=snapshot.aggregate_type,
            aggregate_version=snapshot.aggregate_version,
            event_count=snapshot.event_count,
            snapshot_version=metadata_dict.get("snapshot_version", 1),
            created_at=snapshot.snapshot_timestamp,
            created_by=snapshot.created_by,
            is_compressed=metadata_dict.get("is_compressed", False),
            original_size_bytes=metadata_dict.get("original_size_bytes", 0),
            compressed_size_bytes=metadata_dict.get("compressed_size_bytes", 0),
            compression_ratio=metadata_dict.get("compression_ratio", 1.0),
            checksum=metadata_dict.get("checksum", ""),
            is_validated=False,
        )

    async def validate_snapshot(
        self,
        snapshot_id: str,
    ) -> SnapshotValidationResult:
        """
        Validate a snapshot for integrity and compatibility.

        Checks:
        - Snapshot exists
        - Data can be deserialized
        - Checksum matches (if available)
        - Schema version is compatible
        - Required fields are present

        Args:
            snapshot_id: UUID of snapshot to validate

        Returns:
            Validation result with any errors or warnings
        """
        errors = []
        warnings = []
        checksum_verified = False
        schema_compatible = False

        # Get snapshot
        snapshot = (
            self.db.query(EventSnapshot).filter(EventSnapshot.id == snapshot_id).first()
        )

        if not snapshot:
            errors.append(f"Snapshot {snapshot_id} not found")
            return SnapshotValidationResult(
                is_valid=False,
                snapshot_id=snapshot_id,
                errors=errors,
                warnings=warnings,
            )

        # Extract metadata
        snapshot_data = snapshot.snapshot_data
        metadata = snapshot_data.get("_metadata", {})

        # Validate required fields
        if not snapshot.aggregate_id:
            errors.append("Missing aggregate_id")
        if not snapshot.aggregate_type:
            errors.append("Missing aggregate_type")
        if snapshot.aggregate_version < 0:
            errors.append("Invalid aggregate_version")

        # Validate schema version compatibility
        snapshot_version = metadata.get("snapshot_version", 1)
        if snapshot_version > self.config.snapshot_version:
            errors.append(
                f"Snapshot version {snapshot_version} is newer than "
                f"current version {self.config.snapshot_version}"
            )
        elif snapshot_version < self.config.snapshot_version:
            warnings.append(
                f"Snapshot version {snapshot_version} is older than "
                f"current version {self.config.snapshot_version}. "
                "Migration may be needed."
            )
            schema_compatible = True
        else:
            schema_compatible = True

        # Validate checksum if available
        stored_checksum = metadata.get("checksum")
        if stored_checksum:
            try:
                # Decompress if needed
                if snapshot_data.get("_compressed", False):
                    compressed_hex = snapshot_data["_data"]
                    compressed_bytes = bytes.fromhex(compressed_hex)
                    decompressed = self._decompress_data(compressed_bytes)
                    calculated_checksum = self._calculate_checksum(decompressed)
                else:
                    # Remove metadata for checksum calculation
                    actual_data = {
                        k: v for k, v in snapshot_data.items() if not k.startswith("_")
                    }
                    calculated_checksum = self._calculate_checksum(
                        json.dumps(actual_data, default=str)
                    )

                if calculated_checksum == stored_checksum:
                    checksum_verified = True
                else:
                    errors.append(
                        f"Checksum mismatch: expected {stored_checksum}, "
                        f"got {calculated_checksum}"
                    )
            except Exception as e:
                errors.append(f"Checksum validation failed: {e}")
        else:
            warnings.append("No checksum available for verification")

        # Validate data can be deserialized
        try:
            await self._deserialize_snapshot(snapshot)
        except Exception as e:
            errors.append(f"Failed to deserialize snapshot data: {e}")

        is_valid = len(errors) == 0

        return SnapshotValidationResult(
            is_valid=is_valid,
            snapshot_id=snapshot_id,
            errors=errors,
            warnings=warnings,
            checksum_verified=checksum_verified,
            schema_version_compatible=schema_compatible,
        )

    async def delete_snapshot(
        self,
        snapshot_id: str,
    ) -> bool:
        """
        Delete a specific snapshot.

        Args:
            snapshot_id: UUID of snapshot to delete

        Returns:
            True if deleted, False if not found
        """
        snapshot = (
            self.db.query(EventSnapshot).filter(EventSnapshot.id == snapshot_id).first()
        )

        if not snapshot:
            return False

        self.db.delete(snapshot)
        self.db.commit()

        logger.info(f"Deleted snapshot {snapshot_id}")
        return True

    async def cleanup_old_snapshots(
        self,
        aggregate_id: str,
    ) -> int:
        """
        Cleanup old snapshots for an aggregate based on retention policies.

        Applies both count-based and time-based retention policies.

        Args:
            aggregate_id: ID of the aggregate

        Returns:
            Number of snapshots deleted
        """
        return await self._cleanup_old_snapshots(aggregate_id)

    async def get_snapshot_statistics(
        self,
        aggregate_id: str | None = None,
        aggregate_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Get statistics about snapshots.

        Args:
            aggregate_id: Optional filter by aggregate ID
            aggregate_type: Optional filter by aggregate type

        Returns:
            Dictionary with snapshot statistics
        """
        query = self.db.query(EventSnapshot)

        if aggregate_id:
            query = query.filter(EventSnapshot.aggregate_id == aggregate_id)
        if aggregate_type:
            query = query.filter(EventSnapshot.aggregate_type == aggregate_type)

        total_snapshots = query.count()

        if total_snapshots == 0:
            return {
                "total_snapshots": 0,
                "aggregates_with_snapshots": 0,
                "oldest_snapshot": None,
                "newest_snapshot": None,
                "average_events_per_snapshot": 0.0,
            }

        # Aggregate statistics
        oldest_snapshot = query.order_by(EventSnapshot.snapshot_timestamp).first()
        newest_snapshot = query.order_by(desc(EventSnapshot.snapshot_timestamp)).first()

        avg_events = (
            self.db.query(func.avg(EventSnapshot.event_count))
            .filter(query.whereclause if hasattr(query, "whereclause") else True)
            .scalar()
            or 0.0
        )

        unique_aggregates = (
            self.db.query(func.count(func.distinct(EventSnapshot.aggregate_id)))
            .filter(query.whereclause if hasattr(query, "whereclause") else True)
            .scalar()
            or 0
        )

        return {
            "total_snapshots": total_snapshots,
            "aggregates_with_snapshots": unique_aggregates,
            "oldest_snapshot": oldest_snapshot.snapshot_timestamp
            if oldest_snapshot
            else None,
            "newest_snapshot": newest_snapshot.snapshot_timestamp
            if newest_snapshot
            else None,
            "average_events_per_snapshot": float(avg_events),
        }

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _should_create_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
    ) -> bool:
        """
        Determine if a snapshot should be created based on frequency rules.

        Args:
            aggregate_id: ID of the aggregate
            aggregate_type: Type of the aggregate

        Returns:
            True if snapshot should be created
        """
        # Get latest snapshot
        latest_snapshot = (
            self.db.query(EventSnapshot)
            .filter(EventSnapshot.aggregate_id == aggregate_id)
            .order_by(desc(EventSnapshot.aggregate_version))
            .first()
        )

        # Get current event count
        current_event_count = self.event_store._get_event_count(aggregate_id)

        # If no snapshot exists, check minimum events threshold
        if not latest_snapshot:
            return current_event_count >= self.config.min_events_for_snapshot

        # Check event count threshold
        events_since_snapshot = current_event_count - latest_snapshot.event_count
        if events_since_snapshot >= self.config.snapshot_frequency_events:
            logger.debug(
                f"Snapshot needed: {events_since_snapshot} events since last snapshot "
                f"(threshold: {self.config.snapshot_frequency_events})"
            )
            return True

        # Check time threshold
        time_since_snapshot = datetime.utcnow() - latest_snapshot.snapshot_timestamp
        hours_since_snapshot = time_since_snapshot.total_seconds() / 3600
        if hours_since_snapshot >= self.config.snapshot_frequency_time_hours:
            logger.debug(
                f"Snapshot needed: {hours_since_snapshot:.1f} hours since last snapshot "
                f"(threshold: {self.config.snapshot_frequency_time_hours})"
            )
            return True

        return False

    async def _cleanup_old_snapshots(
        self,
        aggregate_id: str,
    ) -> int:
        """
        Cleanup old snapshots based on retention policies.

        Args:
            aggregate_id: ID of the aggregate

        Returns:
            Number of snapshots deleted
        """
        deleted_count = 0

        # Count-based cleanup: Keep only N most recent snapshots
        all_snapshots = (
            self.db.query(EventSnapshot)
            .filter(EventSnapshot.aggregate_id == aggregate_id)
            .order_by(desc(EventSnapshot.aggregate_version))
            .all()
        )

        if len(all_snapshots) > self.config.max_snapshots_per_aggregate:
            snapshots_to_delete = all_snapshots[
                self.config.max_snapshots_per_aggregate :
            ]
            for snapshot in snapshots_to_delete:
                self.db.delete(snapshot)
                deleted_count += 1

        # Time-based cleanup: Delete snapshots older than retention period
        cutoff_date = datetime.utcnow() - timedelta(
            days=self.config.snapshot_retention_days
        )
        old_snapshots = (
            self.db.query(EventSnapshot)
            .filter(
                and_(
                    EventSnapshot.aggregate_id == aggregate_id,
                    EventSnapshot.snapshot_timestamp < cutoff_date,
                )
            )
            .all()
        )

        for snapshot in old_snapshots:
            # Don't delete if it's one of the most recent N snapshots
            if snapshot not in all_snapshots[: self.config.max_snapshots_per_aggregate]:
                self.db.delete(snapshot)
                deleted_count += 1

        if deleted_count > 0:
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old snapshots for {aggregate_id}")

        return deleted_count

    def _compress_data(self, data: str) -> bytes:
        """
        Compress data using gzip.

        Args:
            data: String data to compress

        Returns:
            Compressed bytes
        """
        return gzip.compress(
            data.encode("utf-8"), compresslevel=self.config.compression_level
        )

    def _decompress_data(self, data: bytes) -> str:
        """
        Decompress gzip data.

        Args:
            data: Compressed bytes

        Returns:
            Decompressed string
        """
        return gzip.decompress(data).decode("utf-8")

    def _calculate_checksum(self, data: str) -> str:
        """
        Calculate SHA-256 checksum of data.

        Args:
            data: String data to checksum

        Returns:
            Hex-encoded checksum
        """
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    async def _deserialize_snapshot(
        self,
        snapshot: EventSnapshot,
    ) -> dict[str, Any]:
        """
        Deserialize snapshot data.

        Args:
            snapshot: EventSnapshot database record

        Returns:
            Deserialized snapshot data
        """
        snapshot_data = snapshot.snapshot_data

        # Handle compressed data
        if snapshot_data.get("_compressed", False):
            compressed_hex = snapshot_data["_data"]
            compressed_bytes = bytes.fromhex(compressed_hex)
            decompressed = self._decompress_data(compressed_bytes)
            actual_data = json.loads(decompressed)
        else:
            # Remove metadata keys
            actual_data = {
                k: v for k, v in snapshot_data.items() if not k.startswith("_")
            }

        return {
            "snapshot_id": str(snapshot.id),
            "aggregate_id": snapshot.aggregate_id,
            "aggregate_type": snapshot.aggregate_type,
            "aggregate_version": snapshot.aggregate_version,
            "event_count": snapshot.event_count,
            "snapshot_timestamp": snapshot.snapshot_timestamp,
            "data": actual_data,
        }


# =============================================================================
# Factory Function
# =============================================================================


def get_snapshot_store(
    db: Session, config: SnapshotConfig | None = None
) -> SnapshotStore:
    """
    Get SnapshotStore instance.

    Args:
        db: Database session
        config: Optional snapshot configuration

    Returns:
        SnapshotStore instance
    """
    return SnapshotStore(db, config)


# =============================================================================
# Utility Functions
# =============================================================================


async def auto_snapshot_aggregate(
    db: Session,
    aggregate_id: str,
    aggregate_type: str,
    state_data: dict[str, Any],
    created_by: str | None = None,
) -> str | None:
    """
    Automatically create snapshot if needed based on frequency rules.

    Convenience function that checks if snapshot is needed and creates it.

    Args:
        db: Database session
        aggregate_id: ID of the aggregate
        aggregate_type: Type of the aggregate
        state_data: Current state data
        created_by: User creating snapshot (optional)

    Returns:
        Snapshot ID if created, None if not needed
    """
    snapshot_store = SnapshotStore(db)

    # This will only create snapshot if frequency rules are met
    try:
        snapshot_id = await snapshot_store.create_snapshot(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            state_data=state_data,
            created_by=created_by,
            force=False,  # Respect frequency rules
        )
        return snapshot_id
    except Exception as e:
        logger.error(f"Auto-snapshot failed for {aggregate_id}: {e}")
        return None


async def cleanup_all_old_snapshots(
    db: Session,
    config: SnapshotConfig | None = None,
) -> dict[str, Any]:
    """
    Cleanup old snapshots for all aggregates.

    Useful for scheduled maintenance tasks.

    Args:
        db: Database session
        config: Optional snapshot configuration

    Returns:
        Statistics about cleanup operation
    """
    snapshot_store = SnapshotStore(db, config)

    # Get all unique aggregate IDs
    unique_aggregates = db.query(EventSnapshot.aggregate_id).distinct().all()

    total_deleted = 0
    aggregates_cleaned = 0

    for (aggregate_id,) in unique_aggregates:
        deleted = await snapshot_store.cleanup_old_snapshots(aggregate_id)
        if deleted > 0:
            total_deleted += deleted
            aggregates_cleaned += 1

    logger.info(
        f"Cleanup complete: deleted {total_deleted} snapshots "
        f"from {aggregates_cleaned} aggregates"
    )

    return {
        "total_snapshots_deleted": total_deleted,
        "aggregates_cleaned": aggregates_cleaned,
        "total_aggregates": len(unique_aggregates),
    }
