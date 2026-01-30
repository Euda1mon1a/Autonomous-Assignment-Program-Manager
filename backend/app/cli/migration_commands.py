"""CLI commands for data migration management.

This module provides CLI commands for:
- Creating and executing migrations
- Validating migrations
- Creating snapshots and rollbacks
- Viewing migration history

Usage:
    python -m app.cli.migration_commands create --name "update_emails" --description "Normalize emails"
    python -m app.cli.migration_commands list --status pending
    python -m app.cli.migration_commands execute MIGRATION_ID --dry-run
    python -m app.cli.migration_commands rollback MIGRATION_ID
"""

from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Data migration management commands")
console = Console()


@app.command()
def create(
    name: str = typer.Argument(..., help="Migration name"),
    description: str = typer.Option(
        "", "--description", "-d", help="Migration description"
    ),
    batch_size: int = typer.Option(100, "--batch-size", "-b", help="Records per batch"),
) -> None:
    """
    Create a new migration record.

    Creates a migration record in the database that can be executed later.
    """
    from app.db.session import SessionLocal
    from app.migrations.migrator import DataMigrator

    db = SessionLocal()
    try:
        migrator = DataMigrator(db)
        migration_id = migrator.create_migration(
            name=name, description=description, batch_size=batch_size, created_by="cli"
        )

        console.print(f"[green]Created migration: {migration_id}[/green]")
        console.print(f"Name: {name}")
        console.print(f"Batch size: {batch_size}")

    except Exception as e:
        console.print(f"[red]Error creating migration: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def list(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to show"),
) -> None:
    """
    List migrations with optional filtering.

    Status options: pending, validating, running, completed, failed, rolled_back, dry_run
    """
    from app.db.session import SessionLocal
    from app.migrations.migrator import DataMigrator, MigrationStatus

    db = SessionLocal()
    try:
        migrator = DataMigrator(db)

        # Parse status if provided
        status_filter = None
        if status:
            try:
                status_filter = MigrationStatus(status.lower())
            except ValueError:
                console.print(f"[red]Invalid status: {status}[/red]")
                console.print(
                    "Valid statuses: pending, validating, running, completed, failed, rolled_back, dry_run"
                )
                raise typer.Exit(1)

        migrations = migrator.list_migrations(status=status_filter, limit=limit)

        if not migrations:
            console.print("[yellow]No migrations found.[/yellow]")
            return

            # Create table
        table = Table(title="Migrations")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Progress", justify="right")
        table.add_column("Created", style="blue")

        for migration in migrations:
            # Calculate progress
            if migration.total_records > 0:
                progress_pct = (
                    migration.processed_records / migration.total_records
                ) * 100
                progress = f"{migration.processed_records}/{migration.total_records} ({progress_pct:.1f}%)"
            else:
                progress = "N/A"

                # Format created date
            created = (
                migration.created_at.strftime("%Y-%m-%d %H:%M")
                if migration.created_at
                else "N/A"
            )

            # Color code status
            status_display = migration.status
            if migration.status == "completed":
                status_display = f"[green]{migration.status}[/green]"
            elif migration.status == "failed":
                status_display = f"[red]{migration.status}[/red]"
            elif migration.status == "running":
                status_display = f"[yellow]{migration.status}[/yellow]"

            table.add_row(
                str(migration.id)[:8] + "...",
                migration.name,
                status_display,
                progress,
                created,
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def show(
    migration_id: str = typer.Argument(..., help="Migration ID"),
) -> None:
    """
    Show detailed information about a migration.
    """
    from app.db.session import SessionLocal
    from app.migrations.migrator import DataMigrator

    db = SessionLocal()
    try:
        migrator = DataMigrator(db)

        try:
            mid = UUID(migration_id)
        except ValueError:
            console.print(f"[red]Invalid migration ID: {migration_id}[/red]")
            raise typer.Exit(1)

        migration = migrator.get_migration(mid)
        if not migration:
            console.print(f"[red]Migration not found: {migration_id}[/red]")
            raise typer.Exit(1)

            # Display migration details
        console.print("\n[bold]Migration Details[/bold]")
        console.print(f"ID: {migration.id}")
        console.print(f"Name: {migration.name}")
        console.print(f"Description: {migration.description or 'N/A'}")
        console.print(f"Status: {migration.status}")
        console.print(f"Batch Size: {migration.batch_size}")
        console.print("\n[bold]Progress[/bold]")
        console.print(f"Total Records: {migration.total_records}")
        console.print(f"Processed: {migration.processed_records}")
        console.print(f"Failed: {migration.failed_records}")

        if migration.total_records > 0:
            progress_pct = (migration.processed_records / migration.total_records) * 100
            console.print(f"Progress: {progress_pct:.2f}%")

        console.print("\n[bold]Timestamps[/bold]")
        console.print(f"Created: {migration.created_at}")
        console.print(f"Started: {migration.started_at or 'N/A'}")
        console.print(f"Completed: {migration.completed_at or 'N/A'}")

        if migration.error_message:
            console.print("\n[bold red]Error[/bold red]")
            console.print(f"{migration.error_message}")

    finally:
        db.close()


@app.command()
def progress(
    migration_id: str = typer.Argument(..., help="Migration ID"),
) -> None:
    """
    Show progress information for a migration.
    """
    from app.db.session import SessionLocal
    from app.migrations.migrator import DataMigrator

    db = SessionLocal()
    try:
        migrator = DataMigrator(db)

        try:
            mid = UUID(migration_id)
        except ValueError:
            console.print(f"[red]Invalid migration ID: {migration_id}[/red]")
            raise typer.Exit(1)

        progress_info = migrator.get_migration_progress(mid)

        console.print(f"\n[bold]{progress_info['name']}[/bold]")
        console.print(f"Status: {progress_info['status']}")
        console.print(f"Progress: {progress_info['progress_percentage']}%")
        console.print(
            f"Processed: {progress_info['processed_records']}/{progress_info['total_records']}"
        )
        console.print(f"Failed: {progress_info['failed_records']}")

        if progress_info["error_message"]:
            console.print(f"\n[red]Error: {progress_info['error_message']}[/red]")

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def snapshot(
    migration_id: str = typer.Argument(..., help="Migration ID"),
    table_name: str = typer.Argument(
        ..., help="Table name (e.g., 'people', 'assignments')"
    ),
    model_path: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Model import path (e.g., 'app.models.person:Person')",
    ),
) -> None:
    """
    Create a snapshot of data before migration.

    Example:
        python -m app.cli.migration_commands snapshot MIGRATION_ID people --model app.models.person:Person
    """
    from app.db.session import SessionLocal
    from app.migrations.rollback import RollbackManager, RollbackStrategy

    db = SessionLocal()
    try:
        # Import model class
        if not model_path:
            console.print("[red]Model path is required (use --model)[/red]")
            raise typer.Exit(1)

        try:
            module_path, class_name = model_path.split(":")
            import importlib

            module = importlib.import_module(module_path)
            model_class = getattr(module, class_name)
        except (ValueError, ImportError, AttributeError) as e:
            console.print(f"[red]Error importing model: {e}[/red]")
            raise typer.Exit(1)

            # Parse migration ID
        try:
            mid = UUID(migration_id)
        except ValueError:
            console.print(f"[red]Invalid migration ID: {migration_id}[/red]")
            raise typer.Exit(1)

            # Create snapshot
        rollback_mgr = RollbackManager(db)
        query = db.query(model_class)

        snapshot_id = rollback_mgr.create_snapshot(
            migration_id=mid,
            query=query,
            table_name=table_name,
            strategy=RollbackStrategy.SNAPSHOT,
        )

        console.print(f"[green]Created snapshot: {snapshot_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error creating snapshot: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def rollback(
    migration_id: str = typer.Argument(..., help="Migration ID to rollback"),
    model_path: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Model import path (e.g., 'app.models.person:Person')",
    ),
) -> None:
    """
    Rollback a migration using its most recent snapshot.

    Example:
        python -m app.cli.migration_commands rollback MIGRATION_ID --model app.models.person:Person
    """
    from app.db.session import SessionLocal
    from app.migrations.rollback import RollbackManager

    db = SessionLocal()
    try:
        # Import model class
        if not model_path:
            console.print("[red]Model path is required (use --model)[/red]")
            raise typer.Exit(1)

        try:
            module_path, class_name = model_path.split(":")
            import importlib

            module = importlib.import_module(module_path)
            model_class = getattr(module, class_name)
        except (ValueError, ImportError, AttributeError) as e:
            console.print(f"[red]Error importing model: {e}[/red]")
            raise typer.Exit(1)

            # Parse migration ID
        try:
            mid = UUID(migration_id)
        except ValueError:
            console.print(f"[red]Invalid migration ID: {migration_id}[/red]")
            raise typer.Exit(1)

            # Confirm rollback
        confirm = typer.confirm(
            f"Are you sure you want to rollback migration {migration_id}?"
        )
        if not confirm:
            console.print("[yellow]Rollback cancelled.[/yellow]")
            return

            # Execute rollback
        rollback_mgr = RollbackManager(db)
        result = rollback_mgr.rollback_migration(mid, model_class)

        if result.success:
            console.print("[green]Rollback completed successfully![/green]")
            console.print(f"Records restored: {result.records_restored}")
        else:
            console.print("[red]Rollback failed![/red]")
            console.print(f"Records restored: {result.records_restored}")
            console.print(f"Records failed: {result.records_failed}")
            console.print(f"Error: {result.error_message}")

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error during rollback: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def list_snapshots(
    migration_id: str = typer.Argument(..., help="Migration ID"),
) -> None:
    """
    List snapshots for a migration.
    """
    from app.db.session import SessionLocal
    from app.migrations.rollback import RollbackManager

    db = SessionLocal()
    try:
        try:
            mid = UUID(migration_id)
        except ValueError:
            console.print(f"[red]Invalid migration ID: {migration_id}[/red]")
            raise typer.Exit(1)

        rollback_mgr = RollbackManager(db)
        snapshots = rollback_mgr.list_snapshots(mid)

        if not snapshots:
            console.print("[yellow]No snapshots found for this migration.[/yellow]")
            return

            # Create table
        table = Table(title=f"Snapshots for Migration {migration_id[:8]}...")
        table.add_column("Snapshot ID", style="cyan", no_wrap=True)
        table.add_column("Table", style="magenta")
        table.add_column("Records", justify="right")
        table.add_column("Created", style="blue")

        for snapshot in snapshots:
            table.add_row(
                str(snapshot.id)[:8] + "...",
                snapshot.table_name,
                str(snapshot.record_count),
                snapshot.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def cleanup(
    days: int = typer.Option(
        30, "--days", "-d", help="Delete snapshots older than N days"
    ),
) -> None:
    """
    Clean up old snapshots to save disk space.
    """
    from app.db.session import SessionLocal
    from app.migrations.rollback import RollbackManager

    db = SessionLocal()
    try:
        # Confirm cleanup
        confirm = typer.confirm(f"Delete snapshots older than {days} days?")
        if not confirm:
            console.print("[yellow]Cleanup cancelled.[/yellow]")
            return

        rollback_mgr = RollbackManager(db)
        deleted_count = rollback_mgr.cleanup_old_snapshots(days)

        console.print(f"[green]Cleaned up {deleted_count} snapshots.[/green]")

    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def history(
    migration_id: str = typer.Option(
        None, "--migration", "-m", help="Filter by migration ID"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to show"),
) -> None:
    """
    Show rollback history.
    """
    from app.db.session import SessionLocal
    from app.migrations.rollback import RollbackManager

    db = SessionLocal()
    try:
        # Parse migration ID if provided
        mid = None
        if migration_id:
            try:
                mid = UUID(migration_id)
            except ValueError:
                console.print(f"[red]Invalid migration ID: {migration_id}[/red]")
                raise typer.Exit(1)

        rollback_mgr = RollbackManager(db)
        rollbacks = rollback_mgr.get_rollback_history(migration_id=mid, limit=limit)

        if not rollbacks:
            console.print("[yellow]No rollback history found.[/yellow]")
            return

            # Create table
        table = Table(title="Rollback History")
        table.add_column("Rollback ID", style="cyan", no_wrap=True)
        table.add_column("Migration ID", style="magenta", no_wrap=True)
        table.add_column("Status", style="yellow")
        table.add_column("Records", justify="right")
        table.add_column("Created", style="blue")

        for rollback in rollbacks:
            # Color code status
            status_display = rollback.status
            if rollback.status == "completed":
                status_display = f"[green]{rollback.status}[/green]"
            elif rollback.status == "failed":
                status_display = f"[red]{rollback.status}[/red]"

            table.add_row(
                str(rollback.id)[:8] + "...",
                str(rollback.migration_id)[:8] + "...",
                status_display,
                str(rollback.records_restored),
                rollback.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def stats() -> None:
    """
    Show migration statistics.
    """
    from app.db.session import SessionLocal
    from app.migrations.migrator import MigrationRecord, MigrationStatus
    from app.migrations.rollback import RollbackRecord, SnapshotRecord

    db = SessionLocal()
    try:
        # Migration stats
        total_migrations = db.query(MigrationRecord).count()
        completed_migrations = (
            db.query(MigrationRecord)
            .filter(MigrationRecord.status == MigrationStatus.COMPLETED.value)
            .count()
        )
        failed_migrations = (
            db.query(MigrationRecord)
            .filter(MigrationRecord.status == MigrationStatus.FAILED.value)
            .count()
        )
        running_migrations = (
            db.query(MigrationRecord)
            .filter(MigrationRecord.status == MigrationStatus.RUNNING.value)
            .count()
        )

        # Snapshot stats
        total_snapshots = db.query(SnapshotRecord).count()

        # Rollback stats
        total_rollbacks = db.query(RollbackRecord).count()
        successful_rollbacks = (
            db.query(RollbackRecord)
            .filter(RollbackRecord.status == "completed")
            .count()
        )

        console.print("\n[bold]Migration Statistics[/bold]")
        console.print(f"Total Migrations: {total_migrations}")
        console.print(f"  Completed: {completed_migrations}")
        console.print(f"  Failed: {failed_migrations}")
        console.print(f"  Running: {running_migrations}")

        console.print("\n[bold]Snapshot Statistics[/bold]")
        console.print(f"Total Snapshots: {total_snapshots}")

        console.print("\n[bold]Rollback Statistics[/bold]")
        console.print(f"Total Rollbacks: {total_rollbacks}")
        console.print(f"  Successful: {successful_rollbacks}")

    finally:
        db.close()


if __name__ == "__main__":
    app()
