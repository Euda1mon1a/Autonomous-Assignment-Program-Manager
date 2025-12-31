"""
Database statistics commands.
"""

import asyncio

import typer
from rich.console import Console
from sqlalchemy import text

from cli.utils.output import print_table, print_error
from cli.utils.database import get_db_manager

app = typer.Typer()
console = Console()


@app.command()
def overview():
    """Show database statistics overview."""
    asyncio.run(show_overview())


@app.command()
def tables(
    top: int = typer.Option(10, "--top", "-n", help="Show top N tables"),
):
    """Show table statistics."""
    asyncio.run(show_table_stats(top))


@app.command()
def indexes():
    """Show index statistics."""
    asyncio.run(show_index_stats())


@app.command()
def cache():
    """Show cache hit statistics."""
    asyncio.run(show_cache_stats())


async def show_overview():
    """Show database overview statistics."""
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            # Database size
            result = await session.execute(
                text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            )
            db_size = result.scalar()

            # Total tables
            result = await session.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            table_count = result.scalar()

            # Total rows (approximate)
            result = await session.execute(
                text(
                    """
                    SELECT SUM(n_live_tup)
                    FROM pg_stat_user_tables
                    """
                )
            )
            total_rows = result.scalar() or 0

            # Active connections
            result = await session.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            )
            active_conn = result.scalar()

            # Total connections
            result = await session.execute(
                text("SELECT count(*) FROM pg_stat_activity")
            )
            total_conn = result.scalar()

            stats = [
                {"metric": "Database Size", "value": db_size},
                {"metric": "Tables", "value": table_count},
                {"metric": "Total Rows (approx)", "value": f"{total_rows:,}"},
                {"metric": "Active Connections", "value": active_conn},
                {"metric": "Total Connections", "value": total_conn},
            ]

            print_table(stats, title="Database Overview", columns=["metric", "value"])

    except Exception as e:
        print_error(f"Failed to get overview: {str(e)}")
        raise typer.Exit(1)


async def show_table_stats(top: int):
    """Show table statistics."""
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            result = await session.execute(
                text(
                    f"""
                    SELECT
                        schemaname || '.' || tablename AS table_name,
                        n_live_tup AS rows,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                                      pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
                    FROM pg_stat_user_tables
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT {top}
                    """
                )
            )

            stats = []
            for row in result:
                stats.append(
                    {
                        "table": row[0].replace("public.", ""),
                        "rows": f"{row[1]:,}",
                        "total": row[2],
                        "table_size": row[3],
                        "indexes": row[4],
                    }
                )

            print_table(
                stats,
                title=f"Top {top} Tables by Size",
                columns=["table", "rows", "total", "table_size", "indexes"],
            )

    except Exception as e:
        print_error(f"Failed to get table stats: {str(e)}")
        raise typer.Exit(1)


async def show_index_stats():
    """Show index usage statistics."""
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            result = await session.execute(
                text(
                    """
                    SELECT
                        schemaname || '.' || tablename AS table_name,
                        indexrelname AS index_name,
                        idx_scan AS scans,
                        idx_tup_read AS tuples_read,
                        idx_tup_fetch AS tuples_fetched,
                        pg_size_pretty(pg_relation_size(indexrelid)) AS size
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                    LIMIT 15
                    """
                )
            )

            stats = []
            for row in result:
                stats.append(
                    {
                        "table": row[0].replace("public.", ""),
                        "index": row[1],
                        "scans": f"{row[2]:,}",
                        "tuples_read": f"{row[3]:,}",
                        "size": row[5],
                    }
                )

            print_table(
                stats,
                title="Index Usage Statistics",
                columns=["table", "index", "scans", "tuples_read", "size"],
            )

    except Exception as e:
        print_error(f"Failed to get index stats: {str(e)}")
        raise typer.Exit(1)


async def show_cache_stats():
    """Show cache hit ratio statistics."""
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            # Table cache hit ratio
            result = await session.execute(
                text(
                    """
                    SELECT
                        schemaname || '.' || tablename AS table_name,
                        heap_blks_read AS disk_reads,
                        heap_blks_hit AS cache_hits,
                        CASE
                            WHEN heap_blks_read + heap_blks_hit = 0 THEN 0
                            ELSE ROUND(100.0 * heap_blks_hit / (heap_blks_read + heap_blks_hit), 2)
                        END AS cache_hit_ratio
                    FROM pg_statio_user_tables
                    WHERE heap_blks_read + heap_blks_hit > 0
                    ORDER BY heap_blks_read + heap_blks_hit DESC
                    LIMIT 15
                    """
                )
            )

            stats = []
            for row in result:
                stats.append(
                    {
                        "table": row[0].replace("public.", ""),
                        "disk_reads": f"{row[1]:,}",
                        "cache_hits": f"{row[2]:,}",
                        "hit_ratio": f"{row[3]:.2f}%",
                    }
                )

            print_table(
                stats,
                title="Cache Hit Ratio by Table",
                columns=["table", "disk_reads", "cache_hits", "hit_ratio"],
            )

    except Exception as e:
        print_error(f"Failed to get cache stats: {str(e)}")
        raise typer.Exit(1)
