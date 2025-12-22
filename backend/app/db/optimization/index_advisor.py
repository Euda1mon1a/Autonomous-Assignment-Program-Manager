"""Index recommendation engine for database optimization.

Analyzes query patterns, table scans, and index usage to recommend
optimal indexes for improving query performance.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class IndexRecommendation:
    """Recommendation for creating an index."""

    table_name: str
    columns: list[str]
    index_type: str  # btree, hash, gin, gist
    priority: str  # high, medium, low
    reason: str
    estimated_benefit: str
    create_statement: str
    current_usage_stats: dict[str, Any] | None = None


@dataclass
class IndexUsageStats:
    """Statistics about index usage."""

    schema_name: str
    table_name: str
    index_name: str
    index_size_mb: float
    scans: int
    tuples_read: int
    tuples_fetched: int
    is_unique: bool
    definition: str


class IndexAdvisor:
    """
    Index recommendation engine.

    Analyzes database queries and table statistics to recommend indexes
    that would improve query performance.

    Features:
    - Analyzes slow queries for missing indexes
    - Detects sequential scans on large tables
    - Identifies unused indexes
    - Recommends composite indexes for common query patterns
    - Provides index usage statistics

    Usage:
        advisor = IndexAdvisor(db)
        recommendations = advisor.analyze_and_recommend()
        unused = advisor.find_unused_indexes()
    """

    def __init__(self, db: Session):
        """
        Initialize index advisor.

        Args:
            db: Database session
        """
        self.db = db

    def analyze_and_recommend(
        self, min_table_size_mb: float = 1.0
    ) -> list[IndexRecommendation]:
        """
        Analyze database and generate index recommendations.

        Args:
            min_table_size_mb: Only analyze tables larger than this

        Returns:
            List of index recommendations ordered by priority
        """
        recommendations = []

        # Get tables with sequential scans
        seq_scan_tables = self._get_sequential_scan_tables(min_table_size_mb)
        for table_info in seq_scan_tables:
            recommendations.extend(
                self._recommend_indexes_for_table(table_info)
            )

        # Analyze slow query patterns
        recommendations.extend(self._analyze_slow_query_patterns())

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order[r.priority])

        return recommendations

    def find_unused_indexes(
        self, min_age_days: int = 7, min_size_mb: float = 10.0
    ) -> list[IndexUsageStats]:
        """
        Find indexes that are not being used.

        Args:
            min_age_days: Only consider indexes older than this
            min_size_mb: Only consider indexes larger than this

        Returns:
            List of unused index statistics
        """
        query = text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid::regclass))::text as size,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_index.indisunique,
                pg_get_indexdef(indexrelid) as definition
            FROM pg_stat_user_indexes
            JOIN pg_index ON pg_stat_user_indexes.indexrelid = pg_index.indexrelid
            WHERE idx_scan = 0
                AND schemaname = 'public'
                AND indexname NOT LIKE '%_pkey'
                AND pg_relation_size(indexrelid) > :min_size_bytes
            ORDER BY pg_relation_size(indexrelid) DESC
        """)

        try:
            result = self.db.execute(
                query, {"min_size_bytes": min_size_mb * 1024 * 1024}
            )
            unused_indexes = []

            for row in result:
                # Parse size (e.g., "15 MB" -> 15.0)
                size_str = row[3]
                size_mb = self._parse_size_to_mb(size_str)

                unused_indexes.append(
                    IndexUsageStats(
                        schema_name=row[0],
                        table_name=row[1],
                        index_name=row[2],
                        index_size_mb=size_mb,
                        scans=row[4],
                        tuples_read=row[5],
                        tuples_fetched=row[6],
                        is_unique=row[7],
                        definition=row[8],
                    )
                )

            return unused_indexes

        except Exception as e:
            logger.error(f"Error finding unused indexes: {e}")
            return []

    def get_index_usage_stats(self) -> list[IndexUsageStats]:
        """
        Get usage statistics for all indexes.

        Returns:
            List of index usage statistics
        """
        query = text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid::regclass))::text as size,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_index.indisunique,
                pg_get_indexdef(indexrelid) as definition
            FROM pg_stat_user_indexes
            JOIN pg_index ON pg_stat_user_indexes.indexrelid = pg_index.indexrelid
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC, pg_relation_size(indexrelid) DESC
        """)

        try:
            result = self.db.execute(query)
            stats = []

            for row in result:
                size_str = row[3]
                size_mb = self._parse_size_to_mb(size_str)

                stats.append(
                    IndexUsageStats(
                        schema_name=row[0],
                        table_name=row[1],
                        index_name=row[2],
                        index_size_mb=size_mb,
                        scans=row[4],
                        tuples_read=row[5],
                        tuples_fetched=row[6],
                        is_unique=row[7],
                        definition=row[8],
                    )
                )

            return stats

        except Exception as e:
            logger.error(f"Error getting index usage stats: {e}")
            return []

    def analyze_table_statistics(
        self, table_name: str
    ) -> dict[str, Any]:
        """
        Get detailed statistics for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table statistics
        """
        query = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))::text as total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename))::text as table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                              pg_relation_size(schemaname||'.'||tablename))::text as indexes_size,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del,
                n_live_tup,
                n_dead_tup,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE tablename = :table_name
        """)

        try:
            result = self.db.execute(query, {"table_name": table_name}).fetchone()

            if not result:
                return {}

            return {
                "schema": result[0],
                "table": result[1],
                "total_size": result[2],
                "table_size": result[3],
                "indexes_size": result[4],
                "sequential_scans": result[5],
                "sequential_tuples_read": result[6],
                "index_scans": result[7],
                "index_tuples_fetched": result[8],
                "inserts": result[9],
                "updates": result[10],
                "deletes": result[11],
                "live_tuples": result[12],
                "dead_tuples": result[13],
                "last_vacuum": result[14],
                "last_autovacuum": result[15],
                "last_analyze": result[16],
                "last_autoanalyze": result[17],
                "scan_ratio": (
                    result[7] / (result[5] + result[7])
                    if (result[5] + result[7]) > 0
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {e}")
            return {}

    def _get_sequential_scan_tables(
        self, min_size_mb: float
    ) -> list[dict[str, Any]]:
        """
        Get tables with high sequential scan counts.

        Args:
            min_size_mb: Minimum table size to consider

        Returns:
            List of table information dictionaries
        """
        query = text("""
            SELECT
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                n_live_tup,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename))::text as size,
                pg_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
                AND seq_scan > idx_scan
                AND n_live_tup > 1000
                AND pg_relation_size(schemaname||'.'||tablename) > :min_size_bytes
            ORDER BY seq_scan DESC
            LIMIT 20
        """)

        try:
            result = self.db.execute(
                query, {"min_size_bytes": min_size_mb * 1024 * 1024}
            )

            tables = []
            for row in result:
                tables.append(
                    {
                        "schema": row[0],
                        "table": row[1],
                        "seq_scan": row[2],
                        "seq_tup_read": row[3],
                        "idx_scan": row[4],
                        "live_tuples": row[5],
                        "size": row[6],
                        "size_bytes": row[7],
                    }
                )

            return tables

        except Exception as e:
            logger.error(f"Error getting sequential scan tables: {e}")
            return []

    def _recommend_indexes_for_table(
        self, table_info: dict[str, Any]
    ) -> list[IndexRecommendation]:
        """
        Recommend indexes for a specific table.

        Args:
            table_info: Table statistics

        Returns:
            List of index recommendations
        """
        recommendations = []
        table_name = table_info["table"]

        # Common patterns for this application
        common_patterns = {
            "assignments": [
                (["person_id", "block_id"], "Frequent joins and lookups"),
                (["block_id", "person_id"], "Reverse join pattern"),
            ],
            "blocks": [
                (["date"], "Date range queries"),
                (["academic_year", "date"], "Year + date filtering"),
            ],
            "persons": [
                (["role"], "Role-based filtering"),
                (["email"], "Login lookups"),
            ],
            "swap_requests": [
                (["status", "created_at"], "Status filtering with ordering"),
                (["requester_id", "status"], "User's active swaps"),
            ],
            "leave_requests": [
                (["person_id", "status"], "User leave lookups"),
                (["start_date", "end_date"], "Date range overlap checks"),
            ],
        }

        if table_name in common_patterns:
            for columns, reason in common_patterns[table_name]:
                # Check if index already exists
                if not self._index_exists(table_name, columns):
                    priority = "high" if table_info["seq_scan"] > 10000 else "medium"

                    recommendations.append(
                        IndexRecommendation(
                            table_name=table_name,
                            columns=columns,
                            index_type="btree",
                            priority=priority,
                            reason=f"{reason} (seq_scan: {table_info['seq_scan']})",
                            estimated_benefit=self._estimate_benefit(table_info),
                            create_statement=self._generate_create_index_sql(
                                table_name, columns, "btree"
                            ),
                            current_usage_stats=table_info,
                        )
                    )

        return recommendations

    def _analyze_slow_query_patterns(self) -> list[IndexRecommendation]:
        """
        Analyze slow query patterns from pg_stat_statements.

        Returns:
            List of index recommendations
        """
        # This would require pg_stat_statements extension
        # For now, return empty list
        # In production, you'd parse query patterns and suggest indexes
        return []

    def _index_exists(self, table_name: str, columns: list[str]) -> bool:
        """
        Check if an index exists on the given columns.

        Args:
            table_name: Table name
            columns: Column names

        Returns:
            True if index exists
        """
        query = text("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE schemaname = 'public'
                AND tablename = :table_name
                AND indexdef ILIKE :pattern
        """)

        try:
            # Build pattern to match column order
            column_pattern = f"%({', '.join(columns)})%"

            result = self.db.execute(
                query, {"table_name": table_name, "pattern": column_pattern}
            ).scalar()

            return result > 0

        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return True  # Assume exists to avoid duplicate recommendations

    def _generate_create_index_sql(
        self, table_name: str, columns: list[str], index_type: str
    ) -> str:
        """
        Generate CREATE INDEX statement.

        Args:
            table_name: Table name
            columns: Column names
            index_type: Index type (btree, hash, etc.)

        Returns:
            CREATE INDEX SQL statement
        """
        index_name = f"idx_{table_name}_{'_'.join(columns)}"
        columns_str = ", ".join(columns)

        return (
            f"CREATE INDEX {index_name} ON {table_name} "
            f"USING {index_type} ({columns_str});"
        )

    def _estimate_benefit(self, table_info: dict[str, Any]) -> str:
        """
        Estimate the benefit of adding an index.

        Args:
            table_info: Table statistics

        Returns:
            Benefit estimate description
        """
        seq_scan = table_info.get("seq_scan", 0)
        live_tuples = table_info.get("live_tuples", 0)

        if seq_scan > 10000 and live_tuples > 10000:
            return "Very High - Frequent scans on large table"
        elif seq_scan > 5000:
            return "High - Frequent sequential scans"
        elif seq_scan > 1000:
            return "Medium - Moderate scan frequency"
        else:
            return "Low - Low scan frequency"

    def _parse_size_to_mb(self, size_str: str) -> float:
        """
        Parse PostgreSQL size string to MB.

        Args:
            size_str: Size string (e.g., "15 MB", "2048 kB")

        Returns:
            Size in MB
        """
        try:
            # Extract number and unit
            match = re.match(r"([\d.]+)\s*(\w+)", size_str)
            if not match:
                return 0.0

            value = float(match.group(1))
            unit = match.group(2).upper()

            # Convert to MB
            conversions = {
                "BYTES": 1 / (1024 * 1024),
                "KB": 1 / 1024,
                "MB": 1,
                "GB": 1024,
                "TB": 1024 * 1024,
            }

            return value * conversions.get(unit, 1)

        except Exception:
            return 0.0
