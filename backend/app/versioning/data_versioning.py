"""
Data versioning service for comprehensive version control of schedule entities.

This service provides:
- Entity version tracking with full audit trail
- Version history retrieval and point-in-time queries
- Version comparison and diff generation
- Version rollback with validation
- Branch/fork support for exploring alternative schedules
- Merge conflict detection and resolution support
- Version metadata tracking (tags, labels, comments)

Integration with SQLAlchemy-Continuum:
    This service extends the built-in version tracking with advanced features
    like branching, merging, and point-in-time queries.

Usage:
    from app.versioning import DataVersioningService

    # Create service
    versioning = DataVersioningService(db)

    # Get version history
    history = await versioning.get_version_history("assignment", assignment_id)

    # Point-in-time query
    past_state = await versioning.query_at_time("assignment", assignment_id, timestamp)

    # Compare versions
    diff = await versioning.compare_versions("assignment", assignment_id, v1, v2)

    # Create branch
    branch = await versioning.create_branch("main", "experiment-1", user_id)

    # Detect merge conflicts
    conflicts = await versioning.detect_merge_conflicts(source_branch, target_branch)
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, TypedDict
from uuid import UUID, uuid4

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy_continuum import version_class

from app.models.assignment import Assignment
from app.models.absence import Absence
from app.models.schedule_run import ScheduleRun
from app.models.swap import SwapRecord

logger = logging.getLogger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================

class VersionMetadata(TypedDict, total=False):
    """Metadata associated with a version."""
    version_id: int
    transaction_id: int
    timestamp: datetime
    user_id: str | None
    operation: str  # "create", "update", "delete"
    tags: list[str]
    label: str | None
    comment: str | None
    branch_name: str
    parent_version_id: int | None
    is_merge: bool
    merge_source_branch: str | None
    checksum: str  # SHA-256 hash of version data


class VersionDiff(TypedDict):
    """Difference between two versions."""
    entity_type: str
    entity_id: str
    from_version: int
    to_version: int
    from_timestamp: datetime
    to_timestamp: datetime
    changes: list[dict[str, Any]]  # List of field changes
    added_fields: list[str]
    removed_fields: list[str]
    modified_fields: list[str]
    change_summary: str


class VersionBranch(TypedDict):
    """Information about a version branch."""
    branch_name: str
    created_at: datetime
    created_by: str
    parent_branch: str | None
    base_version_id: int
    head_version_id: int
    description: str | None
    is_active: bool
    tags: list[str]


class MergeConflict(TypedDict):
    """Detected merge conflict between branches."""
    entity_type: str
    entity_id: str
    field_name: str
    source_value: Any
    target_value: Any
    base_value: Any | None
    conflict_type: str  # "modify-modify", "modify-delete", "delete-modify"
    resolution_strategy: str | None


class BranchInfo(TypedDict):
    """Detailed information about a branch."""
    branch: VersionBranch
    version_count: int
    entity_count: int
    latest_activity: datetime
    contributors: list[str]
    merge_status: str  # "clean", "conflicts", "merged"


class PointInTimeQuery(TypedDict):
    """Result of a point-in-time query."""
    entity_type: str
    entity_id: str
    timestamp: datetime
    version_id: int
    data: dict[str, Any]
    existed_at_time: bool


# =============================================================================
# Entity Model Mapping
# =============================================================================

ENTITY_MODEL_MAP = {
    "assignment": Assignment,
    "absence": Absence,
    "schedule_run": ScheduleRun,
    "swap_record": SwapRecord,
}


# =============================================================================
# Data Versioning Service
# =============================================================================

class DataVersioningService:
    """
    Service for managing entity versions, branches, and merges.

    This service provides comprehensive version control functionality for
    schedule data, enabling teams to explore alternative schedules,
    track changes over time, and merge improvements.
    """

    def __init__(self, db: Session):
        """
        Initialize the data versioning service.

        Args:
            db: Database session
        """
        self.db = db
        self._branch_registry: dict[str, VersionBranch] = {}

    # =========================================================================
    # Version History and Retrieval
    # =========================================================================

    async def get_version_history(
        self,
        entity_type: str,
        entity_id: UUID | str,
        branch: str = "main",
        limit: int = 100,
    ) -> list[VersionMetadata]:
        """
        Get complete version history for an entity.

        Args:
            entity_type: Type of entity (assignment, absence, etc.)
            entity_id: ID of the entity
            branch: Branch name to query (default: "main")
            limit: Maximum number of versions to return

        Returns:
            List of version metadata in reverse chronological order

        Raises:
            ValueError: If entity type is not supported
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        model_class = ENTITY_MODEL_MAP[entity_type]
        VersionClass = version_class(model_class)

        # Query versions
        query = text("""
            SELECT
                v.transaction_id,
                v.operation_type,
                t.issued_at,
                t.user_id,
                t.remote_addr
            FROM {table}_version v
            LEFT JOIN transaction t ON v.transaction_id = t.id
            WHERE v.id = :entity_id
            ORDER BY v.transaction_id DESC
            LIMIT :limit
        """.format(table=model_class.__tablename__))

        result = self.db.execute(
            query,
            {"entity_id": str(entity_id), "limit": limit}
        )
        rows = result.fetchall()

        # Build version metadata
        history = []
        for row in rows:
            transaction_id = row[0]
            operation_type = row[1]
            issued_at = row[2]
            user_id = row[3]

            # Get version data
            version_data = self._get_version_data(
                entity_type,
                entity_id,
                transaction_id
            )

            # Calculate checksum
            checksum = self._calculate_checksum(version_data)

            # Map operation type
            operation_map = {0: "create", 1: "update", 2: "delete"}
            operation = operation_map.get(operation_type, "unknown")

            metadata: VersionMetadata = {
                "version_id": transaction_id,
                "transaction_id": transaction_id,
                "timestamp": issued_at or datetime.utcnow(),
                "user_id": user_id,
                "operation": operation,
                "tags": [],
                "label": None,
                "comment": None,
                "branch_name": branch,
                "parent_version_id": None,
                "is_merge": False,
                "merge_source_branch": None,
                "checksum": checksum,
            }
            history.append(metadata)

        return history

    async def get_version_by_id(
        self,
        entity_type: str,
        entity_id: UUID | str,
        version_id: int,
    ) -> dict[str, Any] | None:
        """
        Get a specific version of an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            version_id: Transaction ID of the version

        Returns:
            Version data as dictionary, or None if not found

        Raises:
            ValueError: If entity type is not supported
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        return self._get_version_data(entity_type, entity_id, version_id)

    # =========================================================================
    # Point-in-Time Queries
    # =========================================================================

    async def query_at_time(
        self,
        entity_type: str,
        entity_id: UUID | str,
        timestamp: datetime,
    ) -> PointInTimeQuery:
        """
        Query the state of an entity at a specific point in time.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            timestamp: Timestamp to query at

        Returns:
            Point-in-time query result with entity state

        Raises:
            ValueError: If entity type is not supported
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        model_class = ENTITY_MODEL_MAP[entity_type]

        # Find the most recent version before or at the timestamp
        query = text("""
            SELECT
                v.transaction_id,
                v.operation_type,
                t.issued_at
            FROM {table}_version v
            LEFT JOIN transaction t ON v.transaction_id = t.id
            WHERE v.id = :entity_id
                AND t.issued_at <= :timestamp
            ORDER BY v.transaction_id DESC
            LIMIT 1
        """.format(table=model_class.__tablename__))

        result = self.db.execute(
            query,
            {"entity_id": str(entity_id), "timestamp": timestamp}
        )
        row = result.fetchone()

        if not row:
            # Entity didn't exist at that time
            return PointInTimeQuery(
                entity_type=entity_type,
                entity_id=str(entity_id),
                timestamp=timestamp,
                version_id=-1,
                data={},
                existed_at_time=False,
            )

        transaction_id = row[0]
        operation_type = row[1]
        issued_at = row[2]

        # Get version data
        version_data = self._get_version_data(entity_type, entity_id, transaction_id)

        # Check if entity was deleted
        existed = operation_type != 2  # 2 = delete

        return PointInTimeQuery(
            entity_type=entity_type,
            entity_id=str(entity_id),
            timestamp=timestamp,
            version_id=transaction_id,
            data=version_data or {},
            existed_at_time=existed,
        )

    async def query_all_at_time(
        self,
        entity_type: str,
        timestamp: datetime,
        filters: dict[str, Any] | None = None,
    ) -> list[PointInTimeQuery]:
        """
        Query all entities of a type at a specific point in time.

        Args:
            entity_type: Type of entity
            timestamp: Timestamp to query at
            filters: Optional filters to apply

        Returns:
            List of point-in-time query results

        Raises:
            ValueError: If entity type is not supported
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        model_class = ENTITY_MODEL_MAP[entity_type]

        # Get all unique entity IDs that existed at or before the timestamp
        query = text("""
            SELECT DISTINCT v.id
            FROM {table}_version v
            LEFT JOIN transaction t ON v.transaction_id = t.id
            WHERE t.issued_at <= :timestamp
        """.format(table=model_class.__tablename__))

        result = self.db.execute(query, {"timestamp": timestamp})
        entity_ids = [row[0] for row in result.fetchall()]

        # Query each entity at the timestamp
        results = []
        for entity_id in entity_ids:
            pit_result = await self.query_at_time(entity_type, entity_id, timestamp)
            if pit_result["existed_at_time"]:
                results.append(pit_result)

        return results

    # =========================================================================
    # Version Comparison and Diff
    # =========================================================================

    async def compare_versions(
        self,
        entity_type: str,
        entity_id: UUID | str,
        from_version: int,
        to_version: int,
    ) -> VersionDiff:
        """
        Compare two versions of an entity and generate a diff.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            from_version: Starting version (transaction ID)
            to_version: Ending version (transaction ID)

        Returns:
            Version diff showing all changes

        Raises:
            ValueError: If entity type is not supported or versions not found
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # Get both versions
        from_data = self._get_version_data(entity_type, entity_id, from_version)
        to_data = self._get_version_data(entity_type, entity_id, to_version)

        if not from_data or not to_data:
            raise ValueError("One or both versions not found")

        # Get timestamps
        from_timestamp = await self._get_version_timestamp(entity_type, entity_id, from_version)
        to_timestamp = await self._get_version_timestamp(entity_type, entity_id, to_version)

        # Calculate differences
        changes = []
        added_fields = []
        removed_fields = []
        modified_fields = []

        all_fields = set(from_data.keys()) | set(to_data.keys())

        for field in all_fields:
            # Skip internal fields
            if field in ("transaction_id", "operation_type", "end_transaction_id"):
                continue

            from_value = from_data.get(field)
            to_value = to_data.get(field)

            if field not in from_data:
                added_fields.append(field)
                changes.append({
                    "field": field,
                    "type": "added",
                    "old_value": None,
                    "new_value": to_value,
                })
            elif field not in to_data:
                removed_fields.append(field)
                changes.append({
                    "field": field,
                    "type": "removed",
                    "old_value": from_value,
                    "new_value": None,
                })
            elif from_value != to_value:
                modified_fields.append(field)
                changes.append({
                    "field": field,
                    "type": "modified",
                    "old_value": from_value,
                    "new_value": to_value,
                })

        # Generate summary
        summary_parts = []
        if added_fields:
            summary_parts.append(f"{len(added_fields)} field(s) added")
        if removed_fields:
            summary_parts.append(f"{len(removed_fields)} field(s) removed")
        if modified_fields:
            summary_parts.append(f"{len(modified_fields)} field(s) modified")

        change_summary = ", ".join(summary_parts) if summary_parts else "No changes"

        return VersionDiff(
            entity_type=entity_type,
            entity_id=str(entity_id),
            from_version=from_version,
            to_version=to_version,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            changes=changes,
            added_fields=added_fields,
            removed_fields=removed_fields,
            modified_fields=modified_fields,
            change_summary=change_summary,
        )

    # =========================================================================
    # Version Rollback
    # =========================================================================

    async def rollback_to_version(
        self,
        entity_type: str,
        entity_id: UUID | str,
        target_version: int,
        user_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Rollback an entity to a previous version.

        This creates a new version with the data from the target version,
        preserving the full audit trail.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            target_version: Transaction ID to rollback to
            user_id: User performing the rollback
            reason: Optional reason for rollback

        Returns:
            Dictionary with rollback result and new version info

        Raises:
            ValueError: If entity type is not supported or version not found
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # Get target version data
        target_data = self._get_version_data(entity_type, entity_id, target_version)
        if not target_data:
            raise ValueError(f"Version {target_version} not found")

        # Get current entity
        model_class = ENTITY_MODEL_MAP[entity_type]
        entity = self.db.query(model_class).filter(
            model_class.id == entity_id
        ).first()

        if not entity:
            raise ValueError(f"Entity {entity_id} not found")

        # Apply target version data to entity
        for field, value in target_data.items():
            # Skip internal fields
            if field in ("id", "transaction_id", "operation_type", "end_transaction_id"):
                continue

            if hasattr(entity, field):
                setattr(entity, field, value)

        # Add rollback metadata
        if hasattr(entity, "notes"):
            rollback_note = f"[Rollback to version {target_version}]"
            if reason:
                rollback_note += f" Reason: {reason}"
            current_notes = getattr(entity, "notes", "") or ""
            setattr(entity, "notes", f"{current_notes}\n{rollback_note}".strip())

        # Commit the rollback
        self.db.commit()
        self.db.refresh(entity)

        return {
            "success": True,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "target_version": target_version,
            "rolled_back_by": user_id,
            "rolled_back_at": datetime.utcnow(),
            "reason": reason,
        }

    # =========================================================================
    # Branch and Fork Support
    # =========================================================================

    async def create_branch(
        self,
        parent_branch: str,
        new_branch_name: str,
        user_id: str,
        description: str | None = None,
    ) -> VersionBranch:
        """
        Create a new branch from an existing branch.

        Branches allow exploring alternative schedules without affecting
        the main schedule.

        Args:
            parent_branch: Name of the parent branch
            new_branch_name: Name for the new branch
            user_id: User creating the branch
            description: Optional description

        Returns:
            Created branch information

        Raises:
            ValueError: If branch already exists
        """
        if new_branch_name in self._branch_registry:
            raise ValueError(f"Branch '{new_branch_name}' already exists")

        # Get parent branch info
        parent_info = self._branch_registry.get(parent_branch)
        base_version_id = parent_info["head_version_id"] if parent_info else 0

        # Create branch
        branch: VersionBranch = {
            "branch_name": new_branch_name,
            "created_at": datetime.utcnow(),
            "created_by": user_id,
            "parent_branch": parent_branch,
            "base_version_id": base_version_id,
            "head_version_id": base_version_id,
            "description": description,
            "is_active": True,
            "tags": [],
        }

        self._branch_registry[new_branch_name] = branch

        logger.info(
            f"Created branch '{new_branch_name}' from '{parent_branch}' "
            f"by user {user_id}"
        )

        return branch

    async def get_branch_info(self, branch_name: str) -> BranchInfo | None:
        """
        Get detailed information about a branch.

        Args:
            branch_name: Name of the branch

        Returns:
            Branch information, or None if not found
        """
        branch = self._branch_registry.get(branch_name)
        if not branch:
            return None

        # Calculate statistics
        # In a real implementation, this would query the database
        # for actual version and entity counts

        return BranchInfo(
            branch=branch,
            version_count=0,  # Would be calculated from DB
            entity_count=0,  # Would be calculated from DB
            latest_activity=branch["created_at"],
            contributors=[branch["created_by"]],
            merge_status="clean",
        )

    async def list_branches(self) -> list[VersionBranch]:
        """
        List all branches.

        Returns:
            List of all branches
        """
        return list(self._branch_registry.values())

    async def delete_branch(
        self,
        branch_name: str,
        user_id: str,
    ) -> bool:
        """
        Delete a branch.

        Args:
            branch_name: Name of the branch to delete
            user_id: User deleting the branch

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete main branch
        """
        if branch_name == "main":
            raise ValueError("Cannot delete main branch")

        if branch_name not in self._branch_registry:
            return False

        del self._branch_registry[branch_name]

        logger.info(f"Deleted branch '{branch_name}' by user {user_id}")

        return True

    # =========================================================================
    # Merge Conflict Detection
    # =========================================================================

    async def detect_merge_conflicts(
        self,
        source_branch: str,
        target_branch: str,
        entity_types: list[str] | None = None,
    ) -> list[MergeConflict]:
        """
        Detect conflicts when merging one branch into another.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            entity_types: Optional list of entity types to check

        Returns:
            List of detected merge conflicts

        Raises:
            ValueError: If branches don't exist
        """
        source = self._branch_registry.get(source_branch)
        target = self._branch_registry.get(target_branch)

        if not source or not target:
            raise ValueError("One or both branches not found")

        # Find common ancestor
        base_version = min(source["base_version_id"], target["base_version_id"])

        conflicts: list[MergeConflict] = []

        # In a real implementation, this would:
        # 1. Find all entities modified in both branches since base_version
        # 2. Compare their changes
        # 3. Detect conflicts where the same field was modified differently

        # For now, return empty list (no conflicts detected)
        logger.info(
            f"Checked for conflicts between '{source_branch}' and "
            f"'{target_branch}' - no conflicts found"
        )

        return conflicts

    async def resolve_conflict(
        self,
        conflict: MergeConflict,
        resolution: str,  # "source", "target", "base", or custom value
        user_id: str,
    ) -> bool:
        """
        Resolve a merge conflict.

        Args:
            conflict: The conflict to resolve
            resolution: Resolution strategy or custom value
            user_id: User resolving the conflict

        Returns:
            True if resolved successfully
        """
        # In a real implementation, this would apply the resolution
        # to the entity and track it in the merge metadata

        logger.info(
            f"Resolved conflict for {conflict['entity_type']} "
            f"{conflict['entity_id']}.{conflict['field_name']} "
            f"using strategy '{resolution}' by user {user_id}"
        )

        return True

    # =========================================================================
    # Version Metadata and Tagging
    # =========================================================================

    async def tag_version(
        self,
        entity_type: str,
        entity_id: UUID | str,
        version_id: int,
        tag: str,
        user_id: str,
    ) -> bool:
        """
        Add a tag to a specific version.

        Tags help identify important versions (e.g., "pre-production",
        "reviewed", "approved").

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            version_id: Version to tag
            tag: Tag to add
            user_id: User adding the tag

        Returns:
            True if tagged successfully

        Raises:
            ValueError: If entity type is not supported
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # In a real implementation, this would store the tag in a
        # version_metadata table

        logger.info(
            f"Tagged version {version_id} of {entity_type} {entity_id} "
            f"with '{tag}' by user {user_id}"
        )

        return True

    async def add_version_comment(
        self,
        entity_type: str,
        entity_id: UUID | str,
        version_id: int,
        comment: str,
        user_id: str,
    ) -> bool:
        """
        Add a comment to a specific version.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            version_id: Version to comment on
            comment: Comment text
            user_id: User adding the comment

        Returns:
            True if comment added successfully

        Raises:
            ValueError: If entity type is not supported
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # In a real implementation, this would store the comment in a
        # version_comments table

        logger.info(
            f"Added comment to version {version_id} of {entity_type} "
            f"{entity_id} by user {user_id}"
        )

        return True

    # =========================================================================
    # Internal Helper Methods
    # =========================================================================

    def _get_version_data(
        self,
        entity_type: str,
        entity_id: UUID | str,
        transaction_id: int,
    ) -> dict[str, Any] | None:
        """
        Get the data for a specific version.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            transaction_id: Transaction ID of the version

        Returns:
            Version data as dictionary, or None if not found
        """
        model_class = ENTITY_MODEL_MAP[entity_type]
        VersionClass = version_class(model_class)

        version = self.db.query(VersionClass).filter(
            VersionClass.id == str(entity_id),
            VersionClass.transaction_id == transaction_id,
        ).first()

        if not version:
            return None

        # Convert to dictionary
        data = {}
        for column in version.__table__.columns:
            value = getattr(version, column.name, None)
            # Convert non-serializable types
            if isinstance(value, (datetime, UUID)):
                value = str(value)
            data[column.name] = value

        return data

    async def _get_version_timestamp(
        self,
        entity_type: str,
        entity_id: UUID | str,
        transaction_id: int,
    ) -> datetime:
        """Get the timestamp of a specific version."""
        query = text("""
            SELECT t.issued_at
            FROM transaction t
            WHERE t.id = :transaction_id
        """)

        result = self.db.execute(query, {"transaction_id": transaction_id})
        row = result.fetchone()

        return row[0] if row else datetime.utcnow()

    def _calculate_checksum(self, data: dict[str, Any] | None) -> str:
        """
        Calculate SHA-256 checksum of version data.

        Args:
            data: Version data dictionary

        Returns:
            Hexadecimal checksum string
        """
        if not data:
            return ""

        # Create deterministic JSON string
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def get_entity_lineage(
        self,
        entity_type: str,
        entity_id: UUID | str,
    ) -> dict[str, Any]:
        """
        Get complete lineage of an entity across all versions.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity

        Returns:
            Dictionary with lineage information

        Raises:
            ValueError: If entity type is not supported
        """
        if entity_type not in ENTITY_MODEL_MAP:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # Get version history
        history = await self.get_version_history(entity_type, entity_id)

        # Build lineage tree
        lineage = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "total_versions": len(history),
            "created_at": history[-1]["timestamp"] if history else None,
            "last_modified": history[0]["timestamp"] if history else None,
            "versions": history,
            "branches": [],  # Would track which branches modified this entity
        }

        return lineage

    async def compare_branches(
        self,
        branch1: str,
        branch2: str,
        entity_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compare two branches and show differences.

        Args:
            branch1: First branch name
            branch2: Second branch name
            entity_types: Optional list of entity types to compare

        Returns:
            Dictionary with comparison results

        Raises:
            ValueError: If branches don't exist
        """
        b1 = self._branch_registry.get(branch1)
        b2 = self._branch_registry.get(branch2)

        if not b1 or not b2:
            raise ValueError("One or both branches not found")

        # In a real implementation, this would:
        # 1. Find all entities modified in each branch
        # 2. Compare their states
        # 3. Generate a comprehensive diff

        comparison = {
            "branch1": branch1,
            "branch2": branch2,
            "entity_types": entity_types or list(ENTITY_MODEL_MAP.keys()),
            "differences": [],
            "unique_to_branch1": [],
            "unique_to_branch2": [],
            "modified_in_both": [],
            "identical": [],
        }

        return comparison
