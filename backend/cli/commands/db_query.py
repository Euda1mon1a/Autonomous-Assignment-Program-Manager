"""
Database query commands for quick data inspection.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from sqlalchemy import text

from cli.utils.output import print_table, print_error, print_json
from cli.utils.database import get_db_manager

app = typer.Typer()
console = Console()


@app.command()
def execute(
    query: str = typer.Argument(..., help="SQL query to execute"),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format (table/json)"
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum rows to return"),
):
    """
    Execute a SQL query and display results.

    Args:
        query: SQL query string
        format: Output format (table or json)
        limit: Maximum rows to return
    """
    asyncio.run(execute_query(query, format, limit))


@app.command()
def persons(
    role: str | None = typer.Option(None, "--role", "-r", help="Filter by role"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum rows"),
):
    """Quick view of persons table."""
    query = "SELECT id, first_name, last_name, email, role, pgy_level FROM persons"

    if role:
        query += f" WHERE role = '{role.upper()}'"

    query += f" LIMIT {limit}"

    asyncio.run(execute_query(query, "table", limit))


@app.command()
def assignments(
    person_id: str | None = typer.Option(
        None, "--person", "-p", help="Filter by person ID"
    ),
    block: int | None = typer.Option(None, "--block", "-b", help="Filter by block"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum rows"),
):
    """Quick view of assignments table."""
    query = """
    SELECT
        a.id,
        a.person_id,
        a.block_id,
        a.rotation_id,
        a.start_date,
        a.end_date
    FROM assignments a
    WHERE 1=1
    """

    if person_id:
        query += f" AND a.person_id = '{person_id}'"

    if block:
        query += f" AND a.block_id = {block}"

    query += f" ORDER BY a.start_date DESC LIMIT {limit}"

    asyncio.run(execute_query(query, "table", limit))


@app.command()
def rotations():
    """Quick view of rotations table."""
    query = "SELECT id, name, description, color FROM rotations ORDER BY name"
    asyncio.run(execute_query(query, "table", 100))


@app.command()
def blocks(
    year: int | None = typer.Option(
        None, "--year", "-y", help="Filter by academic year"
    ),
):
    """Quick view of blocks table."""
    query = "SELECT block_number, start_date, end_date, academic_year FROM blocks"

    if year:
        query += f" WHERE academic_year = {year}"

    query += " ORDER BY start_date"

    asyncio.run(execute_query(query, "table", 100))


async def execute_query(query: str, format: str, limit: int):
    """
    Execute SQL query and display results.

    Args:
        query: SQL query
        format: Output format
        limit: Row limit
    """
    db_manager = get_db_manager()

    try:
        async for session in db_manager.get_session():
            result = await session.execute(text(query))

            # Fetch results
            rows = result.fetchmany(limit)

            if not rows:
                console.print("[yellow]No results[/yellow]")
                return

            # Get column names
            columns = list(result.keys())

            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]

            # Display
            if format == "json":
                print_json(data)
            else:
                print_table(data, columns=columns)

    except Exception as e:
        print_error(f"Query failed: {str(e)}")
        raise typer.Exit(1)
