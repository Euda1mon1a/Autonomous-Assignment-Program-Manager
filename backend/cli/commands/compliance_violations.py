"""
Compliance violations commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_error, print_table, print_success
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def list(
    block: int = typer.Option(None, "--block", "-b", help="Filter by block"),
    rule: str = typer.Option(None, "--rule", "-r", help="Filter by rule"),
    severity: str = typer.Option(None, "--severity", "-s", help="Filter by severity"),
    resolved: bool = typer.Option(False, "--resolved", help="Show resolved violations"),
):
    """
    List compliance violations.

    Args:
        block: Block filter
        rule: Rule filter
        severity: Severity filter
        resolved: Show resolved
    """
    asyncio.run(list_violations(block, rule, severity, resolved))


@app.command()
def show(
    violation_id: str = typer.Argument(..., help="Violation ID"),
):
    """
    Show details of a specific violation.

    Args:
        violation_id: Violation ID
    """
    asyncio.run(show_violation(violation_id))


@app.command()
def resolve(
    violation_id: str = typer.Argument(..., help="Violation ID"),
    resolution: str = typer.Option(
        ..., "--resolution", "-r", prompt=True, help="Resolution notes"
    ),
):
    """
    Mark violation as resolved.

    Args:
        violation_id: Violation ID
        resolution: Resolution notes
    """
    asyncio.run(resolve_violation(violation_id, resolution))


@app.command()
def critical(
    days: int = typer.Option(7, "--days", "-d", help="Days to look back"),
):
    """
    Show critical violations.

    Args:
        days: Days to look back
    """
    asyncio.run(show_critical_violations(days))


async def list_violations(
    block: int = None,
    rule: str = None,
    severity: str = None,
    resolved: bool = False,
):
    """
    List violations.

    Args:
        block: Block filter
        rule: Rule filter
        severity: Severity filter
        resolved: Resolved filter
    """
    api = APIClient()

    try:
        params = {"resolved": resolved}

        if block:
            params["block"] = block
        if rule:
            params["rule"] = rule
        if severity:
            params["severity"] = severity

        response = api.get("/api/v1/compliance/violations", params=params)

        violations = response.get("violations", [])

        if not violations:
            print_success("No violations found")
            return

        print_table(
            violations,
            title="Compliance Violations",
            columns=[
                "id",
                "person_id",
                "rule",
                "severity",
                "detected_at",
                "status",
            ],
        )

    except Exception as e:
        print_error(f"Failed to list violations: {str(e)}")
        raise typer.Exit(1)


async def show_violation(violation_id: str):
    """
    Show violation details.

    Args:
        violation_id: Violation ID
    """
    api = APIClient()

    try:
        response = api.get(f"/api/v1/compliance/violations/{violation_id}")

        violation = response.get("violation", {})

        console.print(f"\n[bold]Violation {violation_id}[/bold]\n")
        console.print(f"Person: {violation.get('person_id')}")
        console.print(f"Rule: {violation.get('rule')}")
        console.print(f"Severity: {violation.get('severity')}")
        console.print(f"Value: {violation.get('value')}")
        console.print(f"Limit: {violation.get('limit')}")
        console.print(f"Detected: {violation.get('detected_at')}")
        console.print(f"Status: {violation.get('status')}")
        console.print("\nDescription:")
        console.print(f"  {violation.get('description')}")

        if violation.get("resolution"):
            console.print("\nResolution:")
            console.print(f"  {violation.get('resolution')}")

    except Exception as e:
        print_error(f"Failed to get violation: {str(e)}")
        raise typer.Exit(1)


async def resolve_violation(violation_id: str, resolution: str):
    """
    Resolve violation.

    Args:
        violation_id: Violation ID
        resolution: Resolution notes
    """
    api = APIClient()

    try:
        response = api.post(
            f"/api/v1/compliance/violations/{violation_id}/resolve",
            json={"resolution": resolution},
        )

        print_success(f"Violation {violation_id} marked as resolved")

    except Exception as e:
        print_error(f"Failed to resolve violation: {str(e)}")
        raise typer.Exit(1)


async def show_critical_violations(days: int):
    """
    Show critical violations.

    Args:
        days: Days to look back
    """
    api = APIClient()

    try:
        response = api.get(
            "/api/v1/compliance/violations/critical",
            params={"days": days},
        )

        violations = response.get("violations", [])

        if not violations:
            print_success("No critical violations")
            return

        console.print(f"\n[red]Found {len(violations)} critical violations[/red]\n")

        print_table(
            violations,
            title="Critical Violations",
            columns=["person_id", "rule", "value", "limit", "detected_at"],
        )

    except Exception as e:
        print_error(f"Failed to get critical violations: {str(e)}")
        raise typer.Exit(1)
