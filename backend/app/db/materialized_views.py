"""Materialized view management for performance optimization.

Provides utilities for creating and managing PostgreSQL materialized views
for frequently accessed, expensive queries.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MaterializedViewManager:
    """Manager for PostgreSQL materialized views."""

    def __init__(self, session: AsyncSession):
        """Initialize materialized view manager.

        Args:
            session: Database session
        """
        self.session = session
        self.views: dict[str, dict] = {}

    async def create_view(
        self,
        view_name: str,
        query: str,
        refresh_interval: timedelta | None = None,
    ) -> None:
        """Create a materialized view.

        Args:
            view_name: Name for the materialized view
            query: SELECT query for the view
            refresh_interval: How often to refresh (None = manual only)
        """
        # Drop existing view if it exists
        await self.drop_view(view_name, if_exists=True)

        # Create materialized view
        create_sql = f"""
            CREATE MATERIALIZED VIEW {view_name}
            AS {query}
            WITH DATA
        """
        await self.session.execute(text(create_sql))
        await self.session.commit()

        # Store metadata
        self.views[view_name] = {
            "created_at": datetime.utcnow(),
            "last_refresh": datetime.utcnow(),
            "refresh_interval": refresh_interval,
            "query": query,
        }

        logger.info(f"Created materialized view: {view_name}")

    async def refresh_view(
        self,
        view_name: str,
        concurrently: bool = True,
    ) -> None:
        """Refresh a materialized view.

        Args:
            view_name: Name of the view to refresh
            concurrently: If True, allows concurrent reads during refresh
        """
        concurrent_str = "CONCURRENTLY" if concurrently else ""
        refresh_sql = f"REFRESH MATERIALIZED VIEW {concurrent_str} {view_name}"

        await self.session.execute(text(refresh_sql))
        await self.session.commit()

        # Update metadata
        if view_name in self.views:
            self.views[view_name]["last_refresh"] = datetime.utcnow()

        logger.info(f"Refreshed materialized view: {view_name}")

    async def drop_view(
        self,
        view_name: str,
        if_exists: bool = True,
    ) -> None:
        """Drop a materialized view.

        Args:
            view_name: Name of the view to drop
            if_exists: If True, don't error if view doesn't exist
        """
        if_exists_str = "IF EXISTS" if if_exists else ""
        drop_sql = f"DROP MATERIALIZED VIEW {if_exists_str} {view_name}"

        await self.session.execute(text(drop_sql))
        await self.session.commit()

        # Remove metadata
        self.views.pop(view_name, None)

        logger.info(f"Dropped materialized view: {view_name}")

    async def create_index_on_view(
        self,
        view_name: str,
        index_name: str,
        columns: list[str],
        unique: bool = False,
    ) -> None:
        """Create an index on a materialized view.

        Args:
            view_name: Name of the materialized view
            index_name: Name for the index
            columns: Columns to index
            unique: If True, create unique index
        """
        unique_str = "UNIQUE" if unique else ""
        columns_str = ", ".join(columns)

        create_index_sql = f"""
            CREATE {unique_str} INDEX {index_name}
            ON {view_name} ({columns_str})
        """

        await self.session.execute(text(create_index_sql))
        await self.session.commit()

        logger.info(f"Created index {index_name} on view {view_name}")

    async def needs_refresh(self, view_name: str) -> bool:
        """Check if a view needs refreshing based on interval.

        Args:
            view_name: Name of the view

        Returns:
            True if view should be refreshed
        """
        if view_name not in self.views:
            return False

        metadata = self.views[view_name]
        refresh_interval = metadata.get("refresh_interval")

        if refresh_interval is None:
            return False

        last_refresh = metadata.get("last_refresh")
        if last_refresh is None:
            return True

        return datetime.utcnow() - last_refresh > refresh_interval

    async def auto_refresh_all(self) -> list[str]:
        """Refresh all views that need refreshing.

        Returns:
            List of refreshed view names
        """
        refreshed = []

        for view_name in self.views:
            if await self.needs_refresh(view_name):
                await self.refresh_view(view_name)
                refreshed.append(view_name)

        return refreshed


# Pre-defined materialized views for common queries


async def create_schedule_summary_view(manager: MaterializedViewManager):
    """Create materialized view for schedule summary statistics."""
    query = """
        SELECT
            b.date,
            b.is_am,
            r.name as rotation_name,
            COUNT(DISTINCT a.person_id) as person_count,
            COUNT(*) as assignment_count
        FROM blocks b
        LEFT JOIN assignments a ON a.block_id = b.id
        LEFT JOIN rotations r ON a.rotation_id = r.id
        WHERE b.date >= CURRENT_DATE - INTERVAL '90 days'
          AND b.date <= CURRENT_DATE + INTERVAL '365 days'
        GROUP BY b.date, b.is_am, r.name
    """

    await manager.create_view(
        "mv_schedule_summary",
        query,
        refresh_interval=timedelta(hours=1),
    )

    # Create index for fast date lookups
    await manager.create_index_on_view(
        "mv_schedule_summary",
        "idx_mv_schedule_summary_date",
        ["date", "is_am"],
    )


async def create_person_workload_view(manager: MaterializedViewManager):
    """Create materialized view for person workload statistics."""
    query = """
        SELECT
            p.id as person_id,
            p.name,
            p.type as person_type,
            COUNT(*) as total_assignments,
            COUNT(*) FILTER (WHERE b.date >= CURRENT_DATE) as future_assignments,
            MIN(b.date) as first_assignment_date,
            MAX(b.date) as last_assignment_date
        FROM persons p
        LEFT JOIN assignments a ON a.person_id = p.id
        LEFT JOIN blocks b ON a.block_id = b.id
        WHERE b.date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY p.id, p.name, p.type
    """

    await manager.create_view(
        "mv_person_workload",
        query,
        refresh_interval=timedelta(hours=6),
    )

    # Create index for fast person lookups
    await manager.create_index_on_view(
        "mv_person_workload",
        "idx_mv_person_workload_person_id",
        ["person_id"],
        unique=True,
    )


async def create_rotation_coverage_view(manager: MaterializedViewManager):
    """Create materialized view for rotation coverage analysis."""
    query = """
        SELECT
            r.id as rotation_id,
            r.name as rotation_name,
            b.date,
            COUNT(a.id) as coverage_count,
            CASE
                WHEN COUNT(a.id) = 0 THEN 'uncovered'
                WHEN COUNT(a.id) < r.min_people THEN 'understaffed'
                WHEN COUNT(a.id) > r.max_people THEN 'overstaffed'
                ELSE 'adequate'
            END as coverage_status
        FROM rotations r
        CROSS JOIN blocks b
        LEFT JOIN assignments a ON a.rotation_id = r.id AND a.block_id = b.id
        WHERE b.date >= CURRENT_DATE
          AND b.date <= CURRENT_DATE + INTERVAL '90 days'
        GROUP BY r.id, r.name, b.date, r.min_people, r.max_people
    """

    await manager.create_view(
        "mv_rotation_coverage",
        query,
        refresh_interval=timedelta(hours=1),
    )

    # Create indexes for common query patterns
    await manager.create_index_on_view(
        "mv_rotation_coverage",
        "idx_mv_rotation_coverage_rotation",
        ["rotation_id", "date"],
    )

    await manager.create_index_on_view(
        "mv_rotation_coverage",
        "idx_mv_rotation_coverage_status",
        ["coverage_status", "date"],
    )
