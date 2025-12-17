"""
Audit service for querying version history.

Provides utilities for accountability tracking - see who changed what, when.
This enhanced version uses the AuditRepository for data access and provides
high-level business logic for audit operations.

Usage:
    from app.services.audit_service import AuditService

    # Create service instance
    service = AuditService(db)

    # Query audit logs with filters
    result = service.query_audit_logs(
        db,
        filters={"entity_type": "assignment", "user_id": "user123"},
        pagination={"page": 1, "page_size": 50},
        sort={"sort_by": "changed_at", "sort_direction": "desc"}
    )

    # Get entity history
    history = service.get_entity_history(db, "assignment", assignment_id)

    # Export audit logs
    csv_data = service.export_audit_logs(db, {"format": "csv"})
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    id: int
    entity_type: str
    entity_id: str
    transaction_id: int
    operation: str
    changed_at: datetime | None
    changed_by: str | None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response for audit log query."""
    items: list[AuditLogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditStatistics(BaseModel):
    """Audit statistics summary."""
    total_changes: int
    changes_by_entity: dict[str, int]
    changes_by_operation: dict[str, int]
    changes_by_user: dict[str, int]
    most_active_day: str | None


class AuditService:
    """
    Service for querying and managing audit data.

    This service provides high-level business logic for audit operations,
    using the AuditRepository for data access.
    """

    def __init__(self, db: Session):
        """Initialize the audit service with a database session."""
        self.db = db
        self.repository = AuditRepository(db)

    def query_audit_logs(
        self,
        db: Session,
        filters: dict[str, Any] | None = None,
        pagination: dict[str, int] | None = None,
        sort: dict[str, str] | None = None,
    ) -> AuditLogResponse:
        """
        Query audit logs with filters, pagination, and sorting.

        Args:
            db: Database session
            filters: Optional filters dict with keys:
                - entity_type: Filter by entity type
                - entity_id: Filter by specific entity ID
                - user_id: Filter by user who made the change
                - operation: Filter by operation type
                - start_date: Filter changes after this date
                - end_date: Filter changes before this date
            pagination: Optional dict with page and page_size
            sort: Optional dict with sort_by and sort_direction

        Returns:
            AuditLogResponse with items and pagination info
        """
        # Set defaults
        pagination = pagination or {}
        page = pagination.get("page", 1)
        page_size = pagination.get("page_size", 50)

        sort = sort or {}
        sort_by = sort.get("sort_by", "changed_at")
        sort_direction = sort.get("sort_direction", "desc")

        # Query repository
        entries, total = self.repository.get_audit_entries(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

        # Convert to Pydantic models
        items = [AuditLogEntry(**entry) for entry in entries]

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return AuditLogResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_entity_history(
        self,
        db: Session,
        entity_type: str,
        entity_id: UUID,
    ) -> list[AuditLogEntry]:
        """
        Get complete version history for a specific entity.

        Args:
            db: Database session
            entity_type: Type of entity (assignment, absence, etc.)
            entity_id: ID of the entity

        Returns:
            List of audit log entries in chronological order
        """
        # Get history from repository
        history = self.repository.get_entity_history(entity_type, entity_id)

        # Also try to get detailed version info from the model
        try:
            detailed_history = self._get_detailed_entity_history(
                db, entity_type, entity_id
            )
            if detailed_history:
                return detailed_history
        except Exception as e:
            logger.warning(f"Could not get detailed history: {e}")

        # Fall back to repository data
        return [AuditLogEntry(**entry) for entry in history]

    def get_user_activity(
        self,
        db: Session,
        user_id: str,
        date_range: tuple[datetime, datetime] | None = None,
    ) -> list[AuditLogEntry]:
        """
        Get audit activity for a specific user.

        Args:
            db: Database session
            user_id: User ID to query
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            List of audit log entries for this user
        """
        filters = {"user_id": user_id}

        if date_range:
            filters["start_date"] = date_range[0]
            filters["end_date"] = date_range[1]

        entries, _ = self.repository.get_audit_entries(
            filters=filters,
            page=1,
            page_size=1000,
            sort_by="changed_at",
            sort_direction="desc",
        )

        return [AuditLogEntry(**entry) for entry in entries]

    def export_audit_logs(
        self,
        db: Session,
        config: dict[str, Any],
    ) -> bytes:
        """
        Export audit logs to CSV or Excel format.

        Args:
            db: Database session
            config: Export configuration dict with keys:
                - format: Export format ("csv" or "excel")
                - filters: Optional filters to apply
                - columns: Optional list of columns to include

        Returns:
            Bytes of the exported file
        """
        export_format = config.get("format", "csv")
        filters = config.get("filters", {})
        columns = config.get("columns") or [
            "id",
            "entity_type",
            "entity_id",
            "operation",
            "changed_at",
            "changed_by",
        ]

        # Get all matching entries
        entries, _ = self.repository.get_audit_entries(
            filters=filters,
            page=1,
            page_size=10000,  # Max export size
            sort_by="changed_at",
            sort_direction="desc",
        )

        if export_format == "csv":
            return self._export_to_csv(entries, columns)
        elif export_format == "excel":
            return self._export_to_excel(entries, columns)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

    def calculate_statistics(
        self,
        db: Session,
        date_range: tuple[datetime, datetime] | None = None,
    ) -> AuditStatistics:
        """
        Calculate audit statistics for a date range.

        Args:
            db: Database session
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            AuditStatistics with summary information
        """
        start_date = None
        end_date = None

        if date_range:
            start_date, end_date = date_range

        stats = self.repository.get_audit_statistics(
            start_date=start_date,
            end_date=end_date,
        )

        return AuditStatistics(**stats)

    # Legacy static methods for backward compatibility
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
        model_type: str | None = None,
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
                "swap_record": "swap_record_version",
            }

            if model_type:
                tables = {model_type: tables.get(model_type)}

            for model, table in tables.items():
                if not table:
                    continue

                try:
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
                except Exception as e:
                    logger.warning(f"Error querying {table}: {e}")
                    continue

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
        since: datetime | None = None,
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

            tables = [
                "assignment_version",
                "absence_version",
                "schedule_run_version",
                "swap_record_version",
            ]
            model_names = ["assignment", "absence", "schedule_run", "swap_record"]

            for table, model in zip(tables, model_names, strict=False):
                try:
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
                except Exception as e:
                    logger.warning(f"Error querying {table}: {e}")
                    continue

            # Sort by changed_at descending
            results.sort(key=lambda x: x["changed_at"] or datetime.min, reverse=True)

            return results[:limit]

        except Exception as e:
            logger.warning(f"Error getting changes by user: {e}")
            return []

    # Private helper methods
    def _get_detailed_entity_history(
        self,
        db: Session,
        entity_type: str,
        entity_id: UUID,
    ) -> list[AuditLogEntry] | None:
        """Get detailed history directly from the model's versions."""
        model_map = {
            "assignment": "app.models.assignment.Assignment",
            "absence": "app.models.absence.Absence",
            "schedule_run": "app.models.schedule_run.ScheduleRun",
            "swap_record": "app.models.swap.SwapRecord",
        }

        model_path = model_map.get(entity_type)
        if not model_path:
            return None

        try:
            # Dynamically import the model
            module_name, class_name = model_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            model_class = getattr(module, class_name)

            # Get the entity
            entity = db.query(model_class).filter(model_class.id == entity_id).first()
            if not entity or not hasattr(entity, "versions"):
                return None

            # Convert versions to audit log entries
            entries = []
            for version in entity.versions:
                entry = AuditLogEntry(
                    id=version.transaction_id,
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    transaction_id=version.transaction_id,
                    operation=_operation_name(version.operation_type),
                    changed_at=version.transaction.issued_at if hasattr(version, "transaction") else None,
                    changed_by=version.transaction.user_id if hasattr(version, "transaction") else None,
                )
                entries.append(entry)

            return entries

        except Exception as e:
            logger.warning(f"Error getting detailed history: {e}")
            return None

    def _export_to_csv(
        self,
        entries: list[dict[str, Any]],
        columns: list[str],
    ) -> bytes:
        """Export audit entries to CSV format."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)

        writer.writeheader()
        for entry in entries:
            # Only include requested columns
            row = {col: entry.get(col, "") for col in columns}
            # Format datetime
            if "changed_at" in row and row["changed_at"]:
                row["changed_at"] = str(row["changed_at"])
            writer.writerow(row)

        return output.getvalue().encode("utf-8")

    def _export_to_excel(
        self,
        entries: list[dict[str, Any]],
        columns: list[str],
    ) -> bytes:
        """Export audit entries to Excel format (requires openpyxl)."""
        try:
            import openpyxl
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            ws.title = "Audit Log"

            # Write header
            ws.append(columns)

            # Write data
            for entry in entries:
                row = [entry.get(col, "") for col in columns]
                # Format datetime
                for i, val in enumerate(row):
                    if isinstance(val, datetime):
                        row[i] = val.isoformat()
                ws.append(row)

            # Save to bytes
            output = io.BytesIO()
            wb.save(output)
            return output.getvalue()

        except ImportError:
            logger.error("openpyxl not installed, cannot export to Excel")
            # Fall back to CSV
            return self._export_to_csv(entries, columns)


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
