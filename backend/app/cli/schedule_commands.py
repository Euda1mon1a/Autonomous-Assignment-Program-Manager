"""Schedule management CLI commands."""

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
from app.scheduling.engine import ScheduleGenerator

logger = get_logger(__name__)


@click.group()
def schedule() -> None:
    """Schedule management commands."""
    pass


@schedule.command()
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--end",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--algorithm",
    type=click.Choice(["greedy", "cp_sat", "pulp", "hybrid"]),
    default="greedy",
    help="Scheduling algorithm to use",
)
@click.option(
    "--timeout",
    type=int,
    default=300,
    help="Solver timeout in seconds",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview schedule without saving",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Save schedule to JSON file",
)
def generate(
    start: datetime,
    end: datetime,
    algorithm: str,
    timeout: int,
    dry_run: bool,
    output: str | None,
) -> None:
    """
    Generate a new schedule for the specified date range.

    This command uses the scheduling engine to create assignments that comply
    with ACGME requirements and institutional policies.

    Example:
        python -m app.cli schedule generate \\
            --start 2025-07-01 --end 2025-09-30 \\
            --algorithm cp_sat --timeout 300
    """
    db = SessionLocal()

    try:
        start_date = start.date()
        end_date = end.date()

        click.echo(f"Generating schedule from {start_date} to {end_date}")
        click.echo(f"Algorithm: {algorithm}")
        click.echo(f"Timeout: {timeout}s")

        if dry_run:
            click.echo("DRY RUN - No changes will be saved")

        # Initialize generator
        generator = ScheduleGenerator(db)

        # Generate schedule
        with click.progressbar(length=100, label="Generating schedule") as bar:
            result = generator.generate(
                start_date=start_date,
                end_date=end_date,
                algorithm=algorithm,
                timeout=timeout,
            )
            bar.update(100)

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("Schedule Generation Complete")
        click.echo("=" * 60)
        click.echo(f"Assignments created: {len(result.assignments)}")
        click.echo(f"Violations: {result.violation_count}")
        click.echo(f"Score: {result.score:.4f}")
        click.echo(f"Generation time: {result.generation_time:.2f}s")

        if result.violations:
            click.echo("\nViolations:")
            for violation in result.violations[:10]:
                click.echo(f"  - {violation}")
            if len(result.violations) > 10:
                click.echo(f"  ... and {len(result.violations) - 10} more")

        # Save to database
        if not dry_run:
            click.echo("\nSaving assignments to database...")
            for assignment in result.assignments:
                db.add(assignment)
            db.commit()
            click.echo("✓ Saved successfully")

        # Export to file
        if output:
            import json

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "algorithm": algorithm,
                "score": result.score,
                "violation_count": result.violation_count,
                "assignments": [
                    {
                        "person_id": a.person_id,
                        "block_id": a.block_id,
                        "rotation_id": a.rotation_id,
                        "date": a.block.date.isoformat() if a.block else None,
                    }
                    for a in result.assignments
                ],
            }

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

            click.echo(f"✓ Exported to {output_path}")

    except Exception as e:
        logger.error(f"Schedule generation failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@schedule.command()
@click.option(
    "--block",
    type=int,
    help="Block number to validate (1-13)",
)
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date for validation range",
)
@click.option(
    "--end",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date for validation range",
)
@click.option(
    "--report",
    is_flag=True,
    help="Generate detailed validation report",
)
def validate(
    block: int | None,
    start: datetime | None,
    end: datetime | None,
    report: bool,
) -> None:
    """
    Validate schedule for ACGME compliance.

    Checks all assignments in the specified date range or block for:
    - 80-hour work week limit
    - 1-in-7 day off requirement
    - Supervision ratios
    - Coverage gaps
    - Constraint violations

    Example:
        python -m app.cli schedule validate --block 10
        python -m app.cli schedule validate --start 2025-07-01 --end 2025-09-30 --report
    """
    from app.scheduling.acgme_validator import ACGMEValidator

    db = SessionLocal()

    try:
        # Determine date range
        if block:
            # Get block dates
            block_obj = db.execute(
                select(Block).where(Block.block_number == block).limit(1)
            ).scalar_one_or_none()

            if not block_obj:
                click.echo(f"Error: Block {block} not found", err=True)
                raise click.Abort()

            start_date = block_obj.date
            # Find last date of block
            last_block = db.execute(
                select(Block)
                .where(Block.block_number == block)
                .order_by(Block.date.desc())
                .limit(1)
            ).scalar_one()
            end_date = last_block.date

        elif start and end:
            start_date = start.date()
            end_date = end.date()
        else:
            # Default to current week
            start_date = date.today()
            end_date = start_date + timedelta(days=7)

        click.echo(f"Validating schedule from {start_date} to {end_date}")

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

        click.echo(f"Loaded {len(assignments)} assignments")

        # Validate
        validator = ACGMEValidator(db)
        violations = validator.validate_assignments(assignments)

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("Validation Results")
        click.echo("=" * 60)

        if not violations:
            click.echo("✓ No violations found - schedule is compliant")
        else:
            click.echo(f"✗ Found {len(violations)} violations:")
            for v in violations:
                click.echo(f"  - {v.severity.upper()}: {v.message}")
                if v.person_id:
                    click.echo(f"    Person: {v.person_id}")
                if v.date:
                    click.echo(f"    Date: {v.date}")

        # Generate report
        if report:
            report_path = Path(f"schedule_validation_{start_date}_{end_date}.md")
            with open(report_path, "w") as f:
                f.write("# Schedule Validation Report\n\n")
                f.write(f"**Date Range:** {start_date} to {end_date}\n")
                f.write(f"**Assignments:** {len(assignments)}\n")
                f.write(f"**Violations:** {len(violations)}\n\n")

                if violations:
                    f.write("## Violations\n\n")
                    for v in violations:
                        f.write(f"- **{v.severity.upper()}**: {v.message}\n")
                        if v.person_id:
                            f.write(f"  - Person: {v.person_id}\n")
                        if v.date:
                            f.write(f"  - Date: {v.date}\n")
                else:
                    f.write("✓ No violations - schedule is ACGME compliant.\n")

            click.echo(f"\n✓ Report saved to {report_path}")

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@schedule.command()
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "excel", "pdf", "ical"]),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output file path",
)
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (defaults to today)",
)
@click.option(
    "--end",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (defaults to start + 90 days)",
)
@click.option(
    "--person",
    type=str,
    help="Filter by person ID or email",
)
def export(
    format: str,
    output: str,
    start: datetime | None,
    end: datetime | None,
    person: str | None,
) -> None:
    """
    Export schedule to various formats.

    Supports exporting to JSON, CSV, Excel, PDF, and iCal formats.

    Example:
        python -m app.cli schedule export --format pdf --output schedule.pdf
        python -m app.cli schedule export --format ical --output schedule.ics --person user@example.com
    """
    db = SessionLocal()

    try:
        start_date = start.date() if start else date.today()
        end_date = end.date() if end else start_date + timedelta(days=90)

        click.echo(f"Exporting schedule from {start_date} to {end_date}")
        click.echo(f"Format: {format}")

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
            # Filter by person
            person_obj = db.execute(
                select(Person).where((Person.id == person) | (Person.email == person))
            ).scalar_one_or_none()

            if not person_obj:
                click.echo(f"Error: Person not found: {person}", err=True)
                raise click.Abort()

            query = query.where(Assignment.person_id == person_obj.id)
            click.echo(f"Filtering for: {person_obj.first_name} {person_obj.last_name}")

        assignments = db.execute(query).scalars().all()
        click.echo(f"Loaded {len(assignments)} assignments")

        # Export based on format
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            import json

            data = [
                {
                    "person": f"{a.person.first_name} {a.person.last_name}",
                    "person_id": a.person_id,
                    "date": a.block.date.isoformat(),
                    "session": a.block.session,
                    "rotation": a.rotation.name if a.rotation else None,
                }
                for a in assignments
            ]

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        elif format == "csv":
            import csv

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Person", "Date", "Session", "Rotation", "Person ID"])

                for a in assignments:
                    writer.writerow(
                        [
                            f"{a.person.first_name} {a.person.last_name}",
                            a.block.date.isoformat(),
                            a.block.session,
                            a.rotation.name if a.rotation else "",
                            a.person_id,
                        ]
                    )

        elif format == "excel":
            try:
                import pandas as pd

                data = {
                    "Person": [
                        f"{a.person.first_name} {a.person.last_name}"
                        for a in assignments
                    ],
                    "Date": [a.block.date for a in assignments],
                    "Session": [a.block.session for a in assignments],
                    "Rotation": [
                        a.rotation.name if a.rotation else "" for a in assignments
                    ],
                }

                df = pd.DataFrame(data)
                df.to_excel(output_path, index=False)

            except ImportError:
                click.echo(
                    "Error: pandas and openpyxl required for Excel export",
                    err=True,
                )
                click.echo("Install with: pip install pandas openpyxl")
                raise click.Abort()

        elif format == "pdf":
            click.echo("PDF export not yet implemented", err=True)
            raise click.Abort()

        elif format == "ical":
            from icalendar import Calendar, Event

            cal = Calendar()
            cal.add("prodid", "-//Residency Scheduler//EN")
            cal.add("version", "2.0")

            for a in assignments:
                event = Event()
                event.add(
                    "summary",
                    f"{a.rotation.name if a.rotation else 'Assignment'}",
                )
                event.add("dtstart", a.block.date)
                event.add("dtend", a.block.date + timedelta(days=1))
                event.add(
                    "description",
                    f"Person: {a.person.first_name} {a.person.last_name}",
                )
                cal.add_component(event)

            with open(output_path, "wb") as f:
                f.write(cal.to_ical())

        click.echo(f"✓ Exported to {output_path}")

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@schedule.command()
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (defaults to today)",
)
@click.option(
    "--end",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (defaults to start + 90 days)",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm deletion without prompt",
)
def clear(
    start: datetime | None,
    end: datetime | None,
    confirm: bool,
) -> None:
    """
    Clear (delete) all assignments in the specified date range.

    WARNING: This is a destructive operation. Use with caution.

    Example:
        python -m app.cli schedule clear --start 2025-07-01 --end 2025-09-30
    """
    db = SessionLocal()

    try:
        start_date = start.date() if start else date.today()
        end_date = end.date() if end else start_date + timedelta(days=90)

        # Count assignments
        count = (
            db.execute(
                select(Assignment)
                .join(Block)
                .where(Block.date >= start_date)
                .where(Block.date <= end_date)
            )
            .scalars()
            .all()
        )

        count = len(count)

        if count == 0:
            click.echo("No assignments found in the specified range")
            return

        # Confirm
        if not confirm:
            if not click.confirm(
                f"Delete {count} assignments from {start_date} to {end_date}?"
            ):
                click.echo("Aborted")
                return

        # Delete
        db.execute(
            Assignment.__table__.delete().where(
                Assignment.block_id.in_(
                    select(Block.id)
                    .where(Block.date >= start_date)
                    .where(Block.date <= end_date)
                )
            )
        )
        db.commit()

        click.echo(f"✓ Deleted {count} assignments")

    except Exception as e:
        logger.error(f"Clear failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()
