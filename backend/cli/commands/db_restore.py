"""
Database restore commands.

Restore database from backup.
"""

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from cli.config import get_config
from cli.utils.output import print_success, print_error, print_info
from cli.utils.progress import step
from cli.utils.prompts import confirm_dangerous

app = typer.Typer()
console = Console()


@app.command()
def from_file(
    backup_file: Path = typer.Argument(..., help="Backup file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Restore database from backup file.

    WARNING: This will overwrite the current database!

    Args:
        backup_file: Path to backup file
        force: Skip confirmation prompt
    """
    if not backup_file.exists():
        print_error(f"Backup file not found: {backup_file}")
        raise typer.Exit(1)

    # Confirm dangerous operation
    if not force:
        if not confirm_dangerous(
            "restore and OVERWRITE",
            "current database",
            "RESTORE",
        ):
            return

    config = get_config()

    # Parse database URL
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

    print_info(f"Restoring from: {backup_file}")

    # Check if compressed
    is_compressed = backup_file.suffix == ".gz"

    with step("Restoring database"):
        if is_compressed:
            # Decompress and restore
            cmd = f"gunzip -c {backup_file} | psql -h {host} -p {port} -U {user} -d {database}"
            shell = True
        else:
            # Direct restore
            cmd = [
                "psql",
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                database,
                "-f",
                str(backup_file),
            ]
            shell = False

        env = {"PGPASSWORD": password}

        result = subprocess.run(
            cmd,
            shell=shell,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print_success("Database restored successfully")
        else:
            print_error(f"Restore failed: {result.stderr}")
            raise typer.Exit(1)


@app.command()
def from_backup(
    name: str = typer.Argument(..., help="Backup name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Restore database from saved backup.

    Args:
        name: Backup name
        force: Skip confirmation
    """
    from cli.commands.db_backup import get_backup_dir

    backup_dir = get_backup_dir()

    # Try to find backup file
    backup_file = None
    for ext in [".sql", ".sql.gz"]:
        potential_file = backup_dir / f"{name}{ext}"
        if potential_file.exists():
            backup_file = potential_file
            break

    if backup_file is None:
        print_error(f"Backup not found: {name}")
        raise typer.Exit(1)

    # Restore from file
    from_file(backup_file, force=force)


@app.command()
def verify(
    backup_file: Path = typer.Argument(..., help="Backup file to verify"),
):
    """
    Verify backup file integrity.

    Args:
        backup_file: Path to backup file
    """
    if not backup_file.exists():
        print_error(f"Backup file not found: {backup_file}")
        raise typer.Exit(1)

    print_info(f"Verifying backup: {backup_file}")

    # Check if compressed
    is_compressed = backup_file.suffix == ".gz"

    with step("Checking file integrity"):
        if is_compressed:
            # Test gzip integrity
            result = subprocess.run(
                ["gzip", "-t", str(backup_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print_success("Backup file is valid (gzip integrity check passed)")
            else:
                print_error("Backup file is corrupted")
                raise typer.Exit(1)
        else:
            # Basic SQL file check
            try:
                with open(backup_file) as f:
                    content = f.read(1000)  # Read first 1KB

                if "PostgreSQL database dump" in content:
                    print_success("Backup file appears to be a valid PostgreSQL dump")
                else:
                    print_error("Backup file does not appear to be a PostgreSQL dump")
                    raise typer.Exit(1)
            except Exception as e:
                print_error(f"Failed to read backup file: {e}")
                raise typer.Exit(1)
