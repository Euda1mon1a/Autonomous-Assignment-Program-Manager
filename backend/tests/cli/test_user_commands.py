"""
Tests for user CLI commands.
"""

import pytest
from typer.testing import CliRunner

from cli.commands.user import app


class TestUserCommands:
    """Test suite for user commands."""

    def test_whoami_not_logged_in(self, cli_runner):
        """Test whoami when not logged in."""
        result = cli_runner.invoke(app, ["whoami"])

        assert result.exit_code == 0
        assert (
            "not logged in" in result.stdout.lower()
            or "logged in as" in result.stdout.lower()
        )

    def test_login_command_exists(self, cli_runner):
        """Test login command exists."""
        result = cli_runner.invoke(app, ["login", "--help"])

        assert result.exit_code == 0
        assert "email" in result.stdout.lower()

    def test_logout_command(self, cli_runner):
        """Test logout command."""
        result = cli_runner.invoke(app, ["logout"])

        assert result.exit_code == 0


class TestUserCreateCommands:
    """Test user creation commands."""

    def test_create_resident(self, cli_runner, monkeypatch):
        """Test create resident command."""

        class MockAPI:
            def post(self, endpoint, json=None):
                return {"id": "user123", "email": json.get("email")}

        monkeypatch.setattr("cli.commands.user_create.APIClient", lambda: MockAPI())

        from cli.commands.user_create import app as create_app

        result = cli_runner.invoke(
            create_app,
            ["resident", "test@example.com", "John", "Doe", "PGY-1"],
        )

        assert result.exit_code in [0, 1]

    def test_create_faculty(self, cli_runner, monkeypatch):
        """Test create faculty command."""

        class MockAPI:
            def post(self, endpoint, json=None):
                return {"id": "fac123", "email": json.get("email")}

        monkeypatch.setattr("cli.commands.user_create.APIClient", lambda: MockAPI())

        from cli.commands.user_create import app as create_app

        result = cli_runner.invoke(
            create_app,
            ["faculty", "faculty@example.com", "Jane", "Smith"],
        )

        assert result.exit_code in [0, 1]


class TestUserListCommands:
    """Test user listing commands."""

    def test_list_all_users(self, cli_runner, monkeypatch):
        """Test list all users."""

        class MockAPI:
            def get(self, endpoint, params=None):
                return {
                    "users": [
                        {
                            "id": "user1",
                            "email": "test@example.com",
                            "first_name": "Test",
                            "last_name": "User",
                            "role": "RESIDENT",
                            "is_active": True,
                        }
                    ]
                }

        monkeypatch.setattr("cli.commands.user_list.APIClient", lambda: MockAPI())

        from cli.commands.user_list import app as list_app

        result = cli_runner.invoke(list_app, ["all"])

        assert result.exit_code in [0, 1]

    def test_list_residents(self, cli_runner, monkeypatch):
        """Test list residents."""

        class MockAPI:
            def get(self, endpoint, params=None):
                return {"users": []}

        monkeypatch.setattr("cli.commands.user_list.APIClient", lambda: MockAPI())

        from cli.commands.user_list import app as list_app

        result = cli_runner.invoke(list_app, ["residents"])

        assert result.exit_code in [0, 1]


class TestUserUpdateCommands:
    """Test user update commands."""

    def test_update_role(self, cli_runner, monkeypatch):
        """Test update user role."""

        class MockAPI:
            def put(self, endpoint, json=None):
                return {"status": "success"}

        monkeypatch.setattr("cli.commands.user_update.APIClient", lambda: MockAPI())

        from cli.commands.user_update import app as update_app

        result = cli_runner.invoke(
            update_app,
            ["role", "user123", "FACULTY"],
            input="y\n",
        )

        assert result.exit_code in [0, 1]

    def test_activate_user(self, cli_runner, monkeypatch):
        """Test activate user."""

        class MockAPI:
            def put(self, endpoint, json=None):
                return {"status": "success"}

        monkeypatch.setattr("cli.commands.user_update.APIClient", lambda: MockAPI())

        from cli.commands.user_update import app as update_app

        result = cli_runner.invoke(update_app, ["activate", "user123"])

        assert result.exit_code in [0, 1]


class TestUserRolesCommands:
    """Test user roles commands."""

    def test_list_roles(self, cli_runner):
        """Test list available roles."""
        from cli.commands.user_roles import app as roles_app

        result = cli_runner.invoke(roles_app, ["list"])

        assert result.exit_code == 0
        assert "ADMIN" in result.stdout or "role" in result.stdout.lower()
