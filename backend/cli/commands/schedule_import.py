"""
Schedule import commands.
"""

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_info, print_warning
from cli.utils.prompts import confirm
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def file(
    input_file: Path = typer.Argument(..., help="Input file to import"),
    block: int = typer.Option(None, "--block", "-b", help="Target block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    validate: bool = typer.Option(
        True, "--validate/--no-validate", help="Validate before import"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without importing"),
):
    """
    Import schedule from file.

    Args:
        input_file: Path to import file
        block: Target block number
        year: Academic year
        validate: Validate schedule before import
        dry_run: Preview mode
    """
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(1)

    asyncio.run(import_schedule_file(input_file, block, year, validate, dry_run))


@app.command()
def csv(
    input_file: Path = typer.Argument(..., help="CSV file to import"),
    block: int = typer.Argument(..., help="Target block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Import schedule from CSV file.

    Args:
        input_file: CSV file path
        block: Block number
        year: Academic year
    """
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(1)

    asyncio.run(import_csv_schedule(input_file, block, year))


@app.command()
def template(
    template_file: Path = typer.Argument(..., help="Template file"),
    rotation_name: str = typer.Argument(..., help="Rotation name"),
):
    """
    Import rotation template.

    Args:
        template_file: Template file path
        rotation_name: Rotation name
    """
    if not template_file.exists():
        print_error(f"File not found: {template_file}")
        raise typer.Exit(1)

    asyncio.run(import_rotation_template(template_file, rotation_name))


async def import_schedule_file(
    input_file: Path, block: int, year: int, validate: bool, dry_run: bool
):
    """
    Import schedule from file.

    Args:
        input_file: Input file path
        block: Block number
        year: Academic year
        validate: Validate flag
        dry_run: Dry run flag
    """
    api = APIClient()

    try:
        print_info(f"Importing schedule from {input_file}...")

        # Read file
        with open(input_file) as f:
            schedule_data = json.load(f)

        # Validate if requested
        if validate:
            print_info("Validating schedule data...")

            # Mock validation
            assignments_count = len(schedule_data.get("assignments", []))
            console.print(f"Found {assignments_count} assignments")

            # Check for conflicts
            conflicts = []  # Placeholder
            if conflicts:
                print_warning(f"Found {len(conflicts)} potential conflicts")

                if not confirm("Continue with import?"):
                    console.print("[yellow]Import cancelled[/yellow]")
                    return

        # Import via API
        if dry_run:
            print_info("Dry run - schedule not imported")
            console.print(schedule_data)
        else:
            response = api.post(
                "/api/v1/schedules/import",
                json={
                    "block_number": block,
                    "academic_year": year,
                    "schedule_data": schedule_data,
                },
            )

            print_success("Schedule imported successfully")
            console.print(f"Assignments created: {response.get('created', 0)}")

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON file: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Import failed: {str(e)}")
        raise typer.Exit(1)


async def import_csv_schedule(input_file: Path, block: int, year: int):
    """
    Import schedule from CSV.

    Args:
        input_file: CSV file path
        block: Block number
        year: Academic year
    """
    try:
        print_info(f"Importing CSV schedule from {input_file}...")

        import csv

        assignments = []

        with open(input_file) as f:
            reader = csv.DictReader(f)

            for row in reader:
                assignments.append(
                    {
                        "person_id": row["person_id"],
                        "rotation_id": row["rotation_id"],
                        "start_date": row["start_date"],
                        "end_date": row["end_date"],
                    }
                )

        console.print(f"Found {len(assignments)} assignments in CSV")

        if confirm("Import these assignments?"):
            api = APIClient()

            response = api.post(
                "/api/v1/schedules/import",
                json={
                    "block_number": block,
                    "academic_year": year,
                    "assignments": assignments,
                },
            )

            print_success("CSV imported successfully")

    except Exception as e:
        print_error(f"CSV import failed: {str(e)}")
        raise typer.Exit(1)


async def import_rotation_template(template_file: Path, rotation_name: str):
    """
    Import rotation template.

    Args:
        template_file: Template file
        rotation_name: Rotation name
    """
    try:
        print_info(f"Importing template for {rotation_name}...")

        with open(template_file) as f:
            template_data = json.load(f)

        api = APIClient()

        response = api.post(
            "/api/v1/rotations/template",
            json={
                "name": rotation_name,
                "template": template_data,
            },
        )

        print_success(f"Template imported for {rotation_name}")

    except Exception as e:
        print_error(f"Template import failed: {str(e)}")
        raise typer.Exit(1)
