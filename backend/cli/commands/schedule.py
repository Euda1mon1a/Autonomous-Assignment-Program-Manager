"""
Schedule operations command group.

Commands:
- generate: Generate schedule for a block
- validate: Validate schedule compliance
- export: Export schedule to file
- import: Import schedule from file
- preview: Preview generated schedule
- conflicts: Show scheduling conflicts
- coverage: Generate coverage report
- optimize: Optimize existing schedule
"""

import typer
from rich.console import Console

app = typer.Typer(help="Schedule operations")
console = Console()


@app.callback()
def callback():
    """Schedule management operations."""
    pass


@app.command()
def status():
    """Show current schedule status."""
    from cli.commands.schedule_preview import show_status

    show_status()


@app.command()
def quick_validate():
    """Quick validation of current schedule."""
    from cli.commands.schedule_validate import quick_check

    quick_check()
