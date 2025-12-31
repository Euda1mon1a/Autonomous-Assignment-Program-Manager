"""
User audit log commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_table
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def show(
    user_id: str = typer.Argument(..., help="User ID or email"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum entries"),
    action: str = typer.Option(None, "--action", "-a", help="Filter by action type"),
):
    """
    Show user audit log.

    Args:
        user_id: User ID or email
        limit: Maximum entries
        action: Action filter
    """
    asyncio.run(show_audit_log(user_id, limit, action))


@app.command()
def all(
    limit: int = typer.Option(100, "--limit", "-n", help="Maximum entries"),
    user: str = typer.Option(None, "--user", "-u", help="Filter by user"),
    action: str = typer.Option(None, "--action", "-a", help="Filter by action"),
):
    """
    Show all audit logs.

    Args:
        limit: Maximum entries
        user: User filter
        action: Action filter
    """
    asyncio.run(show_all_audit_logs(limit, user, action))


@app.command()
def export(
    output: str = typer.Argument(..., help="Output file"),
    start_date: str = typer.Option(None, "--start", help="Start date"),
    end_date: str = typer.Option(None, "--end", help="End date"),
):
    """
    Export audit logs to file.

    Args:
        output: Output file path
        start_date: Start date filter
        end_date: End date filter
    """
    asyncio.run(export_audit_logs(output, start_date, end_date))


async def show_audit_log(user_id: str, limit: int, action: str = None):
    """
    Show user audit log.

    Args:
        user_id: User ID
        limit: Limit
        action: Action filter
    """
    api = APIClient()

    try:
        params = {"limit": limit}

        if action:
            params["action"] = action

        response = api.get(f"/api/v1/users/{user_id}/audit", params=params)

        logs = response.get("logs", [])

        if not logs:
            console.print(f"[yellow]No audit logs found for {user_id}[/yellow]")
            return

        print_table(
            logs,
            title=f"Audit Log for {user_id}",
            columns=["timestamp", "action", "details", "ip_address"],
        )

    except Exception as e:
        print_error(f"Failed to get audit log: {str(e)}")
        raise typer.Exit(1)


async def show_all_audit_logs(limit: int, user: str = None, action: str = None):
    """
    Show all audit logs.

    Args:
        limit: Limit
        user: User filter
        action: Action filter
    """
    api = APIClient()

    try:
        params = {"limit": limit}

        if user:
            params["user"] = user
        if action:
            params["action"] = action

        response = api.get("/api/v1/audit", params=params)

        logs = response.get("logs", [])

        if not logs:
            console.print("[yellow]No audit logs found[/yellow]")
            return

        print_table(
            logs,
            title="Audit Logs",
            columns=["timestamp", "user_id", "action", "details", "ip_address"],
        )

    except Exception as e:
        print_error(f"Failed to get audit logs: {str(e)}")
        raise typer.Exit(1)


async def export_audit_logs(output: str, start_date: str = None, end_date: str = None):
    """
    Export audit logs.

    Args:
        output: Output file
        start_date: Start date
        end_date: End date
    """
    api = APIClient()

    try:
        params = {}

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = api.get("/api/v1/audit/export", params=params)

        import json
        from pathlib import Path

        output_path = Path(output)

        with open(output_path, "w") as f:
            json.dump(response, f, indent=2)

        from cli.utils.output import print_success

        print_success(f"Audit logs exported to {output}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        raise typer.Exit(1)
