"""
Audit service for querying version history.

Provides utilities for accountability tracking - see who changed what, when.

Usage:
    from app.services.audit_service import AuditService

    # Get all changes to an assignment
    history = AuditService.get_assignment_history(db, assignment_id)

    # Get all changes by a specific user
    changes = AuditService.get_changes_by_user(db, user_id, since=datetime)

    # Get recent changes across all tracked models
    recent = AuditService.get_recent_changes(db, hours=24)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuditService:
    """Service for querying audit/version history."""

    @staticmethod
    def get_assignment_history(
        db: Session,
        assignment_id: UUID,
    ) -> list[dict]:
        """
        Get complete version history for an assignment.

        Returns list of changes with:
        - version_id: Transaction ID
        - changed_at: When the change occurred
        - operation: 'insert', 'update', or 'delete'
        - changed_by: User ID who made the change (if tracked)
        - changes: Dict of field changes {field: {old: x, new: y}}
        """
        try:
            from app.models.assignment import Assignment

            # Get the assignment with its version class
            assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
            if not assignment:
                return []

            history = []
            versions = list(assignment.versions)

            for i, version in enumerate(versions):
                entry = {
                    "version_id": version.transaction_id,
                    "changed_at": version.transaction.issued_at if hasattr(version, 'transaction') else None,
                    "operation": _operation_name(version.operation_type),
                    "changed_by": version.transaction.user_id if hasattr(version, 'transaction') else None,
                }

                # Calculate changes from previous version
                if i > 0:
                    prev = versions[i - 1]
                    entry["changes"] = _diff_versions(prev, version)
                else:
                    entry["changes"] = {"_created": True}

                history.append(entry)

            return history

        except Exception as e:
            logger.warning(f"Error getting assignment history: {e}")
            return []

    @staticmethod
    def get_absence_history(
        db: Session,
        absence_id: UUID,
    ) -> list[dict]:
        """Get complete version history for an absence."""
        try:
            from app.models.absence import Absence

            absence = db.query(Absence).filter(Absence.id == absence_id).first()
            if not absence:
                return []

            history = []
            versions = list(absence.versions)

            for i, version in enumerate(versions):
                entry = {
                    "version_id": version.transaction_id,
                    "changed_at": version.transaction.issued_at if hasattr(version, 'transaction') else None,
                    "operation": _operation_name(version.operation_type),
                    "changed_by": version.transaction.user_id if hasattr(version, 'transaction') else None,
                }

                if i > 0:
                    prev = versions[i - 1]
                    entry["changes"] = _diff_versions(prev, version)
                else:
                    entry["changes"] = {"_created": True}

                history.append(entry)

            return history

        except Exception as e:
            logger.warning(f"Error getting absence history: {e}")
            return []

    @staticmethod
    def get_recent_changes(
        db: Session,
        hours: int = 24,
        model_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Get recent changes across all tracked models.

        Args:
            db: Database session
            hours: How far back to look (default 24 hours)
            model_type: Optional filter ('assignment', 'absence', 'schedule_run')

        Returns list of recent changes with model type, ID, and change details.
        """
        try:
            from sqlalchemy import text

            since = datetime.utcnow() - timedelta(hours=hours)

            results = []

            # Query each version table
            tables = {
                "assignment": "assignment_version",
                "absence": "absence_version",
                "schedule_run": "schedule_run_version",
            }

            if model_type:
                tables = {model_type: tables.get(model_type)}

            for model, table in tables.items():
                if not table:
                    continue

                query = text(f"""
                    SELECT v.id, v.transaction_id, v.operation_type, t.issued_at, t.user_id
                    FROM {table} v
                    JOIN transaction t ON v.transaction_id = t.id
                    WHERE t.issued_at >= :since
                    ORDER BY t.issued_at DESC
                    LIMIT 100
                """)

                rows = db.execute(query, {"since": since}).fetchall()

                for row in rows:
                    results.append({
                        "model_type": model,
                        "model_id": str(row[0]),
                        "version_id": row[1],
                        "operation": _operation_name(row[2]),
                        "changed_at": row[3],
                        "changed_by": row[4],
                    })

            # Sort by changed_at descending
            results.sort(key=lambda x: x["changed_at"] or datetime.min, reverse=True)

            return results[:100]  # Limit total results

        except Exception as e:
            logger.warning(f"Error getting recent changes: {e}")
            return []

    @staticmethod
    def get_changes_by_user(
        db: Session,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get all changes made by a specific user.

        Args:
            db: Database session
            user_id: User ID to filter by
            since: Optional start date
            limit: Maximum results to return

        Returns list of changes made by this user.
        """
        try:
            from sqlalchemy import text

            if since is None:
                since = datetime.utcnow() - timedelta(days=30)

            results = []

            tables = ["assignment_version", "absence_version", "schedule_run_version"]
            model_names = ["assignment", "absence", "schedule_run"]

            for table, model in zip(tables, model_names):
                query = text(f"""
                    SELECT v.id, v.transaction_id, v.operation_type, t.issued_at
                    FROM {table} v
                    JOIN transaction t ON v.transaction_id = t.id
                    WHERE t.user_id = :user_id AND t.issued_at >= :since
                    ORDER BY t.issued_at DESC
                    LIMIT :limit
                """)

                rows = db.execute(query, {"user_id": user_id, "since": since, "limit": limit}).fetchall()

                for row in rows:
                    results.append({
                        "model_type": model,
                        "model_id": str(row[0]),
                        "version_id": row[1],
                        "operation": _operation_name(row[2]),
                        "changed_at": row[3],
                    })

            # Sort by changed_at descending
            results.sort(key=lambda x: x["changed_at"] or datetime.min, reverse=True)

            return results[:limit]

        except Exception as e:
            logger.warning(f"Error getting changes by user: {e}")
            return []


def _operation_name(op_type: int) -> str:
    """Convert operation type integer to name."""
    ops = {0: "insert", 1: "update", 2: "delete"}
    return ops.get(op_type, "unknown")


def _diff_versions(old_version, new_version) -> dict:
    """
    Calculate differences between two versions.

    Returns dict of {field: {old: value, new: value}} for changed fields.
    """
    changes = {}

    # Get columns to compare (exclude version-specific columns)
    skip_columns = {"transaction_id", "operation_type", "end_transaction_id"}

    for column in old_version.__table__.columns:
        if column.name in skip_columns:
            continue

        old_val = getattr(old_version, column.name, None)
        new_val = getattr(new_version, column.name, None)

        if old_val != new_val:
            changes[column.name] = {"old": old_val, "new": new_val}

    return changes
