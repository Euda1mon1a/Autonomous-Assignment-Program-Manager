"""
Database migration commands.

Wraps Alembic operations with CLI interface.
"""

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_info
from cli.utils.progress import step

app = typer.Typer()
console = Console()


def get_alembic_dir() -> Path:
    """Get alembic directory path."""
    return Path(__file__).parent.parent.parent / "alembic"


@app.command()
def upgrade(
    revision: str = typer.Argument("head", help="Target revision (default: head)"),
):
    """
    Upgrade database to a later version.

    Args:
        revision: Target revision (default: head for latest)
    """
    with step(f"Upgrading database to {revision}"):
        result = subprocess.run(
            ["alembic", "upgrade", revision],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print_success(f"Database upgraded to {revision}")
        else:
            print_error(f"Migration failed: {result.stderr}")
            raise typer.Exit(1)


@app.command()
def downgrade(
    revision: str = typer.Argument(
        "-1", help="Target revision (default: -1 for previous)"
    ),
):
    """
    Downgrade database to a previous version.

    Args:
        revision: Target revision (default: -1 for one revision back)
    """
    from cli.utils.prompts import confirm

    if not confirm(f"Downgrade database to {revision}?", default=False):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    with step(f"Downgrading database to {revision}"):
        result = subprocess.run(
            ["alembic", "downgrade", revision],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print_success(f"Database downgraded to {revision}")
        else:
            print_error(f"Migration failed: {result.stderr}")
            raise typer.Exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of revisions to show"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full details"),
):
    """
    Show migration history.

    Args:
        limit: Number of revisions to show
        verbose: Show full details
    """
    args = ["alembic", "history"]

    if verbose:
        args.append("--verbose")

    result = subprocess.run(args, capture_output=True, text=True)

    if result.returncode == 0:
        # Show only last N lines if limit specified
        lines = result.stdout.strip().split("\n")
        if limit and len(lines) > limit:
            lines = lines[-limit:]

        console.print("\n".join(lines))
    else:
        print_error(f"Failed to get history: {result.stderr}")
        raise typer.Exit(1)


@app.command()
def current():
    """Show current database revision."""
    result = subprocess.run(
        ["alembic", "current"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        console.print(result.stdout)
    else:
        print_error(f"Failed to get current revision: {result.stderr}")
        raise typer.Exit(1)


@app.command()
def create(
    message: str = typer.Argument(..., help="Migration message"),
    autogenerate: bool = typer.Option(
        True, "--autogenerate/--manual", help="Auto-generate migration"
    ),
):
    """
    Create a new migration.

    Args:
        message: Migration message
        autogenerate: Auto-generate migration from models
    """
    args = ["alembic", "revision"]

    if autogenerate:
        args.append("--autogenerate")

    args.extend(["-m", message])

    with step("Creating migration"):
        result = subprocess.run(args, capture_output=True, text=True)

        if result.returncode == 0:
            print_success(f"Migration created: {message}")
            console.print(result.stdout)
        else:
            print_error(f"Migration creation failed: {result.stderr}")
            raise typer.Exit(1)


def run_init():
    """Initialize database schema."""
    print_info("Initializing database schema...")

    # Run migrations
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print_success("Database initialized successfully")
    else:
        print_error(f"Initialization failed: {result.stderr}")
        raise typer.Exit(1)


def run_reset():
    """Reset database (drop all tables and recreate)."""
    print_info("Resetting database...")

    # Downgrade to base
    result = subprocess.run(
        ["alembic", "downgrade", "base"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print_error(f"Downgrade failed: {result.stderr}")
        raise typer.Exit(1)

    # Upgrade to head
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print_success("Database reset successfully")
    else:
        print_error(f"Upgrade failed: {result.stderr}")
        raise typer.Exit(1)
