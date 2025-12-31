"""
Schedule export commands.
"""

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_info
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def block(
    block_number: int = typer.Argument(..., help="Block number to export"),
    output: Path = typer.Option("schedule.json", "--output", "-o", help="Output file"),
    format: str = typer.Option("json", "--format", "-f", help="Format (json/csv/xlsx)"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Export schedule for a block.

    Args:
        block_number: Block number
        output: Output file path
        format: Export format
        year: Academic year
    """
    asyncio.run(export_block_schedule(block_number, output, format, year))


@app.command()
def person(
    person_id: str = typer.Argument(..., help="Person ID"),
    output: Path = typer.Option(
        "person_schedule.json", "--output", "-o", help="Output file"
    ),
    format: str = typer.Option("json", "--format", "-f", help="Format (json/csv/xlsx)"),
    start_date: str = typer.Option(None, "--start", help="Start date"),
    end_date: str = typer.Option(None, "--end", help="End date"),
):
    """
    Export schedule for a person.

    Args:
        person_id: Person ID
        output: Output file
        format: Export format
        start_date: Start date (optional)
        end_date: End date (optional)
    """
    asyncio.run(export_person_schedule(person_id, output, format, start_date, end_date))


@app.command()
def year(
    year: int = typer.Argument(..., help="Academic year"),
    output: Path = typer.Option(
        "year_schedule.xlsx", "--output", "-o", help="Output file"
    ),
    format: str = typer.Option("xlsx", "--format", "-f", help="Format (json/xlsx)"),
):
    """
    Export entire year schedule.

    Args:
        year: Academic year
        output: Output file
        format: Export format
    """
    asyncio.run(export_year_schedule(year, output, format))


@app.command()
def template(
    rotation_type: str = typer.Argument(..., help="Rotation type"),
    output: Path = typer.Option("template.json", "--output", "-o", help="Output file"),
):
    """
    Export rotation template.

    Args:
        rotation_type: Rotation type
        output: Output file
    """
    asyncio.run(export_rotation_template(rotation_type, output))


async def export_block_schedule(block: int, output: Path, format: str, year: int):
    """
    Export block schedule to file.

    Args:
        block: Block number
        output: Output path
        format: Format
        year: Academic year
    """
    api = APIClient()

    try:
        print_info(f"Exporting Block {block} schedule to {output}...")

        # Get schedule data from API
        response = api.get(
            f"/api/v1/schedules/export/{block}",
            params={"year": year, "format": format},
        )

        # Write to file
        if format == "json":
            import json

            with open(output, "w") as f:
                json.dump(response, f, indent=2)
        elif format == "csv":
            import csv

            with open(output, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=response[0].keys())
                writer.writeheader()
                writer.writerows(response)
        elif format == "xlsx":
            # Would use openpyxl or similar
            print_error("XLSX export not yet implemented")
            raise typer.Exit(1)

        print_success(f"Schedule exported to {output}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise typer.Exit(1)


async def export_person_schedule(
    person_id: str,
    output: Path,
    format: str,
    start_date: str = None,
    end_date: str = None,
):
    """Export person's schedule."""
    api = APIClient()

    try:
        print_info(f"Exporting schedule for {person_id} to {output}...")

        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = api.get(f"/api/v1/schedules/person/{person_id}", params=params)

        # Write to file (similar to export_block_schedule)
        import json

        with open(output, "w") as f:
            json.dump(response, f, indent=2)

        print_success(f"Schedule exported to {output}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise typer.Exit(1)


async def export_year_schedule(year: int, output: Path, format: str):
    """Export entire year schedule."""
    api = APIClient()

    try:
        print_info(f"Exporting {year} academic year schedule to {output}...")

        response = api.get(f"/api/v1/schedules/year/{year}", params={"format": format})

        import json

        with open(output, "w") as f:
            json.dump(response, f, indent=2)

        print_success(f"Year schedule exported to {output}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise typer.Exit(1)


async def export_rotation_template(rotation_type: str, output: Path):
    """Export rotation template."""
    api = APIClient()

    try:
        print_info(f"Exporting {rotation_type} template to {output}...")

        response = api.get(f"/api/v1/rotations/template/{rotation_type}")

        import json

        with open(output, "w") as f:
            json.dump(response, f, indent=2)

        print_success(f"Template exported to {output}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise typer.Exit(1)
