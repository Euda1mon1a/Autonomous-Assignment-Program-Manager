"""
Database health check commands.
"""

import asyncio
from datetime import datetime

import typer
from rich.console import Console
from sqlalchemy import text

from cli.utils.output import print_success, print_error, print_table
from cli.utils.database import get_db_manager

app = typer.Typer()
console = Console()


@app.command()
def check():
    """Check database health and connectivity."""
    asyncio.run(check_health())


@app.command()
def tables():
    """List all database tables."""
    asyncio.run(list_tables())


@app.command()
def connections():
    """Show active database connections."""
    asyncio.run(show_connections())


async def check_health():
    """Run health check on database."""
    from rich.table import Table

    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            # Check connection
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print_success("Database connection: OK")

            # Check version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            console.print(f"PostgreSQL version: {version.split(',')[0]}")

            # Check database size
            result = await session.execute(
                text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            )
            db_size = result.scalar()
            console.print(f"Database size: {db_size}")

            # Check table count
            result = await session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                )
            )
            table_count = result.scalar()
            console.print(f"Tables: {table_count}")

            # Check active connections
            result = await session.execute(
                text("SELECT count(*) FROM pg_stat_activity")
            )
            conn_count = result.scalar()
            console.print(f"Active connections: {conn_count}")

    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        raise typer.Exit(1)


async def list_tables():
    """List all database tables with row counts."""
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            # Get all tables
            result = await session.execute(
                text(
                    """
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                    """
                )
            )

            tables_data = []
            for row in result:
                schema, table, size = row

                # Get row count
                count_result = await session.execute(
                    text(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                )
                row_count = count_result.scalar()

                tables_data.append({
                    "table": table,
                    "rows": row_count,
                    "size": size,
                })

            print_table(tables_data, title="Database Tables", columns=["table", "rows", "size"])

    except Exception as e:
        print_error(f"Failed to list tables: {str(e)}")
        raise typer.Exit(1)


async def show_connections():
    """Show active database connections."""
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            result = await session.execute(
                text(
                    """
                    SELECT
                        pid,
                        usename,
                        application_name,
                        client_addr,
                        state,
                        query_start,
                        state_change
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                    ORDER BY query_start DESC
                    """
                )
            )

            connections_data = []
            for row in result:
                pid, user, app, addr, state, query_start, state_change = row

                connections_data.append({
                    "pid": pid,
                    "user": user,
                    "application": app or "-",
                    "address": str(addr) if addr else "local",
                    "state": state,
                    "since": query_start.strftime("%H:%M:%S") if query_start else "-",
                })

            print_table(
                connections_data,
                title="Active Connections",
                columns=["pid", "user", "application", "address", "state", "since"],
            )

    except Exception as e:
        print_error(f"Failed to show connections: {str(e)}")
        raise typer.Exit(1)
