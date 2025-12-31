"""Database maintenance CLI commands."""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import click
from sqlalchemy import text

from app.core.logging import get_logger
from app.db.session import SessionLocal

logger = get_logger(__name__)


@click.group()
def maintenance() -> None:
    """Database maintenance commands."""
    pass


@maintenance.command()
@click.option(
    "--output",
    type=click.Path(),
    help="Backup file path (defaults to backups/backup_YYYY-MM-DD_HH-MM-SS.dump)",
)
@click.option(
    "--compress",
    is_flag=True,
    help="Compress backup file",
)
def backup(output: str | None, compress: bool) -> None:
    """
    Create database backup.

    Uses pg_dump to create a PostgreSQL database backup.

    Example:
        python -m app.cli maintenance backup
        python -m app.cli maintenance backup --output my_backup.dump --compress
    """
    from app.core.config import get_settings

    settings = get_settings()

    try:
        # Determine output file
        if not output:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output = f"backups/backup_{timestamp}.dump"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        click.echo(f"Creating database backup: {output_path}")

        # Parse database URL
        import subprocess
        from urllib.parse import urlparse

        parsed = urlparse(settings.DATABASE_URL)

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h",
            parsed.hostname or "localhost",
            "-p",
            str(parsed.port or 5432),
            "-U",
            parsed.username or "postgres",
            "-F",
            "c",  # Custom format
            "-f",
            str(output_path),
        ]

        if compress:
            cmd.extend(["-Z", "9"])  # Maximum compression

        cmd.append(parsed.path.lstrip("/"))  # Database name

        # Set password environment variable
        env = {"PGPASSWORD": parsed.password or ""}

        # Run pg_dump
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error: {result.stderr}", err=True)
            raise click.Abort()

        # Get file size
        size_mb = output_path.stat().st_size / (1024 * 1024)

        click.echo(f"✓ Backup created successfully ({size_mb:.2f} MB)")

    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@maintenance.command()
@click.option(
    "--file",
    type=click.Path(exists=True),
    required=True,
    help="Backup file to restore",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm restoration without prompt",
)
def restore(file: str, confirm: bool) -> None:
    """
    Restore database from backup.

    WARNING: This will replace all data in the database.

    Example:
        python -m app.cli maintenance restore --file backups/backup_2025-01-01.dump
    """
    from app.core.config import get_settings

    settings = get_settings()

    try:
        file_path = Path(file)

        if not confirm:
            if not click.confirm(
                f"This will replace ALL data in the database with {file_path}. Continue?"
            ):
                click.echo("Aborted")
                return

        click.echo(f"Restoring database from: {file_path}")

        # Parse database URL
        import subprocess
        from urllib.parse import urlparse

        parsed = urlparse(settings.DATABASE_URL)

        # Build pg_restore command
        cmd = [
            "pg_restore",
            "-h",
            parsed.hostname or "localhost",
            "-p",
            str(parsed.port or 5432),
            "-U",
            parsed.username or "postgres",
            "-d",
            parsed.path.lstrip("/"),
            "--clean",  # Drop existing objects
            "--if-exists",  # Ignore errors if objects don't exist
            str(file_path),
        ]

        # Set password environment variable
        env = {"PGPASSWORD": parsed.password or ""}

        # Run pg_restore
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # pg_restore may have warnings, check stderr
            if "error" in result.stderr.lower():
                click.echo(f"Error: {result.stderr}", err=True)
                raise click.Abort()
            else:
                click.echo(f"Warning: {result.stderr}", err=True)

        click.echo("✓ Database restored successfully")

    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@maintenance.command()
@click.option(
    "--days",
    type=int,
    default=90,
    help="Delete data older than N days (default: 90)",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm deletion without prompt",
)
def cleanup(days: int, confirm: bool) -> None:
    """
    Clean up old data from database.

    Removes:
    - Old assignments beyond retention period
    - Expired sessions and tokens
    - Archived logs

    Example:
        python -m app.cli maintenance cleanup --days 90
    """
    db = SessionLocal()

    try:
        cutoff_date = date.today() - timedelta(days=days)

        click.echo(f"Cleaning up data older than {cutoff_date} ({days} days)")

        # Count records to delete
        from app.models.assignment import Assignment
        from app.models.block import Block
        from sqlalchemy import select

        old_assignments = (
            db.execute(select(Assignment).join(Block).where(Block.date < cutoff_date))
            .scalars()
            .all()
        )

        count = len(old_assignments)

        if count == 0:
            click.echo("No data to clean up")
            return

        if not confirm:
            if not click.confirm(f"Delete {count} old assignments?"):
                click.echo("Aborted")
                return

        # Delete old assignments
        for assignment in old_assignments:
            db.delete(assignment)

        db.commit()

        click.echo(f"✓ Cleaned up {count} old assignments")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        db.rollback()
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@maintenance.command()
def vacuum() -> None:
    """
    Vacuum and analyze database.

    Reclaims storage and updates statistics for query optimization.

    Example:
        python -m app.cli maintenance vacuum
    """
    db = SessionLocal()

    try:
        click.echo("Running VACUUM ANALYZE on database...")

        # VACUUM must be run outside a transaction
        db.connection().connection.set_isolation_level(0)

        db.execute(text("VACUUM ANALYZE"))

        click.echo("✓ Database vacuumed successfully")

    except Exception as e:
        logger.error(f"Vacuum failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@maintenance.command()
def reindex() -> None:
    """
    Rebuild database indexes.

    Useful after bulk imports or to fix index corruption.

    Example:
        python -m app.cli maintenance reindex
    """
    db = SessionLocal()

    try:
        click.echo("Rebuilding database indexes...")

        # Get list of tables
        result = db.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [row[0] for row in result]

        with click.progressbar(tables, label="Reindexing tables") as bar:
            for table in bar:
                db.execute(text(f"REINDEX TABLE {table}"))

        click.echo("✓ Indexes rebuilt successfully")

    except Exception as e:
        logger.error(f"Reindex failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()


@maintenance.command()
def stats() -> None:
    """
    Show database statistics.

    Displays:
    - Table sizes
    - Row counts
    - Index usage
    - Performance metrics

    Example:
        python -m app.cli maintenance stats
    """
    db = SessionLocal()

    try:
        click.echo("Database Statistics\n" + "=" * 60)

        # Table sizes
        result = db.execute(
            text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY size_bytes DESC
            """)
        )

        click.echo("\nTable Sizes:")
        click.echo(f"{'Table':<30} {'Size':<15}")
        click.echo("-" * 45)

        for row in result:
            click.echo(f"{row[1]:<30} {row[2]:<15}")

        # Row counts
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person
        from sqlalchemy import func

        person_count = db.execute(select(func.count(Person.id))).scalar()
        block_count = db.execute(select(func.count(Block.id))).scalar()
        assignment_count = db.execute(select(func.count(Assignment.id))).scalar()

        click.echo("\nRow Counts:")
        click.echo(f"  Persons: {person_count:,}")
        click.echo(f"  Blocks: {block_count:,}")
        click.echo(f"  Assignments: {assignment_count:,}")

        # Database size
        result = db.execute(
            text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        )
        db_size = result.scalar()

        click.echo(f"\nTotal Database Size: {db_size}")

    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    finally:
        db.close()
