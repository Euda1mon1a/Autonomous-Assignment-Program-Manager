"""Database administration and optimization API routes.

Provides endpoints for database performance monitoring, query analysis,
and optimization recommendations. Restricted to admin users only.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.auth.permissions.decorators import require_role
from app.db.optimization import IndexAdvisor, QueryAnalyzer
from app.db.optimization.query_builder import OptimizedQueryBuilder
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class ConnectionPoolStats(BaseModel):
    """Connection pool statistics."""

    pool_size: int = Field(..., description="Configured pool size")
    max_overflow: int = Field(..., description="Maximum overflow connections")
    checked_out: int = Field(..., description="Currently checked out connections")
    overflow: int = Field(..., description="Current overflow connections")
    total_connections: int = Field(..., description="Total connections")
    utilization_percent: float = Field(..., description="Pool utilization percentage")


class IndexRecommendationResponse(BaseModel):
    """Index recommendation."""

    table_name: str
    columns: list[str]
    index_type: str
    priority: str
    reason: str
    estimated_benefit: str
    create_statement: str


class IndexUsageStatsResponse(BaseModel):
    """Index usage statistics."""

    schema_name: str
    table_name: str
    index_name: str
    index_size_mb: float
    scans: int
    tuples_read: int
    tuples_fetched: int
    is_unique: bool
    definition: str


class TableStatisticsResponse(BaseModel):
    """Table statistics."""

    schema: str
    table: str
    total_size: str
    table_size: str
    indexes_size: str
    sequential_scans: int
    sequential_tuples_read: int
    index_scans: int
    index_tuples_fetched: int
    inserts: int
    updates: int
    deletes: int
    live_tuples: int
    dead_tuples: int
    scan_ratio: float
    last_vacuum: Optional[str] = None
    last_autovacuum: Optional[str] = None
    last_analyze: Optional[str] = None
    last_autoanalyze: Optional[str] = None


class QueryStatsResponse(BaseModel):
    """Query statistics for a request."""

    request_id: str
    total_queries: int
    total_duration_ms: float
    avg_duration_ms: float
    slow_queries: int
    n_plus_one_warnings: int
    query_types: dict[str, int]
    recommendations: list[str]


class SlowQueryInfo(BaseModel):
    """Slow query information."""

    sql: str
    duration_ms: float
    timestamp: str


class NPlusOneWarning(BaseModel):
    """N+1 query warning."""

    type: str
    query_count: int
    total_duration_ms: float
    avg_duration_ms: float
    sql_pattern: str
    recommendation: str


class DetailedQueryStats(BaseModel):
    """Detailed query statistics."""

    request_id: str
    total_queries: int
    total_duration_ms: float
    avg_duration_ms: float
    slow_queries: int
    n_plus_one_warnings: int
    n_plus_one_details: list[NPlusOneWarning]
    query_types: dict[str, int]
    slowest_queries: list[SlowQueryInfo]
    recommendations: list[str]


class DatabaseHealthResponse(BaseModel):
    """Database health check response."""

    status: str
    connection_pool: ConnectionPoolStats
    database_size_mb: float
    active_connections: int
    total_tables: int
    total_indexes: int
    recommendations: list[str]


# ============================================================================
# Routes
# ============================================================================


@router.get(
    "/db-admin/health",
    response_model=DatabaseHealthResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_database_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DatabaseHealthResponse:
    """
    Get comprehensive database health metrics.

    Requires ADMIN role.

    Returns:
        Database health information including pool stats and recommendations
    """
    try:
        from sqlalchemy import text

        # Get connection pool stats
        pool = db.get_bind().pool
        pool_stats = ConnectionPoolStats(
            pool_size=pool.size(),
            max_overflow=pool._max_overflow,
            checked_out=pool.checkedout(),
            overflow=pool.overflow(),
            total_connections=pool.checkedout() + pool.overflow(),
            utilization_percent=round(
                (pool.checkedout() + pool.overflow()) / (pool.size() + pool._max_overflow) * 100,
                2
            ),
        )

        # Get database size
        db_size_query = text("""
            SELECT pg_database_size(current_database()) / (1024.0 * 1024.0) as size_mb
        """)
        db_size_mb = db.execute(db_size_query).scalar()

        # Get active connections
        active_conn_query = text("""
            SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
        """)
        active_connections = db.execute(active_conn_query).scalar()

        # Get table count
        table_count_query = text("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        total_tables = db.execute(table_count_query).scalar()

        # Get index count
        index_count_query = text("""
            SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'
        """)
        total_indexes = db.execute(index_count_query).scalar()

        # Generate recommendations
        recommendations = []
        if pool_stats.utilization_percent > 80:
            recommendations.append(
                "Connection pool utilization high (>80%) - consider increasing pool size"
            )
        if active_connections > 50:
            recommendations.append(
                f"High number of active connections ({active_connections}) - investigate slow queries"
            )
        if db_size_mb > 10000:  # 10GB
            recommendations.append(
                f"Database size large ({db_size_mb:.1f}MB) - consider archiving old data"
            )

        status = "healthy"
        if pool_stats.utilization_percent > 90 or active_connections > 100:
            status = "warning"

        return DatabaseHealthResponse(
            status=status,
            connection_pool=pool_stats,
            database_size_mb=round(db_size_mb, 2),
            active_connections=active_connections,
            total_tables=total_tables,
            total_indexes=total_indexes,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred retrieving database health",
        )


@router.get(
    "/db-admin/indexes/recommendations",
    response_model=list[IndexRecommendationResponse],
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_index_recommendations(
    min_table_size_mb: float = Query(1.0, ge=0, description="Minimum table size to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[IndexRecommendationResponse]:
    """
    Get index recommendations based on query patterns.

    Analyzes table statistics and query patterns to suggest indexes
    that could improve performance.

    Requires ADMIN role.

    Args:
        min_table_size_mb: Only analyze tables larger than this size

    Returns:
        List of index recommendations
    """
    try:
        advisor = IndexAdvisor(db)
        recommendations = advisor.analyze_and_recommend(
            min_table_size_mb=min_table_size_mb
        )

        return [
            IndexRecommendationResponse(
                table_name=rec.table_name,
                columns=rec.columns,
                index_type=rec.index_type,
                priority=rec.priority,
                reason=rec.reason,
                estimated_benefit=rec.estimated_benefit,
                create_statement=rec.create_statement,
            )
            for rec in recommendations
        ]

    except Exception as e:
        logger.error(f"Error getting index recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred analyzing index recommendations",
        )


@router.get(
    "/db-admin/indexes/unused",
    response_model=list[IndexUsageStatsResponse],
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_unused_indexes(
    min_age_days: int = Query(7, ge=1, description="Minimum index age in days"),
    min_size_mb: float = Query(10.0, ge=0, description="Minimum index size in MB"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[IndexUsageStatsResponse]:
    """
    Find unused indexes that could be removed.

    Identifies indexes that haven't been used recently and are consuming space.

    Requires ADMIN role.

    Args:
        min_age_days: Only consider indexes older than this
        min_size_mb: Only consider indexes larger than this

    Returns:
        List of unused indexes
    """
    try:
        advisor = IndexAdvisor(db)
        unused = advisor.find_unused_indexes(
            min_age_days=min_age_days,
            min_size_mb=min_size_mb,
        )

        return [
            IndexUsageStatsResponse(
                schema_name=idx.schema_name,
                table_name=idx.table_name,
                index_name=idx.index_name,
                index_size_mb=idx.index_size_mb,
                scans=idx.scans,
                tuples_read=idx.tuples_read,
                tuples_fetched=idx.tuples_fetched,
                is_unique=idx.is_unique,
                definition=idx.definition,
            )
            for idx in unused
        ]

    except Exception as e:
        logger.error(f"Error finding unused indexes: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred finding unused indexes",
        )


@router.get(
    "/db-admin/indexes/usage",
    response_model=list[IndexUsageStatsResponse],
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_index_usage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[IndexUsageStatsResponse]:
    """
    Get usage statistics for all indexes.

    Provides comprehensive index usage data for analysis.

    Requires ADMIN role.

    Returns:
        List of index usage statistics
    """
    try:
        advisor = IndexAdvisor(db)
        stats = advisor.get_index_usage_stats()

        return [
            IndexUsageStatsResponse(
                schema_name=idx.schema_name,
                table_name=idx.table_name,
                index_name=idx.index_name,
                index_size_mb=idx.index_size_mb,
                scans=idx.scans,
                tuples_read=idx.tuples_read,
                tuples_fetched=idx.tuples_fetched,
                is_unique=idx.is_unique,
                definition=idx.definition,
            )
            for idx in stats
        ]

    except Exception as e:
        logger.error(f"Error getting index usage stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred retrieving index usage statistics",
        )


@router.get(
    "/db-admin/tables/{table_name}/stats",
    response_model=TableStatisticsResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_table_statistics(
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TableStatisticsResponse:
    """
    Get detailed statistics for a specific table.

    Provides comprehensive table metrics including size, scans, and maintenance info.

    Requires ADMIN role.

    Args:
        table_name: Name of the table to analyze

    Returns:
        Table statistics
    """
    try:
        advisor = IndexAdvisor(db)
        stats = advisor.analyze_table_statistics(table_name)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found",
            )

        return TableStatisticsResponse(
            schema=stats["schema"],
            table=stats["table"],
            total_size=stats["total_size"],
            table_size=stats["table_size"],
            indexes_size=stats["indexes_size"],
            sequential_scans=stats["sequential_scans"],
            sequential_tuples_read=stats["sequential_tuples_read"],
            index_scans=stats["index_scans"],
            index_tuples_fetched=stats["index_tuples_fetched"],
            inserts=stats["inserts"],
            updates=stats["updates"],
            deletes=stats["deletes"],
            live_tuples=stats["live_tuples"],
            dead_tuples=stats["dead_tuples"],
            scan_ratio=round(stats["scan_ratio"], 4),
            last_vacuum=str(stats["last_vacuum"]) if stats["last_vacuum"] else None,
            last_autovacuum=str(stats["last_autovacuum"]) if stats["last_autovacuum"] else None,
            last_analyze=str(stats["last_analyze"]) if stats["last_analyze"] else None,
            last_autoanalyze=str(stats["last_autoanalyze"]) if stats["last_autoanalyze"] else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting table statistics for {table_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred retrieving table statistics",
        )


@router.get(
    "/db-admin/queries/stats",
    response_model=QueryStatsResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_query_statistics(
    request_id: str = Query(..., description="Request ID to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QueryStatsResponse:
    """
    Get query statistics for a tracked request.

    Note: Requires query tracking to be enabled for the request.

    Requires ADMIN role.

    Args:
        request_id: Request identifier

    Returns:
        Query statistics
    """
    try:
        # This would require query tracking to be enabled
        # For now, return a placeholder response
        logger.info(f"Query stats requested for request_id: {request_id}")

        return QueryStatsResponse(
            request_id=request_id,
            total_queries=0,
            total_duration_ms=0.0,
            avg_duration_ms=0.0,
            slow_queries=0,
            n_plus_one_warnings=0,
            query_types={},
            recommendations=[
                "Query tracking not currently active - enable QueryAnalyzer to track queries"
            ],
        )

    except Exception as e:
        logger.error(f"Error getting query statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred retrieving query statistics",
        )


@router.post(
    "/db-admin/vacuum/{table_name}",
    dependencies=[Depends(require_role("ADMIN"))],
)
async def vacuum_table(
    table_name: str,
    analyze: bool = Query(True, description="Also run ANALYZE"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """
    Run VACUUM on a specific table.

    Reclaims storage and updates statistics.

    Requires ADMIN role.

    Args:
        table_name: Name of the table
        analyze: Whether to also run ANALYZE

    Returns:
        Success message
    """
    try:
        from sqlalchemy import text

        # Validate table name to prevent SQL injection
        if not table_name.replace("_", "").isalnum():
            raise HTTPException(
                status_code=400,
                detail="Invalid table name",
            )

        # Check if table exists
        check_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = :table_name
            )
        """)
        exists = db.execute(check_query, {"table_name": table_name}).scalar()

        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found",
            )

        # VACUUM cannot run in a transaction, so we need to commit first
        db.commit()

        # Run VACUUM
        if analyze:
            vacuum_query = text(f"VACUUM ANALYZE {table_name}")
        else:
            vacuum_query = text(f"VACUUM {table_name}")

        # Execute with autocommit
        connection = db.connection()
        connection.execute(vacuum_query)

        logger.info(f"VACUUM{'ANALYZE' if analyze else ''} completed for table {table_name}")

        return {
            "message": f"VACUUM {'ANALYZE ' if analyze else ''}completed successfully for {table_name}",
            "table": table_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running VACUUM on {table_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred running VACUUM",
        )
