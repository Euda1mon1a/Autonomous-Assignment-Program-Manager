"""CLI commands for block schedule import and analysis.

Parse block schedules from Excel files with fuzzy-tolerant parsing.
Handles column shifts, merged cells, and name variations.

Usage:
    python -m app.cli.block_import_commands parse schedule.xlsx 10
    python -m app.cli.block_import_commands parse schedule.xlsx 10 -o json
    python -m app.cli.block_import_commands parse schedule.xlsx 10 -m block10.md
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Block schedule import commands")
console = Console()


@app.command("parse")
def parse_block(
    file: Path = typer.Argument(..., help="Path to Excel schedule file"),
    block: int = typer.Argument(..., help="Block number to parse (1-13)"),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format: table, json"
    ),
    markdown_file: Path | None = typer.Option(
        None, "--markdown", "-m", help="Write markdown summary to file"
    ),
    include_fmit: bool = typer.Option(
        True, "--fmit/--no-fmit", help="Include FMIT schedule"
    ),
):
    """
    Parse a block schedule from an Excel file.

    Shows resident roster by template and FMIT schedule.
    Handles human-edited spreadsheets with column shifts and name variations.

    Examples:
        parse schedule.xlsx 10
        parse schedule.xlsx 10 --output json
        parse schedule.xlsx 10 --markdown docs/schedules/BLOCK_10_SUMMARY.md
    """
    from app.services.xlsx_import import parse_block_schedule, parse_fmit_attending
    from app.services.block_markdown import generate_block_markdown

    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    if not 1 <= block <= 13:
        console.print(f"[red]Error:[/red] Block must be 1-13, got {block}")
        raise typer.Exit(1)

    try:
        result = parse_block_schedule(filepath=str(file), block_number=block)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # Parse FMIT if requested
    fmit_weeks = None
    if include_fmit:
        try:
            all_fmit = parse_fmit_attending(filepath=str(file))
            fmit_weeks = [f for f in all_fmit if f.block_number == block]
        except Exception:
            pass  # FMIT sheet not found, that's OK

    if output == "json":
        # JSON output
        data = {
            "block_number": result.block_number,
            "start_date": result.start_date.isoformat() if result.start_date else None,
            "end_date": result.end_date.isoformat() if result.end_date else None,
            "total_residents": len(result.residents),
            "residents_by_template": result.get_residents_by_template(),
            "fmit_schedule": (
                [
                    {
                        "week": f.week_number,
                        "faculty": f.faculty_name,
                        "holiday_call": f.is_holiday_call,
                    }
                    for f in fmit_weeks
                ]
                if fmit_weeks
                else []
            ),
            "warnings": result.warnings,
            "errors": result.errors,
        }
        console.print_json(json.dumps(data, indent=2, default=str))
    else:
        # Rich table output
        _render_block_summary(result, fmit_weeks)

    # Generate markdown if requested
    if markdown_file:
        content = generate_block_markdown(result, fmit_weeks=fmit_weeks)
        markdown_file.parent.mkdir(parents=True, exist_ok=True)
        markdown_file.write_text(content)
        console.print(f"\n[green]Markdown written to:[/green] {markdown_file}")


@app.command("roster")
def show_roster(
    file: Path = typer.Argument(..., help="Path to Excel schedule file"),
    block: int = typer.Argument(..., help="Block number"),
    template: str | None = typer.Option(
        None, "--template", "-t", help="Filter by template (R1, R2, R3)"
    ),
):
    """
    Show resident roster grouped by rotation template.

    Displays as Rich table with columns: Template, Role, Name, Confidence
    """
    from app.services.xlsx_import import parse_block_schedule

    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    try:
        result = parse_block_schedule(filepath=str(file), block_number=block)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    by_template = result.get_residents_by_template()

    if template:
        if template not in by_template:
            console.print(
                f"[yellow]No residents found for template {template}[/yellow]"
            )
            console.print(f"Available templates: {list(by_template.keys())}")
            return
        by_template = {template: by_template[template]}

    table = Table(title=f"Block {result.block_number} Roster")
    table.add_column("Template", style="cyan", width=10)
    table.add_column("Role", style="yellow", width=10)
    table.add_column("Name", style="green")
    table.add_column("Confidence", justify="right", width=12)

    for tmpl in sorted(by_template.keys()):
        for r in by_template[tmpl]:
            conf = r.get("confidence", 1.0)
            conf_color = "green" if conf >= 0.9 else "yellow" if conf >= 0.8 else "red"
            table.add_row(
                tmpl,
                r["role"],
                r["name"],
                f"[{conf_color}]{conf:.0%}[/{conf_color}]",
            )

    console.print(table)
    console.print(f"\nTotal: {len(result.residents)} residents")


@app.command("fmit")
def show_fmit(
    file: Path = typer.Argument(..., help="Path to Excel schedule file"),
    block: int | None = typer.Option(
        None, "--block", "-b", help="Filter by block number"
    ),
):
    """
    Show FMIT attending schedule.

    Displays weekly faculty assignments for inpatient teaching.
    """
    from app.services.xlsx_import import parse_fmit_attending

    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    try:
        fmit_weeks = parse_fmit_attending(filepath=str(file))
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not fmit_weeks:
        console.print("[yellow]No FMIT schedule found[/yellow]")
        return

    if block:
        fmit_weeks = [f for f in fmit_weeks if f.block_number == block]
        if not fmit_weeks:
            console.print(f"[yellow]No FMIT data for Block {block}[/yellow]")
            return

    table = Table(title="FMIT Attending Schedule")
    table.add_column("Block", style="cyan", width=8)
    table.add_column("Week", style="yellow", width=6)
    table.add_column("Faculty", style="green")
    table.add_column("Holiday", width=8)

    current_block = None
    for f in fmit_weeks:
        if f.block_number != current_block:
            if current_block is not None:
                table.add_row("", "", "", "")  # Separator
            current_block = f.block_number

        holiday = "⭐" if f.is_holiday_call else ""
        table.add_row(
            str(f.block_number),
            str(f.week_number),
            f.faculty_name,
            holiday,
        )

    console.print(table)


def _render_block_summary(result, fmit_weeks=None):
    """Render block summary with Rich tables."""
    # Header
    console.print(f"\n[bold cyan]Block {result.block_number} Summary[/bold cyan]")
    if result.start_date and result.end_date:
        console.print(
            f"Date Range: {result.start_date.strftime('%B %d')} - "
            f"{result.end_date.strftime('%B %d, %Y')}"
        )
    console.print()

    # Roster by template
    by_template = result.get_residents_by_template()

    for template in ["R3", "R2", "R1"]:
        if template in by_template:
            residents = by_template[template]
            table = Table(title=f"{template} Rotation ({len(residents)} residents)")
            table.add_column("Role", style="yellow", width=10)
            table.add_column("Name", style="green")
            table.add_column("Conf", justify="right", width=8)

            for r in residents:
                conf = r.get("confidence", 1.0)
                conf_color = (
                    "green" if conf >= 0.9 else "yellow" if conf >= 0.8 else "red"
                )
                table.add_row(
                    r["role"],
                    r["name"],
                    f"[{conf_color}]{conf:.0%}[/{conf_color}]",
                )

            console.print(table)
            console.print()

    # FMIT schedule
    if fmit_weeks:
        table = Table(title="FMIT Attending")
        table.add_column("Week", style="cyan")
        table.add_column("Faculty", style="green")

        for f in fmit_weeks:
            table.add_row(str(f.week_number), f.faculty_name)

        console.print(table)
        console.print()

    # Warnings
    if result.warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for w in result.warnings[:5]:  # Show first 5
            console.print(f"  ⚠ {w}")
        if len(result.warnings) > 5:
            console.print(f"  ... and {len(result.warnings) - 5} more")
        console.print()

    # Errors
    if result.errors:
        console.print("[red]Errors:[/red]")
        for e in result.errors:
            console.print(f"  ❌ {e}")
        console.print()


if __name__ == "__main__":
    app()
