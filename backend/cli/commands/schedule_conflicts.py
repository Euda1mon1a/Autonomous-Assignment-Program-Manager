"""
Schedule conflict detection and resolution commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_info, print_table, print_success
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def detect(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    severity: str = typer.Option(None, "--severity", "-s", help="Filter by severity (high/medium/low)"),
):
    """
    Detect scheduling conflicts.

    Args:
        block: Block number
        year: Academic year
        severity: Severity filter
    """
    asyncio.run(detect_conflicts(block, year, severity))


@app.command()
def resolve(
    conflict_id: str = typer.Argument(..., help="Conflict ID to resolve"),
    method: str = typer.Option("auto", "--method", "-m", help="Resolution method (auto/manual/suggest)"),
):
    """
    Resolve a specific conflict.

    Args:
        conflict_id: Conflict ID
        method: Resolution method
    """
    asyncio.run(resolve_conflict(conflict_id, method))


@app.command()
def person(
    person_id: str = typer.Argument(..., help="Person ID"),
    days: int = typer.Option(30, "--days", "-d", help="Days to check"),
):
    """
    Check conflicts for a specific person.

    Args:
        person_id: Person ID
        days: Number of days to check
    """
    asyncio.run(check_person_conflicts(person_id, days))


@app.command()
def double_booking(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Find double-booking conflicts.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(find_double_bookings(block, year))


async def detect_conflicts(block: int, year: int, severity: str = None):
    """
    Detect schedule conflicts.

    Args:
        block: Block number
        year: Academic year
        severity: Severity filter
    """
    api = APIClient()

    try:
        print_info(f"Detecting conflicts for Block {block}...")

        params = {"block": block, "year": year}
        if severity:
            params["severity"] = severity

        response = api.get("/api/v1/schedules/conflicts", params=params)

        conflicts = response.get("conflicts", [])

        if not conflicts:
            print_success("No conflicts detected")
            return

        console.print(f"\n[yellow]Found {len(conflicts)} conflicts[/yellow]\n")

        print_table(
            conflicts,
            title="Schedule Conflicts",
            columns=["id", "type", "person_id", "date", "severity", "description"],
        )

    except Exception as e:
        print_error(f"Conflict detection failed: {str(e)}")
        raise typer.Exit(1)


async def resolve_conflict(conflict_id: str, method: str):
    """
    Resolve a specific conflict.

    Args:
        conflict_id: Conflict ID
        method: Resolution method
    """
    api = APIClient()

    try:
        print_info(f"Resolving conflict {conflict_id}...")

        response = api.post(
            f"/api/v1/schedules/conflicts/{conflict_id}/resolve",
            json={"method": method},
        )

        if response.get("resolved"):
            print_success(f"Conflict {conflict_id} resolved")
            console.print(f"Resolution: {response.get('resolution', 'N/A')}")
        else:
            print_error("Could not resolve conflict")
            console.print(f"Reason: {response.get('reason', 'Unknown')}")

    except Exception as e:
        print_error(f"Resolution failed: {str(e)}")
        raise typer.Exit(1)


async def check_person_conflicts(person_id: str, days: int):
    """
    Check conflicts for a person.

    Args:
        person_id: Person ID
        days: Days to check
    """
    api = APIClient()

    try:
        print_info(f"Checking conflicts for {person_id} (next {days} days)...")

        response = api.get(
            f"/api/v1/schedules/conflicts/person/{person_id}",
            params={"days": days},
        )

        conflicts = response.get("conflicts", [])

        if not conflicts:
            print_success(f"No conflicts found for {person_id}")
            return

        console.print(f"\n[yellow]Found {len(conflicts)} conflicts for {person_id}[/yellow]\n")

        print_table(
            conflicts,
            columns=["date", "type", "severity", "description"],
        )

    except Exception as e:
        print_error(f"Conflict check failed: {str(e)}")
        raise typer.Exit(1)


async def find_double_bookings(block: int, year: int):
    """
    Find double-booking conflicts.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        print_info("Finding double-booking conflicts...")

        response = api.get(
            "/api/v1/schedules/conflicts/double-bookings",
            params={"block": block, "year": year},
        )

        double_bookings = response.get("double_bookings", [])

        if not double_bookings:
            print_success("No double-bookings detected")
            return

        console.print(f"\n[red]Found {len(double_bookings)} double-bookings![/red]\n")

        print_table(
            double_bookings,
            title="Double-Booking Conflicts",
            columns=["person_id", "date", "assignments", "overlap_hours"],
        )

    except Exception as e:
        print_error(f"Double-booking check failed: {str(e)}")
        raise typer.Exit(1)
