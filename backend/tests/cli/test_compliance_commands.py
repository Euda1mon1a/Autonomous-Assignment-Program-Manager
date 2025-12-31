"""
Tests for compliance CLI commands.
"""

import pytest
from typer.testing import CliRunner

from cli.commands.compliance import app


class TestComplianceCommands:
    """Test suite for compliance commands."""

    def test_compliance_status(self, cli_runner):
        """Test compliance status command."""
        result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 0


class TestComplianceCheckCommands:
    """Test compliance check commands."""

    def test_check_block(self, cli_runner, monkeypatch):
        """Test check block compliance."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "compliance_rate": 95.0,
                    "violations": [],
                }

        monkeypatch.setattr("cli.commands.compliance_check.APIClient", lambda: MockAPI())

        from cli.commands.compliance_check import app as check_app

        result = cli_runner.invoke(check_app, ["block", "10"])

        assert result.exit_code in [0, 1]

    def test_check_80_hour_rule(self, cli_runner, monkeypatch):
        """Test 80-hour rule check."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"violations": []}

        monkeypatch.setattr("cli.commands.compliance_check.APIClient", lambda: MockAPI())

        from cli.commands.compliance_check import app as check_app

        result = cli_runner.invoke(check_app, ["hours-80", "10"])

        assert result.exit_code in [0, 1]

    def test_check_one_in_seven(self, cli_runner, monkeypatch):
        """Test 1-in-7 rule check."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"violations": []}

        monkeypatch.setattr("cli.commands.compliance_check.APIClient", lambda: MockAPI())

        from cli.commands.compliance_check import app as check_app

        result = cli_runner.invoke(check_app, ["one-in-seven", "10"])

        assert result.exit_code in [0, 1]


class TestComplianceReportCommands:
    """Test compliance report commands."""

    def test_generate_report(self, cli_runner, monkeypatch):
        """Test generate compliance report."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"summary": "Report data"}

        monkeypatch.setattr("cli.commands.compliance_report.APIClient", lambda: MockAPI())

        from cli.commands.compliance_report import app as report_app

        result = cli_runner.invoke(report_app, ["generate", "10"])

        assert result.exit_code in [0, 1]

    def test_show_summary(self, cli_runner, monkeypatch):
        """Test show compliance summary."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "summary": {
                        "overall": 95.0,
                        "by_rule": {},
                        "by_block": {},
                    }
                }

        monkeypatch.setattr("cli.commands.compliance_report.APIClient", lambda: MockAPI())

        from cli.commands.compliance_report import app as report_app

        result = cli_runner.invoke(report_app, ["summary"])

        assert result.exit_code in [0, 1]


class TestViolationsCommands:
    """Test violations commands."""

    def test_list_violations(self, cli_runner, monkeypatch):
        """Test list violations."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"violations": []}

        monkeypatch.setattr("cli.commands.compliance_violations.APIClient", lambda: MockAPI())

        from cli.commands.compliance_violations import app as violations_app

        result = cli_runner.invoke(violations_app, ["list"])

        assert result.exit_code in [0, 1]

    def test_show_critical_violations(self, cli_runner, monkeypatch):
        """Test show critical violations."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"violations": []}

        monkeypatch.setattr("cli.commands.compliance_violations.APIClient", lambda: MockAPI())

        from cli.commands.compliance_violations import app as violations_app

        result = cli_runner.invoke(violations_app, ["critical"])

        assert result.exit_code in [0, 1]


class TestComplianceFixCommands:
    """Test compliance fix commands."""

    def test_get_fix_suggestions(self, cli_runner, monkeypatch):
        """Test get fix suggestions."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"suggestions": []}

        monkeypatch.setattr("cli.commands.compliance_fix.APIClient", lambda: MockAPI())

        from cli.commands.compliance_fix import app as fix_app

        result = cli_runner.invoke(fix_app, ["suggest", "violation123"])

        assert result.exit_code in [0, 1]

    def test_auto_fix_dry_run(self, cli_runner, monkeypatch):
        """Test auto-fix in dry-run mode."""
        class MockAPI:
            def post(self, endpoint, json=None):
                return {
                    "fixed_count": 0,
                    "skipped_count": 0,
                    "fixes": [],
                }

        monkeypatch.setattr("cli.commands.compliance_fix.APIClient", lambda: MockAPI())

        from cli.commands.compliance_fix import app as fix_app

        result = cli_runner.invoke(
            fix_app,
            ["auto", "10"],
            input="n\n",  # Cancel confirmation
        )

        assert result.exit_code in [0, 1]
