"""
Database management command group.

Commands:
- migrate: Run database migrations
- seed: Seed database with test data
- backup: Create database backup
- restore: Restore from backup
- health: Check database health
- stats: Show database statistics
"""

import typer
from rich.console import Console

app = typer.Typer(help="Database management commands")
console = Console()


@app.callback()
def callback():
    """Database management operations."""
    pass


@app.command()
def status():
    """Show database status and connection info."""
    from cli.commands.db_health import check_health

    check_health()


@app.command()
def init():
    """Initialize database schema."""
    from cli.commands.db_migrate import run_init

    run_init()


@app.command()
def reset():
    """Reset database (WARNING: Destructive operation)."""
    from cli.utils.prompts import confirm_dangerous

    if confirm_dangerous("reset", "entire database", "RESET"):
        from cli.commands.db_migrate import run_reset

        run_reset()
    else:
        console.print("[yellow]Operation cancelled[/yellow]")
