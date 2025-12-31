"""
CLI authentication utilities.

Handles:
- API token management
- Session persistence
- Token refresh
- Authentication headers
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

import httpx
from rich.console import Console

from cli.config import get_config_dir

console = Console()


class AuthManager:
    """Manage CLI authentication and API tokens."""

    def __init__(self):
        """Initialize auth manager."""
        self.config_dir = get_config_dir()
        self.token_file = self.config_dir / "token.json"

    def login(self, email: str, password: str, api_url: str) -> bool:
        """
        Authenticate with API and store token.

        Args:
            email: User email
            password: User password
            api_url: API base URL

        Returns:
            True if login successful, False otherwise
        """
        try:
            response = httpx.post(
                f"{api_url}/api/v1/auth/login",
                data={"username": email, "password": password},
            )

            if response.status_code == 200:
                data = response.json()
                token_data = {
                    "access_token": data["access_token"],
                    "token_type": data.get("token_type", "bearer"),
                    "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                    "email": email,
                }

                self._save_token(token_data)
                console.print("[green]Login successful[/green]")
                return True
            else:
                console.print(f"[red]Login failed: {response.text}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]Login error: {str(e)}[/red]")
            return False

    def logout(self) -> None:
        """Remove stored authentication token."""
        if self.token_file.exists():
            self.token_file.unlink()
            console.print("[green]Logged out successfully[/green]")
        else:
            console.print("[yellow]No active session[/yellow]")

    def get_token(self) -> str | None:
        """
        Get stored authentication token.

        Returns:
            Access token if valid, None otherwise
        """
        token_data = self._load_token()

        if not token_data:
            return None

        # Check expiration
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() >= expires_at:
            console.print("[yellow]Token expired. Please login again.[/yellow]")
            self.logout()
            return None

        return token_data["access_token"]

    def get_headers(self) -> dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Headers dictionary with authorization
        """
        token = self.get_token()

        if token:
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

        return {"Content-Type": "application/json"}

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.get_token() is not None

    def get_user_info(self) -> dict[str, str] | None:
        """
        Get stored user information.

        Returns:
            User info dictionary or None
        """
        token_data = self._load_token()

        if token_data:
            return {
                "email": token_data.get("email", ""),
                "expires_at": token_data.get("expires_at", ""),
            }

        return None

    def _save_token(self, token_data: dict[str, str]) -> None:
        """Save token data to file."""
        with open(self.token_file, "w") as f:
            json.dump(token_data, f, indent=2)

        # Secure permissions (owner read/write only)
        self.token_file.chmod(0o600)

    def _load_token(self) -> dict[str, str] | None:
        """Load token data from file."""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None


def require_auth(func):
    """
    Decorator to require authentication for CLI commands.

    Usage:
        @app.command()
        @require_auth
        def protected_command():
            pass
    """

    def wrapper(*args, **kwargs):
        auth = AuthManager()

        if not auth.is_authenticated():
            console.print(
                "[red]Authentication required. Please run 'scheduler-cli login'[/red]"
            )
            raise typer.Exit(1)

        return func(*args, **kwargs)

    return wrapper
