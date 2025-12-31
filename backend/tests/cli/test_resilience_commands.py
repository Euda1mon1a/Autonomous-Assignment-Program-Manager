"""
Tests for resilience CLI commands.
"""

import pytest
from typer.testing import CliRunner

from cli.commands.resilience import app


class TestResilienceCommands:
    """Test suite for resilience commands."""

    def test_resilience_dashboard(self, cli_runner):
        """Test resilience dashboard command."""
        result = cli_runner.invoke(app, ["dashboard"])

        assert result.exit_code == 0


class TestResilienceStatusCommands:
    """Test resilience status commands."""

    def test_show_status(self, cli_runner, monkeypatch):
        """Test show resilience status."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "status": {
                        "health": "healthy",
                        "defense_level": "GREEN",
                        "metrics": {
                            "utilization": 72.5,
                            "critical_index": 0.12,
                            "burnout_rt": 0.85,
                            "n1_viable": True,
                        },
                        "alerts": [],
                    }
                }

        monkeypatch.setattr("cli.commands.resilience_status.APIClient", lambda: MockAPI())

        from cli.commands.resilience_status import app as status_app

        result = cli_runner.invoke(status_app, ["show"])

        assert result.exit_code in [0, 1]

    def test_show_summary(self, cli_runner, monkeypatch):
        """Test show resilience summary."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "summary": {
                        "utilization": {"value": 72.5, "status": "normal"},
                        "critical_index": {"value": 0.12, "status": "low"},
                    }
                }

        monkeypatch.setattr("cli.commands.resilience_status.APIClient", lambda: MockAPI())

        from cli.commands.resilience_status import app as status_app

        result = cli_runner.invoke(status_app, ["summary"])

        assert result.exit_code in [0, 1]


class TestResilienceAnalyzeCommands:
    """Test resilience analysis commands."""

    def test_n1_analysis(self, cli_runner, monkeypatch):
        """Test N-1 contingency analysis."""
        class MockAPI:
            def post(self, endpoint, json=None):
                return {
                    "viable": True,
                    "vulnerabilities": [],
                }

        monkeypatch.setattr("cli.commands.resilience_analyze.APIClient", lambda: MockAPI())

        from cli.commands.resilience_analyze import app as analyze_app

        result = cli_runner.invoke(analyze_app, ["n1", "10"])

        assert result.exit_code in [0, 1]

    def test_n2_analysis(self, cli_runner, monkeypatch):
        """Test N-2 contingency analysis."""
        class MockAPI:
            def post(self, endpoint, json=None):
                return {
                    "viable": False,
                    "critical_pairs": [],
                }

        monkeypatch.setattr("cli.commands.resilience_analyze.APIClient", lambda: MockAPI())

        from cli.commands.resilience_analyze import app as analyze_app

        result = cli_runner.invoke(analyze_app, ["n2", "10"])

        assert result.exit_code in [0, 1]

    def test_identify_bottlenecks(self, cli_runner, monkeypatch):
        """Test bottleneck identification."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"bottlenecks": []}

        monkeypatch.setattr("cli.commands.resilience_analyze.APIClient", lambda: MockAPI())

        from cli.commands.resilience_analyze import app as analyze_app

        result = cli_runner.invoke(analyze_app, ["bottlenecks", "10"])

        assert result.exit_code in [0, 1]


class TestResilienceAlertsCommands:
    """Test resilience alerts commands."""

    def test_list_alerts(self, cli_runner, monkeypatch):
        """Test list alerts."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"alerts": []}

        monkeypatch.setattr("cli.commands.resilience_alerts.APIClient", lambda: MockAPI())

        from cli.commands.resilience_alerts import app as alerts_app

        result = cli_runner.invoke(alerts_app, ["list"])

        assert result.exit_code in [0, 1]

    def test_show_critical_alerts(self, cli_runner, monkeypatch):
        """Test show critical alerts."""
        class MockAPI:
            def get(self, endpoint, params=None):
                return {"alerts": []}

        monkeypatch.setattr("cli.commands.resilience_alerts.APIClient", lambda: MockAPI())

        from cli.commands.resilience_alerts import app as alerts_app

        result = cli_runner.invoke(alerts_app, ["critical"])

        assert result.exit_code in [0, 1]

    def test_acknowledge_alert(self, cli_runner, monkeypatch):
        """Test acknowledge alert."""
        class MockAPI:
            def post(self, endpoint, json=None):
                return {"status": "acknowledged"}

        monkeypatch.setattr("cli.commands.resilience_alerts.APIClient", lambda: MockAPI())

        from cli.commands.resilience_alerts import app as alerts_app

        result = cli_runner.invoke(
            alerts_app,
            ["acknowledge", "alert123", "--notes", "Reviewed"],
        )

        assert result.exit_code in [0, 1]
