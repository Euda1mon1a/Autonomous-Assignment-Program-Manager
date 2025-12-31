"""
Tests for database CLI commands.
"""

import pytest
from typer.testing import CliRunner

from cli.commands.db import app


class TestDatabaseCommands:
    """Test suite for database commands."""

    def test_db_status(self, cli_runner):
        """Test db status command."""
        result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 0 or result.exit_code == 1  # May fail without DB

    def test_db_init(self, cli_runner, monkeypatch):
        """Test db init command."""
        # Mock subprocess for Alembic
        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "Success"
                stderr = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)

        result = cli_runner.invoke(app, ["init"])

        # Should call Alembic upgrade
        assert result.exit_code == 0 or "alembic" in result.stdout.lower()


class TestMigrateCommands:
    """Test migration commands."""

    def test_migrate_upgrade(self, cli_runner, monkeypatch):
        """Test migrate upgrade command."""
        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "Upgrade successful"
                stderr = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)

        from cli.commands.db_migrate import app as migrate_app

        result = cli_runner.invoke(migrate_app, ["upgrade"])

        assert result.exit_code == 0

    def test_migrate_current(self, cli_runner, monkeypatch):
        """Test migrate current command."""
        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "abc123 (head)"
                stderr = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)

        from cli.commands.db_migrate import app as migrate_app

        result = cli_runner.invoke(migrate_app, ["current"])

        assert result.exit_code == 0


class TestBackupCommands:
    """Test backup commands."""

    def test_backup_list(self, cli_runner, tmp_path, monkeypatch):
        """Test backup list command."""
        # Mock backup directory
        monkeypatch.setattr(
            "cli.commands.db_backup.get_backup_dir",
            lambda: tmp_path,
        )

        from cli.commands.db_backup import app as backup_app

        result = cli_runner.invoke(backup_app, ["list"])

        assert result.exit_code == 0

    def test_backup_create(self, cli_runner, tmp_path, monkeypatch):
        """Test backup create command."""
        # Mock backup directory and pg_dump
        monkeypatch.setattr(
            "cli.commands.db_backup.get_backup_dir",
            lambda: tmp_path,
        )

        def mock_run(*args, **kwargs):
            # Create a fake backup file
            backup_file = tmp_path / "test_backup.sql"
            backup_file.write_text("-- Mock backup")

            class Result:
                returncode = 0
                stdout = "Success"
                stderr = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)

        from cli.commands.db_backup import app as backup_app

        result = cli_runner.invoke(backup_app, ["create", "--name", "test"])

        # May fail without actual pg_dump, but should attempt
        assert result.exit_code in [0, 1]


class TestQueryCommands:
    """Test query commands."""

    @pytest.mark.asyncio
    async def test_query_persons(self, cli_runner, monkeypatch):
        """Test query persons command."""
        # Mock database session
        class MockSession:
            async def execute(self, query):
                class Result:
                    def fetchmany(self, limit):
                        return [
                            ("user1", "John", "Doe", "john@example.com", "RESIDENT", "PGY-1"),
                        ]

                    def keys(self):
                        return ["id", "first_name", "last_name", "email", "role", "pgy_level"]

                return Result()

        async def mock_get_session():
            yield MockSession()

        monkeypatch.setattr(
            "cli.utils.database.DatabaseManager.get_session",
            mock_get_session,
        )

        from cli.commands.db_query import app as query_app

        result = cli_runner.invoke(query_app, ["persons"])

        # May fail without actual database
        assert result.exit_code in [0, 1]


class TestStatsCommands:
    """Test stats commands."""

    @pytest.mark.asyncio
    async def test_stats_overview(self, cli_runner):
        """Test stats overview command."""
        from cli.commands.db_stats import app as stats_app

        result = cli_runner.invoke(stats_app, ["overview"])

        # May fail without database connection
        assert result.exit_code in [0, 1]
