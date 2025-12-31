"""
ACGME compliance command group.

Commands:
- check: Run compliance check
- report: Generate compliance report
- violations: Show violations
- fix: Auto-fix suggestions
- hours: Check work hour compliance
- supervision: Check supervision ratios
- days-off: Check 1-in-7 rule
"""

import typer
from rich.console import Console

app = typer.Typer(help="ACGME compliance checking")
console = Console()


@app.callback()
def callback():
    """ACGME compliance operations."""
    pass


@app.command()
def status():
    """Show overall compliance status."""
    from cli.commands.compliance_report import show_compliance_status

    show_compliance_status()
