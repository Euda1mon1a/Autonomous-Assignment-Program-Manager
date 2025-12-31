"""
Database maintenance commands (VACUUM, ANALYZE, REINDEX).
"""

import asyncio

import typer
from rich.console import Console
from sqlalchemy import text

from cli.utils.output import print_success, print_error, print_info
from cli.utils.progress import step
from cli.utils.database import get_db_manager

app = typer.Typer()
console = Console()


@app.command()
def vacuum(
    full: bool = typer.Option(False, "--full", help="Run VACUUM FULL (locks table)"),
    analyze: bool = typer.Option(True, "--analyze/--no-analyze", help="Run ANALYZE after VACUUM"),
    table: str = typer.Option(None, "--table", "-t", help="Specific table to vacuum"),
):
    """
    Run VACUUM to reclaim storage.

    Args:
        full: Run VACUUM FULL (slower, locks table, but reclaims more space)
        analyze: Run ANALYZE after VACUUM
        table: Specific table name (None for all tables)
    """
    asyncio.run(run_vacuum(full, analyze, table))


@app.command()
def analyze(
    table: str = typer.Option(None, "--table", "-t", help="Specific table to analyze"),
):
    """
    Run ANALYZE to update statistics.

    Args:
        table: Specific table name (None for all tables)
    """
    asyncio.run(run_analyze(table))


@app.command()
def reindex(
    table: str = typer.Option(None, "--table", "-t", help="Specific table to reindex"),
    index: str = typer.Option(None, "--index", "-i", help="Specific index to rebuild"),
):
    """
    Rebuild indexes.

    Args:
        table: Specific table name
        index: Specific index name
    """
    asyncio.run(run_reindex(table, index))


async def run_vacuum(full: bool, analyze: bool, table: str = None):
    """
    Run VACUUM operation.

    Args:
        full: VACUUM FULL flag
        analyze: Run ANALYZE after VACUUM
        table: Table name (optional)
    """
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            # Build VACUUM command
            if full:
                cmd = "VACUUM FULL"
            else:
                cmd = "VACUUM"

            if analyze:
                cmd += " ANALYZE"

            if table:
                cmd += f' "{table}"'

            print_info(f"Running: {cmd}")

            with step("Vacuuming database"):
                # VACUUM cannot run in transaction block
                await session.connection(execution_options={"isolation_level": "AUTOCOMMIT"})
                await session.execute(text(cmd))

            print_success("VACUUM completed")

    except Exception as e:
        print_error(f"VACUUM failed: {str(e)}")
        raise typer.Exit(1)


async def run_analyze(table: str = None):
    """
    Run ANALYZE operation.

    Args:
        table: Table name (optional)
    """
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            if table:
                cmd = f'ANALYZE "{table}"'
            else:
                cmd = "ANALYZE"

            print_info(f"Running: {cmd}")

            with step("Analyzing tables"):
                await session.execute(text(cmd))
                await session.commit()

            print_success("ANALYZE completed")

    except Exception as e:
        print_error(f"ANALYZE failed: {str(e)}")
        raise typer.Exit(1)


async def run_reindex(table: str = None, index: str = None):
    """
    Run REINDEX operation.

    Args:
        table: Table name (optional)
        index: Index name (optional)
    """
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            if index:
                cmd = f'REINDEX INDEX "{index}"'
            elif table:
                cmd = f'REINDEX TABLE "{table}"'
            else:
                cmd = "REINDEX DATABASE CONCURRENTLY"

            print_info(f"Running: {cmd}")

            with step("Reindexing"):
                # REINDEX cannot run in transaction block
                await session.connection(execution_options={"isolation_level": "AUTOCOMMIT"})
                await session.execute(text(cmd))

            print_success("REINDEX completed")

    except Exception as e:
        print_error(f"REINDEX failed: {str(e)}")
        raise typer.Exit(1)
