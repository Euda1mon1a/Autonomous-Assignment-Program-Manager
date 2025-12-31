"""
Database backup commands.

Create and manage database backups.
"""

import subprocess
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from cli.config import get_config
from cli.utils.output import print_success, print_error, print_info, format_bytes
from cli.utils.progress import step

app = typer.Typer()
console = Console()


def get_backup_dir() -> Path:
    """Get backup directory path."""
    from cli.config import get_config_dir

    backup_dir = get_config_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


@app.command()
def create(
    name: str = typer.Option(None, "--name", "-n", help="Backup name"),
    compress: bool = typer.Option(
        True, "--compress/--no-compress", help="Compress backup"
    ),
):
    """
    Create database backup.

    Args:
        name: Custom backup name (default: timestamp)
        compress: Compress backup file
    """
    if name is None:
        name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    backup_dir = get_backup_dir()
    backup_file = backup_dir / f"{name}.sql"

    if compress:
        backup_file = backup_dir / f"{name}.sql.gz"

    config = get_config()

    # Parse database URL
    # Format: postgresql+asyncpg://user:pass@host:port/database
    db_url = config.database_url.replace("postgresql+asyncpg://", "")
    parts = db_url.split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")
    host_port = host_db[0].split(":")

    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ""
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    database = host_db[1]

    print_info(f"Creating backup: {backup_file.name}")

    with step("Backing up database"):
        # Use pg_dump
        cmd = [
            "pg_dump",
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            database,
            "-F",
            "p",  # Plain text format
        ]

        if compress:
            cmd.extend(["|", "gzip", ">", str(backup_file)])
            shell_cmd = " ".join(cmd)
        else:
            cmd.extend(["-f", str(backup_file)])
            shell_cmd = " ".join(cmd)

        env = {"PGPASSWORD": password}

        result = subprocess.run(
            shell_cmd if compress else cmd,
            shell=compress,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            file_size = backup_file.stat().st_size
            print_success(
                f"Backup created: {backup_file.name} ({format_bytes(file_size)})"
            )
        else:
            print_error(f"Backup failed: {result.stderr}")
            raise typer.Exit(1)


@app.command()
def list():
    """List available backups."""
    from rich.table import Table

    backup_dir = get_backup_dir()
    backups = sorted(
        backup_dir.glob("*.sql*"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not backups:
        console.print("[yellow]No backups found[/yellow]")
        return

    table = Table(title="Available Backups")
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Created", style="yellow")

    for backup in backups:
        stat = backup.stat()
        created = datetime.fromtimestamp(stat.st_mtime)

        table.add_row(
            backup.name,
            format_bytes(stat.st_size),
            created.strftime("%Y-%m-%d %H:%M:%S"),
        )

    console.print(table)


@app.command()
def delete(
    name: str = typer.Argument(..., help="Backup name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Delete a backup.

    Args:
        name: Backup name
        force: Skip confirmation
    """
    backup_dir = get_backup_dir()
    backup_file = backup_dir / name

    if not backup_file.exists():
        print_error(f"Backup not found: {name}")
        raise typer.Exit(1)

    if not force:
        from cli.utils.prompts import confirm

        if not confirm(f"Delete backup {name}?", default=False):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    backup_file.unlink()
    print_success(f"Backup deleted: {name}")


@app.command()
def cleanup(
    keep: int = typer.Option(5, "--keep", "-k", help="Number of backups to keep"),
    days: int = typer.Option(
        30, "--days", "-d", help="Delete backups older than N days"
    ),
):
    """
    Cleanup old backups.

    Args:
        keep: Number of recent backups to keep
        days: Delete backups older than N days
    """
    from datetime import timedelta

    backup_dir = get_backup_dir()
    backups = sorted(
        backup_dir.glob("*.sql*"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    deleted_count = 0
    cutoff_date = datetime.now() - timedelta(days=days)

    for i, backup in enumerate(backups):
        # Keep recent backups
        if i < keep:
            continue

        # Check age
        created = datetime.fromtimestamp(backup.stat().st_mtime)
        if created < cutoff_date:
            backup.unlink()
            deleted_count += 1
            print_info(f"Deleted old backup: {backup.name}")

    if deleted_count > 0:
        print_success(f"Deleted {deleted_count} old backups")
    else:
        print_info("No old backups to delete")
