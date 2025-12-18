"""
Audit service for querying version history with SQLAlchemy-Continuum integration.

This service provides real audit data from SQLAlchemy-Continuum version tables,
mapping them to the audit schemas expected by the API. Falls back to mock data
if real data is unavailable.

Usage:
    from app.services.audit_service import get_audit_logs

    # Query audit logs with filters
    result = get_audit_logs(
        db,
        page=1,
        page_size=25,
        entity_types=["assignment", "absence"],
        start_date="2025-01-01",
    )
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy_continuum import version_class

from app.core.types import AuditStatistics
from app.models.assignment import Assignment
from app.models.absence import Absence
from app.models.person import Person
from app.models.schedule_run import ScheduleRun
from app.models.swap import SwapRecord
from app.models.user import User
from app.schemas.audit import AuditLogEntry, AuditUser, FieldChange

logger = logging.getLogger(__name__)


# Map entity types to their model classes
ENTITY_MODEL_MAP = {
    "assignment": Assignment,
    "absence": Absence,
    "schedule_run": ScheduleRun,
    "swap_record": SwapRecord,
}

# Map entity types to version table names
VERSION_TABLE_MAP = {
    "assignment": "assignment_version",
    "absence": "absence_version",
    "schedule_run": "schedule_run_version",
    "swap_record": "swap_record_version",
}


def get_audit_logs(
    db: Session,
    page: int = 1,
    page_size: int = 25,
    start_date: str | None = None,
    end_date: str | None = None,
    entity_types: list[str] | None = None,
    actions: list[str] | None = None,
    user_ids: list[str] | None = None,
    severity: list[str] | None = None,
    search: str | None = None,
    entity_id: str | None = None,
    acgme_overrides_only: bool = False,
) -> tuple[list[AuditLogEntry], int]:
    """
    Get audit logs from SQLAlchemy-Continuum version tables.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of results per page
        start_date: Filter changes after this date (ISO format)
        end_date: Filter changes before this date (ISO format)
        entity_types: List of entity types to include
        actions: List of action types to include
        user_ids: List of user IDs to filter by
        severity: List of severity levels to filter by
        search: Search query for entity names/reasons
        entity_id: Filter by specific entity ID
        acgme_overrides_only: Only show ACGME overrides

    Returns:
        Tuple of (list of AuditLogEntry, total count)
    """
    try:
        # Determine which tables to query
        tables_to_query = entity_types if entity_types else list(VERSION_TABLE_MAP.keys())

        all_entries = []

        # Query each version table
        for entity_type in tables_to_query:
            if entity_type not in VERSION_TABLE_MAP:
                continue

            try:
                entries = _query_version_table(
                    db,
                    entity_type=entity_type,
                    start_date=start_date,
                    end_date=end_date,
                    entity_id=entity_id,
                    user_ids=user_ids,
                )
                all_entries.extend(entries)
            except Exception as e:
                logger.warning(f"Error querying {entity_type} versions: {e}")
                continue

        # Apply filters
        filtered_entries = _apply_filters(
            all_entries,
            actions=actions,
            severity=severity,
            search=search,
            acgme_overrides_only=acgme_overrides_only,
        )

        # Sort by timestamp descending
        filtered_entries.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        total = len(filtered_entries)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entries = filtered_entries[start_idx:end_idx]

        return paginated_entries, total

    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return [], 0


def _query_version_table(
    db: Session,
    entity_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
    entity_id: str | None = None,
    user_ids: list[str] | None = None,
) -> list[AuditLogEntry]:
    """Query a specific version table and convert to AuditLogEntry format."""
    table_name = VERSION_TABLE_MAP[entity_type]
    model_class = ENTITY_MODEL_MAP[entity_type]

    # Build query
    where_clauses = ["1=1"]
    params = {}

    if entity_id:
        where_clauses.append("v.id = :entity_id")
        params["entity_id"] = entity_id

    if start_date:
        where_clauses.append("t.issued_at >= :start_date")
        params["start_date"] = datetime.fromisoformat(start_date.replace('Z', ''))

    if end_date:
        where_clauses.append("t.issued_at <= :end_date")
        params["end_date"] = datetime.fromisoformat(end_date.replace('Z', ''))

    if user_ids:
        placeholders = ",".join([f":user_{i}" for i in range(len(user_ids))])
        where_clauses.append(f"t.user_id IN ({placeholders})")
        for i, user_id in enumerate(user_ids):
            params[f"user_{i}"] = user_id

    where_sql = " AND ".join(where_clauses)

    query = text(f"""
        SELECT
            v.id,
            v.transaction_id,
            v.operation_type,
            t.issued_at,
            t.user_id,
            t.remote_addr
        FROM {table_name} v
        LEFT JOIN transaction t ON v.transaction_id = t.id
        WHERE {where_sql}
        ORDER BY t.issued_at DESC
        LIMIT 1000
    """)

    rows = db.execute(query, params).fetchall()

    entries = []
    for row in rows:
        try:
            entry = _build_audit_entry(
                db,
                entity_type=entity_type,
                entity_id=str(row[0]),
                transaction_id=row[1],
                operation_type=row[2],
                issued_at=row[3],
                user_id=row[4],
                remote_addr=row[5],
            )
            if entry:
                entries.append(entry)
        except Exception as e:
            logger.warning(f"Error building audit entry: {e}")
            continue

    return entries


def _build_audit_entry(
    db: Session,
    entity_type: str,
    entity_id: str,
    transaction_id: int,
    operation_type: int,
    issued_at: datetime | None,
    user_id: str | None,
    remote_addr: str | None,
) -> AuditLogEntry | None:
    """Build an AuditLogEntry from version data."""
    try:
        # Map operation type to action
        operation_map = {0: "create", 1: "update", 2: "delete"}
        action = operation_map.get(operation_type, "unknown")

        # Determine severity based on action and entity type
        severity = _determine_severity(entity_type, action, operation_type)

        # Get user info
        audit_user = _get_audit_user(db, user_id)

        # Get entity name
        entity_name = _get_entity_name(db, entity_type, entity_id)

        # Get field changes
        changes = _get_field_changes(db, entity_type, entity_id, transaction_id)

        # Check if this is an ACGME override
        acgme_override = False
        acgme_justification = None
        if entity_type == "assignment":
            acgme_override, acgme_justification = _check_acgme_override(
                db, entity_id, transaction_id
            )

        # Build the entry
        timestamp = issued_at.isoformat() + "Z" if issued_at else datetime.utcnow().isoformat() + "Z"

        return AuditLogEntry(
            id=f"{entity_type}-{transaction_id}",
            timestamp=timestamp,
            entityType=entity_type,
            entityId=entity_id,
            entityName=entity_name,
            action=action,
            severity=severity,
            user=audit_user,
            changes=changes,
            metadata={
                "transaction_id": transaction_id,
                "operation_type": operation_type,
            },
            ipAddress=remote_addr,
            userAgent=None,
            acgmeOverride=acgme_override,
            acgmeJustification=acgme_justification,
        )

    except Exception as e:
        logger.warning(f"Error building audit entry: {e}")
        return None


def _get_audit_user(db: Session, user_id: str | None) -> AuditUser:
    """Get user information for audit entry."""
    if not user_id:
        return AuditUser(
            id="system",
            name="System",
            email=None,
            role="system",
        )

    try:
        # Try to parse as UUID
        try:
            user_uuid = UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, AttributeError):
            # Not a valid UUID, try username
            user = db.query(User).filter(User.username == user_id).first()

        if user:
            return AuditUser(
                id=str(user.id),
                name=user.username,
                email=user.email,
                role=user.role,
            )
    except Exception as e:
        logger.warning(f"Error getting user {user_id}: {e}")

    # Fallback for unknown user
    return AuditUser(
        id=user_id,
        name=f"User {user_id[:8]}",
        email=None,
        role="unknown",
    )


def _get_entity_name(db: Session, entity_type: str, entity_id: str) -> str | None:
    """Get a human-readable name for the entity."""
    try:
        if entity_type == "assignment":
            assignment = db.query(Assignment).filter(Assignment.id == entity_id).first()
            if assignment and assignment.person:
                return f"Assignment - {assignment.person.name}"
            return "Assignment"

        elif entity_type == "absence":
            absence = db.query(Absence).filter(Absence.id == entity_id).first()
            if absence and absence.person:
                return f"{absence.absence_type.title()} - {absence.person.name}"
            return "Absence"

        elif entity_type == "schedule_run":
            schedule_run = db.query(ScheduleRun).filter(ScheduleRun.id == entity_id).first()
            if schedule_run:
                return f"Schedule Run - {schedule_run.start_date} to {schedule_run.end_date}"
            return "Schedule Run"

        elif entity_type == "swap_record":
            swap = db.query(SwapRecord).filter(SwapRecord.id == entity_id).first()
            if swap:
                return f"Swap Request - {swap.status}"
            return "Swap Request"

    except Exception as e:
        logger.warning(f"Error getting entity name: {e}")

    return None


def _get_field_changes(
    db: Session,
    entity_type: str,
    entity_id: str,
    transaction_id: int,
) -> list[FieldChange] | None:
    """Get field changes for this version."""
    try:
        model_class = ENTITY_MODEL_MAP.get(entity_type)
        if not model_class:
            return None

        # Get the version class
        VersionClass = version_class(model_class)

        # Get current and previous versions
        current_version = db.query(VersionClass).filter(
            VersionClass.id == entity_id,
            VersionClass.transaction_id == transaction_id,
        ).first()

        if not current_version:
            return None

        # Get previous version
        previous_version = db.query(VersionClass).filter(
            VersionClass.id == entity_id,
            VersionClass.transaction_id < transaction_id,
        ).order_by(VersionClass.transaction_id.desc()).first()

        if not previous_version:
            # This is the first version (create), no changes to show
            return None

        # Compare versions
        changes = []
        for column in current_version.__table__.columns:
            col_name = column.name

            # Skip internal columns
            if col_name in ('transaction_id', 'operation_type', 'end_transaction_id'):
                continue

            old_value = getattr(previous_version, col_name, None)
            new_value = getattr(current_version, col_name, None)

            if old_value != new_value:
                # Convert to string for display
                old_str = str(old_value) if old_value is not None else None
                new_str = str(new_value) if new_value is not None else None

                changes.append(FieldChange(
                    field=col_name,
                    oldValue=old_str,
                    newValue=new_str,
                    displayName=_format_field_name(col_name),
                ))

        return changes if changes else None

    except Exception as e:
        logger.warning(f"Error getting field changes: {e}")
        return None


def _check_acgme_override(
    db: Session,
    entity_id: str,
    transaction_id: int,
) -> tuple[bool, str | None]:
    """Check if this assignment has an ACGME override."""
    try:
        assignment = db.query(Assignment).filter(Assignment.id == entity_id).first()
        if assignment and assignment.override_reason:
            return True, assignment.override_reason
    except Exception as e:
        logger.warning(f"Error checking ACGME override: {e}")

    return False, None


def _determine_severity(entity_type: str, action: str, operation_type: int) -> str:
    """Determine severity level for an audit entry."""
    # Delete operations are warnings
    if operation_type == 2:
        return "warning"

    # ACGME-related entities are more critical
    if entity_type == "assignment":
        if action == "override":
            return "critical"
        return "info"

    if entity_type == "schedule_run":
        return "info"

    # Default
    return "info"


def _format_field_name(field_name: str) -> str:
    """Format a field name for display."""
    # Convert snake_case to Title Case
    return " ".join(word.capitalize() for word in field_name.split("_"))


def _apply_filters(
    entries: list[AuditLogEntry],
    actions: list[str] | None = None,
    severity: list[str] | None = None,
    search: str | None = None,
    acgme_overrides_only: bool = False,
) -> list[AuditLogEntry]:
    """Apply additional filters to audit entries."""
    filtered = entries

    if actions:
        filtered = [e for e in filtered if e.action in actions]

    if severity:
        filtered = [e for e in filtered if e.severity in severity]

    if search:
        search_lower = search.lower()
        filtered = [
            e for e in filtered
            if (e.entity_name and search_lower in e.entity_name.lower())
            or (e.reason and search_lower in e.reason.lower())
            or search_lower in e.action.lower()
        ]

    if acgme_overrides_only:
        filtered = [e for e in filtered if e.acgme_override]

    return filtered


def get_audit_users(db: Session) -> list[AuditUser]:
    """Get list of users who have audit activity."""
    try:
        # Query transaction table for unique users
        query = text("""
            SELECT DISTINCT t.user_id
            FROM transaction t
            WHERE t.user_id IS NOT NULL
            ORDER BY t.user_id
            LIMIT 100
        """)

        rows = db.execute(query).fetchall()

        users = []
        seen_ids = set()

        for row in rows:
            user_id = row[0]
            if user_id in seen_ids:
                continue
            seen_ids.add(user_id)

            audit_user = _get_audit_user(db, user_id)
            users.append(audit_user)

        return users

    except Exception as e:
        logger.error(f"Error getting audit users: {e}")
        return []


def get_audit_statistics(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
) -> AuditStatistics:
    """
    Calculate audit statistics for a date range.

    Returns:
        AuditStatistics with:
        - totalEntries: Total number of changes
        - entriesByAction: Changes grouped by action
        - entriesByEntityType: Changes grouped by entity type
        - entriesBySeverity: Changes grouped by severity
        - acgmeOverrideCount: Number of ACGME overrides
        - uniqueUsers: Number of unique users
    """
    try:
        # Get all entries for date range
        entries, total = get_audit_logs(
            db,
            page=1,
            page_size=10000,
            start_date=start_date,
            end_date=end_date,
        )

        # Count by action
        entries_by_action = {}
        for entry in entries:
            entries_by_action[entry.action] = entries_by_action.get(entry.action, 0) + 1

        # Count by entity type
        entries_by_entity_type = {}
        for entry in entries:
            entries_by_entity_type[entry.entity_type] = entries_by_entity_type.get(entry.entity_type, 0) + 1

        # Count by severity
        entries_by_severity = {}
        for entry in entries:
            entries_by_severity[entry.severity] = entries_by_severity.get(entry.severity, 0) + 1

        # Count ACGME overrides
        acgme_override_count = sum(1 for entry in entries if entry.acgme_override)

        # Count unique users
        unique_users = len({entry.user.id for entry in entries})

        return {
            "totalEntries": total,
            "entriesByAction": entries_by_action,
            "entriesByEntityType": entries_by_entity_type,
            "entriesBySeverity": entries_by_severity,
            "acgmeOverrideCount": acgme_override_count,
            "uniqueUsers": unique_users,
        }

    except Exception as e:
        logger.error(f"Error calculating audit statistics: {e}")
        return {
            "totalEntries": 0,
            "entriesByAction": {},
            "entriesByEntityType": {},
            "entriesBySeverity": {},
            "acgmeOverrideCount": 0,
            "uniqueUsers": 0,
        }
