#!/usr/bin/env python3
"""
Database backup script.

Creates PostgreSQL database backups with compression and retention management.

Usage:
    python scripts/ops/backup_database.py
    python scripts/ops/backup_database.py --output /backups/manual_backup.dump
    python scripts/ops/backup_database.py --retention-days 30
    python scripts/ops/backup_database.py --no-compress
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.core.config import get_settings


def create_backup(
    output_path: Path,
    compress: bool = True,
    verbose: bool = False,
) -> bool:
    """Create database backup."""
    settings = get_settings()

    try:
        # Parse database URL
        parsed = urlparse(settings.DATABASE_URL)

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-F", "c",  # Custom format (required for pg_restore)
            "-f", str(output_path),
        ]

        if compress:
            cmd.extend(["-Z", "9"])  # Maximum compression

        if verbose:
            cmd.append("--verbose")

        cmd.append(parsed.path.lstrip("/"))  # Database name

        # Set password environment variable
        env = {"PGPASSWORD": parsed.password or ""}

        # Run pg_dump
        if verbose:
            print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=not verbose,
            text=True,
        )

        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return False

        # Get file size
        size_mb = output_path.stat().st_size / (1024 * 1024)

        print(f"✓ Backup created: {output_path}")
        print(f"  Size: {size_mb:.2f} MB")

        return True

    except Exception as e:
        print(f"Error creating backup: {e}", file=sys.stderr)
        return False


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> None:
    """Remove backups older than retention period."""
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    removed_count = 0
    removed_size = 0

    for backup_file in backup_dir.glob("backup_*.dump"):
        # Check file modification time
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

        if mtime < cutoff_date:
            size = backup_file.stat().st_size
            backup_file.unlink()
            removed_count += 1
            removed_size += size

    if removed_count > 0:
        removed_mb = removed_size / (1024 * 1024)
        print(f"✓ Removed {removed_count} old backups ({removed_mb:.2f} MB)")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database backup script"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Backup file path (defaults to backups/backup_YYYY-MM-DD_HH-MM-SS.dump)",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("backups"),
        help="Backup directory (default: backups)",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Disable compression",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Keep backups for N days (default: 30)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    try:
        # Determine output file
        if args.output:
            output_path = args.output
            backup_dir = output_path.parent
        else:
            backup_dir = args.backup_dir
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = backup_dir / f"backup_{timestamp}.dump"

        # Create backup directory
        backup_dir.mkdir(parents=True, exist_ok=True)

        print(f"Creating database backup...")

        # Create backup
        success = create_backup(
            output_path=output_path,
            compress=not args.no_compress,
            verbose=args.verbose,
        )

        if not success:
            return 1

        # Cleanup old backups
        if args.retention_days > 0:
            cleanup_old_backups(backup_dir, args.retention_days)

        print("\n✓ Backup complete")
        return 0

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
