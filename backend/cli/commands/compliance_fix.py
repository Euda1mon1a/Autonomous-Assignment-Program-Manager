"""
Compliance auto-fix suggestion commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_info, print_table
from cli.utils.prompts import confirm
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def suggest(
    violation_id: str = typer.Argument(..., help="Violation ID"),
):
    """
    Get fix suggestions for a violation.

    Args:
        violation_id: Violation ID
    """
    asyncio.run(get_fix_suggestions(violation_id))


@app.command()
def apply(
    violation_id: str = typer.Argument(..., help="Violation ID"),
    suggestion_id: int = typer.Argument(..., help="Suggestion ID to apply"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without applying"),
):
    """
    Apply a fix suggestion.

    Args:
        violation_id: Violation ID
        suggestion_id: Suggestion ID
        dry_run: Dry run mode
    """
    asyncio.run(apply_fix_suggestion(violation_id, suggestion_id, dry_run))


@app.command()
def auto(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    max_fixes: int = typer.Option(10, "--max", help="Maximum fixes to apply"),
):
    """
    Automatically fix violations where possible.

    Args:
        block: Block number
        year: Academic year
        max_fixes: Maximum fixes to apply
    """
    if not confirm(f"Auto-fix violations for Block {block}?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    asyncio.run(auto_fix_violations(block, year, max_fixes))


async def get_fix_suggestions(violation_id: str):
    """
    Get fix suggestions.

    Args:
        violation_id: Violation ID
    """
    api = APIClient()

    try:
        print_info(f"Getting fix suggestions for violation {violation_id}...")

        response = api.get(f"/api/v1/compliance/violations/{violation_id}/suggestions")

        suggestions = response.get("suggestions", [])

        if not suggestions:
            console.print("[yellow]No automatic fixes available[/yellow]")
            return

        console.print(f"\n[bold]Fix Suggestions for {violation_id}:[/bold]\n")

        print_table(
            suggestions,
            columns=["id", "type", "description", "impact", "confidence"],
        )

    except Exception as e:
        print_error(f"Failed to get suggestions: {str(e)}")
        raise typer.Exit(1)


async def apply_fix_suggestion(violation_id: str, suggestion_id: int, dry_run: bool):
    """
    Apply fix suggestion.

    Args:
        violation_id: Violation ID
        suggestion_id: Suggestion ID
        dry_run: Dry run flag
    """
    api = APIClient()

    try:
        print_info(f"Applying fix suggestion {suggestion_id}...")

        response = api.post(
            f"/api/v1/compliance/violations/{violation_id}/fix",
            json={
                "suggestion_id": suggestion_id,
                "dry_run": dry_run,
            },
        )

        if dry_run:
            print_info("Preview mode - changes not applied")
            console.print("\n[bold]Proposed Changes:[/bold]")
            console.print(response.get("changes", {}))
        else:
            print_success("Fix applied successfully")
            console.print(f"Violation status: {response.get('status')}")

    except Exception as e:
        print_error(f"Failed to apply fix: {str(e)}")
        raise typer.Exit(1)


async def auto_fix_violations(block: int, year: int, max_fixes: int):
    """
    Auto-fix violations.

    Args:
        block: Block number
        year: Academic year
        max_fixes: Maximum fixes
    """
    api = APIClient()

    try:
        print_info("Running auto-fix for compliance violations...")

        response = api.post(
            "/api/v1/compliance/auto-fix",
            json={
                "block_number": block,
                "academic_year": year,
                "max_fixes": max_fixes,
            },
        )

        fixed_count = response.get("fixed_count", 0)
        skipped_count = response.get("skipped_count", 0)

        console.print(f"\n[bold]Auto-Fix Results:[/bold]")
        console.print(f"Fixed: {fixed_count}")
        console.print(f"Skipped: {skipped_count}")

        if response.get("fixes"):
            print_table(
                response["fixes"],
                title="Applied Fixes",
                columns=["violation_id", "fix_type", "status"],
            )

    except Exception as e:
        print_error(f"Auto-fix failed: {str(e)}")
        raise typer.Exit(1)
