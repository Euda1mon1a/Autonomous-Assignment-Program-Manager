"""
Main CLI entry point for Residency Scheduler management.

Usage:
    scheduler-cli db migrate
    scheduler-cli schedule generate --block 10
    scheduler-cli user create --email admin@example.com
    scheduler-cli compliance check
"""

import typer
from rich.console import Console

from cli.commands import db, schedule, user, compliance, resilience

app = typer.Typer(
    name="scheduler-cli",
    help="Residency Scheduler CLI Management Tool",
    add_completion=True,
)

console = Console()

# Register command groups
app.add_typer(db.app, name="db", help="Database management commands")
app.add_typer(schedule.app, name="schedule", help="Schedule operations")
app.add_typer(user.app, name="user", help="User management")
app.add_typer(compliance.app, name="compliance", help="ACGME compliance checking")
app.add_typer(resilience.app, name="resilience", help="Resilience framework monitoring")


@app.callback()
def callback():
    """
    Residency Scheduler CLI - Medical residency scheduling management tool.

    Designed for military medical residency programs with ACGME compliance.
    """
    pass


@app.command()
def version():
    """Show CLI version information."""
    from cli import __version__
    console.print(f"[bold blue]Residency Scheduler CLI v{__version__}[/bold blue]")
    console.print("Military Medical Residency Scheduling System")


@app.command()
def info():
    """Show system information and health status."""
    from cli.utils.output import print_system_info
    print_system_info()


if __name__ == "__main__":
    app()
