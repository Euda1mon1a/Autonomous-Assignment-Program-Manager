"""
Schedule coverage analysis commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_info, print_table, print_success
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def analyze(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    rotation: str = typer.Option(None, "--rotation", "-r", help="Specific rotation"),
):
    """
    Analyze schedule coverage.

    Args:
        block: Block number
        year: Academic year
        rotation: Specific rotation to analyze
    """
    asyncio.run(analyze_coverage(block, year, rotation))


@app.command()
def gaps(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Find coverage gaps.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(find_coverage_gaps(block, year))


@app.command()
def report(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    output: str = typer.Option(None, "--output", "-o", help="Output file (PDF/HTML)"),
):
    """
    Generate coverage report.

    Args:
        block: Block number
        year: Academic year
        output: Output file path
    """
    asyncio.run(generate_coverage_report(block, year, output))


@app.command()
def daily(
    date: str = typer.Argument(..., help="Date to check (YYYY-MM-DD)"),
):
    """
    Show coverage for a specific date.

    Args:
        date: Date to check
    """
    asyncio.run(show_daily_coverage(date))


async def analyze_coverage(block: int, year: int, rotation: str = None):
    """
    Analyze schedule coverage.

    Args:
        block: Block number
        year: Academic year
        rotation: Specific rotation
    """
    api = APIClient()

    try:
        print_info(f"Analyzing coverage for Block {block}...")

        params = {"block": block, "year": year}
        if rotation:
            params["rotation"] = rotation

        response = api.get("/api/v1/schedules/coverage/analyze", params=params)

        coverage = response.get("coverage", {})

        console.print(f"\n[bold]Coverage Analysis - Block {block}[/bold]\n")

        # Overall coverage
        overall = coverage.get("overall", 0)
        console.print(f"Overall Coverage: {overall:.1f}%")

        # By rotation
        by_rotation = coverage.get("by_rotation", {})
        rotation_data = [
            {"rotation": name, "coverage": f"{value:.1f}%"}
            for name, value in by_rotation.items()
        ]

        if rotation_data:
            print_table(
                rotation_data,
                title="Coverage by Rotation",
                columns=["rotation", "coverage"],
            )

        # Identify issues
        if overall < 90:
            console.print("\n[yellow]⚠ Coverage below 90% threshold[/yellow]")

    except Exception as e:
        print_error(f"Coverage analysis failed: {str(e)}")
        raise typer.Exit(1)


async def find_coverage_gaps(block: int, year: int):
    """
    Find coverage gaps.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        print_info("Finding coverage gaps...")

        response = api.get(
            "/api/v1/schedules/coverage/gaps",
            params={"block": block, "year": year},
        )

        gaps = response.get("gaps", [])

        if not gaps:
            print_success("No coverage gaps detected")
            return

        console.print(f"\n[yellow]Found {len(gaps)} coverage gaps[/yellow]\n")

        print_table(
            gaps,
            title="Coverage Gaps",
            columns=["date", "rotation", "shift", "required", "assigned", "deficit"],
        )

    except Exception as e:
        print_error(f"Gap detection failed: {str(e)}")
        raise typer.Exit(1)


async def generate_coverage_report(block: int, year: int, output: str = None):
    """
    Generate coverage report.

    Args:
        block: Block number
        year: Academic year
        output: Output file
    """
    api = APIClient()

    try:
        print_info("Generating coverage report...")

        response = api.get(
            "/api/v1/schedules/coverage/report",
            params={"block": block, "year": year, "format": "json"},
        )

        if output:
            import json

            with open(output, "w") as f:
                json.dump(response, f, indent=2)

            print_success(f"Report saved to {output}")
        else:
            # Display summary
            console.print(response.get("summary", "No summary available"))

    except Exception as e:
        print_error(f"Report generation failed: {str(e)}")
        raise typer.Exit(1)


async def show_daily_coverage(date: str):
    """
    Show coverage for a specific date.

    Args:
        date: Date string
    """
    api = APIClient()

    try:
        print_info(f"Loading coverage for {date}...")

        response = api.get(
            "/api/v1/schedules/coverage/daily",
            params={"date": date},
        )

        shifts = response.get("shifts", [])

        console.print(f"\n[bold]Coverage for {date}[/bold]\n")

        print_table(
            shifts,
            columns=["shift", "rotation", "required", "assigned", "names"],
        )

    except Exception as e:
        print_error(f"Failed to load coverage: {str(e)}")
        raise typer.Exit(1)
