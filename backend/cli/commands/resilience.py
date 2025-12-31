"""
Resilience framework command group.

Commands:
- status: Show resilience status dashboard
- analyze: N-1/N-2 contingency analysis
- alerts: Show resilience alerts
- burnout: Burnout risk analysis
- utilization: System utilization metrics
- defense: Defense-in-depth status
"""

import typer
from rich.console import Console

app = typer.Typer(help="Resilience framework monitoring")
console = Console()


@app.callback()
def callback():
    """Resilience framework operations."""
    pass


@app.command()
def dashboard():
    """Show resilience dashboard (alias for status)."""
    from cli.commands.resilience_status import show_dashboard

    show_dashboard()
