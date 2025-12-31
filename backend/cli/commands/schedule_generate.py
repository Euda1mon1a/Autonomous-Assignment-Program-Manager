"""
Schedule generation commands.
"""

import asyncio
from datetime import date

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_info
from cli.utils.progress import progress_bar
from cli.utils.prompts import confirm
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def block(
    block_number: int = typer.Argument(..., help="Block number (1-12)"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without saving"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmations"),
):
    """
    Generate schedule for a specific block.

    Args:
        block_number: Block number (1-12)
        year: Academic year
        dry_run: Preview without saving
        force: Skip confirmations
    """
    if not (1 <= block_number <= 12):
        print_error("Block number must be between 1 and 12")
        raise typer.Exit(1)

    if not dry_run and not force:
        if not confirm(f"Generate schedule for Block {block_number}?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    asyncio.run(generate_block_schedule(block_number, year, dry_run))


@app.command()
def range(
    start_block: int = typer.Argument(..., help="Start block"),
    end_block: int = typer.Argument(..., help="End block"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Generate schedules for a range of blocks.

    Args:
        start_block: Starting block number
        end_block: Ending block number
        year: Academic year
    """
    if not (1 <= start_block <= 12) or not (1 <= end_block <= 12):
        print_error("Block numbers must be between 1 and 12")
        raise typer.Exit(1)

    if start_block > end_block:
        print_error("Start block must be <= end block")
        raise typer.Exit(1)

    if not confirm(f"Generate schedules for Blocks {start_block}-{end_block}?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    asyncio.run(generate_range_schedules(start_block, end_block, year))


@app.command()
def year(
    year: int = typer.Argument(..., help="Academic year"),
    skip_existing: bool = typer.Option(
        False, "--skip-existing", help="Skip blocks with schedules"
    ),
):
    """
    Generate schedules for entire academic year.

    Args:
        year: Academic year
        skip_existing: Skip blocks that already have schedules
    """
    if not confirm(f"Generate schedules for entire {year} academic year?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    asyncio.run(generate_year_schedules(year, skip_existing))


async def generate_block_schedule(block_number: int, year: int, dry_run: bool):
    """
    Generate schedule for a block.

    Args:
        block_number: Block number
        year: Academic year
        dry_run: Preview mode
    """
    api = APIClient()

    try:
        print_info(f"Generating schedule for Block {block_number} ({year})...")

        # Call schedule generation API
        with progress_bar("Generating schedule") as progress:
            task = progress.add_task("Generating...", total=100)

            # Mock progress updates
            for i in range(0, 100, 20):
                progress.update(task, completed=i)
                await asyncio.sleep(0.5)

            # Make API call
            response = api.post(
                "/api/v1/schedules/generate",
                json={
                    "block_number": block_number,
                    "academic_year": year,
                    "dry_run": dry_run,
                },
            )

            progress.update(task, completed=100)

        if dry_run:
            print_info("Preview mode - schedule not saved")
            console.print(response)
        else:
            print_success(f"Schedule generated for Block {block_number}")
            console.print(
                f"Assignments created: {response.get('assignments_count', 0)}"
            )

    except Exception as e:
        print_error(f"Generation failed: {str(e)}")
        raise typer.Exit(1)


async def generate_range_schedules(start: int, end: int, year: int):
    """
    Generate schedules for block range.

    Args:
        start: Start block
        end: End block
        year: Academic year
    """
    print_info(f"Generating schedules for Blocks {start}-{end} ({year})...")

    for block in range(start, end + 1):
        console.print(f"\n[bold]Block {block}[/bold]")
        await generate_block_schedule(block, year, dry_run=False)


async def generate_year_schedules(year: int, skip_existing: bool):
    """
    Generate schedules for entire year.

    Args:
        year: Academic year
        skip_existing: Skip existing schedules
    """
    print_info(f"Generating schedules for {year} academic year...")

    for block in range(1, 13):
        console.print(f"\n[bold]Block {block}[/bold]")

        if skip_existing:
            # Check if block has existing schedule
            # Placeholder - would check via API
            pass

        await generate_block_schedule(block, year, dry_run=False)

    print_success(f"All schedules generated for {year}")
