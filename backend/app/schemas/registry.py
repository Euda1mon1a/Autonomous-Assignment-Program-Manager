"""
Schema registry service for managing Pydantic schema versions.

This module provides a comprehensive schema registry for the Residency Scheduler,
enabling schema versioning, compatibility validation, evolution tracking, and
documentation generation.

Key features:
- Schema registration and storage
- Semantic versioning with compatibility checks
- Forward/backward compatibility validation
- Schema lookup by name and version
- Deprecation and lifecycle management
- Automatic documentation generation
- Change notifications

Usage:
    from app.schemas.registry import SchemaRegistry
    from app.db.session import get_db

    db = next(get_db())
    registry = SchemaRegistry(db)

    # Register a new schema version
    result = await registry.register_schema(
        name="PersonCreate",
        schema_definition={"type": "object", "properties": {...}},
        version=2,
        compatibility_type="backward",
        description="Added email validation",
        created_by="user123"
    )

    # Get the latest version
    schema = await registry.get_schema("PersonCreate")

    # Get a specific version
    schema = await registry.get_schema("PersonCreate", version=1)

    # Check compatibility
    is_compatible = await registry.check_compatibility(
        "PersonCreate",
        new_schema_definition,
        "backward"
    )
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.schema_version import (
    SchemaChangeEvent,
    SchemaCompatibilityType,
    SchemaStatus,
    SchemaVersion,
)

logger = logging.getLogger(__name__)


# Pydantic schemas for API
class SchemaRegistrationRequest(BaseModel):
    """Request to register a new schema version."""
    name: str = Field(..., description="Schema name")
    version: int = Field(..., gt=0, description="Version number")
    schema_definition: dict[str, Any] = Field(..., description="JSON schema definition")
    compatibility_type: str = Field(
        default="backward",
        description="Compatibility type: none, backward, forward, full, transitive"
    )
    description: str | None = Field(None, description="Schema description")
    changelog: str | None = Field(None, description="Changes from previous version")
    migration_notes: str | None = Field(None, description="Migration instructions")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    created_by: str | None = Field(None, description="User ID")


class SchemaResponse(BaseModel):
    """Response schema for schema version."""
    id: UUID
    name: str
    version: int
    schema_definition: dict[str, Any]
    compatibility_type: str
    status: str
    is_default: bool
    deprecated_at: datetime | None = None
    archived_at: datetime | None = None
    removed_at: datetime | None = None
    description: str | None = None
    changelog: str | None = None
    migration_notes: str | None = None
    tags: list[str]
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchemaCompatibilityResult(BaseModel):
    """Result of schema compatibility check."""
    compatible: bool
    compatibility_type: str
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class SchemaDocumentation(BaseModel):
    """Generated documentation for a schema."""
    name: str
    current_version: int
    total_versions: int
    description: str | None
    fields: list[dict[str, Any]]
    compatibility_history: list[dict[str, Any]]
    deprecation_info: dict[str, Any] | None
    examples: list[dict[str, Any]] = Field(default_factory=list)
    migration_guides: list[dict[str, Any]] = Field(default_factory=list)


class SchemaEvolutionRule:
    """
    Rules for schema evolution based on compatibility type.

    Defines what changes are allowed for each compatibility type to maintain
    backward and forward compatibility guarantees.
    """

    @staticmethod
    def validate_backward_compatibility(
        old_schema: dict[str, Any],
        new_schema: dict[str, Any]
    ) -> list[str]:
        """
        Validate backward compatibility (new schema can read old data).

        Allowed changes:
        - Add optional fields
        - Remove required constraints
        - Widen types (e.g., int -> number)
        - Add enum values

        Disallowed changes:
        - Remove fields
        - Add required fields
        - Narrow types
        - Remove enum values

        Args:
            old_schema: Previous schema definition
            new_schema: New schema definition

        Returns:
            List of violation messages (empty if compatible)
        """
        violations = []

        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        # Check for removed fields
        removed_fields = set(old_props.keys()) - set(new_props.keys())
        if removed_fields:
            violations.append(
                f"Backward incompatible: Removed fields {removed_fields}"
            )

        # Check for new required fields
        new_required_fields = new_required - old_required
        if new_required_fields:
            violations.append(
                f"Backward incompatible: Added required fields {new_required_fields}"
            )

        # Check for type narrowing
        for field_name in old_props:
            if field_name in new_props:
                old_type = old_props[field_name].get("type")
                new_type = new_props[field_name].get("type")

                if old_type and new_type and old_type != new_type:
                    # Check if type change is compatible
                    if not SchemaEvolutionRule._is_type_widening(old_type, new_type):
                        violations.append(
                            f"Backward incompatible: Type changed for field "
                            f"'{field_name}' from {old_type} to {new_type}"
                        )

        return violations

    @staticmethod
    def validate_forward_compatibility(
        old_schema: dict[str, Any],
        new_schema: dict[str, Any]
    ) -> list[str]:
        """
        Validate forward compatibility (old schema can read new data).

        Allowed changes:
        - Remove optional fields
        - Add required constraints
        - Narrow types

        Disallowed changes:
        - Add fields
        - Remove required fields
        - Widen types

        Args:
            old_schema: Previous schema definition
            new_schema: New schema definition

        Returns:
            List of violation messages (empty if compatible)
        """
        violations = []

        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        # Check for new fields
        new_fields = set(new_props.keys()) - set(old_props.keys())
        if new_fields:
            violations.append(
                f"Forward incompatible: Added fields {new_fields}"
            )

        # Check for removed required fields
        removed_required = old_required - new_required
        if removed_required:
            violations.append(
                f"Forward incompatible: Removed required constraints from "
                f"{removed_required}"
            )

        return violations

    @staticmethod
    def validate_full_compatibility(
        old_schema: dict[str, Any],
        new_schema: dict[str, Any]
    ) -> list[str]:
        """
        Validate full compatibility (both backward and forward).

        Args:
            old_schema: Previous schema definition
            new_schema: New schema definition

        Returns:
            List of violation messages (empty if compatible)
        """
        violations = []
        violations.extend(
            SchemaEvolutionRule.validate_backward_compatibility(
                old_schema,
                new_schema
            )
        )
        violations.extend(
            SchemaEvolutionRule.validate_forward_compatibility(
                old_schema,
                new_schema
            )
        )
        return violations

    @staticmethod
    def _is_type_widening(old_type: str, new_type: str) -> bool:
        """
        Check if a type change is widening (compatible).

        Examples of widening:
        - integer -> number
        - string -> any

        Args:
            old_type: Previous type
            new_type: New type

        Returns:
            True if the type change is widening
        """
        widening_rules = {
            "integer": {"number"},
            "number": set(),
            "string": set(),
            "boolean": set(),
            "array": set(),
            "object": set(),
        }

        return new_type in widening_rules.get(old_type, set())


class SchemaRegistry:
    """
    Schema registry for managing Pydantic schema versions.

    Provides comprehensive schema versioning, compatibility validation,
    and lifecycle management.
    """

    def __init__(self, db: Session | AsyncSession):
        """
        Initialize schema registry.

        Args:
            db: Database session (sync or async)
        """
        self.db = db
        self.is_async = isinstance(db, AsyncSession)

    async def register_schema(
        self,
        name: str,
        schema_definition: dict[str, Any],
        version: int,
        compatibility_type: str = "backward",
        description: str | None = None,
        changelog: str | None = None,
        migration_notes: str | None = None,
        tags: list[str] | None = None,
        created_by: str | None = None,
        make_default: bool = False,
    ) -> dict[str, Any]:
        """
        Register a new schema version.

        Args:
            name: Schema name
            schema_definition: JSON schema definition
            version: Version number
            compatibility_type: Compatibility type
            description: Schema description
            changelog: Changes from previous version
            migration_notes: Migration instructions
            tags: Searchable tags
            created_by: User ID
            make_default: Set as default version

        Returns:
            Dict with schema_version and success status

        Raises:
            ValueError: If schema already exists or compatibility check fails
        """
        # Check if version already exists
        existing = await self._get_schema_by_name_version(name, version)
        if existing:
            raise ValueError(
                f"Schema {name} version {version} already exists"
            )

        # Validate compatibility with previous version if exists
        if version > 1:
            previous_version = await self._get_schema_by_name_version(
                name,
                version - 1
            )
            if previous_version:
                compat_result = await self.check_compatibility(
                    name,
                    schema_definition,
                    compatibility_type,
                    compare_to_version=version - 1
                )

                if not compat_result.compatible:
                    raise ValueError(
                        f"Schema incompatible with version {version - 1}: "
                        f"{', '.join(compat_result.violations)}"
                    )

        # Create new schema version
        schema_version = SchemaVersion(
            name=name,
            version=version,
            schema_definition=schema_definition,
            compatibility_type=compatibility_type,
            status=SchemaStatus.ACTIVE.value,
            is_default=make_default,
            description=description,
            changelog=changelog,
            migration_notes=migration_notes,
            tags=tags or [],
            created_by=created_by,
        )

        self.db.add(schema_version)

        # If making this the default, unset other defaults
        if make_default:
            await self._unset_default_versions(name, exclude_id=schema_version.id)

        # Create change event
        change_event = SchemaChangeEvent(
            schema_version_id=schema_version.id,
            schema_name=name,
            event_type="created",
            new_version=version,
            changed_by=created_by,
            change_description=changelog,
        )

        self.db.add(change_event)

        if self.is_async:
            await self.db.commit()
            await self.db.refresh(schema_version)
        else:
            self.db.commit()
            self.db.refresh(schema_version)

        # Trigger notification (async)
        await self._notify_schema_change(change_event)

        logger.info(f"Registered schema {name} version {version}")

        return {
            "schema_version": schema_version,
            "success": True,
            "message": f"Schema {name} version {version} registered successfully"
        }

    async def get_schema(
        self,
        name: str,
        version: int | None = None
    ) -> SchemaVersion | None:
        """
        Get a schema version by name and optional version number.

        If version is not specified, returns the default version or latest active.

        Args:
            name: Schema name
            version: Optional version number

        Returns:
            SchemaVersion or None if not found
        """
        if version is not None:
            return await self._get_schema_by_name_version(name, version)

        # Get default version or latest active
        if self.is_async:
            stmt = (
                select(SchemaVersion)
                .where(SchemaVersion.name == name)
                .where(
                    or_(
                        SchemaVersion.is_default.is_(True),
                        SchemaVersion.status == SchemaStatus.ACTIVE.value
                    )
                )
                .order_by(
                    desc(SchemaVersion.is_default),
                    desc(SchemaVersion.version)
                )
            )
            result = await self.db.execute(stmt)
            return result.scalars().first()
        else:
            return (
                self.db.query(SchemaVersion)
                .filter(SchemaVersion.name == name)
                .filter(
                    or_(
                        SchemaVersion.is_default.is_(True),
                        SchemaVersion.status == SchemaStatus.ACTIVE.value
                    )
                )
                .order_by(
                    desc(SchemaVersion.is_default),
                    desc(SchemaVersion.version)
                )
                .first()
            )

    async def list_schemas(
        self,
        name_filter: str | None = None,
        status_filter: list[str] | None = None,
        tags: list[str] | None = None,
        include_archived: bool = False,
    ) -> list[SchemaVersion]:
        """
        List schema versions with optional filters.

        Args:
            name_filter: Filter by schema name (partial match)
            status_filter: Filter by status
            tags: Filter by tags
            include_archived: Include archived schemas

        Returns:
            List of matching schema versions
        """
        if self.is_async:
            stmt = select(SchemaVersion)

            if name_filter:
                stmt = stmt.where(SchemaVersion.name.ilike(f"%{name_filter}%"))

            if status_filter:
                stmt = stmt.where(SchemaVersion.status.in_(status_filter))
            elif not include_archived:
                stmt = stmt.where(
                    SchemaVersion.status != SchemaStatus.ARCHIVED.value
                )

            if tags:
                # Filter by tags (PostgreSQL JSON array contains)
                for tag in tags:
                    stmt = stmt.where(SchemaVersion.tags.contains([tag]))

            stmt = stmt.order_by(SchemaVersion.name, desc(SchemaVersion.version))

            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        else:
            query = self.db.query(SchemaVersion)

            if name_filter:
                query = query.filter(
                    SchemaVersion.name.ilike(f"%{name_filter}%")
                )

            if status_filter:
                query = query.filter(SchemaVersion.status.in_(status_filter))
            elif not include_archived:
                query = query.filter(
                    SchemaVersion.status != SchemaStatus.ARCHIVED.value
                )

            if tags:
                for tag in tags:
                    query = query.filter(SchemaVersion.tags.contains([tag]))

            return query.order_by(
                SchemaVersion.name,
                desc(SchemaVersion.version)
            ).all()

    async def check_compatibility(
        self,
        schema_name: str,
        new_schema_definition: dict[str, Any],
        compatibility_type: str,
        compare_to_version: int | None = None,
    ) -> SchemaCompatibilityResult:
        """
        Check if a new schema definition is compatible with existing version.

        Args:
            schema_name: Schema name
            new_schema_definition: New schema definition to check
            compatibility_type: Desired compatibility type
            compare_to_version: Specific version to compare against

        Returns:
            SchemaCompatibilityResult with compatibility status and violations
        """
        # Get schema to compare against
        if compare_to_version is not None:
            existing_schema = await self._get_schema_by_name_version(
                schema_name,
                compare_to_version
            )
        else:
            existing_schema = await self.get_schema(schema_name)

        if not existing_schema:
            return SchemaCompatibilityResult(
                compatible=True,
                compatibility_type=compatibility_type,
                warnings=["No existing schema to compare against"]
            )

        old_definition = existing_schema.schema_definition
        violations = []
        warnings = []
        suggestions = []

        # Validate based on compatibility type
        if compatibility_type == SchemaCompatibilityType.BACKWARD.value:
            violations = SchemaEvolutionRule.validate_backward_compatibility(
                old_definition,
                new_schema_definition
            )
        elif compatibility_type == SchemaCompatibilityType.FORWARD.value:
            violations = SchemaEvolutionRule.validate_forward_compatibility(
                old_definition,
                new_schema_definition
            )
        elif compatibility_type == SchemaCompatibilityType.FULL.value:
            violations = SchemaEvolutionRule.validate_full_compatibility(
                old_definition,
                new_schema_definition
            )
        elif compatibility_type == SchemaCompatibilityType.TRANSITIVE.value:
            # Check against all previous versions
            all_versions = await self._get_all_schema_versions(schema_name)
            for version_schema in all_versions:
                version_violations = (
                    SchemaEvolutionRule.validate_full_compatibility(
                        version_schema.schema_definition,
                        new_schema_definition
                    )
                )
                if version_violations:
                    violations.extend([
                        f"v{version_schema.version}: {v}"
                        for v in version_violations
                    ])

        # Add suggestions for common issues
        if violations:
            suggestions.append(
                "Consider using a higher version number for breaking changes"
            )
            suggestions.append(
                "Review migration notes to help users adapt to changes"
            )

        return SchemaCompatibilityResult(
            compatible=len(violations) == 0,
            compatibility_type=compatibility_type,
            violations=violations,
            warnings=warnings,
            suggestions=suggestions,
        )

    async def deprecate_schema(
        self,
        name: str,
        version: int,
        deprecated_by: str | None = None,
        removal_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Mark a schema version as deprecated.

        Args:
            name: Schema name
            version: Version to deprecate
            deprecated_by: User ID
            removal_date: When this version will be removed

        Returns:
            Dict with success status

        Raises:
            ValueError: If schema not found or already deprecated
        """
        schema = await self._get_schema_by_name_version(name, version)
        if not schema:
            raise ValueError(f"Schema {name} version {version} not found")

        if schema.status == SchemaStatus.DEPRECATED.value:
            raise ValueError(f"Schema {name} version {version} already deprecated")

        if schema.status == SchemaStatus.ARCHIVED.value:
            raise ValueError(f"Schema {name} version {version} is archived")

        schema.status = SchemaStatus.DEPRECATED.value
        schema.deprecated_at = datetime.utcnow()
        schema.removed_at = removal_date

        # Create change event
        change_event = SchemaChangeEvent(
            schema_version_id=schema.id,
            schema_name=name,
            event_type="deprecated",
            new_version=version,
            changed_by=deprecated_by,
            change_description=f"Deprecated, removal planned for {removal_date}",
        )

        self.db.add(change_event)

        if self.is_async:
            await self.db.commit()
        else:
            self.db.commit()

        # Trigger notification
        await self._notify_schema_change(change_event)

        logger.info(f"Deprecated schema {name} version {version}")

        return {
            "success": True,
            "message": f"Schema {name} version {version} marked as deprecated"
        }

    async def archive_schema(
        self,
        name: str,
        version: int,
        archived_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Archive a schema version (no longer usable).

        Args:
            name: Schema name
            version: Version to archive
            archived_by: User ID

        Returns:
            Dict with success status

        Raises:
            ValueError: If schema not found
        """
        schema = await self._get_schema_by_name_version(name, version)
        if not schema:
            raise ValueError(f"Schema {name} version {version} not found")

        schema.status = SchemaStatus.ARCHIVED.value
        schema.archived_at = datetime.utcnow()

        # Create change event
        change_event = SchemaChangeEvent(
            schema_version_id=schema.id,
            schema_name=name,
            event_type="archived",
            new_version=version,
            changed_by=archived_by,
            change_description="Archived and no longer usable",
        )

        self.db.add(change_event)

        if self.is_async:
            await self.db.commit()
        else:
            self.db.commit()

        # Trigger notification
        await self._notify_schema_change(change_event)

        logger.info(f"Archived schema {name} version {version}")

        return {
            "success": True,
            "message": f"Schema {name} version {version} archived"
        }

    async def set_default_version(
        self,
        name: str,
        version: int,
        changed_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Set a schema version as the default.

        Args:
            name: Schema name
            version: Version to make default
            changed_by: User ID

        Returns:
            Dict with success status

        Raises:
            ValueError: If schema not found or not usable
        """
        schema = await self._get_schema_by_name_version(name, version)
        if not schema:
            raise ValueError(f"Schema {name} version {version} not found")

        if not schema.is_usable:
            raise ValueError(
                f"Schema {name} version {version} is not usable "
                f"(status: {schema.status})"
            )

        # Unset other defaults
        await self._unset_default_versions(name, exclude_id=schema.id)

        schema.is_default = True

        # Create change event
        change_event = SchemaChangeEvent(
            schema_version_id=schema.id,
            schema_name=name,
            event_type="made_default",
            new_version=version,
            changed_by=changed_by,
            change_description=f"Version {version} set as default",
        )

        self.db.add(change_event)

        if self.is_async:
            await self.db.commit()
        else:
            self.db.commit()

        # Trigger notification
        await self._notify_schema_change(change_event)

        logger.info(f"Set schema {name} version {version} as default")

        return {
            "success": True,
            "message": f"Schema {name} version {version} set as default"
        }

    async def generate_documentation(
        self,
        name: str,
        version: int | None = None,
    ) -> SchemaDocumentation:
        """
        Generate comprehensive documentation for a schema.

        Args:
            name: Schema name
            version: Optional specific version (uses default if not specified)

        Returns:
            SchemaDocumentation with full schema details

        Raises:
            ValueError: If schema not found
        """
        schema = await self.get_schema(name, version)
        if not schema:
            raise ValueError(f"Schema {name} not found")

        # Get all versions for history
        all_versions = await self._get_all_schema_versions(name)

        # Extract field information
        fields = []
        properties = schema.schema_definition.get("properties", {})
        required_fields = set(schema.schema_definition.get("required", []))

        for field_name, field_def in properties.items():
            fields.append({
                "name": field_name,
                "type": field_def.get("type", "unknown"),
                "required": field_name in required_fields,
                "description": field_def.get("description"),
                "default": field_def.get("default"),
                "constraints": {
                    k: v for k, v in field_def.items()
                    if k not in ("type", "description", "default")
                },
            })

        # Build compatibility history
        compatibility_history = [
            {
                "version": v.version,
                "compatibility_type": v.compatibility_type,
                "status": v.status,
                "changelog": v.changelog,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in all_versions
        ]

        # Deprecation info
        deprecation_info = None
        if schema.status == SchemaStatus.DEPRECATED.value:
            deprecation_info = {
                "deprecated_at": (
                    schema.deprecated_at.isoformat()
                    if schema.deprecated_at else None
                ),
                "removed_at": (
                    schema.removed_at.isoformat()
                    if schema.removed_at else None
                ),
                "migration_notes": schema.migration_notes,
            }

        # Build migration guides
        migration_guides = []
        for i, version_schema in enumerate(all_versions):
            if i > 0 and version_schema.migration_notes:
                migration_guides.append({
                    "from_version": all_versions[i - 1].version,
                    "to_version": version_schema.version,
                    "notes": version_schema.migration_notes,
                })

        return SchemaDocumentation(
            name=name,
            current_version=schema.version,
            total_versions=len(all_versions),
            description=schema.description,
            fields=fields,
            compatibility_history=compatibility_history,
            deprecation_info=deprecation_info,
            migration_guides=migration_guides,
        )

    # Private helper methods

    async def _get_schema_by_name_version(
        self,
        name: str,
        version: int
    ) -> SchemaVersion | None:
        """Get a specific schema version."""
        if self.is_async:
            stmt = select(SchemaVersion).where(
                and_(
                    SchemaVersion.name == name,
                    SchemaVersion.version == version
                )
            )
            result = await self.db.execute(stmt)
            return result.scalars().first()
        else:
            return (
                self.db.query(SchemaVersion)
                .filter(
                    and_(
                        SchemaVersion.name == name,
                        SchemaVersion.version == version
                    )
                )
                .first()
            )

    async def _get_all_schema_versions(self, name: str) -> list[SchemaVersion]:
        """Get all versions of a schema, ordered by version."""
        if self.is_async:
            stmt = (
                select(SchemaVersion)
                .where(SchemaVersion.name == name)
                .order_by(SchemaVersion.version)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        else:
            return (
                self.db.query(SchemaVersion)
                .filter(SchemaVersion.name == name)
                .order_by(SchemaVersion.version)
                .all()
            )

    async def _unset_default_versions(
        self,
        name: str,
        exclude_id: UUID | None = None
    ) -> None:
        """Unset default flag for all versions of a schema."""
        if self.is_async:
            stmt = (
                select(SchemaVersion)
                .where(SchemaVersion.name == name)
                .where(SchemaVersion.is_default.is_(True))
            )

            if exclude_id:
                stmt = stmt.where(SchemaVersion.id != exclude_id)

            result = await self.db.execute(stmt)
            schemas = result.scalars().all()

            for schema in schemas:
                schema.is_default = False
        else:
            query = (
                self.db.query(SchemaVersion)
                .filter(SchemaVersion.name == name)
                .filter(SchemaVersion.is_default.is_(True))
            )

            if exclude_id:
                query = query.filter(SchemaVersion.id != exclude_id)

            for schema in query.all():
                schema.is_default = False

    async def _notify_schema_change(self, change_event: SchemaChangeEvent) -> None:
        """
        Send notifications for schema changes.

        This is a placeholder for integration with the notification system.
        In production, this would trigger webhooks, emails, or other notifications.

        Args:
            change_event: The change event to notify about
        """
        try:
            # Mark notification as sent
            change_event.notification_sent = True
            change_event.notified_at = datetime.utcnow()

            logger.info(
                f"Schema change notification: {change_event.schema_name} "
                f"v{change_event.new_version} - {change_event.event_type}"
            )

            # Integrate with notification service
            await self.notify_schema_change(
                schema_name=change_event.schema_name,
                change_type=change_event.event_type,
                details={
                    "version": change_event.new_version,
                    "previous_version": change_event.previous_version,
                    "description": change_event.change_description,
                    "changed_by": change_event.changed_by,
                }
            )

        except Exception as e:
            logger.error(
                f"Failed to send schema change notification: {e}",
                exc_info=True
            )

    async def notify_schema_change(
        self,
        schema_name: str,
        change_type: str,
        details: dict = None
    ):
        """
        Notify about schema changes via notification service.

        Args:
            schema_name: Name of changed schema
            change_type: Type of change (created, updated, deleted, deprecated, archived)
            details: Additional change details
        """
        try:
            from app.models.person import Person
            from app.notifications.service import NotificationService
            from app.notifications.notification_types import NotificationType

            service = NotificationService(self.db)

            # Get admin users who should be notified
            admin_ids = await self._get_schema_admin_ids()

            if not admin_ids:
                logger.warning("No admin users found to notify about schema change")
                return

            # Create notification data
            message = f"Schema '{schema_name}' was {change_type}"
            if details:
                if details.get("version"):
                    message += f" (version {details['version']})"
                if details.get("description"):
                    message += f": {details['description']}"

            # Send notifications to all admins
            notification_data = {
                "schema_name": schema_name,
                "change_type": change_type,
                "version": details.get("version") if details else None,
                "description": details.get("description") if details else None,
                "message": message,
            }

            # Use a generic notification type or create a custom one
            # For now, we'll use the notification service directly without a specific type
            for admin_id in admin_ids:
                try:
                    # Create an in-app notification record directly
                    from app.models.notification import Notification

                    notification_record = Notification(
                        recipient_id=admin_id,
                        notification_type="schema_change",
                        subject=f"Schema Change: {schema_name}",
                        body=message,
                        data=notification_data,
                        priority="normal",
                        channels_delivered="in_app",
                    )
                    self.db.add(notification_record)
                except Exception as notify_error:
                    logger.warning(
                        f"Failed to notify admin {admin_id} about schema change: {notify_error}"
                    )

            # Commit all notifications
            if self.is_async:
                await self.db.commit()
            else:
                self.db.commit()

            logger.info(f"Notified {len(admin_ids)} admins about schema change: {schema_name}")

        except Exception as e:
            logger.warning(f"Failed to send schema change notification: {e}")

    async def _get_schema_admin_ids(self) -> list:
        """
        Get list of admin user IDs who should be notified about schema changes.

        Returns:
            List of admin user UUIDs
        """
        try:
            from app.models.person import Person
            from app.models.user import User

            admin_roles = ("admin", "coordinator")

            # Query for users with ADMIN or COORDINATOR roles and map to person records by email
            if self.is_async:
                stmt = (
                    select(Person.id)
                    .join(User, User.email == Person.email)
                    .where(User.role.in_(admin_roles))
                )
                result = await self.db.execute(stmt)
                admin_ids = list(result.scalars().all())
            else:
                persons = (
                    self.db.query(Person.id)
                    .join(User, User.email == Person.email)
                    .filter(User.role.in_(admin_roles))
                    .all()
                )
                admin_ids = [p.id for p in persons]

            if not admin_ids:
                logger.warning(
                    "No admin or coordinator person records found for schema notifications"
                )

            return admin_ids
        except Exception as e:
            logger.error(f"Failed to get admin user IDs: {e}")
            return []


# Convenience functions for common operations

async def get_latest_schema(
    db: Session | AsyncSession,
    schema_name: str
) -> SchemaVersion | None:
    """
    Get the latest (default or most recent active) version of a schema.

    Args:
        db: Database session
        schema_name: Schema name

    Returns:
        SchemaVersion or None
    """
    registry = SchemaRegistry(db)
    return await registry.get_schema(schema_name)


async def validate_schema_compatibility(
    db: Session | AsyncSession,
    schema_name: str,
    new_definition: dict[str, Any],
    compatibility_type: str = "backward"
) -> bool:
    """
    Quick check if a schema definition is compatible.

    Args:
        db: Database session
        schema_name: Schema name
        new_definition: New schema definition
        compatibility_type: Desired compatibility type

    Returns:
        True if compatible, False otherwise
    """
    registry = SchemaRegistry(db)
    result = await registry.check_compatibility(
        schema_name,
        new_definition,
        compatibility_type
    )
    return result.compatible
