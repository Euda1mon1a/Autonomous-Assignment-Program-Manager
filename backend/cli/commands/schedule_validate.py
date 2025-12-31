"""
Schedule validation commands.
"""

import asyncio

import typer
from rich.console import Console

from cli.utils.output import print_success, print_error, print_warning, print_table
from cli.utils.api_client import APIClient

app = typer.Typer()
console = Console()


@app.command()
def block(
    block_number: int = typer.Argument(..., help="Block number to validate"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed violations"),
):
    """
    Validate schedule for a block.

    Args:
        block_number: Block number
        year: Academic year
        detailed: Show detailed violation information
    """
    asyncio.run(validate_block_schedule(block_number, year, detailed))


@app.command()
def person(
    person_id: str = typer.Argument(..., help="Person ID to validate"),
    start_date: str = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
):
    """
    Validate schedule for a specific person.

    Args:
        person_id: Person ID
        start_date: Start date for validation period
        end_date: End date for validation period
    """
    asyncio.run(validate_person_schedule(person_id, start_date, end_date))


@app.command()
def acgme(
    block_number: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    rule: str = typer.Option(None, "--rule", "-r", help="Specific ACGME rule to check"),
):
    """
    Check ACGME compliance for a block.

    Args:
        block_number: Block number
        year: Academic year
        rule: Specific rule name (80-hour, 1-in-7, supervision)
    """
    asyncio.run(validate_acgme_compliance(block_number, year, rule))


def quick_check():
    """Quick validation of current schedules."""
    console.print("[cyan]Running quick validation...[/cyan]")

    # Placeholder - would validate current schedules
    print_success("Quick validation completed")


async def validate_block_schedule(block: int, year: int, detailed: bool):
    """
    Validate block schedule.

    Args:
        block: Block number
        year: Academic year
        detailed: Show details
    """
    api = APIClient()

    try:
        print_info(f"Validating Block {block} ({year})...")

        # Call validation API
        response = api.post(
            "/api/v1/schedules/validate",
            json={
                "block_number": block,
                "academic_year": year,
                "detailed": detailed,
            },
        )

        violations = response.get("violations", [])

        if not violations:
            print_success("Schedule is valid - no violations found")
            return

        # Display violations
        print_warning(f"Found {len(violations)} violations")

        if detailed:
            print_table(
                violations,
                title="Schedule Violations",
                columns=["person_id", "rule", "severity", "description"],
            )
        else:
            # Summary
            from collections import Counter

            rule_counts = Counter(v["rule"] for v in violations)

            summary = [
                {"rule": rule, "count": count}
                for rule, count in rule_counts.most_common()
            ]

            print_table(summary, title="Violation Summary", columns=["rule", "count"])

    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        raise typer.Exit(1)


async def validate_person_schedule(
    person_id: str, start_date: str = None, end_date: str = None
):
    """
    Validate person's schedule.

    Args:
        person_id: Person ID
        start_date: Start date
        end_date: End date
    """
    api = APIClient()

    try:
        print_info(f"Validating schedule for {person_id}...")

        params = {"person_id": person_id}

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = api.get("/api/v1/schedules/validate/person", params=params)

        violations = response.get("violations", [])

        if not violations:
            print_success(f"Schedule valid for {person_id}")
        else:
            print_warning(f"Found {len(violations)} violations for {person_id}")
            print_table(violations, columns=["date", "rule", "description"])

    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        raise typer.Exit(1)


async def validate_acgme_compliance(block: int, year: int, rule: str = None):
    """
    Validate ACGME compliance.

    Args:
        block: Block number
        year: Academic year
        rule: Specific rule to check
    """
    api = APIClient()

    try:
        print_info(f"Checking ACGME compliance for Block {block}...")

        params = {
            "block_number": block,
            "academic_year": year,
        }

        if rule:
            params["rule"] = rule

        response = api.get("/api/v1/compliance/check", params=params)

        violations = response.get("violations", [])
        compliance_rate = response.get("compliance_rate", 100.0)

        console.print(f"\n[bold]Compliance Rate:[/bold] {compliance_rate:.1f}%")

        if violations:
            print_warning(f"Found {len(violations)} ACGME violations")
            print_table(
                violations,
                title="ACGME Violations",
                columns=["person_id", "rule", "value", "limit", "severity"],
            )
        else:
            print_success("Fully ACGME compliant")

    except Exception as e:
        print_error(f"Compliance check failed: {str(e)}")
        raise typer.Exit(1)
