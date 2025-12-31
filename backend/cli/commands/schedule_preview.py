"""
Schedule preview commands.
"""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from cli.utils.output import print_error, print_info, print_table
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def block(
    block_number: int = typer.Argument(..., help="Block number to preview"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    format: str = typer.Option("table", "--format", "-f", help="Format (table/calendar)"),
):
    """
    Preview schedule for a block.

    Args:
        block_number: Block number
        year: Academic year
        format: Display format
    """
    asyncio.run(preview_block_schedule(block_number, year, format))


@app.command()
def person(
    person_id: str = typer.Argument(..., help="Person ID"),
    weeks: int = typer.Option(4, "--weeks", "-w", help="Number of weeks to show"),
):
    """
    Preview schedule for a person.

    Args:
        person_id: Person ID
        weeks: Number of weeks to display
    """
    asyncio.run(preview_person_schedule(person_id, weeks))


@app.command()
def calendar(
    block_number: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Show calendar view of schedule.

    Args:
        block_number: Block number
        year: Academic year
    """
    asyncio.run(show_calendar_view(block_number, year))


def show_status():
    """Show current schedule status."""
    console.print("[cyan]Current Schedule Status[/cyan]")

    # Placeholder - would show actual status
    console.print("Block 10: In progress")
    console.print("Completion: 75%")


async def preview_block_schedule(block: int, year: int, format: str):
    """
    Preview block schedule.

    Args:
        block: Block number
        year: Academic year
        format: Display format
    """
    api = APIClient()

    try:
        print_info(f"Loading Block {block} schedule...")

        # Get schedule data
        response = api.get(
            f"/api/v1/schedules/block/{block}",
            params={"year": year},
        )

        assignments = response.get("assignments", [])

        if not assignments:
            print_info("No assignments found for this block")
            return

        console.print(f"\n[bold]Block {block} Schedule ({year})[/bold]")
        console.print(f"Total assignments: {len(assignments)}\n")

        if format == "table":
            # Table view
            print_table(
                assignments,
                columns=["person_id", "rotation", "start_date", "end_date"],
            )
        elif format == "calendar":
            # Calendar view
            show_calendar(assignments)

    except Exception as e:
        print_error(f"Preview failed: {str(e)}")
        raise typer.Exit(1)


async def preview_person_schedule(person_id: str, weeks: int):
    """
    Preview person's schedule.

    Args:
        person_id: Person ID
        weeks: Number of weeks
    """
    api = APIClient()

    try:
        print_info(f"Loading schedule for {person_id}...")

        response = api.get(
            f"/api/v1/schedules/person/{person_id}",
            params={"weeks": weeks},
        )

        assignments = response.get("assignments", [])

        if not assignments:
            print_info(f"No assignments found for {person_id}")
            return

        console.print(f"\n[bold]{person_id} Schedule[/bold]")
        console.print(f"Next {weeks} weeks\n")

        print_table(
            assignments,
            columns=["date", "rotation", "shift_type", "hours"],
        )

    except Exception as e:
        print_error(f"Preview failed: {str(e)}")
        raise typer.Exit(1)


async def show_calendar_view(block: int, year: int):
    """
    Show calendar view of schedule.

    Args:
        block: Block number
        year: Academic year
    """
    print_info("Generating calendar view...")

    # Placeholder - would generate actual calendar
    console.print(f"\nBlock {block} Calendar ({year})")
    console.print("=" * 70)

    # Mock calendar display
    console.print("Week 1: Mon | Tue | Wed | Thu | Fri | Sat | Sun")
    console.print("        IP  | IP  | IP  | IP  | IP  | OFF | OFF")

    print_info("Calendar view is a placeholder - full implementation pending")


def show_calendar(assignments: list):
    """
    Display assignments in calendar format.

    Args:
        assignments: List of assignments
    """
    # Simplified calendar view
    table = Table(title="Schedule Calendar")

    table.add_column("Person", style="cyan")
    table.add_column("Week 1", style="green")
    table.add_column("Week 2", style="green")
    table.add_column("Week 3", style="green")
    table.add_column("Week 4", style="green")

    # Group by person
    by_person = {}
    for assignment in assignments:
        person = assignment["person_id"]
        if person not in by_person:
            by_person[person] = []
        by_person[person].append(assignment)

    # Display
    for person, assigns in by_person.items():
        # Simplified - just show rotation names
        rotations = [a.get("rotation", "-") for a in assigns[:4]]
        while len(rotations) < 4:
            rotations.append("-")

        table.add_row(person, *rotations)

    console.print(table)
