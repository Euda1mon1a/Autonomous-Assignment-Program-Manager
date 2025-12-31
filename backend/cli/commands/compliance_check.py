"""
Compliance check commands.
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
    block_number: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed violations"
    ),
):
    """
    Check ACGME compliance for a block.

    Args:
        block_number: Block number
        year: Academic year
        detailed: Show details
    """
    asyncio.run(check_block_compliance(block_number, year, detailed))


@app.command()
def person(
    person_id: str = typer.Argument(..., help="Person ID"),
    weeks: int = typer.Option(4, "--weeks", "-w", help="Number of weeks to check"),
):
    """
    Check compliance for a person.

    Args:
        person_id: Person ID
        weeks: Weeks to check
    """
    asyncio.run(check_person_compliance(person_id, weeks))


@app.command()
def hours_80(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Check 80-hour work week rule.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(check_80_hour_rule(block, year))


@app.command()
def one_in_seven(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Check 1-in-7 days off rule.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(check_one_in_seven_rule(block, year))


@app.command()
def supervision(
    block: int = typer.Argument(..., help="Block number"),
    year: int = typer.Option(2024, "--year", "-y", help="Academic year"),
):
    """
    Check supervision ratio requirements.

    Args:
        block: Block number
        year: Academic year
    """
    asyncio.run(check_supervision_ratios(block, year))


async def check_block_compliance(block: int, year: int, detailed: bool):
    """
    Check block compliance.

    Args:
        block: Block number
        year: Academic year
        detailed: Detailed flag
    """
    api = APIClient()

    try:
        console.print(f"\n[bold]Checking ACGME Compliance - Block {block}[/bold]\n")

        response = api.get(
            "/api/v1/compliance/check",
            params={
                "block_number": block,
                "academic_year": year,
                "detailed": detailed,
            },
        )

        compliance_rate = response.get("compliance_rate", 0)
        violations = response.get("violations", [])

        # Display compliance rate
        if compliance_rate >= 95:
            print_success(f"Compliance Rate: {compliance_rate:.1f}%")
        elif compliance_rate >= 85:
            print_warning(f"Compliance Rate: {compliance_rate:.1f}%")
        else:
            print_error(f"Compliance Rate: {compliance_rate:.1f}%")

        # Display violations
        if not violations:
            print_success("No violations found")
            return

        console.print(f"\n[yellow]Found {len(violations)} violations[/yellow]\n")

        if detailed:
            print_table(
                violations,
                title="ACGME Violations",
                columns=[
                    "person_id",
                    "rule",
                    "value",
                    "limit",
                    "severity",
                    "description",
                ],
            )
        else:
            # Summary by rule
            from collections import Counter

            rule_counts = Counter(v["rule"] for v in violations)
            summary = [
                {"rule": rule, "count": count}
                for rule, count in rule_counts.most_common()
            ]

            print_table(summary, title="Violations by Rule", columns=["rule", "count"])

    except Exception as e:
        print_error(f"Compliance check failed: {str(e)}")
        raise typer.Exit(1)


async def check_person_compliance(person_id: str, weeks: int):
    """
    Check person compliance.

    Args:
        person_id: Person ID
        weeks: Weeks to check
    """
    api = APIClient()

    try:
        console.print(f"\n[bold]Checking compliance for {person_id}[/bold]\n")

        response = api.get(
            f"/api/v1/compliance/person/{person_id}",
            params={"weeks": weeks},
        )

        status = response.get("status", "unknown")
        violations = response.get("violations", [])

        if status == "compliant":
            print_success(f"{person_id} is compliant")
        else:
            print_warning(f"{person_id} has compliance issues")

        if violations:
            print_table(
                violations,
                columns=["date", "rule", "value", "limit"],
            )

    except Exception as e:
        print_error(f"Compliance check failed: {str(e)}")
        raise typer.Exit(1)


async def check_80_hour_rule(block: int, year: int):
    """
    Check 80-hour work week rule.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        console.print("\n[bold]80-Hour Work Week Compliance[/bold]\n")

        response = api.get(
            "/api/v1/compliance/80-hour",
            params={"block": block, "year": year},
        )

        violations = response.get("violations", [])

        if not violations:
            print_success("All residents within 80-hour limit")
            return

        print_warning(f"{len(violations)} residents over 80 hours")

        print_table(
            violations,
            title="80-Hour Violations",
            columns=["person_id", "week", "hours_worked", "overage"],
        )

    except Exception as e:
        print_error(f"80-hour check failed: {str(e)}")
        raise typer.Exit(1)


async def check_one_in_seven_rule(block: int, year: int):
    """
    Check 1-in-7 days off rule.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        console.print("\n[bold]1-in-7 Days Off Compliance[/bold]\n")

        response = api.get(
            "/api/v1/compliance/1-in-7",
            params={"block": block, "year": year},
        )

        violations = response.get("violations", [])

        if not violations:
            print_success("All residents have 1 day off per 7 days")
            return

        print_warning(f"{len(violations)} violations of 1-in-7 rule")

        print_table(
            violations,
            title="1-in-7 Violations",
            columns=["person_id", "period", "days_worked", "last_day_off"],
        )

    except Exception as e:
        print_error(f"1-in-7 check failed: {str(e)}")
        raise typer.Exit(1)


async def check_supervision_ratios(block: int, year: int):
    """
    Check supervision ratios.

    Args:
        block: Block number
        year: Academic year
    """
    api = APIClient()

    try:
        console.print("\n[bold]Supervision Ratio Compliance[/bold]\n")

        response = api.get(
            "/api/v1/compliance/supervision",
            params={"block": block, "year": year},
        )

        violations = response.get("violations", [])

        if not violations:
            print_success("All supervision ratios met")
            return

        print_warning(f"{len(violations)} supervision ratio violations")

        print_table(
            violations,
            title="Supervision Violations",
            columns=[
                "rotation",
                "date",
                "residents",
                "faculty",
                "ratio",
                "required_ratio",
            ],
        )

    except Exception as e:
        print_error(f"Supervision check failed: {str(e)}")
        raise typer.Exit(1)
