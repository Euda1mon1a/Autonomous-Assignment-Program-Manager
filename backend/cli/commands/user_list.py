"""
User listing commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_table, print_json
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def all(
    role: str = typer.Option(None, "--role", "-r", help="Filter by role"),
    active: bool = typer.Option(None, "--active", help="Filter by active status"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table/json)"),
    limit: int = typer.Option(100, "--limit", "-n", help="Maximum results"),
):
    """
    List all users.

    Args:
        role: Filter by role
        active: Filter by active status
        format: Output format
        limit: Maximum results
    """
    asyncio.run(list_all_users(role, active, format, limit))


@app.command()
def residents(
    pgy_level: str = typer.Option(None, "--pgy", help="Filter by PGY level"),
    format: str = typer.Option("table", "--format", "-f", help="Output format"),
):
    """
    List all residents.

    Args:
        pgy_level: Filter by PGY level
        format: Output format
    """
    asyncio.run(list_residents(pgy_level, format))


@app.command()
def faculty(
    format: str = typer.Option("table", "--format", "-f", help="Output format"),
):
    """
    List all faculty.

    Args:
        format: Output format
    """
    asyncio.run(list_faculty(format))


@app.command()
def inactive(
    days: int = typer.Option(90, "--days", "-d", help="Inactive for N days"),
):
    """
    List inactive users.

    Args:
        days: Number of days inactive
    """
    asyncio.run(list_inactive_users(days))


async def list_all_users(
    role: str = None, active: bool = None, format: str = "table", limit: int = 100
):
    """
    List all users.

    Args:
        role: Role filter
        active: Active filter
        format: Output format
        limit: Result limit
    """
    api = APIClient()

    try:
        params = {"limit": limit}

        if role:
            params["role"] = role.upper()

        if active is not None:
            params["active"] = active

        response = api.get("/api/v1/users", params=params)
        users = response.get("users", [])

        if not users:
            console.print("[yellow]No users found[/yellow]")
            return

        if format == "json":
            print_json(users)
        else:
            print_table(
                users,
                title="Users",
                columns=["id", "email", "first_name", "last_name", "role", "pgy_level", "is_active"],
            )

    except Exception as e:
        print_error(f"Failed to list users: {str(e)}")
        raise typer.Exit(1)


async def list_residents(pgy_level: str = None, format: str = "table"):
    """
    List residents.

    Args:
        pgy_level: PGY level filter
        format: Output format
    """
    api = APIClient()

    try:
        params = {"role": "RESIDENT"}

        if pgy_level:
            params["pgy_level"] = pgy_level

        response = api.get("/api/v1/users", params=params)
        residents = response.get("users", [])

        if not residents:
            console.print("[yellow]No residents found[/yellow]")
            return

        if format == "json":
            print_json(residents)
        else:
            print_table(
                residents,
                title="Residents",
                columns=["id", "first_name", "last_name", "email", "pgy_level", "is_active"],
            )

    except Exception as e:
        print_error(f"Failed to list residents: {str(e)}")
        raise typer.Exit(1)


async def list_faculty(format: str = "table"):
    """
    List faculty.

    Args:
        format: Output format
    """
    api = APIClient()

    try:
        response = api.get("/api/v1/users", params={"role": "FACULTY"})
        faculty = response.get("users", [])

        if not faculty:
            console.print("[yellow]No faculty found[/yellow]")
            return

        if format == "json":
            print_json(faculty)
        else:
            print_table(
                faculty,
                title="Faculty",
                columns=["id", "first_name", "last_name", "email", "is_active"],
            )

    except Exception as e:
        print_error(f"Failed to list faculty: {str(e)}")
        raise typer.Exit(1)


async def list_inactive_users(days: int):
    """
    List inactive users.

    Args:
        days: Days inactive
    """
    api = APIClient()

    try:
        response = api.get("/api/v1/users/inactive", params={"days": days})
        inactive = response.get("users", [])

        if not inactive:
            console.print(f"[green]No users inactive for {days} days[/green]")
            return

        print_table(
            inactive,
            title=f"Inactive Users ({days} days)",
            columns=["id", "email", "last_login", "days_inactive"],
        )

    except Exception as e:
        print_error(f"Failed to list inactive users: {str(e)}")
        raise typer.Exit(1)
