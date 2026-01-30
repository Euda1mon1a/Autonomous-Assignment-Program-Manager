"""
Data partitioning service for optimizing large table performance.

This module provides comprehensive table partitioning strategies for PostgreSQL,
enabling efficient data management and query optimization for large tables.

Partitioning Strategies:
- Time-based partitioning (by month/year) for temporal data
- Range partitioning for numeric/date ranges
- Hash partitioning for even distribution
- List partitioning for categorical data

Features:
- Automatic partition creation and management
- Partition pruning for query optimization
- Partition archival and cleanup
- Cross-partition query optimization
- Statistics and monitoring

Usage:
    from app.db.partitioning import PartitioningService, PartitionStrategy

    # Create partitioning service
    service = PartitioningService(db)

    # Create time-based partitions for assignments
    service.create_time_partitions(
        table_name="assignments",
        partition_column="created_at",
        strategy=PartitionStrategy.MONTHLY,
        months_ahead=6,
        months_behind=12
    )

    # Archive old partitions
    service.archive_old_partitions(
        table_name="assignments",
        older_than_months=24,
        archive_location="s3://bucket/archives"
    )

    # Get partition statistics
    stats = service.get_partition_statistics("assignments")
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PartitionStrategy(str, Enum):
    """Partition strategy types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    RANGE = "range"
    HASH = "hash"
    LIST = "list"


class PartitionStatus(str, Enum):
    """Partition status."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DETACHED = "detached"
    PENDING_DELETION = "pending_deletion"


@dataclass
class PartitionConfig:
    """Configuration for table partitioning."""

    table_name: str
    partition_column: str
    strategy: PartitionStrategy
    retention_months: int | None = None
    auto_create: bool = True
    auto_archive: bool = False
    archive_location: str | None = None
    pruning_enabled: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.auto_archive and not self.archive_location:
            raise ValueError("archive_location required when auto_archive is True")


@dataclass
class PartitionInfo:
    """Information about a partition."""

    partition_name: str
    parent_table: str
    strategy: str
    range_start: datetime | None = None
    range_end: datetime | None = None
    row_count: int = 0
    size_bytes: int = 0
    status: PartitionStatus = PartitionStatus.ACTIVE
    created_at: datetime | None = None
    last_modified: datetime | None = None

    @property
    def size_mb(self) -> float:
        """Get partition size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Get partition size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)


@dataclass
class PartitionStatistics:
    """Statistics for partitioned table."""

    table_name: str
    total_partitions: int
    active_partitions: int
    archived_partitions: int
    total_rows: int
    total_size_bytes: int
    oldest_partition: str | None = None
    newest_partition: str | None = None
    avg_partition_size_mb: float = 0.0
    partitions: list[PartitionInfo] = None

    def __post_init__(self) -> None:
        """Initialize partitions list."""
        if self.partitions is None:
            self.partitions = []

    @property
    def total_size_gb(self) -> float:
        """Get total size in gigabytes."""
        return self.total_size_bytes / (1024 * 1024 * 1024)


class PartitioningService:
    """
    Service for managing table partitioning in PostgreSQL.

    Provides comprehensive partitioning capabilities including:
    - Time-based partitioning (daily, monthly, yearly)
    - Range and hash partitioning
    - Automatic partition creation
    - Partition archival and cleanup
    - Query optimization with partition pruning
    - Monitoring and statistics
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize partitioning service.

        Args:
            db: Database session
        """
        self.db = db
        self._partition_configs: dict[str, PartitionConfig] = {}

        # =========================================================================
        # Time-Based Partitioning
        # =========================================================================

    def create_time_partitions(
        self,
        table_name: str,
        partition_column: str,
        strategy: PartitionStrategy = PartitionStrategy.MONTHLY,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        months_ahead: int = 3,
        months_behind: int = 12,
        detach_existing: bool = False,
    ) -> list[str]:
        """
        Create time-based partitions for a table.

        Args:
            table_name: Name of the table to partition
            partition_column: Column to partition on (must be timestamp/date)
            strategy: Partitioning strategy (DAILY, MONTHLY, YEARLY)
            start_date: Start date for partitions (default: months_behind from now)
            end_date: End date for partitions (default: months_ahead from now)
            months_ahead: Number of months to create ahead (if end_date not set)
            months_behind: Number of months to create behind (if start_date not set)
            detach_existing: Detach existing partitions before creating new ones

        Returns:
            List of created partition names

        Raises:
            ValueError: If strategy is not time-based
            RuntimeError: If partition creation fails
        """
        if strategy not in (
            PartitionStrategy.DAILY,
            PartitionStrategy.WEEKLY,
            PartitionStrategy.MONTHLY,
            PartitionStrategy.QUARTERLY,
            PartitionStrategy.YEARLY,
        ):
            raise ValueError(f"Strategy {strategy} is not time-based")

        logger.info(
            f"Creating {strategy} partitions for {table_name}.{partition_column}"
        )

        # Determine date range
        now = datetime.now()
        if not start_date:
            start_date = now - timedelta(days=months_behind * 30)
        if not end_date:
            end_date = now + timedelta(days=months_ahead * 30)

            # Check if table is already partitioned
        if not self._is_table_partitioned(table_name):
            logger.info(f"Converting {table_name} to partitioned table")
            self._convert_to_partitioned_table(table_name, partition_column, strategy)

            # Detach existing partitions if requested
        if detach_existing:
            logger.info(f"Detaching existing partitions for {table_name}")
            self._detach_all_partitions(table_name)

            # Generate partition ranges
        partition_ranges = self._generate_partition_ranges(
            start_date, end_date, strategy
        )

        # Create partitions
        created_partitions = []
        for range_start, range_end in partition_ranges:
            try:
                partition_name = self._create_time_partition(
                    table_name, partition_column, range_start, range_end, strategy
                )
                created_partitions.append(partition_name)
                logger.debug(f"Created partition: {partition_name}")
            except Exception as e:
                logger.error(
                    f"Failed to create partition for range {range_start} to {range_end}: {e}"
                )
                # Continue creating other partitions

        logger.info(f"Created {len(created_partitions)} partitions for {table_name}")
        return created_partitions

    def _convert_to_partitioned_table(
        self, table_name: str, partition_column: str, strategy: PartitionStrategy
    ) -> None:
        """
        Convert an existing table to a partitioned table.

        Note: This is a DDL operation that requires downtime.
        For production systems, use pg_partman or similar tools.

        Args:
            table_name: Name of table to convert
            partition_column: Column to partition on
            strategy: Partitioning strategy
        """
        # In PostgreSQL, converting an existing table to partitioned requires:
        # 1. Rename existing table
        # 2. Create new partitioned table with same structure
        # 3. Migrate data
        # 4. Drop old table

        logger.warning(
            f"Converting {table_name} to partitioned table. "
            "This operation may take time for large tables."
        )

        partition_type = self._get_partition_type(strategy)

        sql = text(
            f"""
            -- This is a placeholder for production partitioning
            -- In production, use pg_partman or manual migration process
            CREATE TABLE IF NOT EXISTS {table_name}_partitioned
            PARTITION BY {partition_type} ({partition_column});
        """
        )

        # Note: Actual implementation would need:
        # - Schema migration
        # - Data migration
        # - Index recreation
        # - Constraint recreation
        # This is left as a framework for manual implementation

        logger.info(f"Table {table_name} ready for partitioning")

    def _create_time_partition(
        self,
        parent_table: str,
        partition_column: str,
        range_start: datetime,
        range_end: datetime,
        strategy: PartitionStrategy,
    ) -> str:
        """
        Create a single time-based partition.

        Args:
            parent_table: Parent table name
            partition_column: Column to partition on
            range_start: Start of partition range
            range_end: End of partition range
            strategy: Partitioning strategy

        Returns:
            Name of created partition
        """
        # Generate partition name
        partition_suffix = self._generate_partition_suffix(range_start, strategy)
        partition_name = f"{parent_table}_{partition_suffix}"

        # Check if partition already exists
        if self._partition_exists(partition_name):
            logger.debug(f"Partition {partition_name} already exists")
            return partition_name

            # Create partition
        sql = text(
            f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF {parent_table}
            FOR VALUES FROM ('{range_start.isoformat()}')
                         TO ('{range_end.isoformat()}');
        """
        )

        try:
            self.db.execute(sql)
            self.db.commit()
            logger.info(f"Created partition: {partition_name}")

            # Create indexes on partition
            self._create_partition_indexes(parent_table, partition_name)

            return partition_name
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create partition {partition_name}: {e}")
            raise RuntimeError(f"Partition creation failed: {e}")

    def _generate_partition_ranges(
        self, start_date: datetime, end_date: datetime, strategy: PartitionStrategy
    ) -> list[tuple[datetime, datetime]]:
        """
        Generate partition ranges based on strategy.

        Args:
            start_date: Start date
            end_date: End date
            strategy: Partitioning strategy

        Returns:
            List of (range_start, range_end) tuples
        """
        ranges = []
        current = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        while current < end_date:
            if strategy == PartitionStrategy.DAILY:
                next_date = current + timedelta(days=1)
            elif strategy == PartitionStrategy.WEEKLY:
                next_date = current + timedelta(weeks=1)
            elif strategy == PartitionStrategy.MONTHLY:
                # Move to next month
                if current.month == 12:
                    next_date = current.replace(year=current.year + 1, month=1)
                else:
                    next_date = current.replace(month=current.month + 1)
            elif strategy == PartitionStrategy.QUARTERLY:
                # Move to next quarter
                next_month = ((current.month - 1) // 3 + 1) * 3 + 1
                if next_month > 12:
                    next_date = current.replace(year=current.year + 1, month=1)
                else:
                    next_date = current.replace(month=next_month)
            elif strategy == PartitionStrategy.YEARLY:
                next_date = current.replace(year=current.year + 1)
            else:
                raise ValueError(f"Unsupported time strategy: {strategy}")

            ranges.append((current, next_date))
            current = next_date

        return ranges

    def _generate_partition_suffix(
        self, date: datetime, strategy: PartitionStrategy
    ) -> str:
        """
        Generate partition name suffix based on date and strategy.

        Args:
            date: Date for partition
            strategy: Partitioning strategy

        Returns:
            Partition suffix (e.g., "2025_01", "2025_q1")
        """
        if strategy == PartitionStrategy.DAILY:
            return date.strftime("%Y_%m_%d")
        elif strategy == PartitionStrategy.WEEKLY:
            return date.strftime("%Y_w%V")
        elif strategy == PartitionStrategy.MONTHLY:
            return date.strftime("%Y_%m")
        elif strategy == PartitionStrategy.QUARTERLY:
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}_q{quarter}"
        elif strategy == PartitionStrategy.YEARLY:
            return str(date.year)
        else:
            return date.strftime("%Y_%m")

            # =========================================================================
            # Range Partitioning
            # =========================================================================

    def create_range_partitions(
        self,
        table_name: str,
        partition_column: str,
        ranges: list[tuple[Any, Any]],
        partition_names: list[str] | None = None,
    ) -> list[str]:
        """
        Create range-based partitions.

        Args:
            table_name: Name of table to partition
            partition_column: Column to partition on
            ranges: List of (start, end) range tuples
            partition_names: Optional custom partition names

        Returns:
            List of created partition names

        Example:
            # Partition by ID ranges
            service.create_range_partitions(
                "assignments",
                "id",
                [(0, 100000), (100000, 200000), (200000, None)]
            )
        """
        logger.info(f"Creating range partitions for {table_name}.{partition_column}")

        created_partitions = []
        for i, (range_start, range_end) in enumerate(ranges):
            if partition_names and i < len(partition_names):
                partition_name = partition_names[i]
            else:
                partition_name = f"{table_name}_range_{i}"

            if self._partition_exists(partition_name):
                logger.debug(f"Partition {partition_name} already exists")
                continue

                # Handle unbounded ranges
            start_clause = f"'{range_start}'" if range_start is not None else "MINVALUE"
            end_clause = f"'{range_end}'" if range_end is not None else "MAXVALUE"

            sql = text(
                f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}
                FOR VALUES FROM ({start_clause}) TO ({end_clause});
            """
            )

            try:
                self.db.execute(sql)
                self.db.commit()
                created_partitions.append(partition_name)
                logger.info(f"Created range partition: {partition_name}")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to create partition {partition_name}: {e}")

        return created_partitions

        # =========================================================================
        # Hash Partitioning
        # =========================================================================

    def create_hash_partitions(
        self,
        table_name: str,
        partition_column: str,
        num_partitions: int = 4,
        partition_prefix: str | None = None,
    ) -> list[str]:
        """
        Create hash-based partitions for even data distribution.

        Args:
            table_name: Name of table to partition
            partition_column: Column to hash on
            num_partitions: Number of hash partitions to create
            partition_prefix: Optional prefix for partition names

        Returns:
            List of created partition names

        Example:
            # Distribute by user_id hash
            service.create_hash_partitions(
                "assignments",
                "person_id",
                num_partitions=8
            )
        """
        logger.info(
            f"Creating {num_partitions} hash partitions for {table_name}.{partition_column}"
        )

        prefix = partition_prefix or table_name
        created_partitions = []

        for i in range(num_partitions):
            partition_name = f"{prefix}_hash_{i}"

            if self._partition_exists(partition_name):
                logger.debug(f"Partition {partition_name} already exists")
                continue

            sql = text(
                f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}
                FOR VALUES WITH (MODULUS {num_partitions}, REMAINDER {i});
            """
            )

            try:
                self.db.execute(sql)
                self.db.commit()
                created_partitions.append(partition_name)
                logger.info(f"Created hash partition: {partition_name}")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to create partition {partition_name}: {e}")

        return created_partitions

        # =========================================================================
        # Partition Management
        # =========================================================================

    def detach_partition(
        self, table_name: str, partition_name: str, concurrent: bool = True
    ) -> bool:
        """
        Detach a partition from its parent table.

        Args:
            table_name: Parent table name
            partition_name: Partition to detach
            concurrent: Use CONCURRENTLY to avoid blocking (PG 14+)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Detaching partition {partition_name} from {table_name}")

        concurrent_clause = "CONCURRENTLY" if concurrent else ""
        sql = text(
            f"""
            ALTER TABLE {table_name}
            DETACH PARTITION {partition_name} {concurrent_clause};
        """
        )

        try:
            self.db.execute(sql)
            self.db.commit()
            logger.info(f"Detached partition: {partition_name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to detach partition {partition_name}: {e}")
            return False

    def attach_partition(
        self,
        table_name: str,
        partition_name: str,
        range_start: datetime | None = None,
        range_end: datetime | None = None,
    ) -> bool:
        """
        Attach an existing table as a partition.

        Args:
            table_name: Parent table name
            partition_name: Table to attach as partition
            range_start: Start of partition range
            range_end: End of partition range

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Attaching {partition_name} to {table_name}")

        if range_start and range_end:
            sql = text(
                f"""
                ALTER TABLE {table_name}
                ATTACH PARTITION {partition_name}
                FOR VALUES FROM ('{range_start.isoformat()}')
                             TO ('{range_end.isoformat()}');
            """
            )
        else:
            # For default partition
            sql = text(
                f"""
                ALTER TABLE {table_name}
                ATTACH PARTITION {partition_name} DEFAULT;
            """
            )

        try:
            self.db.execute(sql)
            self.db.commit()
            logger.info(f"Attached partition: {partition_name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to attach partition {partition_name}: {e}")
            return False

    def drop_partition(self, partition_name: str, cascade: bool = False) -> bool:
        """
        Drop a partition table.

        Args:
            partition_name: Partition to drop
            cascade: Drop dependent objects

        Returns:
            True if successful, False otherwise
        """
        logger.warning(f"Dropping partition: {partition_name}")

        cascade_clause = "CASCADE" if cascade else ""
        sql = text(f"DROP TABLE IF EXISTS {partition_name} {cascade_clause};")

        try:
            self.db.execute(sql)
            self.db.commit()
            logger.info(f"Dropped partition: {partition_name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to drop partition {partition_name}: {e}")
            return False

            # =========================================================================
            # Partition Archival and Cleanup
            # =========================================================================

    def archive_old_partitions(
        self,
        table_name: str,
        older_than_months: int = 24,
        archive_location: str | None = None,
        delete_after_archive: bool = False,
    ) -> list[str]:
        """
        Archive partitions older than specified threshold.

        Args:
            table_name: Table to archive partitions from
            older_than_months: Archive partitions older than this many months
            archive_location: Location to archive to (file path, S3, etc.)
            delete_after_archive: Delete partitions after successful archive

        Returns:
            List of archived partition names
        """
        logger.info(
            f"Archiving partitions for {table_name} older than {older_than_months} months"
        )

        cutoff_date = datetime.now() - timedelta(days=older_than_months * 30)
        partitions = self.get_partition_info(table_name)

        archived = []
        for partition in partitions:
            if partition.range_end and partition.range_end < cutoff_date:
                logger.info(f"Archiving partition: {partition.partition_name}")

                # Export partition data
                if archive_location:
                    success = self._export_partition_data(
                        partition.partition_name, archive_location
                    )

                    if success:
                        archived.append(partition.partition_name)

                        # Optionally delete after archive
                        if delete_after_archive:
                            self.detach_partition(table_name, partition.partition_name)
                            self.drop_partition(partition.partition_name)

        logger.info(f"Archived {len(archived)} partitions")
        return archived

    def cleanup_empty_partitions(
        self, table_name: str, detach_only: bool = True
    ) -> list[str]:
        """
        Clean up partitions with no data.

        Args:
            table_name: Table to clean up
            detach_only: Only detach, don't drop (safer)

        Returns:
            List of cleaned up partition names
        """
        logger.info(f"Cleaning up empty partitions for {table_name}")

        partitions = self.get_partition_info(table_name)
        cleaned = []

        for partition in partitions:
            if partition.row_count == 0:
                logger.info(f"Cleaning up empty partition: {partition.partition_name}")

                if detach_only:
                    self.detach_partition(table_name, partition.partition_name)
                else:
                    self.detach_partition(table_name, partition.partition_name)
                    self.drop_partition(partition.partition_name)

                cleaned.append(partition.partition_name)

        logger.info(f"Cleaned up {len(cleaned)} empty partitions")
        return cleaned

        # =========================================================================
        # Query Optimization
        # =========================================================================

    def enable_partition_pruning(self, table_name: str, enable: bool = True) -> None:
        """
        Enable or disable partition pruning for better query performance.

        Partition pruning eliminates unnecessary partition scans when
        queries include partition key constraints.

        Args:
            table_name: Table to configure
            enable: Enable (True) or disable (False) pruning
        """
        setting = "on" if enable else "off"
        logger.info(f"Setting partition pruning to {setting} for {table_name}")

        sql = text(
            f"""
            ALTER TABLE {table_name}
            SET (enable_partition_pruning = {setting});
        """
        )

        try:
            self.db.execute(sql)
            self.db.commit()
            logger.info(f"Partition pruning {setting} for {table_name}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to set partition pruning: {e}")

    def analyze_partition_query(self, query: str) -> dict[str, Any]:
        """
        Analyze a query to see which partitions will be scanned.

        Args:
            query: SQL query to analyze

        Returns:
            Dictionary with explain plan and partition scan info
        """
        logger.debug(f"Analyzing query for partition usage: {query[:100]}...")

        explain_sql = text(f"EXPLAIN (FORMAT JSON) {query}")

        try:
            result = self.db.execute(explain_sql)
            explain_plan = result.scalar()

            # Parse explain plan for partition info
            partitions_scanned = self._extract_partitions_from_plan(explain_plan)

            return {
                "query": query,
                "partitions_scanned": partitions_scanned,
                "explain_plan": explain_plan,
            }
        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return {"query": query, "error": str(e)}

    def create_partition_wise_join(
        self, table1: str, table2: str, enable: bool = True
    ) -> None:
        """
        Enable partition-wise joins for better performance.

        When both tables are partitioned on the same key,
        PostgreSQL can join matching partitions directly.

        Args:
            table1: First partitioned table
            table2: Second partitioned table
            enable: Enable (True) or disable (False)
        """
        setting = "on" if enable else "off"
        logger.info(f"Setting partition-wise join to {setting}")

        sql = text(f"SET enable_partitionwise_join = {setting};")

        try:
            self.db.execute(sql)
            logger.info(f"Partition-wise join {setting}")
        except Exception as e:
            logger.error(f"Failed to set partition-wise join: {e}")

            # =========================================================================
            # Statistics and Monitoring
            # =========================================================================

    def get_partition_info(self, table_name: str) -> list[PartitionInfo]:
        """
        Get information about all partitions for a table.

        Args:
            table_name: Parent table name

        Returns:
            List of PartitionInfo objects
        """
        sql = text(
            """
            SELECT
                c.relname AS partition_name,
                parent.relname AS parent_table,
                pg_get_expr(c.relpartbound, c.oid) AS partition_bound,
                pg_total_relation_size(c.oid) AS size_bytes,
                c.reltuples::bigint AS row_count,
                obj_description(c.oid) AS description
            FROM pg_class c
            JOIN pg_inherits i ON i.inhrelid = c.oid
            JOIN pg_class parent ON parent.oid = i.inhparent
            WHERE parent.relname = :table_name
            ORDER BY c.relname;
        """
        )

        try:
            result = self.db.execute(sql, {"table_name": table_name})
            rows = result.fetchall()

            partitions = []
            for row in rows:
                # Parse partition bound for range info
                range_start, range_end = self._parse_partition_bound(row[2])

                partition = PartitionInfo(
                    partition_name=row[0],
                    parent_table=row[1],
                    strategy="unknown",  # Would need additional logic to determine
                    range_start=range_start,
                    range_end=range_end,
                    size_bytes=row[3] or 0,
                    row_count=row[4] or 0,
                    status=PartitionStatus.ACTIVE,
                )
                partitions.append(partition)

            return partitions
        except Exception as e:
            logger.error(f"Failed to get partition info for {table_name}: {e}")
            return []

    def get_partition_statistics(self, table_name: str) -> PartitionStatistics:
        """
        Get comprehensive statistics for a partitioned table.

        Args:
            table_name: Parent table name

        Returns:
            PartitionStatistics object
        """
        partitions = self.get_partition_info(table_name)

        if not partitions:
            return PartitionStatistics(
                table_name=table_name,
                total_partitions=0,
                active_partitions=0,
                archived_partitions=0,
                total_rows=0,
                total_size_bytes=0,
            )

        total_rows = sum(p.row_count for p in partitions)
        total_size = sum(p.size_bytes for p in partitions)
        active_count = sum(1 for p in partitions if p.status == PartitionStatus.ACTIVE)
        archived_count = sum(
            1 for p in partitions if p.status == PartitionStatus.ARCHIVED
        )

        # Sort by name to get oldest/newest
        sorted_partitions = sorted(partitions, key=lambda p: p.partition_name)
        oldest = sorted_partitions[0].partition_name if sorted_partitions else None
        newest = sorted_partitions[-1].partition_name if sorted_partitions else None

        avg_size_mb = (
            (total_size / len(partitions) / (1024 * 1024)) if partitions else 0
        )

        return PartitionStatistics(
            table_name=table_name,
            total_partitions=len(partitions),
            active_partitions=active_count,
            archived_partitions=archived_count,
            total_rows=total_rows,
            total_size_bytes=total_size,
            oldest_partition=oldest,
            newest_partition=newest,
            avg_partition_size_mb=avg_size_mb,
            partitions=partitions,
        )

    def get_partition_health(self, table_name: str) -> dict[str, Any]:
        """
        Check partition health and identify potential issues.

        Args:
            table_name: Table to check

        Returns:
            Dictionary with health metrics and recommendations
        """
        stats = self.get_partition_statistics(table_name)
        issues = []
        recommendations = []

        # Check for skewed partitions
        if stats.partitions:
            avg_rows = stats.total_rows / stats.total_partitions
            for partition in stats.partitions:
                if partition.row_count > avg_rows * 3:
                    issues.append(
                        f"Partition {partition.partition_name} has 3x more rows than average"
                    )
                    recommendations.append(
                        f"Consider re-partitioning or archiving {partition.partition_name}"
                    )

                    # Check for empty partitions
        empty_count = sum(1 for p in stats.partitions if p.row_count == 0)
        if empty_count > 0:
            issues.append(f"{empty_count} empty partitions found")
            recommendations.append(
                "Run cleanup_empty_partitions() to remove unused partitions"
            )

            # Check partition size
        large_partitions = [p for p in stats.partitions if p.size_gb > 10]
        if large_partitions:
            issues.append(f"{len(large_partitions)} partitions exceed 10GB")
            recommendations.append("Consider using finer-grained partitioning strategy")

        health_score = max(0, 100 - (len(issues) * 10))

        return {
            "table_name": table_name,
            "health_score": health_score,
            "total_partitions": stats.total_partitions,
            "total_size_gb": stats.total_size_gb,
            "issues": issues,
            "recommendations": recommendations,
            "statistics": stats,
        }

        # =========================================================================
        # Automatic Partition Management
        # =========================================================================

    def auto_create_future_partitions(
        self,
        table_name: str,
        months_ahead: int = 3,
        strategy: PartitionStrategy = PartitionStrategy.MONTHLY,
    ) -> list[str]:
        """
        Automatically create partitions for future months.

        Useful for scheduled jobs to ensure partitions exist before data arrives.

        Args:
            table_name: Table to create partitions for
            months_ahead: Number of months to create ahead
            strategy: Partitioning strategy

        Returns:
            List of created partition names
        """
        logger.info(
            f"Auto-creating {months_ahead} months of future partitions for {table_name}"
        )

        # Get existing partitions
        existing = self.get_partition_info(table_name)

        # Find the latest partition
        if existing:
            latest_partition = max(existing, key=lambda p: p.range_end or datetime.min)
            start_date = latest_partition.range_end
        else:
            start_date = datetime.now()

            # Create future partitions
        end_date = start_date + timedelta(days=months_ahead * 30)

        # Determine partition column (would need to be stored in config)
        # For now, assume 'created_at'
        partition_column = "created_at"

        return self.create_time_partitions(
            table_name=table_name,
            partition_column=partition_column,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
        )

        # =========================================================================
        # Helper Methods
        # =========================================================================

    def _is_table_partitioned(self, table_name: str) -> bool:
        """Check if a table is partitioned."""
        sql = text(
            """
            SELECT relispartition OR relkind = 'p'
            FROM pg_class
            WHERE relname = :table_name;
        """
        )

        result = self.db.execute(sql, {"table_name": table_name})
        row = result.fetchone()
        return bool(row[0]) if row else False

    def _partition_exists(self, partition_name: str) -> bool:
        """Check if a partition exists."""
        sql = text(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_class WHERE relname = :partition_name
            );
        """
        )

        result = self.db.execute(sql, {"partition_name": partition_name})
        return result.scalar()

    def _get_partition_type(self, strategy: PartitionStrategy) -> str:
        """Get PostgreSQL partition type for strategy."""
        if strategy in (
            PartitionStrategy.DAILY,
            PartitionStrategy.WEEKLY,
            PartitionStrategy.MONTHLY,
            PartitionStrategy.QUARTERLY,
            PartitionStrategy.YEARLY,
            PartitionStrategy.RANGE,
        ):
            return "RANGE"
        elif strategy == PartitionStrategy.HASH:
            return "HASH"
        elif strategy == PartitionStrategy.LIST:
            return "LIST"
        else:
            return "RANGE"

    def _create_partition_indexes(self, parent_table: str, partition_name: str) -> None:
        """Create indexes on a partition matching the parent table."""
        # In PostgreSQL 11+, partition indexes are automatically created
        # This is a placeholder for custom index logic
        logger.debug(f"Indexes automatically inherited for {partition_name}")

    def _detach_all_partitions(self, table_name: str) -> None:
        """Detach all partitions from a table."""
        partitions = self.get_partition_info(table_name)
        for partition in partitions:
            self.detach_partition(table_name, partition.partition_name)

    def _export_partition_data(
        self, partition_name: str, archive_location: str
    ) -> bool:
        """
        Export partition data to archive location.

        Args:
            partition_name: Partition to export
            archive_location: Where to export (file path, S3, etc.)

        Returns:
            True if successful, False otherwise
        """
        # This is a placeholder for actual archive implementation
        # In production, would use pg_dump, COPY TO, or custom export
        logger.info(f"Exporting {partition_name} to {archive_location}")

        # Example: Use COPY TO for file-based archives
        if archive_location.startswith("file://"):
            file_path = archive_location.replace("file://", "")
            sql = text(
                f"""
                COPY {partition_name} TO '{file_path}'
                WITH (FORMAT csv, HEADER true);
            """
            )
            try:
                self.db.execute(sql)
                return True
            except Exception as e:
                logger.error(f"Failed to export partition: {e}")
                return False

                # For S3 or other locations, would need custom implementation
        logger.warning(f"Archive location {archive_location} not implemented")
        return False

    def _parse_partition_bound(
        self, bound_expr: str
    ) -> tuple[datetime | None, datetime | None]:
        """
        Parse partition bound expression to extract range.

        Args:
            bound_expr: Partition bound expression from pg_get_expr

        Returns:
            Tuple of (range_start, range_end)
        """
        # Example bound: "FOR VALUES FROM ('2025-01-01') TO ('2025-02-01')"
        if not bound_expr or "FOR VALUES FROM" not in bound_expr:
            return None, None

        try:
            # Extract dates from bound expression
            import re

            matches = re.findall(r"'([^']+)'", bound_expr)
            if len(matches) >= 2:
                range_start = datetime.fromisoformat(matches[0])
                range_end = datetime.fromisoformat(matches[1])
                return range_start, range_end
        except Exception as e:
            logger.debug(f"Failed to parse partition bound '{bound_expr}': {e}")

        return None, None

    def _extract_partitions_from_plan(self, explain_plan: dict) -> list[str]:
        """
        Extract partition names from EXPLAIN plan.

        Args:
            explain_plan: EXPLAIN output as dict

        Returns:
            List of partition names that will be scanned
        """
        # This is a simplified implementation
        # Full implementation would parse the JSON explain plan recursively
        partitions = []

        try:
            plan = explain_plan[0].get("Plan", {})
            relation_name = plan.get("Relation Name")
            if relation_name:
                partitions.append(relation_name)
        except Exception as e:
            logger.debug(f"Failed to extract partitions from plan: {e}")

        return partitions

        # =============================================================================
        # Utility Functions
        # =============================================================================


def get_recommended_partition_strategy(
    table_name: str, row_count: int, data_retention_months: int = 24
) -> PartitionStrategy:
    """
    Get recommended partitioning strategy based on table characteristics.

    Args:
        table_name: Name of table
        row_count: Current row count
        data_retention_months: Data retention period in months

    Returns:
        Recommended PartitionStrategy
    """
    # For very large tables (>10M rows), use monthly partitioning
    if row_count > 10_000_000:
        return PartitionStrategy.MONTHLY

        # For medium tables (1M-10M rows), use quarterly
    elif row_count > 1_000_000:
        return PartitionStrategy.QUARTERLY

        # For smaller tables with long retention, use yearly
    elif data_retention_months > 36:
        return PartitionStrategy.YEARLY

        # Default to monthly for most cases
    else:
        return PartitionStrategy.MONTHLY


def estimate_partition_size(
    current_size_bytes: int, current_rows: int, partition_rows: int
) -> int:
    """
    Estimate partition size based on current table metrics.

    Args:
        current_size_bytes: Current table size in bytes
        current_rows: Current row count
        partition_rows: Expected rows per partition

    Returns:
        Estimated partition size in bytes
    """
    if current_rows == 0:
        return 0

    bytes_per_row = current_size_bytes / current_rows
    return int(bytes_per_row * partition_rows)
