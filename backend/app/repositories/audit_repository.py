"""
Audit repository for querying SQLAlchemy-Continuum version history.

This repository provides low-level data access to audit logs stored by
SQLAlchemy-Continuum. It queries the transaction and version tables to
retrieve historical changes to versioned models.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuditRepository:
    """
    Repository for querying audit data from SQLAlchemy-Continuum.

    Provides access to version history and transaction data for all
    versioned models (Assignment, Absence, ScheduleRun, SwapRecord).
    """

    # Map entity types to their version table names
    VERSION_TABLES = {
        "assignment": "assignment_version",
        "absence": "absence_version",
        "schedule_run": "schedule_run_version",
        "swap_record": "swap_record_version",
    }

    def __init__(self, db: Session):
        """Initialize the audit repository with a database session."""
        self.db = db

    def _validate_and_quote_table_name(self, table_name: str) -> str:
        """
        Validate table name against allowlist and return quoted identifier.

        Args:
            table_name: The table name to validate and quote

        Returns:
            Properly quoted table name for use in SQL

        Raises:
            ValueError: If table name is not in allowlist
        """
        # Validate against allowlist
        if table_name not in self.VERSION_TABLES.values():
            raise ValueError(f"Invalid table name: {table_name}")

        # Return quoted identifier (PostgreSQL uses double quotes)
        # This prevents SQL injection even if allowlist is bypassed
        return f'"{table_name}"'

    def get_audit_entries(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "changed_at",
        sort_direction: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Get audit entries with filtering, pagination, and sorting.

        Args:
            filters: Optional filters dict with keys:
                - entity_type: Filter by entity type (assignment, absence, etc.)
                - entity_id: Filter by specific entity ID
                - user_id: Filter by user who made the change
                - operation: Filter by operation type (insert, update, delete)
                - start_date: Filter changes after this date
                - end_date: Filter changes before this date
            page: Page number (1-indexed)
            page_size: Number of results per page
            sort_by: Field to sort by (changed_at, entity_type, operation)
            sort_direction: Sort direction (asc or desc)

        Returns:
            Tuple of (list of audit entries, total count)
        """
        filters = filters or {}

        try:
            # Determine which tables to query
            entity_type = filters.get("entity_type")
            if entity_type:
                tables = {entity_type: self.VERSION_TABLES.get(entity_type)}
                if not tables[entity_type]:
                    return [], 0
            else:
                tables = self.VERSION_TABLES

            all_entries = []

            # Query each version table
            for model_name, table_name in tables.items():
                if not table_name:
                    continue

                # Build query with filters
                query = self._build_audit_query(
                    table_name=table_name,
                    model_name=model_name,
                    filters=filters,
                )

                try:
                    rows = self.db.execute(
                        query, self._build_query_params(filters)
                    ).fetchall()

                    for row in rows:
                        all_entries.append(
                            {
                                "id": row[0],
                                "entity_type": model_name,
                                "entity_id": str(row[1]),
                                "transaction_id": row[2],
                                "operation": self._operation_name(row[3]),
                                "changed_at": row[4],
                                "changed_by": row[5],
                            }
                        )
                except Exception as e:
                    logger.warning(f"Error querying {table_name}: {e}")
                    continue

            # Sort entries
            all_entries = self._sort_entries(all_entries, sort_by, sort_direction)

            # Calculate pagination
            total_count = len(all_entries)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            return all_entries[start_idx:end_idx], total_count

        except Exception as e:
            logger.error(f"Error getting audit entries: {e}")
            return [], 0

    def get_audit_entry_by_id(
        self,
        entry_id: int,
        entity_type: str,
    ) -> dict[str, Any] | None:
        """
        Get a specific audit entry by its version ID and entity type.

        Args:
            entry_id: The version record ID
            entity_type: Type of entity (assignment, absence, etc.)

        Returns:
            Dict with audit entry details or None if not found
        """
        table_name = self.VERSION_TABLES.get(entity_type)
        if not table_name:
            logger.warning(f"Unknown entity type: {entity_type}")
            return None

        try:
            # Validate and quote table name to prevent SQL injection
            quoted_table = self._validate_and_quote_table_name(table_name)

            query = text(f"""
                SELECT v.id, v.transaction_id, v.operation_type,
                       t.issued_at, t.user_id
                FROM {quoted_table} v
                LEFT JOIN transaction t ON v.transaction_id = t.id
                WHERE v.id = :entry_id
            """)

            row = self.db.execute(query, {"entry_id": entry_id}).fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "entity_type": entity_type,
                "transaction_id": row[1],
                "operation": self._operation_name(row[2]),
                "changed_at": row[3],
                "changed_by": row[4],
            }

        except Exception as e:
            logger.error(f"Error getting audit entry {entry_id}: {e}")
            return None

    def get_audit_statistics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get audit statistics for a date range.

        Args:
            start_date: Start of date range (optional)
            end_date: End of date range (optional)

        Returns:
            Dict with statistics:
                - total_changes: Total number of changes
                - changes_by_entity: Changes grouped by entity type
                - changes_by_operation: Changes grouped by operation
                - changes_by_user: Changes grouped by user
                - most_active_day: Date with most changes
        """
        try:
            stats = {
                "total_changes": 0,
                "changes_by_entity": {},
                "changes_by_operation": {"insert": 0, "update": 0, "delete": 0},
                "changes_by_user": {},
                "most_active_day": None,
            }

            date_filter = ""
            params = {}

            if start_date:
                date_filter += " AND t.issued_at >= :start_date"
                params["start_date"] = start_date
            if end_date:
                date_filter += " AND t.issued_at <= :end_date"
                params["end_date"] = end_date

            # Aggregate across all version tables
            for model_name, table_name in self.VERSION_TABLES.items():
                try:
                    # Validate and quote table name to prevent SQL injection
                    quoted_table = self._validate_and_quote_table_name(table_name)

                    query = text(f"""
                        SELECT
                            COUNT(*) as total,
                            v.operation_type,
                            t.user_id,
                            DATE(t.issued_at) as change_date
                        FROM {quoted_table} v
                        LEFT JOIN transaction t ON v.transaction_id = t.id
                        WHERE 1=1 {date_filter}
                        GROUP BY v.operation_type, t.user_id, DATE(t.issued_at)
                    """)

                    rows = self.db.execute(query, params).fetchall()

                    entity_total = 0
                    for row in rows:
                        count = row[0]
                        op_type = row[1]
                        user_id = row[2] or "system"

                        entity_total += count
                        stats["total_changes"] += count

                        # Count by operation
                        op_name = self._operation_name(op_type)
                        stats["changes_by_operation"][op_name] += count

                        # Count by user
                        if user_id not in stats["changes_by_user"]:
                            stats["changes_by_user"][user_id] = 0
                        stats["changes_by_user"][user_id] += count

                    stats["changes_by_entity"][model_name] = entity_total

                except Exception as e:
                    logger.warning(f"Error getting stats for {table_name}: {e}")
                    continue

            return stats

        except Exception as e:
            logger.error(f"Error calculating audit statistics: {e}")
            return {
                "total_changes": 0,
                "changes_by_entity": {},
                "changes_by_operation": {},
                "changes_by_user": {},
                "most_active_day": None,
            }

    def get_users_with_audit_activity(self) -> list[dict[str, Any]]:
        """
        Get list of users who have made changes in the audit log.

        Returns:
            List of dicts with user_id and change_count
        """
        try:
            query = text("""
                SELECT user_id, COUNT(*) as change_count
                FROM transaction
                WHERE user_id IS NOT NULL
                GROUP BY user_id
                ORDER BY change_count DESC
            """)

            rows = self.db.execute(query).fetchall()

            return [{"user_id": row[0], "change_count": row[1]} for row in rows]

        except Exception as e:
            logger.error(f"Error getting users with audit activity: {e}")
            return []

    def mark_entries_reviewed(
        self,
        entry_ids: list[int],
        reviewer_id: str,
        notes: str | None = None,
    ) -> int:
        """
        Mark audit entries as reviewed (placeholder for future feature).

        This would require a separate audit_review table to track reviews.
        Currently returns 0 as this feature is not yet implemented.

        Args:
            entry_ids: List of entry IDs to mark as reviewed
            reviewer_id: ID of user reviewing the entries
            notes: Optional review notes

        Returns:
            Number of entries marked as reviewed (currently 0)
        """
        # This would require an audit_review table which doesn't exist yet
        # Placeholder for future implementation
        logger.info(
            f"Review marking requested for {len(entry_ids)} entries by {reviewer_id}"
        )
        return 0

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> list[dict[str, Any]]:
        """
        Get complete version history for a specific entity.

        Args:
            entity_type: Type of entity (assignment, absence, etc.)
            entity_id: ID of the entity

        Returns:
            List of version history entries in chronological order
        """
        table_name = self.VERSION_TABLES.get(entity_type)
        if not table_name:
            logger.warning(f"Unknown entity type: {entity_type}")
            return []

        try:
            # Validate and quote table name to prevent SQL injection
            quoted_table = self._validate_and_quote_table_name(table_name)

            query = text(f"""
                SELECT v.id, v.transaction_id, v.operation_type,
                       t.issued_at, t.user_id
                FROM {quoted_table} v
                LEFT JOIN transaction t ON v.transaction_id = t.id
                WHERE v.id = :entity_id
                ORDER BY t.issued_at ASC
            """)

            rows = self.db.execute(query, {"entity_id": str(entity_id)}).fetchall()

            return [
                {
                    "version_id": row[0],
                    "transaction_id": row[1],
                    "operation": self._operation_name(row[2]),
                    "changed_at": row[3],
                    "changed_by": row[4],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting entity history for {entity_id}: {e}")
            return []

    def _build_audit_query(
        self,
        table_name: str,
        model_name: str,
        filters: dict[str, Any],
    ) -> text:
        """Build SQL query for audit entries with filters."""
        # Validate and quote table name to prevent SQL injection
        quoted_table = self._validate_and_quote_table_name(table_name)

        where_clauses = []

        if filters.get("entity_id"):
            where_clauses.append("v.id = :entity_id")

        if filters.get("user_id"):
            where_clauses.append("t.user_id = :user_id")

        if filters.get("operation"):
            op_map = {"insert": 0, "update": 1, "delete": 2}
            if filters["operation"] in op_map:
                where_clauses.append(
                    f"v.operation_type = {op_map[filters['operation']]}"
                )

        if filters.get("start_date"):
            where_clauses.append("t.issued_at >= :start_date")

        if filters.get("end_date"):
            where_clauses.append("t.issued_at <= :end_date")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query_sql = f"""
            SELECT v.id, v.id as entity_id, v.transaction_id, v.operation_type,
                   t.issued_at, t.user_id
            FROM {quoted_table} v
            LEFT JOIN transaction t ON v.transaction_id = t.id
            WHERE {where_sql}
            ORDER BY t.issued_at DESC
            LIMIT 1000
        """

        return text(query_sql)

    def _build_query_params(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Build query parameters from filters."""
        params = {}

        if filters.get("entity_id"):
            params["entity_id"] = str(filters["entity_id"])
        if filters.get("user_id"):
            params["user_id"] = filters["user_id"]
        if filters.get("start_date"):
            params["start_date"] = filters["start_date"]
        if filters.get("end_date"):
            params["end_date"] = filters["end_date"]

        return params

    def _sort_entries(
        self,
        entries: list[dict[str, Any]],
        sort_by: str,
        sort_direction: str,
    ) -> list[dict[str, Any]]:
        """Sort audit entries."""
        reverse = sort_direction.lower() == "desc"

        if sort_by == "changed_at":
            entries.sort(
                key=lambda x: x.get("changed_at") or datetime.min, reverse=reverse
            )
        elif sort_by == "entity_type":
            entries.sort(key=lambda x: x.get("entity_type", ""), reverse=reverse)
        elif sort_by == "operation":
            entries.sort(key=lambda x: x.get("operation", ""), reverse=reverse)

        return entries

    @staticmethod
    def _operation_name(op_type: int) -> str:
        """Convert operation type integer to name."""
        ops = {0: "insert", 1: "update", 2: "delete"}
        return ops.get(op_type, "unknown")
