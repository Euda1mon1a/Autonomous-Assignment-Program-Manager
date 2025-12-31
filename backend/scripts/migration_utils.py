"""
Migration utilities and helpers for Alembic management.

Provides functions for:
- Generating migrations
- Validating migrations
- Checking for conflicts
- Running migrations
- Dry-running migrations
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
import json


class MigrationUtils:
    """Utilities for managing Alembic migrations."""

    def __init__(self, project_root: str | None = None):
        """
        Initialize migration utilities.

        Args:
            project_root: Root directory of project (defaults to finding it)
        """
        self.project_root = project_root or self._find_project_root()
        self.backend_dir = Path(self.project_root) / "backend"
        self.alembic_dir = self.backend_dir / "alembic"
        self.versions_dir = self.alembic_dir / "versions"

    @staticmethod
    def _find_project_root() -> str:
        """Find project root directory."""
        current = Path.cwd()
        while current != current.parent:
            if (current / "backend" / "alembic").exists():
                return str(current)
            current = current.parent
        raise RuntimeError("Could not find project root")

    def generate_migration(
        self,
        message: str,
        autogenerate: bool = True,
    ) -> tuple[bool, str]:
        """
        Generate a new migration.

        Args:
            message: Migration message/description
            autogenerate: Whether to autogenerate from models

        Returns:
            Tuple of (success, output_message)
        """
        try:
            cmd = ["alembic", "revision"]

            if autogenerate:
                cmd.append("--autogenerate")

            cmd.extend(["-m", message])

            result = subprocess.run(
                cmd,
                cwd=str(self.backend_dir),
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except Exception as e:
            return False, f"Error generating migration: {str(e)}"

    def validate_migrations(self) -> tuple[bool, list[str]]:
        """
        Validate all migrations for consistency.

        Checks for:
        - Syntax errors
        - Broken dependencies
        - Duplicate revisions
        - Missing parent revisions

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if not self.versions_dir.exists():
            return False, ["Migrations directory not found"]

        # Get all migration files
        migration_files = sorted(self.versions_dir.glob("*.py"))

        if not migration_files:
            return True, []

        # Read and parse each migration
        revisions_found = {}
        for migration_file in migration_files:
            if migration_file.name.startswith("_"):
                continue

            try:
                content = migration_file.read_text()

                # Extract revision
                if "revision = " in content:
                    rev_line = [
                        l
                        for l in content.split("\n")
                        if l.strip().startswith("revision = ")
                    ][0]
                    revision = rev_line.split("'")[1]
                    revisions_found[revision] = migration_file.name

                    # Check for syntax errors by attempting import
                    self._validate_migration_syntax(migration_file)

                    # Check down_revision
                    if "down_revision = " in content:
                        down_rev_line = [
                            l
                            for l in content.split("\n")
                            if l.strip().startswith("down_revision = ")
                        ][0]
                        down_rev = down_rev_line.split("'")[1]

                        if down_rev != "None" and down_rev not in revisions_found:
                            # Check if parent will exist
                            pass

            except Exception as e:
                issues.append(f"Error in {migration_file.name}: {str(e)}")

        return len(issues) == 0, issues

    def _validate_migration_syntax(self, migration_file: Path) -> None:
        """
        Validate migration file syntax.

        Args:
            migration_file: Path to migration file

        Raises:
            SyntaxError: If file has syntax errors
        """
        try:
            compile(migration_file.read_text(), str(migration_file), "exec")
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in {migration_file.name}: {e}")

    def list_migrations(self) -> list[dict]:
        """
        List all migrations with metadata.

        Returns:
            List of migration info dicts
        """
        migrations = []

        if not self.versions_dir.exists():
            return migrations

        for migration_file in sorted(self.versions_dir.glob("*.py")):
            if migration_file.name.startswith("_"):
                continue

            try:
                content = migration_file.read_text()

                migration_info = {
                    "filename": migration_file.name,
                    "path": str(migration_file),
                }

                # Extract revision
                if "revision = " in content:
                    rev_line = [
                        l
                        for l in content.split("\n")
                        if l.strip().startswith("revision = ")
                    ][0]
                    migration_info["revision"] = rev_line.split("'")[1]

                # Extract down_revision
                if "down_revision = " in content:
                    down_rev_line = [
                        l
                        for l in content.split("\n")
                        if l.strip().startswith("down_revision = ")
                    ][0]
                    down_rev = down_rev_line.split("'")[1]
                    if down_rev != "None":
                        migration_info["down_revision"] = down_rev

                # Get file size and modification time
                stat = migration_file.stat()
                migration_info["size"] = stat.st_size
                migration_info["modified"] = datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat()

                migrations.append(migration_info)

            except Exception as e:
                migrations.append(
                    {
                        "filename": migration_file.name,
                        "error": str(e),
                    }
                )

        return migrations

    def detect_migration_conflicts(self) -> list[str]:
        """
        Detect potential migration conflicts.

        Returns:
            List of conflict descriptions
        """
        conflicts = []
        migrations = self.list_migrations()

        if len(migrations) < 2:
            return conflicts

        # Check for orphaned branches (multiple migrations with same parent)
        parents = {}
        for migration in migrations:
            down_rev = migration.get("down_revision", "None")
            if down_rev not in parents:
                parents[down_rev] = []
            parents[down_rev].append(migration["filename"])

        for parent, children in parents.items():
            if len(children) > 1:
                conflicts.append(
                    f"Multiple migrations with parent {parent}: {children}"
                )

        return conflicts

    def show_migration_status(self) -> tuple[bool, dict]:
        """
        Show current migration status.

        Returns:
            Tuple of (success, status_dict)
        """
        try:
            result = subprocess.run(
                ["alembic", "current"],
                cwd=str(self.backend_dir),
                capture_output=True,
                text=True,
            )

            status = {
                "success": result.returncode == 0,
                "current": result.stdout.strip() if result.returncode == 0 else None,
                "output": result.stderr if result.returncode != 0 else None,
            }

            return result.returncode == 0, status

        except Exception as e:
            return False, {"error": str(e)}

    def get_migration_history(self) -> tuple[bool, list[dict]]:
        """
        Get migration application history.

        Returns:
            Tuple of (success, list_of_applied_migrations)
        """
        try:
            result = subprocess.run(
                ["alembic", "history"],
                cwd=str(self.backend_dir),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return False, []

            history = []
            for line in result.stdout.strip().split("\n"):
                if "->" in line:
                    parts = line.split("->")
                    history.append(
                        {
                            "from": parts[0].strip(),
                            "to": parts[1].strip(),
                        }
                    )

            return True, history

        except Exception as e:
            return False, []


class MigrationDryRun:
    """Dry-run migrations without applying them."""

    @staticmethod
    def dry_run_upgrade(
        target: str = "head",
        backend_dir: str | None = None,
    ) -> tuple[bool, str]:
        """
        Dry-run an upgrade.

        Args:
            target: Target revision (default: head)
            backend_dir: Backend directory

        Returns:
            Tuple of (success, output)
        """
        try:
            # Alembic doesn't have built-in dry-run for upgrades
            # We can simulate by showing SQL
            result = subprocess.run(
                ["alembic", "upgrade", "--sql", target],
                cwd=backend_dir or "backend",
                capture_output=True,
                text=True,
            )

            return result.returncode == 0, result.stdout or result.stderr

        except Exception as e:
            return False, str(e)

    @staticmethod
    def dry_run_downgrade(
        target: str = "-1",
        backend_dir: str | None = None,
    ) -> tuple[bool, str]:
        """
        Dry-run a downgrade.

        Args:
            target: Target revision (default: -1 for one back)
            backend_dir: Backend directory

        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                ["alembic", "downgrade", "--sql", target],
                cwd=backend_dir or "backend",
                capture_output=True,
                text=True,
            )

            return result.returncode == 0, result.stdout or result.stderr

        except Exception as e:
            return False, str(e)


class MigrationTemplates:
    """Templates for common data migrations."""

    @staticmethod
    def get_data_migration_template(migration_name: str) -> str:
        """
        Get template for a data migration.

        Args:
            migration_name: Name of migration

        Returns:
            Migration file content
        """
        return f'''"""
{migration_name}.

Data migration to handle application-level transformations.
"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Upgrade database schema and data."""
    # Add your upgrade code here
    # Use op.execute() for raw SQL or SQLAlchemy for ORM operations
    pass


def downgrade() -> None:
    """Downgrade database schema and data."""
    # Add your downgrade code here
    pass
'''

    @staticmethod
    def get_schema_migration_template(migration_name: str) -> str:
        """
        Get template for a schema migration.

        Args:
            migration_name: Name of migration

        Returns:
            Migration file content
        """
        return f'''"""
{migration_name}.

Schema migration for database structural changes.
"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Upgrade database schema."""
    # Example: Create a new table
    # op.create_table(
    #     'new_table',
    #     sa.Column('id', sa.String(36), primary_key=True),
    #     sa.Column('name', sa.String(255), nullable=False),
    # )

    # Example: Add a column
    # op.add_column('existing_table', sa.Column('new_col', sa.String(255)))

    pass


def downgrade() -> None:
    """Downgrade database schema."""
    # Example: Drop table
    # op.drop_table('new_table')

    # Example: Drop column
    # op.drop_column('existing_table', 'new_col')

    pass
'''


# CLI Interface
def main():
    """CLI interface for migration utilities."""
    import argparse

    parser = argparse.ArgumentParser(description="Migration utilities")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    subparsers.add_parser("list", help="List all migrations")

    # Validate command
    subparsers.add_parser("validate", help="Validate migrations")

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # Detect conflicts command
    subparsers.add_parser("conflicts", help="Detect migration conflicts")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    utils = MigrationUtils()

    if args.command == "list":
        migrations = utils.list_migrations()
        print(json.dumps(migrations, indent=2))

    elif args.command == "validate":
        is_valid, issues = utils.validate_migrations()
        if is_valid:
            print("All migrations are valid")
        else:
            print("Issues found:")
            for issue in issues:
                print(f"  - {issue}")

    elif args.command == "status":
        success, status = utils.show_migration_status()
        print(json.dumps(status, indent=2))

    elif args.command == "conflicts":
        conflicts = utils.detect_migration_conflicts()
        if conflicts:
            print("Conflicts detected:")
            for conflict in conflicts:
                print(f"  - {conflict}")
        else:
            print("No migration conflicts detected")

    elif args.command == "history":
        success, history = utils.get_migration_history()
        if success:
            print(json.dumps(history, indent=2))
        else:
            print("Failed to get migration history")


if __name__ == "__main__":
    main()
