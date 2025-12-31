"""
Pytest fixtures for CLI tests.
"""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Provide a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_api_response(monkeypatch):
    """Mock API responses."""
    def _mock_response(data):
        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise Exception(f"HTTP {self.status_code}")

        return MockResponse(data)

    return _mock_response


@pytest.fixture
def mock_config(monkeypatch):
    """Mock CLI configuration."""
    from cli.config import CLIConfig

    config = CLIConfig(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        api_url="http://localhost:8000",
        output_format="table",
        color_output=False,
        verbose=False,
        profile="test",
    )

    monkeypatch.setattr("cli.config.get_config", lambda: config)
    return config


@pytest.fixture
def mock_auth(monkeypatch):
    """Mock authentication."""
    class MockAuth:
        def get_token(self):
            return "mock_token"

        def get_headers(self):
            return {
                "Authorization": "Bearer mock_token",
                "Content-Type": "application/json",
            }

        def is_authenticated(self):
            return True

    monkeypatch.setattr("cli.utils.auth.AuthManager", lambda: MockAuth())
    return MockAuth()
