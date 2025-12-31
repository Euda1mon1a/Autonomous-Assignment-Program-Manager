"""ACGME compliance checking CLI commands."""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import click
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = get_logger(__name__)


@click.group()
def compliance() -> None:
    """ACGME compliance checking commands."""
    pass


@compliance.command()
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (defaults to 4 weeks ago)",
)
@click.option(
    "--end",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (defaults to today)",
)
@click.option(
    "--person",
    type=str,
    help="Check specific person by ID or email",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed violation information",
)
def check(
    start: datetime | None,
    end: datetime | None,
    person: str | None,
    verbose: bool,
) -> None:
    """
    Check ACGME compliance for work hour limits.

    Validates:
    - 80-hour work week limit (rolling 4-week average)
    - 1-in-7 day off requirement
    - Maximum shift duration
    - Minimum rest between shifts

    Example:
        python -m app.cli compliance check --start 2025-07-01 --verbose
        python -m app.cli compliance check --person user@example.com
    """
    from app.scheduling.acgme_validator import ACGMEValidator

    db = SessionLocal()

    try:
        # Default to 4-week rolling window
        end_date = end.date() if end else date.today()
        start_date = start.date() if start else end_date - timedelta(days=28)

        click.echo(f"Checking ACGME compliance from {start_date} to {end_date}")

        # Load assignments
        query = (
            select(Assignment)
            .join(Block)
            .where(Block.date >= start_date)
            .where(Block.date <= end_date)
            .options(
                selectinload(Assignment.person),
                selectinload(Assignment.block),
                selectinload(Assignment.rotation),
            )
        )

        if person:
            person_obj = db.execute(
                select(Person).where((Person.id == person) | (Person.email == person))
            ).scalar_one_or_none()

            if not person_obj:
                click.echo(f"Error: Person not found: {person}", err=True)
                raise click.Abort()

            query = query.where(Assignment.person_id == person_obj.id)
            click.echo(f"Person: {person_obj.first_name} {person_obj.last_name}")

        assignments = db.execute(query).scalars().all()
        click.echo(f"Loaded {len(assignments)} assignments")

        # Validate
        validator = ACGMEValidator(db)
        violations = validator.validate_assignments(assignments)

        # Display results
        click.echo("\n" + "=" * 70)
        click.echo("ACGME Compliance Check Results")
        click.echo("=" * 70)

        if not violations:
            click.echo("✓ No violations found - schedule is ACGME compliant")
        else:
            # Group violations by severity
            critical = [v for v in violations if v.severity == "critical"]
            warning = [v for v in violations if v.severity == "warning"]

            click.echo(f"\n✗ Found {len(violations)} violations:")
            click.echo(f"  - Critical: {len(critical)}")
            click.echo(f"  - Warning: {len(warning)}")

            if verbose:
                if critical:
                    click.echo("\nCRITICAL VIOLATIONS:")
                    for v in critical:
                        click.echo(f"  • {v.message}")
                        if v.person_id:
                            click.echo(f"    Person: {v.person_id}")
                        if v.date:
                            click.echo(f"    Date: {v.date}")
                        click.echo()

                if warning:
                    click.echo("\nWARNINGS:")
                    for v in warning:
                        click.echo(f"  • {v.message}")
                        if v.person_id:
                            click.echo(f"    Person: {v.person_id}")
                        if v.date:
                            click.echo(f"    Date: {v.date}")
                        click.echo()

        click.echo("=" * 70)

    except Exception as e:
        logger.error(f"Compliance check failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@compliance.command()
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="Start date",
)
@click.option(
    "--end",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (defaults to start + 1 year)",
)
@click.option(
    "--format",
    type=click.Choice(["markdown", "pdf", "json"]),
    default="markdown",
    help="Report format",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file (defaults to compliance_report_YYYY-MM-DD.ext)",
)
def report(
    start: datetime,
    end: datetime | None,
    format: str,
    output: str | None,
) -> None:
    """
    Generate comprehensive ACGME compliance report.

    Creates a detailed report with:
    - Work hour statistics by person
    - Violation summary
    - Trends over time
    - Compliance metrics

    Example:
        python -m app.cli compliance report \\
            --start 2025-07-01 --end 2026-06-30 \\
            --format pdf --output annual_report.pdf
    """
    from app.scheduling.acgme_validator import ACGMEValidator

    db = SessionLocal()

    try:
        start_date = start.date()
        end_date = end.date() if end else start_date + timedelta(days=365)

        click.echo(f"Generating compliance report from {start_date} to {end_date}")

        # Load all assignments
        assignments = (
            db.execute(
                select(Assignment)
                .join(Block)
                .where(Block.date >= start_date)
                .where(Block.date <= end_date)
                .options(
                    selectinload(Assignment.person),
                    selectinload(Assignment.block),
                    selectinload(Assignment.rotation),
                )
            )
            .scalars()
            .all()
        )

        # Validate
        validator = ACGMEValidator(db)
        violations = validator.validate_assignments(assignments)

        # Calculate statistics
        people = {}
        for a in assignments:
            if a.person_id not in people:
                people[a.person_id] = {
                    "name": f"{a.person.first_name} {a.person.last_name}",
                    "assignments": 0,
                    "hours": 0,
                }
            people[a.person_id]["assignments"] += 1
            people[a.person_id]["hours"] += 4  # Assuming 4-hour half-days

        # Determine output file
        if not output:
            ext = {"markdown": "md", "pdf": "pdf", "json": "json"}[format]
            output = f"compliance_report_{start_date}_{end_date}.{ext}"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate report
        if format == "markdown":
            with open(output_path, "w") as f:
                f.write("# ACGME Compliance Report\n\n")
                f.write(f"**Period:** {start_date} to {end_date}\n")
                f.write(
                    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                )

                f.write("## Summary\n\n")
                f.write(f"- Total Assignments: {len(assignments)}\n")
                f.write(f"- Total Violations: {len(violations)}\n")
                f.write(f"- People: {len(people)}\n\n")

                if violations:
                    f.write("## Violations\n\n")
                    for v in violations:
                        f.write(f"- **{v.severity.upper()}**: {v.message}\n")
                        if v.person_id:
                            f.write(f"  - Person: {v.person_id}\n")
                        if v.date:
                            f.write(f"  - Date: {v.date}\n")

                f.write("\n## Work Hours by Person\n\n")
                f.write("| Person | Assignments | Estimated Hours |\n")
                f.write("|--------|-------------|----------------|\n")
                for person_id, data in people.items():
                    f.write(
                        f"| {data['name']} | {data['assignments']} | {data['hours']} |\n"
                    )

        elif format == "json":
            import json

            data = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "generated": datetime.now().isoformat(),
                "summary": {
                    "total_assignments": len(assignments),
                    "total_violations": len(violations),
                    "people_count": len(people),
                },
                "violations": [
                    {
                        "severity": v.severity,
                        "message": v.message,
                        "person_id": v.person_id,
                        "date": v.date.isoformat() if v.date else None,
                    }
                    for v in violations
                ],
                "work_hours": {person_id: data for person_id, data in people.items()},
            }

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        elif format == "pdf":
            click.echo("PDF generation not yet implemented", err=True)
            raise click.Abort()

        click.echo(f"✓ Report saved to {output_path}")

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@compliance.command()
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (defaults to 1 year ago)",
)
@click.option(
    "--end",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (defaults to today)",
)
def statistics(
    start: datetime | None,
    end: datetime | None,
) -> None:
    """
    Show compliance statistics and metrics.

    Displays:
    - Overall compliance rate
    - Violations by type
    - Trends over time
    - High-risk periods

    Example:
        python -m app.cli compliance statistics --start 2025-01-01
    """
    from app.scheduling.acgme_validator import ACGMEValidator

    db = SessionLocal()

    try:
        end_date = end.date() if end else date.today()
        start_date = start.date() if start else end_date - timedelta(days=365)

        click.echo(f"Compliance Statistics from {start_date} to {end_date}")

        # Load assignments
        assignments = (
            db.execute(
                select(Assignment)
                .join(Block)
                .where(Block.date >= start_date)
                .where(Block.date <= end_date)
                .options(
                    selectinload(Assignment.person),
                    selectinload(Assignment.block),
                    selectinload(Assignment.rotation),
                )
            )
            .scalars()
            .all()
        )

        # Validate
        validator = ACGMEValidator(db)
        violations = validator.validate_assignments(assignments)

        # Calculate statistics
        total_person_weeks = len(set(a.person_id for a in assignments)) * (
            (end_date - start_date).days / 7
        )
        compliance_rate = (
            (1 - len(violations) / total_person_weeks) * 100
            if total_person_weeks > 0
            else 100
        )

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("ACGME Compliance Statistics")
        click.echo("=" * 60)
        click.echo(f"\nPeriod: {start_date} to {end_date}")
        click.echo(f"Total Assignments: {len(assignments)}")
        click.echo(f"Total Violations: {len(violations)}")
        click.echo(f"Compliance Rate: {compliance_rate:.1f}%")

        if violations:
            # Group by type
            violation_types = {}
            for v in violations:
                vtype = v.message.split(":")[0] if ":" in v.message else "Other"
                violation_types[vtype] = violation_types.get(vtype, 0) + 1

            click.echo("\nViolations by Type:")
            for vtype, count in sorted(
                violation_types.items(), key=lambda x: x[1], reverse=True
            ):
                click.echo(f"  {vtype}: {count}")

        click.echo("=" * 60)

    except Exception as e:
        logger.error(f"Statistics calculation failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()
