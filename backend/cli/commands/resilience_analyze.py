"""
Resilience analysis commands (N-1, N-2 contingency).
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_success, print_warning, print_table
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def n1(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Run N-1 contingency analysis.

    Tests if schedule remains viable with 1 resource removed.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(analyze_n1_contingency(block, year))


@app.command()
def n2(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Run N-2 contingency analysis.

    Tests if schedule remains viable with 2 resources removed.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(analyze_n2_contingency(block, year))


@app.command()
def bottlenecks(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Identify scheduling bottlenecks.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(identify_bottlenecks(block, year))


@app.command()
def capacity(
    rotation: str = typer.Argument(..., help="Rotation name"),
    date: str = typer.Option(None, "--date", help="Specific date (YYYY-MM-DD)"),
):
    """
    Analyze capacity for a rotation.

    Args:
        rotation: Rotation name
        date: Specific date
    """
    asyncio.run(analyze_capacity(rotation, date))


async def analyze_n1_contingency(block: int, year: int):
    """
    Run N-1 analysis.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        console.print(f"\n[bold]N-1 Contingency Analysis - Block {block}[/bold]\n")

        response = api.post(
            "/api/v1/resilience/analyze/n1",
            json={"block_number": block, "academic_year": year},
        )

        viable = response.get("viable", False)
        vulnerabilities = response.get("vulnerabilities", [])

        if viable:
            print_success("Schedule is N-1 viable")
        else:
            print_warning("Schedule is NOT N-1 viable")

        if vulnerabilities:
            console.print(
                f"\n[yellow]Found {len(vulnerabilities)} vulnerabilities[/yellow]\n"
            )

            print_table(
                vulnerabilities,
                title="N-1 Vulnerabilities",
                columns=["person_id", "rotation", "impact", "mitigation"],
            )

    except Exception as e:
        print_error(f"N-1 analysis failed: {str(e)}")
        raise typer.Exit(1)


async def analyze_n2_contingency(block: int, year: int):
    """
    Run N-2 analysis.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        console.print(f"\n[bold]N-2 Contingency Analysis - Block {block}[/bold]\n")

        response = api.post(
            "/api/v1/resilience/analyze/n2",
            json={"block_number": block, "academic_year": year},
        )

        viable = response.get("viable", False)
        critical_pairs = response.get("critical_pairs", [])

        if viable:
            print_success("Schedule is N-2 viable")
        else:
            print_warning("Schedule is NOT N-2 viable")

        if critical_pairs:
            console.print(
                f"\n[yellow]Found {len(critical_pairs)} critical pairs[/yellow]\n"
            )

            print_table(
                critical_pairs,
                title="Critical Pairs (N-2)",
                columns=["person_1", "person_2", "impact", "affected_rotations"],
            )

    except Exception as e:
        print_error(f"N-2 analysis failed: {str(e)}")
        raise typer.Exit(1)


async def identify_bottlenecks(block: int, year: int):
    """
    Identify bottlenecks.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        console.print("\n[bold]Bottleneck Analysis[/bold]\n")

        response = api.get(
            "/api/v1/resilience/bottlenecks",
            params={"block": block, "year": year},
        )

        bottlenecks = response.get("bottlenecks", [])

        if not bottlenecks:
            print_success("No bottlenecks detected")
            return

        console.print(f"[yellow]Found {len(bottlenecks)} bottlenecks[/yellow]\n")

        print_table(
            bottlenecks,
            title="Scheduling Bottlenecks",
            columns=["rotation", "date", "severity", "description", "recommendation"],
        )

    except Exception as e:
        print_error(f"Bottleneck analysis failed: {str(e)}")
        raise typer.Exit(1)


async def analyze_capacity(rotation: str, date: str = None):
    """
    Analyze capacity.

    Args:
        rotation: Rotation name
        date: Date
    """
    api = APIClient()

    try:
        console.print(f"\n[bold]Capacity Analysis - {rotation}[/bold]\n")

        params = {"rotation": rotation}
        if date:
            params["date"] = date

        response = api.get("/api/v1/resilience/capacity", params=params)

        capacity = response.get("capacity", {})

        console.print(f"Total Capacity: {capacity.get('total', 0)}")
        console.print(f"Used: {capacity.get('used', 0)}")
        console.print(f"Available: {capacity.get('available', 0)}")
        console.print(f"Utilization: {capacity.get('utilization', 0):.1f}%")

        if capacity.get("utilization", 0) > 80:
            print_warning("⚠ Utilization above 80% threshold")

    except Exception as e:
        print_error(f"Capacity analysis failed: {str(e)}")
        raise typer.Exit(1)
