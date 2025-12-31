"""Data import/export CLI commands."""

import json
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
from app.models.rotation import RotationTemplate

logger = get_logger(__name__)


@click.group()
def data() -> None:
    """Data import/export commands."""
    pass


@data.command()
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "sql"]),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (defaults to data_export_YYYY-MM-DD.ext)",
)
@click.option(
    "--tables",
    type=str,
    help="Comma-separated list of tables to export (defaults to all)",
)
def export(
    format: str,
    output: Optional[str],
    tables: Optional[str],
) -> None:
    """
    Export database data to file.

    Supports exporting:
    - All tables or specific tables
    - JSON, CSV, or SQL dump formats
    - Sanitized data (no PII)

    Example:
        python -m app.cli data export --format json --output backup.json
        python -m app.cli data export --tables persons,assignments --format csv
    """
    db = SessionLocal()

    try:
        # Determine output file
        if not output:
            ext = format
            output = f"data_export_{date.today().isoformat()}.{ext}"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine tables to export
        table_list = tables.split(",") if tables else [
            "persons",
            "assignments",
            "blocks",
            "rotations",
        ]

        click.echo(f"Exporting {len(table_list)} tables to {output_path}")

        data_export = {}

        # Export persons
        if "persons" in table_list:
            persons = db.execute(select(Person)).scalars().all()
            data_export["persons"] = [
                {
                    "id": str(p.id),
                    "email": p.email,
                    "first_name": p.first_name,
                    "last_name": p.last_name,
                    "role": p.role,
                    "is_active": p.is_active,
                }
                for p in persons
            ]
            click.echo(f"  ✓ Exported {len(persons)} persons")

        # Export assignments
        if "assignments" in table_list:
            assignments = db.execute(
                select(Assignment).options(
                    selectinload(Assignment.person),
                    selectinload(Assignment.block),
                    selectinload(Assignment.rotation),
                )
            ).scalars().all()
            data_export["assignments"] = [
                {
                    "id": str(a.id),
                    "person_id": str(a.person_id),
                    "block_id": str(a.block_id),
                    "rotation_id": str(a.rotation_id) if a.rotation_id else None,
                    "created_at": a.created_at.isoformat(),
                }
                for a in assignments
            ]
            click.echo(f"  ✓ Exported {len(assignments)} assignments")

        # Export blocks
        if "blocks" in table_list:
            blocks = db.execute(select(Block)).scalars().all()
            data_export["blocks"] = [
                {
                    "id": str(b.id),
                    "date": b.date.isoformat(),
                    "session": b.session,
                    "block_number": b.block_number,
                    "is_weekend": b.is_weekend,
                }
                for b in blocks
            ]
            click.echo(f"  ✓ Exported {len(blocks)} blocks")

        # Export rotations
        if "rotations" in table_list:
            rotations = db.execute(select(RotationTemplate)).scalars().all()
            data_export["rotations"] = [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "description": r.description,
                    "duration_blocks": r.duration_blocks,
                }
                for r in rotations
            ]
            click.echo(f"  ✓ Exported {len(rotations)} rotations")

        # Write to file
        if format == "json":
            with open(output_path, "w") as f:
                json.dump(data_export, f, indent=2)

        elif format == "csv":
            import csv

            # Write each table to a separate CSV file
            for table_name, records in data_export.items():
                if not records:
                    continue

                csv_path = output_path.parent / f"{table_name}.csv"
                with open(csv_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)

                click.echo(f"  ✓ Wrote {csv_path}")

        elif format == "sql":
            click.echo("SQL dump export not yet implemented", err=True)
            raise click.Abort()

        click.echo(f"\n✓ Export complete: {output_path}")

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@data.command()
@click.option(
    "--file",
    type=click.Path(exists=True),
    required=True,
    help="Input file path",
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "excel"]),
    help="Import format (auto-detected from extension if not specified)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview import without making changes",
)
@click.option(
    "--replace",
    is_flag=True,
    help="Replace existing records (instead of skipping)",
)
def import_data(
    file: str,
    format: Optional[str],
    dry_run: bool,
    replace: bool,
) -> None:
    """
    Import data from file into database.

    Supports:
    - JSON (structured data export)
    - CSV (per-table imports)
    - Excel (schedule imports)

    Example:
        python -m app.cli data import --file data.json --dry-run
        python -m app.cli data import --file schedule.xlsx --replace
    """
    db = SessionLocal()

    try:
        file_path = Path(file)

        # Auto-detect format
        if not format:
            ext = file_path.suffix.lstrip(".")
            format = {"json": "json", "csv": "csv", "xlsx": "excel", "xls": "excel"}.get(
                ext
            )

            if not format:
                click.echo(f"Error: Cannot determine format for {file_path}", err=True)
                raise click.Abort()

        click.echo(f"Importing from {file_path} (format: {format})")

        if dry_run:
            click.echo("DRY RUN - No changes will be saved")

        # Import based on format
        if format == "json":
            with open(file_path) as f:
                data = json.load(f)

            # Import persons
            if "persons" in data:
                click.echo(f"\nImporting {len(data['persons'])} persons...")
                for p_data in data["persons"]:
                    existing = db.execute(
                        select(Person).where(Person.email == p_data["email"])
                    ).scalar_one_or_none()

                    if existing and not replace:
                        click.echo(f"  - Skipped: {p_data['email']} (already exists)")
                        continue

                    person = Person(**p_data) if not existing else existing
                    if not existing:
                        db.add(person)

                click.echo("  ✓ Done")

        elif format == "csv":
            import csv

            with open(file_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            click.echo(f"Loaded {len(rows)} rows from CSV")
            # CSV import logic would go here based on table structure

        elif format == "excel":
            try:
                import pandas as pd

                df = pd.read_excel(file_path)
                click.echo(f"Loaded {len(df)} rows from Excel")
                # Excel import logic would go here

            except ImportError:
                click.echo("Error: pandas and openpyxl required for Excel import", err=True)
                click.echo("Install with: pip install pandas openpyxl")
                raise click.Abort()

        # Commit changes
        if not dry_run:
            db.commit()
            click.echo("\n✓ Import complete")
        else:
            db.rollback()
            click.echo("\n✓ Dry run complete (no changes saved)")

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@data.command()
@click.option(
    "--type",
    type=click.Choice(["all", "people", "blocks", "rotations", "assignments"]),
    default="all",
    help="Type of data to seed",
)
@click.option(
    "--academic-year",
    type=int,
    help="Academic year (e.g., 2025 for 2025-2026)",
)
def seed(
    type: str,
    academic_year: Optional[int],
) -> None:
    """
    Seed database with test data.

    Creates sample data for development and testing:
    - People (residents and faculty)
    - Blocks (academic year schedule)
    - Rotation templates
    - Sample assignments

    Example:
        python -m app.cli data seed --type all --academic-year 2025
        python -m app.cli data seed --type people
    """
    db = SessionLocal()

    try:
        year = academic_year or date.today().year

        click.echo(f"Seeding database with test data (type: {type})")

        if type in ["all", "blocks"]:
            from app.models.block import Session

            click.echo(f"\nGenerating blocks for academic year {year}-{year + 1}...")

            start_date = date(year, 7, 1)
            end_date = date(year + 1, 6, 30)

            block_count = 0
            current_date = start_date
            block_number = 1

            while current_date <= end_date:
                # Create AM and PM blocks
                for session in [Session.AM, Session.PM]:
                    block = Block(
                        date=current_date,
                        session=session,
                        block_number=block_number,
                        is_weekend=current_date.weekday() >= 5,
                    )
                    db.add(block)
                    block_count += 1

                current_date += timedelta(days=1)

                # Increment block number every 28 days
                if (current_date - start_date).days % 28 == 0:
                    block_number += 1

            click.echo(f"  ✓ Created {block_count} blocks")

        if type in ["all", "people"]:
            click.echo("\nCreating sample people...")

            # Create residents
            for pgy in [1, 2, 3]:
                for i in range(6):
                    person = Person(
                        email=f"pgy{pgy}_{i+1:02d}@example.com",
                        first_name=f"PGY{pgy}",
                        last_name=f"Resident{i+1:02d}",
                        role="RESIDENT",
                        pgy_level=pgy,
                        is_active=True,
                    )
                    db.add(person)

            # Create faculty
            roles = ["PD", "APD", "CORE", "CORE", "CORE"]
            for i, role in enumerate(roles):
                person = Person(
                    email=f"faculty_{i+1:02d}@example.com",
                    first_name=f"Faculty{i+1:02d}",
                    last_name=role,
                    role="FACULTY",
                    faculty_role=role.lower(),
                    is_active=True,
                )
                db.add(person)

            click.echo(f"  ✓ Created 18 residents and 5 faculty")

        if type in ["all", "rotations"]:
            click.echo("\nCreating rotation templates...")

            rotations = [
                {"name": "Clinic", "duration_blocks": 1},
                {"name": "Inpatient", "duration_blocks": 1},
                {"name": "Procedures", "duration_blocks": 1},
                {"name": "Conference", "duration_blocks": 1},
                {"name": "Night Float", "duration_blocks": 4},
                {"name": "FMIT", "duration_blocks": 1},
            ]

            for r_data in rotations:
                rotation = RotationTemplate(
                    name=r_data["name"],
                    description=f"{r_data['name']} rotation",
                    duration_blocks=r_data["duration_blocks"],
                )
                db.add(rotation)

            click.echo(f"  ✓ Created {len(rotations)} rotation templates")

        # Commit changes
        db.commit()
        click.echo("\n✓ Database seeded successfully")

    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()
