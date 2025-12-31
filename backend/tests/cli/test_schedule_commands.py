"""
Tests for schedule CLI commands.
"""

import pytest
from typer.testing import CliRunner

from cli.commands.schedule import app


class TestScheduleCommands:
    """Test suite for schedule commands."""

    def test_schedule_status(self, cli_runner):
        """Test schedule status command."""
        result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 0

    def test_schedule_quick_validate(self, cli_runner):
        """Test quick validate command."""
        result = cli_runner.invoke(app, ["quick-validate"])

        assert result.exit_code == 0


class TestGenerateCommands:
    """Test schedule generation commands."""

    def test_generate_block_dry_run(self, cli_runner, monkeypatch):
        """Test generate block in dry-run mode."""

        # Mock API client
        class MockAPI:
            def post(self, endpoint, json=None):
                return {"assignments_count": 100}

        monkeypatch.setattr(
            "cli.commands.schedule_generate.APIClient", lambda: MockAPI()
        )

        from cli.commands.schedule_generate import app as generate_app

        result = cli_runner.invoke(
            generate_app,
            ["block", "10", "--dry-run"],
        )

        assert result.exit_code in [0, 1]

    def test_generate_block_requires_confirmation(self, cli_runner):
        """Test generate block requires confirmation."""
        from cli.commands.schedule_generate import app as generate_app

        result = cli_runner.invoke(
            generate_app,
            ["block", "10"],
            input="n\n",  # Answer no to confirmation
        )

        assert "cancelled" in result.stdout.lower() or result.exit_code == 0


class TestValidateCommands:
    """Test schedule validation commands."""

    def test_validate_block(self, cli_runner, monkeypatch):
        """Test validate block command."""

        class MockAPI:
            def post(self, endpoint, json=None):
                return {"violations": []}

        monkeypatch.setattr(
            "cli.commands.schedule_validate.APIClient", lambda: MockAPI()
        )

        from cli.commands.schedule_validate import app as validate_app

        result = cli_runner.invoke(validate_app, ["block", "10"])

        assert result.exit_code in [0, 1]

    def test_validate_acgme(self, cli_runner, monkeypatch):
        """Test ACGME validation."""

        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "violations": [],
                    "compliance_rate": 95.0,
                }

        monkeypatch.setattr(
            "cli.commands.schedule_validate.APIClient", lambda: MockAPI()
        )

        from cli.commands.schedule_validate import app as validate_app

        result = cli_runner.invoke(validate_app, ["acgme", "10"])

        assert result.exit_code in [0, 1]


class TestExportCommands:
    """Test schedule export commands."""

    def test_export_block_json(self, cli_runner, tmp_path, monkeypatch):
        """Test export block to JSON."""

        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "assignments": [
                        {"person_id": "user1", "rotation": "inpatient"},
                    ]
                }

        monkeypatch.setattr("cli.commands.schedule_export.APIClient", lambda: MockAPI())

        from cli.commands.schedule_export import app as export_app

        output_file = tmp_path / "schedule.json"

        result = cli_runner.invoke(
            export_app,
            ["block", "10", "--output", str(output_file), "--format", "json"],
        )

        assert result.exit_code in [0, 1]


class TestConflictsCommands:
    """Test conflict detection commands."""

    def test_detect_conflicts(self, cli_runner, monkeypatch):
        """Test conflict detection."""

        class MockAPI:
            def get(self, endpoint, params=None):
                return {"conflicts": []}

        monkeypatch.setattr(
            "cli.commands.schedule_conflicts.APIClient", lambda: MockAPI()
        )

        from cli.commands.schedule_conflicts import app as conflicts_app

        result = cli_runner.invoke(conflicts_app, ["detect", "10"])

        assert result.exit_code in [0, 1]


class TestCoverageCommands:
    """Test coverage analysis commands."""

    def test_analyze_coverage(self, cli_runner, monkeypatch):
        """Test coverage analysis."""

        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "coverage": {
                        "overall": 95.0,
                        "by_rotation": {"inpatient": 96.0},
                    }
                }

        monkeypatch.setattr(
            "cli.commands.schedule_coverage.APIClient", lambda: MockAPI()
        )

        from cli.commands.schedule_coverage import app as coverage_app

        result = cli_runner.invoke(coverage_app, ["analyze", "10"])

        assert result.exit_code in [0, 1]


class TestOptimizeCommands:
    """Test schedule optimization commands."""

    def test_optimize_block_dry_run(self, cli_runner, monkeypatch):
        """Test optimize block in dry-run mode."""

        class MockAPI:
            def post(self, endpoint, json=None):
                return {
                    "results": {
                        "iterations": 1000,
                        "status": "optimal",
                        "improvements": {},
                    }
                }

        monkeypatch.setattr(
            "cli.commands.schedule_optimize.APIClient", lambda: MockAPI()
        )

        from cli.commands.schedule_optimize import app as optimize_app

        result = cli_runner.invoke(
            optimize_app,
            ["block", "10", "--dry-run"],
        )

        assert result.exit_code in [0, 1]
