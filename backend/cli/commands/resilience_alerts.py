"""
Resilience alerts commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_success, print_table
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def list(
    severity: str = typer.Option(None, "--severity", "-s", help="Filter by severity"),
    active: bool = typer.Option(True, "--active/--all", help="Show only active alerts"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum alerts to show"),
):
    """
    List resilience alerts.

    Args:
        severity: Severity filter
        active: Active filter
        limit: Result limit
    """
    asyncio.run(list_alerts(severity, active, limit))


@app.command()
def show(
    alert_id: str = typer.Argument(..., help="Alert ID"),
):
    """
    Show alert details.

    Args:
        alert_id: Alert ID
    """
    asyncio.run(show_alert(alert_id))


@app.command()
def acknowledge(
    alert_id: str = typer.Argument(..., help="Alert ID"),
    notes: str = typer.Option(None, "--notes", "-n", help="Acknowledgement notes"),
):
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert ID
        notes: Notes
    """
    asyncio.run(acknowledge_alert(alert_id, notes))


@app.command()
def critical():
    """Show critical alerts only."""
    asyncio.run(show_critical_alerts())


async def list_alerts(severity: str = None, active: bool = True, limit: int = 50):
    """
    List alerts.

    Args:
        severity: Severity filter
        active: Active filter
        limit: Limit
    """
    api = APIClient()

    try:
        params = {"active": active, "limit": limit}

        if severity:
            params["severity"] = severity

        response = api.get("/api/v1/resilience/alerts", params=params)

        alerts = response.get("alerts", [])

        if not alerts:
            print_success("No alerts")
            return

        print_table(
            alerts,
            title="Resilience Alerts",
            columns=["id", "severity", "type", "message", "created_at", "status"],
        )

    except Exception as e:
        print_error(f"Failed to list alerts: {str(e)}")
        raise typer.Exit(1)


async def show_alert(alert_id: str):
    """
    Show alert details.

    Args:
        alert_id: Alert ID
    """
    api = APIClient()

    try:
        response = api.get(f"/api/v1/resilience/alerts/{alert_id}")

        alert = response.get("alert", {})

        console.print(f"\n[bold]Alert {alert_id}[/bold]\n")
        console.print(f"Severity: {alert.get('severity')}")
        console.print(f"Type: {alert.get('type')}")
        console.print(f"Message: {alert.get('message')}")
        console.print(f"Created: {alert.get('created_at')}")
        console.print(f"Status: {alert.get('status')}")

        if alert.get("details"):
            console.print("\nDetails:")
            console.print(f"  {alert.get('details')}")

        if alert.get("acknowledged_by"):
            console.print(f"\nAcknowledged by: {alert.get('acknowledged_by')}")
            console.print(f"Notes: {alert.get('acknowledgement_notes')}")

    except Exception as e:
        print_error(f"Failed to get alert: {str(e)}")
        raise typer.Exit(1)


async def acknowledge_alert(alert_id: str, notes: str = None):
    """
    Acknowledge alert.

    Args:
        alert_id: Alert ID
        notes: Notes
    """
    api = APIClient()

    try:
        response = api.post(
            f"/api/v1/resilience/alerts/{alert_id}/acknowledge",
            json={"notes": notes},
        )

        print_success(f"Alert {alert_id} acknowledged")

    except Exception as e:
        print_error(f"Failed to acknowledge alert: {str(e)}")
        raise typer.Exit(1)


async def show_critical_alerts():
    """Show critical alerts."""
    api = APIClient()

    try:
        response = api.get(
            "/api/v1/resilience/alerts",
            params={"severity": "critical", "active": True},
        )

        alerts = response.get("alerts", [])

        if not alerts:
            print_success("No critical alerts")
            return

        console.print(f"\n[bold red]Critical Alerts ({len(alerts)})[/bold red]\n")

        print_table(
            alerts,
            title="Critical Alerts",
            columns=["id", "type", "message", "created_at"],
        )

    except Exception as e:
        print_error(f"Failed to get critical alerts: {str(e)}")
        raise typer.Exit(1)
