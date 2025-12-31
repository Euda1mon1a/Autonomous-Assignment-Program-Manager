"""
Resilience status dashboard commands.
"""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.utils.output import print_error
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def show():
    """Show comprehensive resilience status."""
    asyncio.run(show_resilience_status())


@app.command()
def summary():
    """Show resilience summary."""
    asyncio.run(show_resilience_summary())


@app.command()
def metrics(
    period: str = typer.Option("week", "--period", "-p", help="Period (day/week/month)"),
):
    """
    Show resilience metrics.

    Args:
        period: Time period
    """
    asyncio.run(show_resilience_metrics(period))


def show_dashboard():
    """Quick resilience dashboard."""
    console.print("\n[bold cyan]Resilience Dashboard[/bold cyan]\n")

    # Mock data
    console.print("[bold]Overall Health:[/bold] [green]HEALTHY[/green]")
    console.print("[bold]Defense Level:[/bold] GREEN")
    console.print("[bold]Utilization:[/bold] 72.5%")
    console.print("[bold]Critical Index:[/bold] 0.12 (Low Risk)")
    console.print("[bold]Active Alerts:[/bold] 2")


async def show_resilience_status():
    """
    Show comprehensive resilience status.
    """
    api = APIClient()

    try:
        response = api.get("/api/v1/resilience/status")

        status = response.get("status", {})

        # Create status panel
        console.print("\n[bold]Resilience Status Dashboard[/bold]\n")

        # Overall health
        health = status.get("health", "unknown")
        health_color = {
            "healthy": "green",
            "warning": "yellow",
            "critical": "red",
        }.get(health.lower(), "white")

        console.print(f"[bold]Overall Health:[/bold] [{health_color}]{health.upper()}[/{health_color}]")

        # Defense levels
        defense_level = status.get("defense_level", "UNKNOWN")
        console.print(f"[bold]Defense Level:[/bold] {defense_level}")

        # Key metrics
        metrics = status.get("metrics", {})
        console.print(f"\n[bold]Key Metrics:[/bold]")
        console.print(f"  Utilization: {metrics.get('utilization', 0):.1f}%")
        console.print(f"  Critical Index: {metrics.get('critical_index', 0):.2f}")
        console.print(f"  Burnout Rt: {metrics.get('burnout_rt', 0):.2f}")
        console.print(f"  N-1 Viable: {metrics.get('n1_viable', False)}")

        # Alerts
        alerts = status.get("alerts", [])
        if alerts:
            console.print(f"\n[bold yellow]Active Alerts ({len(alerts)}):[/bold yellow]")
            for alert in alerts[:5]:
                console.print(f"  • {alert.get('message')}")

    except Exception as e:
        print_error(f"Failed to get resilience status: {str(e)}")
        raise typer.Exit(1)


async def show_resilience_summary():
    """Show resilience summary."""
    api = APIClient()

    try:
        response = api.get("/api/v1/resilience/summary")

        summary = response.get("summary", {})

        # Create summary table
        table = Table(title="Resilience Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")

        for metric, data in summary.items():
            table.add_row(
                metric,
                str(data.get("value", "-")),
                data.get("status", "-"),
            )

        console.print(table)

    except Exception as e:
        print_error(f"Failed to get summary: {str(e)}")
        raise typer.Exit(1)


async def show_resilience_metrics(period: str):
    """
    Show resilience metrics.

    Args:
        period: Time period
    """
    api = APIClient()

    try:
        response = api.get(
            "/api/v1/resilience/metrics",
            params={"period": period},
        )

        metrics = response.get("metrics", [])

        from cli.utils.output import print_table

        print_table(
            metrics,
            title=f"Resilience Metrics ({period})",
            columns=["timestamp", "utilization", "critical_index", "burnout_rt", "defense_level"],
        )

    except Exception as e:
        print_error(f"Failed to get metrics: {str(e)}")
        raise typer.Exit(1)
