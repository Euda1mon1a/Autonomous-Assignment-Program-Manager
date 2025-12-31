"""
Schedule optimization commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_info, print_success, print_table
from cli.utils.progress import progress_bar
from cli.utils.prompts import confirm

app = typer.Typer()
console = Console()


@app.command()
def block(
    block_number: int = typer.Argument(..., help="Block number to optimize"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    objective: str = typer.Option(
        "balanced", "--objective", "-obj", help="Optimization objective"
    ),
    max_iterations: int = typer.Option(1000, "--max-iter", help="Maximum iterations"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without applying"),
):
    """
    Optimize schedule for a block.

    Objectives:
    - balanced: Balance workload across residents
    - coverage: Maximize coverage
    - preferences: Maximize preference satisfaction
    - fairness: Equitable distribution

    Args:
        block_number: Block number
        year: Academic year
        objective: Optimization objective
        max_iterations: Max solver iterations
        dry_run: Preview mode
    """
    if not dry_run:
        if not confirm(f"Optimize Block {block_number} schedule?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    asyncio.run(
        optimize_block_schedule(block_number, year, objective, max_iterations, dry_run)
    )


@app.command()
def person(
    person_id: str = typer.Argument(..., help="Person ID"),
    start_date: str = typer.Option(None, "--start", help="Start date"),
    end_date: str = typer.Option(None, "--end", help="End date"),
):
    """
    Optimize schedule for a specific person.

    Args:
        person_id: Person ID
        start_date: Start date
        end_date: End date
    """
    asyncio.run(optimize_person_schedule(person_id, start_date, end_date))


@app.command()
def workload(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    target_hours: float = typer.Option(60.0, "--target", help="Target hours per week"),
):
    """
    Optimize workload distribution.

    Args:
        block: Block number
        year: Academic year
        target_hours: Target hours per week
    """
    asyncio.run(optimize_workload(block, year, target_hours))


@app.command()
def preferences(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    weight: float = typer.Option(0.5, "--weight", help="Preference weight (0.0-1.0)"),
):
    """
    Optimize to maximize preference satisfaction.

    Args:
        block: Block number
        year: Academic year
        weight: Preference weight
    """
    asyncio.run(optimize_preferences(block, year, weight))


async def optimize_block_schedule(
    block: int, year: int, objective: str, max_iterations: int, dry_run: bool
):
    """
    Optimize block schedule.

    Args:
        block: Block number
        year: Academic year
        objective: Optimization objective
        max_iterations: Max iterations
        dry_run: Dry run flag
    """
    from cli.utils.api_client import APIClient

    api = APIClient()

    try:
        print_info(f"Optimizing Block {block} schedule (objective: {objective})...")

        # Start optimization
        with progress_bar("Optimizing schedule", total=100) as progress:
            task = progress.add_task("Optimizing...", total=max_iterations)

            # Call optimization API
            response = api.post(
                "/api/v1/schedules/optimize",
                json={
                    "block_number": block,
                    "academic_year": year,
                    "objective": objective,
                    "max_iterations": max_iterations,
                    "dry_run": dry_run,
                },
            )

            # Update progress (in real implementation, would poll for progress)
            for i in range(0, max_iterations, 100):
                progress.update(task, completed=min(i, max_iterations))
                await asyncio.sleep(0.1)

            progress.update(task, completed=max_iterations)

        # Show results
        if dry_run:
            print_info("Preview mode - changes not applied")

        results = response.get("results", {})
        improvements = results.get("improvements", {})

        console.print("\n[bold]Optimization Results[/bold]\n")
        console.print(f"Objective: {objective}")
        console.print(f"Iterations: {results.get('iterations', 0)}")
        console.print(f"Status: {results.get('status', 'unknown')}")

        if improvements:
            improvement_data = [
                {
                    "metric": k,
                    "before": v["before"],
                    "after": v["after"],
                    "change": v["change"],
                }
                for k, v in improvements.items()
            ]

            print_table(
                improvement_data,
                title="Improvements",
                columns=["metric", "before", "after", "change"],
            )

        if not dry_run:
            print_success("Schedule optimized and saved")

    except Exception as e:
        print_error(f"Optimization failed: {str(e)}")
        raise typer.Exit(1)


async def optimize_person_schedule(
    person_id: str, start_date: str = None, end_date: str = None
):
    """
    Optimize person's schedule.

    Args:
        person_id: Person ID
        start_date: Start date
        end_date: End date
    """
    from cli.utils.api_client import APIClient

    api = APIClient()

    try:
        print_info(f"Optimizing schedule for {person_id}...")

        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = api.post(
            f"/api/v1/schedules/optimize/person/{person_id}",
            json=params,
        )

        print_success(f"Schedule optimized for {person_id}")
        console.print(response.get("summary", {}))

    except Exception as e:
        print_error(f"Optimization failed: {str(e)}")
        raise typer.Exit(1)


async def optimize_workload(block: int, year: int, target_hours: float):
    """
    Optimize workload distribution.

    Args:
        block: Block number
        year: Academic year
        target_hours: Target hours
    """
    from cli.utils.api_client import APIClient

    api = APIClient()

    try:
        print_info("Optimizing workload distribution...")

        response = api.post(
            "/api/v1/schedules/optimize/workload",
            json={
                "block_number": block,
                "academic_year": year,
                "target_hours": target_hours,
            },
        )

        print_success("Workload optimized")
        console.print(response.get("distribution", {}))

    except Exception as e:
        print_error(f"Workload optimization failed: {str(e)}")
        raise typer.Exit(1)


async def optimize_preferences(block: int, year: int, weight: float):
    """
    Optimize preference satisfaction.

    Args:
        block: Block number
        year: Academic year
        weight: Preference weight
    """
    from cli.utils.api_client import APIClient

    api = APIClient()

    try:
        print_info("Optimizing preference satisfaction...")

        response = api.post(
            "/api/v1/schedules/optimize/preferences",
            json={
                "block_number": block,
                "academic_year": year,
                "preference_weight": weight,
            },
        )

        satisfaction_rate = response.get("satisfaction_rate", 0)

        print_success(f"Preferences optimized (satisfaction: {satisfaction_rate:.1f}%)")

    except Exception as e:
        print_error(f"Preference optimization failed: {str(e)}")
        raise typer.Exit(1)
